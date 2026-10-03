# Project Mental Model

This document explains how Packard Power Rankings fits together at runtime. It is intended as an onboarding map: start here to understand where data enters the system, where calculations happen, and which code owns each responsibility.

## System at a Glance

```text
Browser
  |
  v
React frontend :3000
  |
  | HTTP requests
  v
FastAPI backend :8000 --------------------> MongoDB :27017
  |                                             ^
  | enqueue long-running work                   |
  v                                             | write results
Redis :6379 ------> ARQ worker ------> ranking algorithm

Separate development path:

CSV fixtures ------> tests/isolation/algorithm ------> generated CSV output
```

The public side reads rankings and predictions from MongoDB. Its canonical entry point is `/`; ranking lists use sport-first paths such as `/football/mens/college`, the complete directory is `/teams`, team details are under `/team`, and predictions are under `/predictions`. The admin side lives under `/admin`, loads game data, and starts calculations that update MongoDB. Redis and the ARQ worker keep those calculations out of normal HTTP request processing.

Season archives are filesystem snapshots rather than live MongoDB views. FastAPI writes ranked JSON and self-contained HTML into the shared `archive_data` volume. React reads the JSON through `/api/archives`, while Caddy serves the generated pages directly under `/archive/<year>/`.

See the [season archive mental model](../frontend/public/archive/README.md) for year isolation, overwrite behavior, runtime storage, reset interactions, and recovery considerations.

The AWS Lightsail production topology adds Caddy in front of the same logical services:

```text
Internet :443 -> Caddy -> React static files
                       `-> /api -> FastAPI -> MongoDB
                                           `-> Redis -> ARQ worker
```

Only Caddy publishes production host ports. The database and queue remain reachable only over the Docker network. See the [Lightsail runbook](../deploy/lightsail/README.md) for provisioning and operations.

## Runtime Services

[`docker-compose.yml`](../docker-compose.yml) starts five services:

| Service | Responsibility | Port |
| --- | --- | --- |
| `frontend` | React and CoreUI browser application | `3000` |
| `backend` | FastAPI routes, validation, and application services | `8000` |
| `db` | MongoDB application storage | `27017` |
| `redis` | Queue and job-state storage | `6379` |
| `arq_worker` | Executes ranking and z-score jobs from Redis | None exposed |

The backend and worker use the same Python image and source tree. The difference is their command: the backend starts Uvicorn, while the worker starts `api.service.tasks.WorkerSettings`.

## The Organizing Key

Most application operations are scoped by a three-part key:

```python
(sport_type, gender, level)
```

For example:

```python
("football", "mens", "high_school")
```

The frontend sends these values as query parameters. The routers convert them into a tuple, and the service layer uses that tuple to select the correct MongoDB document and algorithm settings.

[`backend/api/config/constants.py`](../backend/api/config/constants.py) maps each supported key to:

- A MongoDB document `_id`
- A ranking sensitivity value, `k_value`
- Home-field advantage
- Average game score
- Game-set length

This key is the thread connecting the user interface, API, database, and ranking algorithm.

## Code Ownership

```text
frontend/src/
|-- api.js                    Shared Axios client and auth header
|-- routes.js                 Browser route definitions
|-- store.js                  Selected sport/gender/level and admin state
|-- components/               Shared navigation and page chrome
|-- layout/                   Main CoreUI application shell
|-- services/                 Authentication helpers
`-- views/                    Public and admin screens

backend/api/
|-- main.py                   FastAPI application entry point
|-- routers/                  HTTP endpoints and request dependencies
|-- schemas/                  Pydantic request/response definitions
|-- service/                  Business logic and MongoDB access
|-- config/                   Dataset IDs and sport-specific constants
`-- utils/algorithm/          Production ranking pipeline

tests/isolation/algorithm/
|-- run.py                    Standalone pipeline entry point
|-- upload.py                 CSV loading and validation
|-- data_cleaning.py          Input normalization
|-- data_enrichment.py        Adds current rankings and constants
|-- main.py                   Ranking calculations
|-- output.py                 CSV output
`-- *.csv                     Input fixtures and expected/generated results
```

The intended backend dependency direction is:

```text
router -> service -> database or algorithm
                    ^
schema/config -------|
```

Routers define the HTTP contract. Services own application behavior. Algorithm modules own calculation details.

## Application Startup

1. MongoDB starts and stores its files under `data/db/`.
2. Redis starts and passes its health check.
3. FastAPI starts from `api.main:app` and registers both route modules.
4. The ARQ worker starts and registers the algorithm, z-score, quiet-period dispatcher, and weekly catch-up tasks.
5. React starts and sends API requests to `http://localhost:8000`.

