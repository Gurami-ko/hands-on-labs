import streamlit as st
import pandas as pd
import joblib
import requests
from pathlib import Path

st.set_page_config(
    page_title='Soccer 2026 Match Predictor',
    page_icon='⚽',
    layout='centered'
)

@st.cache_resource
def load_artifacts():
    model = joblib.load(Path('models/match_predictor.pkl'))
    team_data = joblib.load(Path('models/team_data.pkl'))
    return model, team_data['team_stats'], team_data['feature_cols']

@st.cache_data
def load_matches():
    return pd.read_csv(Path('data/results.csv'), parse_dates=['date'])

model, team_stats, feature_cols = load_artifacts()
matches_df = load_matches()

st.title('⚽ Soccer 2026 Match Predictor')
st.caption('Predictions based on historical international football results (1872–2026).')

team_names = sorted(team_stats.keys())

tab1, tab2, tab3 = st.tabs(['⚽ Predictor', '📖 Team History', '📋 Rules of the Game'])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        default_a = team_names.index('Brazil') if 'Brazil' in team_names else 0
        team_a = st.selectbox('Team A', team_names, index=default_a)
    with col2:
        default_b = team_names.index('Argentina') if 'Argentina' in team_names else 1
        team_b = st.selectbox('Team B', team_names, index=default_b)

    is_neutral = st.checkbox('Neutral venue', value=True)
    is_major   = st.checkbox('Major tournament (e.g. World Cup)', value=True)

    if st.button('Predict', type='primary', use_container_width=True):
        if team_a == team_b:
            st.error('Please pick two different teams.')
        else:
            a = team_stats[team_a]
            b = team_stats[team_b]

            row = pd.DataFrame([{
                'team_a_winrate':      a['winrate'],
                'team_b_winrate':      b['winrate'],
                'team_a_goal_avg':     a['goal_avg'],
                'team_b_goal_avg':     b['goal_avg'],
                'team_a_recent_form':  a['recent_form'],
                'team_b_recent_form':  b['recent_form'],
                'is_neutral':          int(is_neutral),
                'is_major_tournament': int(is_major),
            }])[feature_cols]

            proba = model.predict_proba(row)[0]
            p_a, p_draw, p_b = float(proba[0]), float(proba[1]), float(proba[2])

            st.subheader('Prediction')
            m1, m2, m3 = st.columns(3)
            m1.metric(f'{team_a} wins', f'{p_a:.1%}')
            m2.metric('Draw',           f'{p_draw:.1%}')
            m3.metric(f'{team_b} wins', f'{p_b:.1%}')

            st.write('')
            st.progress(p_a,    text=f'{team_a} wins: {p_a:.1%}')
            st.progress(p_draw, text=f'Draw: {p_draw:.1%}')
            st.progress(p_b,    text=f'{team_b} wins: {p_b:.1%}')

            st.subheader('Team statistics')
            stats_table = pd.DataFrame({
                'Team':           [team_a, team_b],
                'Win rate':       [f"{a['winrate']:.3f}",      f"{b['winrate']:.3f}"],
                'Avg goals':      [f"{a['goal_avg']:.2f}",     f"{b['goal_avg']:.2f}"],
                'Recent form':    [f"{a['recent_form']:.3f}",  f"{b['recent_form']:.3f}"],
                'Matches played': [a['matches_played'],         b['matches_played']],
            }).set_index('Team')
            st.table(stats_table)

@st.cache_data(ttl=3600)
def fetch_wikipedia_bio(team_name):
    try:
        title = f"{team_name} national football team"
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('extract')
        return None
    except Exception:
        return None

