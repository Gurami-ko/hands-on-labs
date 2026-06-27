# App Improvements Plan: Team History & Rules of the Game

## Top-Level Overview

The existing `app.py` is a single-page Streamlit app that predicts football match outcomes. The goal is to extend it with two new features without changing any existing prediction logic:

1. **Team History tab** — a team selector that shows all-time record (W/D/L), total goals scored/conceded, last 5 results, all computed from `results.csv`, plus a short written biography fetched live from the Wikipedia REST API.
2. **Rules of the Game tab** — a static structured guide covering the basic rules of football.

The approach is to wrap the entire app in `st.tabs(["⚽ Predictor", "📖 Team History", "📋 Rules of the Game"])` so all three features live on one page without navigation changes. All existing prediction code moves into the first tab unchanged.

The `results.csv` dataset (columns: `date`, `home_team`, `away_team`, `home_score`, `away_score`, `tournament`, `city`, `country`, `neutral`) is already present at `data/results.csv` and is the sole data source for team stats. The Wikipedia REST API (`https://en.wikipedia.org/api/rest_v1/page/summary/{title}`) requires no API key and returns a plain `extract` field suitable for a bio.

---

## Sub-Tasks

---

### Sub-Task 1: Restructure app.py to use tabs

**Intent**
Wrap the existing predictor UI in a `st.tabs` call so the new Team History and Rules tabs can be added without disrupting the current layout.

**Expected Outcomes**
- `app.py` has three tabs: "⚽ Predictor", "📖 Team History", "📋 Rules of the Game"
- All existing predictor code (inputs, button, results) is inside the first tab and behaves identically to today
- The two new tabs exist but can be empty placeholders for now

**Todo List**
1. Load `results.csv` into a cached DataFrame (using `@st.cache_data`) alongside the existing `load_artifacts()` — this will be reused by the Team History tab
2. Add `tab1, tab2, tab3 = st.tabs([...])` immediately after the title and caption
3. Move all existing predictor UI code into a `with tab1:` block
4. Add empty `with tab2:` and `with tab3:` blocks as placeholders

**Relevant Context**
- File: `hands-on-labs/02_football_lab_june/03_jupyter_notebook/app.py`
- Existing `load_artifacts()` uses `@st.cache_resource` — the new CSV loader should use `@st.cache_data` (appropriate for DataFrames)
- The title `st.title(...)` and `st.caption(...)` should remain outside the tabs so they always appear at the top

**Status:** `[x] done`

---

### Sub-Task 2: Build the Team History tab

**Intent**
Add a team selector to tab 2 that shows all-time W/D/L record, total goals scored/conceded, and last 5 match results — all computed on the fly from `results.csv`. Below the stats, display a short written biography fetched from the Wikipedia REST API.

**Expected Outcomes**
- Tab 2 has a single `st.selectbox` populated with the same `team_names` list used in tab 1
- Below the selector: a metrics row showing Wins, Draws, Losses, Goals Scored, Goals Conceded
- A table showing the last 5 matches (date, opponent, score, result W/D/L)
- A section titled "About [Team]" showing the Wikipedia extract if found, or a friendly "No biography available for this team." message if the API returns no result or errors

**Todo List**
1. Add a `st.selectbox("Select a team", team_names)` in `with tab2:`
2. Filter `matches_df` for rows where `home_team == selected` or `away_team == selected`
3. Compute W/D/L: a win is when the selected team scored more goals; a draw is equal scores; a loss is fewer
4. Compute goals scored (home_score when home, away_score when away) and goals conceded (the reverse)
5. Display wins, draws, losses, goals scored, goals conceded using `st.metric` in a 5-column row
6. Sort the team's matches by date descending, take the first 5, build a display DataFrame with columns: Date, Opponent, Score, Result (W/D/L)
7. Display the last 5 results with `st.table`
8. Define a helper function `fetch_wikipedia_bio(team_name)` that calls `https://en.wikipedia.org/api/rest_v1/page/summary/{team_name} national football team` using `requests.get` with a 5-second timeout; returns the `extract` string on success or `None` on any exception or non-200 response
9. Call the helper, display the bio under an `st.subheader("About [team]")`, or show `st.info("No biography available for this team.")` if `None` is returned
10. Wrap the Wikipedia call in `@st.cache_data(ttl=3600)` to avoid re-fetching on every interaction

**Relevant Context**
- File: `hands-on-labs/02_football_lab_june/03_jupyter_notebook/app.py`
- `results.csv` columns: `date`, `home_team`, `away_team`, `home_score`, `away_score`, `tournament`, `city`, `country`, `neutral`
- Wikipedia REST API endpoint (no auth needed): `https://en.wikipedia.org/api/rest_v1/page/summary/{title}` — returns JSON with an `extract` field
- `requests` is already installed (Task 1 of the notebook)
- `team_names` is already available from Sub-Task 1

**Status:** `[x] done`

---

### Sub-Task 3: Build the Rules of the Game tab

**Intent**
Add a static, well-structured guide to the rules of football in tab 3. No external data or API calls — all content is written inline.

**Expected Outcomes**
- Tab 3 displays a readable guide covering: objective, players & positions, match duration, scoring, restarts, offside, fouls & cards, penalty shootouts
- Content is structured with `st.subheader` / `st.markdown` sections, not a wall of text
- Uses `st.expander` for each rule category so the page stays compact and the user can expand only what they want to read

**Todo List**
1. Add a brief intro line in `with tab3:` (e.g. "New to football? Here are the essential rules.")
2. Create one `st.expander` per rule category, each with a clear heading and 3–5 bullet points written in plain English:
   - **The Objective** — score more goals than the opponent
   - **Players & Positions** — 11 players per side, goalkeeper, outfield positions
   - **Match Duration** — two 45-minute halves, stoppage time, extra time
   - **Scoring** — whole ball must cross the goal line
   - **Restarts** — kick-off, throw-ins, goal kicks, corner kicks, free kicks
   - **Offside Rule** — simplified explanation with the key condition
   - **Fouls & Cards** — yellow/red cards, direct and indirect free kicks
   - **Penalty Shootout** — when it happens and how it works

**Relevant Context**
- File: `hands-on-labs/02_football_lab_june/03_jupyter_notebook/app.py`
- Use only `st.expander`, `st.markdown`, `st.subheader` — no external data or libraries

**Status:** `[x] done`

---

### Sub-Task 4: Add a Task 11 cell to the notebook

**Intent**
The notebook (`bob_generated_code.ipynb`) is the lab's source of truth. The app improvements should be documented there as a new Task 11 so the notebook stays in sync with `app.py`.

**Expected Outcomes**
- `bob_generated_code.ipynb` has a new heading cell "Task 11: Enhance the app with Team History and Rules" followed by a `%%writefile app.py` code cell containing the full updated `app.py`

**Todo List**
1. After all three app.py sub-tasks are complete and verified, add a markdown heading cell and a `%%writefile app.py` code cell at the end of `bob_generated_code.ipynb` containing the complete updated `app.py`

**Relevant Context**
- File: `hands-on-labs/02_football_lab_june/03_jupyter_notebook/bob_generated_code.ipynb`
- Must follow the same pattern as Task 9: first line of the code cell is `%%writefile app.py`, rest is the full file content

**Status:** `[x] done`