In production, React is compiled with `/api` as its API base URL. Caddy strips that external prefix before proxying to FastAPI, while `ROOT_PATH=/api` keeps generated documentation URLs correct.

[`backend/api/main.py`](../backend/api/main.py) does not add route prefixes, so endpoints such as `/teams/`, `/token/`, and `/run_algorithm/{iterations}` all live directly under the backend root URL.

## Public Read Workflow

The public application has three main data paths.

### Team Rankings

```text
Teams page
  -> GET /teams/?sport_type=...&gender=...&level=...
  -> user_routes.list_teams
  -> UsersServices.retrieve_sports_info
  -> sports_data.temp2
  -> searchable/sortable rankings table
```

The list response contains identity, current power ranking, overall and division ranks, division, wins, and losses.

### Team Detail

```text
Team page
  -> GET /teams/{team_name}/?sport_type=...&gender=...&level=...
  -> UsersServices.retrieve_team_info
  -> team metadata, ranking history, record, and season opponents
```

Game records include both scores, whether the team was home, z-scores, date, opponent, and a generated game ID.

### Predictions

```text
Prediction form
  -> GET /predictions/                       Load team names
  -> select two teams and home-field option
  -> GET /predictions/{team1}/{team2}/{hfa}  Calculate scores
  -> UsersServices.score_predictions
```

Predictions use current power rankings, sport-level constants, and scoring history. They are calculated on request and are not queued as background jobs.

## Admin Authentication

There is one admin account in the current model.

1. `/setup/admin/` creates the initial account when the `X-Setup-Token` header matches `SETUP_TOKEN`.
2. `/token/` verifies the username and bcrypt password hash.
3. The backend signs a JWT with `SECRET_KEY` and sets it in an `HttpOnly`, `SameSite=Strict` cookie.
4. The shared Axios client sends the cookie with API requests without exposing it to frontend JavaScript.
5. Admin routes call `require_admin()` to validate the token and confirm that the admin still exists.
6. Bearer JWTs remain available for command-line and automated clients.

The browser validates its cookie-backed session when the application starts. Public routes remain available without authentication, `/admin/login` is the dedicated sign-in page, and every `/admin` application route is wrapped by `RequireAdmin`. A signed-out visitor is returned to the admin page they originally requested after a successful login. Caddy and the React development server both fall back to `index.html`, so clean browser URLs continue to work when opened directly or refreshed.

Logging out expires the cookie. Deleting the admin account immediately invalidates its tokens; the backend does not maintain a separate per-token revocation list.

## Admin Data-Ingestion Workflow

The admin selects a sport, gender, and level from the shared dropdowns before adding games. The selected values form the dataset key used by every request. Games can be entered individually or uploaded as a CSV.

```text
Select CSV
  -> confirm that the file belongs to the selected dataset
  -> browser parses and validates every row
  -> POST /games/upload/
  -> backend repeats the full validation
  -> reject duplicate games within the file or existing dataset
  -> reject unknown teams and require team metadata to be imported first
  -> store normalized games in MongoDB
  -> store the validated source CSV under uploads/ for reference
  -> store only upload metadata and its relative path in MongoDB

Individual game form
  -> browser validates the six game fields
  -> POST /games/
  -> use the same team lookup, duplicate, and storage workflow
```

The expected game CSV has six columns and no header:

```text
date,home_team,away_team,home_score,away_score,neutral_site
```

Dates may use `YYYY-MM-DD` or `MM/DD/YYYY`. Scores must be nonnegative integers, the teams must be different, and `neutral_site` must be `0` or `999`. Files are UTF-8, headerless, limited to six columns, 5 MB, and 5,000 games. A duplicate is the same pair of teams on the same date, regardless of case or which team is listed as home.

Canonical games are individual documents in `sports_data.games`. Each record has the dataset key, stable team IDs and names, normalized date, scores, neutral-site value, source upload ID, and z-scores. A unique identity uses the dataset, date, and sorted team IDs, so home/away reversal is still a duplicate and a later team rename does not change game identity.

Validated source files are immutable references under `UPLOAD_DIR`. Local Docker maps that directory to root `uploads/`; Lightsail uses the persistent `upload_data` volume. `sports_data.csv_files` stores only filename, relative path, upload ID, upload time, game count, and sports week. Existing Mongo blobs are migrated to the filesystem once during backend startup.