with tab2:
    selected_team = st.selectbox('Select a team', team_names)

    team_matches = matches_df[
        (matches_df['home_team'] == selected_team) |
        (matches_df['away_team'] == selected_team)
    ].copy()

    def classify(row, team):
        if row['home_team'] == team:
            scored, conceded = row['home_score'], row['away_score']
        else:
            scored, conceded = row['away_score'], row['home_score']
        if scored > conceded:
            return 'W', scored, conceded
        elif scored == conceded:
            return 'D', scored, conceded
        else:
            return 'L', scored, conceded

    results_data = team_matches.apply(lambda r: classify(r, selected_team), axis=1)
    team_matches['_result']   = results_data.apply(lambda x: x[0])
    team_matches['_scored']   = results_data.apply(lambda x: x[1])
    team_matches['_conceded'] = results_data.apply(lambda x: x[2])

    wins   = (team_matches['_result'] == 'W').sum()
    draws  = (team_matches['_result'] == 'D').sum()
    losses = (team_matches['_result'] == 'L').sum()
    goals_scored   = int(team_matches['_scored'].sum())
    goals_conceded = int(team_matches['_conceded'].sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Wins',           wins)
    c2.metric('Draws',          draws)
    c3.metric('Losses',         losses)
    c4.metric('Goals Scored',   goals_scored)
    c5.metric('Goals Conceded', goals_conceded)

    st.subheader('Last 5 Results')
    last5 = team_matches.sort_values('date', ascending=False).head(5)

    def build_last5_row(row, team):
        if row['home_team'] == team:
            opponent = row['away_team']
            score    = f"{int(row['home_score'])} – {int(row['away_score'])}"
        else:
            opponent = row['home_team']
            score    = f"{int(row['away_score'])} – {int(row['home_score'])}"
        return pd.Series({
            'Date':     row['date'].strftime('%Y-%m-%d'),
            'Opponent': opponent,
            'Score':    score,
            'Result':   row['_result'],
        })

    last5_display = last5.apply(lambda r: build_last5_row(r, selected_team), axis=1).reset_index(drop=True)
    st.table(last5_display)

    st.subheader(f'About {selected_team}')
    bio = fetch_wikipedia_bio(selected_team)
    if bio:
        st.write(bio)
    else:
        st.info('No biography available for this team.')

with tab3:
    st.write('New to football? Here are the essential rules of the game.')

    with st.expander('🎯 The Objective'):
        st.markdown("""
- The aim is to score more goals than the opposing team by the end of the match.
- A goal is scored when the whole ball crosses the goal line between the posts and under the crossbar.
- The team with the most goals at the end wins. If scores are level it is a draw (in group stages) or the game may go to extra time/penalties (knockout rounds).
        """)

    with st.expander('👥 Players & Positions'):
        st.markdown("""
- Each team fields **11 players**, including one designated **goalkeeper**.
- Common outfield positions: **defenders** (protect their goal), **midfielders** (link defence and attack), **forwards/strikers** (score goals).
- Teams may make up to **5 substitutions** per match (3 in some competitions).
- A team reduced to fewer than 7 players must forfeit the match.
        """)

    with st.expander('⏱️ Match Duration'):
        st.markdown("""
- A standard match consists of **two 45-minute halves** with a 15-minute half-time break.
- The referee adds **stoppage time** at the end of each half to compensate for injuries, substitutions, and delays.
- In knockout competitions, if the score is level after 90 minutes, **extra time** (two 15-minute periods) is played.
- If still level after extra time, the match is decided by a **penalty shootout**.
        """)

    with st.expander('⚽ Scoring'):
        st.markdown("""
- A goal counts when the **entire ball** crosses the goal line between the goalposts and under the crossbar.
- **Own goals** (accidentally scored by a defending player) count for the attacking team.
- Goals scored in open play, from free kicks, penalties, and corners all count equally.
- The Video Assistant Referee (**VAR**) may review goals to check for offside or handball.
        """)

    with st.expander('🔄 Restarts'):
        st.markdown("""
- **Kick-off**: starts each half and restarts play after a goal.
- **Throw-in**: awarded when the ball goes out of play over the sideline — thrown in by the opposing team to the one that last touched it.
- **Goal kick**: awarded to the defending team when the ball crosses the goal line last touched by an attacker.
- **Corner kick**: awarded to the attacking team when the ball crosses the goal line last touched by a defender.
- **Free kick**: awarded after a foul — can be **direct** (shot straight at goal) or **indirect** (must touch another player first).
        """)

    with st.expander('🚩 The Offside Rule'):
        st.markdown("""
- A player is in an **offside position** if they are nearer to the opponent's goal line than both the ball and the **second-to-last defender** at the moment the ball is played to them.
- Being offside is **not an offence by itself** — it only becomes one if the player is actively involved in play.
- A player **cannot be offside** from a goal kick, throw-in, or corner kick.
- VAR uses a line system to check marginal offside calls.
        """)

    with st.expander('🟨🟥 Fouls & Cards'):
        st.markdown("""
- A **foul** is called when a player trips, pushes, holds, or handles the ball illegally.
- **Yellow card** = a formal warning. Two yellow cards in the same match = automatic red card.
- **Red card** = the player is immediately sent off and cannot be replaced — their team plays with 10 players.
- A **straight red** can be given for serious foul play, violent conduct, or denying an obvious goal-scoring opportunity.
- Fouls inside the penalty area result in a **penalty kick**.
        """)

    with st.expander('🥅 Penalty Shootout'):
        st.markdown("""
- Used in **knockout rounds** when the score is still level after extra time.
- Each team nominates 5 players to take turns shooting from the **penalty spot** (11 metres from goal).
- The team that scores the most of their 5 penalties wins.
- If still level after 5 each, it goes to **sudden death** — teams alternate one penalty at a time until one scores and the other misses.
- The goalkeeper must stay on their line until the ball is kicked.
        """)