Automatically created teams initialize all fields the algorithm expects, including the team ID, a neutral initial ranking, recent opponents, season opponents, wins, and losses. The existing `/check-teams/` and `/add_teams/` endpoints remain available for fixture loading and detailed team metadata maintenance, but the Add Games page no longer requires that separate step.

## Background-Job Workflow

Ranking and z-score calculations use Redis because they can outlive a normal request.

```text
Game add/update/delete
  -> increment the selected dataset's games_revision
  -> mark that dataset stale and record ranking_requested_at
  -> minute dispatcher waits for 10 quiet minutes
  -> enqueue run_main_algorithm in Redis
Manual alternative
  -> POST /run_algorithm/{iterations} enqueues immediately and returns task_id
  -> ARQ worker claims the job
  -> worker captures games_revision and a per-dataset Redis guard
  -> AdminTeamsService starts MainAlgorithm
  -> algorithm reads canonical games and team seeds from MongoDB
  -> algorithm replaces derived rankings and season records
  -> algorithm calculates and persists z-scores
  -> worker marks rankings current only if games_revision is unchanged
  -> frontend polls GET /execution-history/ while the job is active
```

The automatic dispatcher runs every minute, but only datasets whose last game change is at least `RANKING_DEBOUNCE_SECONDS` old are eligible. The default is 600 seconds. A weekly catch-up runs Sunday at 1:00 AM in `RANKING_TIMEZONE` and queues any stale datasets without waiting for the quiet period. Both use `AUTO_RANKING_ITERATIONS`; the defaults are `America/Denver` and one iteration.

The same Redis guard prevents overlapping manual, automatic, and weekly runs for a dataset. The admin Run Algorithm button remains available for immediate corrections and troubleshooting, and execution history identifies each run's source. A ranking run completes the whole pipeline, including z-scores. `/calc_z_scores/` remains available as an advanced action to refresh only z-scores.

## Ranking Pipeline

The production pipeline is orchestrated by [`backend/api/utils/algorithm/run.py`](../backend/api/utils/algorithm/run.py):

1. `load_games()` reads all canonical games for the selected dataset in date and game-ID order.
2. `retrieve_teams(use_initial=True)` loads team IDs, names, divisions, and the first ranking seed while clearing transient recent-opponent state.
3. `run.py` adapts the Mongo documents to the algorithm's Pandas contract.
4. `data_cleaning.py` normalizes scores and names.
5. `data_enrichment.py` combines every game with current in-memory rankings and dataset constants.
6. `main.py` normalizes score margins, calculates expected and actual performance, and derives ranking changes.
7. Ranking changes propagate through the recent-opponent graph with decreasing influence at greater depth.
8. Steps 3 through 7 repeat for the requested number of iterations, entirely in memory.
9. `output.py` replaces wins, losses, rankings, recent opponents, and reciprocal `season_opp` views in MongoDB.
10. The same canonical games are used to calculate z-scores, which are written to both `games` and the team-facing records.

Iterations let results settle across connected opponents. Every invocation starts from the stored initial ranking, so the same games and iteration count produce the same result instead of compounding a previous run.

## MongoDB Mental Model

The code currently selects database names directly, even though the connection URI comes from the environment.

| Database | Collection | Purpose |
| --- | --- | --- |
| `sports_data` | `temp2` | Teams plus derived rankings and reciprocal season-game views |
| `sports_data` | `games` | Canonical normalized current-season game documents |
| `sports_data` | `csv_files` | Source-upload metadata and filesystem paths; no CSV bytes |
| `sports_data` | `flagged_games` | User-reported games that need review |
| `sports_data` | `previous_season` | Previous-season reference data |
| `admin_details` | `admin` | The admin username and password hash |

The central `temp2` shape is conceptually:

```text
dataset document
|-- _id
|-- sport_type
|-- gender
|-- level
`-- teams[]
    |-- team_id
    |-- team_name
    |-- division/conference/state
    |-- overall_rank/division_rank
    |-- power_ranking[]             Date-to-value history
    |-- recent_opp[]                IDs used for ranking propagation
    |-- season_opp[]                Game records and z-scores
    |-- wins
    `-- losses
```

One `temp2` document represents one sport/gender/level dataset. Its nested game views support public team pages, but they are derived from the separate canonical `games` collection and may be fully rebuilt.

### Index and Connection Model

FastAPI creates the application indexes idempotently during startup. The `temp2`, `csv_files`, `flagged_games`, and `previous_season` collections each have a unique compound index on `(sport_type, gender, level)`. Canonical games have a unique `(sport_type, gender, level, identity)` index plus a `(sport_type, gender, level, game_date)` lookup index. The admin collection has a unique index on `username`.

All backend services share one Motor client and connection pool. `MONGO_MAX_POOL_SIZE` can override the default maximum of 50 connections per backend process.

MongoDB's built-in `_id` index remains the fastest path for operations that already know the configured dataset ID. Team views remain embedded arrays, so rebuilding them scales with dataset size. Canonical game search, update, and deletion no longer require scanning CSV blobs or reciprocal team arrays.

## Two Algorithm Workspaces

There are two similar but differently connected algorithm implementations:

| Location | Data source | Output | Use |
| --- | --- | --- | --- |
| `backend/api/utils/algorithm/` | MongoDB teams and canonical games | MongoDB updates | Running application |
| `tests/isolation/algorithm/` | Local CSV fixtures | Generated CSVs | Isolated development and comparison |

The standalone runner starts with `TEAMSNEW.csv`, processes `GAMES1.csv` through `GAMES3.csv` in order, carries updated team state forward, and writes generated output files. Changes to shared ranking behavior may need to be applied to both workspaces so they do not drift.

## Where to Make Changes

| Goal | Start here |
| --- | --- |
| Change a page or form | `frontend/src/views/` |
| Change navigation or page registration | `frontend/src/_nav.js` and `frontend/src/routes.js` |
| Change API base URL or token headers | `frontend/src/api.js` |
| Add or change an HTTP endpoint | `backend/api/routers/` |
| Change request validation | `backend/api/schemas/items.py` |
| Change public queries or predictions | `backend/api/service/users_teams.py` |
| Change admin CRUD or game storage | `backend/api/service/admin_teams.py` |
| Change source-file persistence | `backend/api/service/upload_storage.py` |
| Change login or JWT behavior | `backend/api/service/admin_service.py` |
| Change dataset constants | `backend/api/config/constants.py` |
| Change ranking math | Both algorithm `main.py` files |
| Change pipeline sequencing | The relevant algorithm `run.py` |
| Add a background task | `backend/api/service/tasks.py` and an admin route |
| Change local service wiring | `docker-compose.yml` |

## Current Boundaries to Remember

- The frontend API URL, FastAPI CORS origins, trusted hosts, root path, and Redis connection are environment-configurable. Their defaults preserve the local development workflow; the Lightsail stack supplies production values.
- `MONGO_DB_NAME` affects the connection URI, but Python services explicitly select `sports_data` and `admin_details` databases.
- Dataset IDs and algorithm constants are hard-coded in `config/constants.py`; a database must contain documents with those IDs.
- The schema permits football and both gender values, but `LEVEL_CONSTANTS` only defines men's football datasets.
- The integrated and standalone algorithms are separate copies and can diverge.
- Source files are audit references, not operational input. Updating or deleting a game changes canonical and derived Mongo records but does not rewrite the original upload.

## Suggested Reading Order

For a first pass through the code, read:

1. [`docker-compose.yml`](../docker-compose.yml) to see the running services.
2. [`frontend/src/routes.js`](../frontend/src/routes.js) to see the available screens.
3. [`backend/api/main.py`](../backend/api/main.py) and the two files in `backend/api/routers/` to see the API surface.
4. `backend/api/service/users_teams.py` for public reads and predictions.
5. `backend/api/service/admin_teams.py` for ingestion and database updates.
6. `backend/api/service/tasks.py` and `backend/api/utils/algorithm/run.py` for queued processing.
7. The production algorithm modules in order: `run`, `data_cleaning`, `data_enrichment`, `main`, and `output`.

That path follows the same direction as a real request and avoids beginning with the densest calculation code.

## End-to-End Test Data

[`tests/application/`](../tests/application/) contains a fresh-database seed, team metadata, connected weekly game files, expected records, negative cases, and an HTTP smoke-test sequence. Its README describes the safe execution order and identifies the final destructive maintenance checks.

Run the automated happy-path suite from the repository root with `make test-app`. Use `make test-app-reset CONFIRM_TEST_RESET=1` to replace every local application collection and fixture upload file with the full baseline: six datasets, 60 current teams, 60 canonical games, six source uploads, six flagged games, and six previous-season datasets. Destructive maintenance endpoint checks are kept behind `make test-app-maintenance CONFIRM_DESTRUCTIVE=1`.

The default test account is `test-admin` with password `test-admin-password`. The full fixture reset recreates that account; the separately guarded `make test-admin-reset CONFIRM_ADMIN_RESET=1` target replaces only `admin_details.admin`. Both reset commands are for isolated local data and must not be used with shared or production databases.
