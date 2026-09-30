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

CSV fixtures ------> isotests/algorithm ------> generated CSV output
```

The public side reads rankings and predictions from MongoDB. The admin side loads game data and starts calculations that update MongoDB. Redis and the ARQ worker keep those calculations out of normal HTTP request processing.

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

isotests/algorithm/
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
4. The ARQ worker starts and registers the algorithm and z-score tasks.
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
3. The backend returns a JWT signed with `SECRET_KEY`.
4. The frontend stores it under `access_token` in browser local storage.
5. The shared Axios client sends `Authorization: Bearer <token>` on protected requests.
6. Admin routes call `require_admin()` to validate the token.

Logging out removes the token from the browser. The backend does not currently maintain a token revocation list.

## Admin Data-Ingestion Workflow

The normal sequence for adding games is:

```text
Select CSV
  -> browser parses rows with Papa Parse
  -> extract home and away team names
  -> POST /check-teams/
  -> add missing team metadata through POST /add_teams/
  -> POST /upload_csv/
  -> store original CSV bytes for later processing
```

The expected game CSV has six columns and no header:

```text
date,home_team,away_team,home_score,away_score,neutral_site
```

Uploaded files are grouped by the organizing key in `sports_data.csv_files`. Each stored entry contains the filename, binary file data, upload date, and a `sports_week` value taken from the first row's date.

Adding missing teams initializes the fields the algorithm expects, including the team ID, ranking history, recent opponents, season opponents, wins, and losses.

## Background-Job Workflow

Ranking and z-score calculations use Redis because they can outlive a normal request.

```text
Admin Calculate Values page
  -> POST /run_algorithm/{iterations}
  -> FastAPI enqueues run_main_algorithm in Redis
  -> API immediately returns task_id
  -> ARQ worker claims the job
  -> AdminTeamsService starts MainAlgorithm
  -> algorithm reads CSV and team data from MongoDB
  -> algorithm writes results to MongoDB
  -> frontend polls GET /task-status/{task_id}
```

The frontend polls every three seconds while a job is queued or in progress. Z-scores follow the same pattern through `/calc_z_scores/` and the `calc_z_score` worker function.

## Ranking Pipeline

The production pipeline is orchestrated by [`backend/api/utils/algorithm/run.py`](../backend/api/utils/algorithm/run.py):

1. `load_csv()` retrieves all uploaded files for the selected dataset.
2. `retrieve_teams()` loads each team's ID, name, latest power ranking, and recent opponents.
3. `upload.py` turns one stored CSV into a Pandas DataFrame.
4. `data_cleaning.py` normalizes names, scores, dates, and flags.
5. `data_enrichment.py` combines each game with current team rankings and dataset constants.
6. `main.py` normalizes score margins, calculates expected and actual performance, and derives ranking changes.
7. Ranking changes propagate through the recent-opponent graph with decreasing influence at greater depth.
8. `output.py` updates team rankings, records, recent opponents, and season game history in MongoDB.
9. The process repeats for every uploaded file and for the requested number of iterations.

Iterations let results settle across connected opponents. A team's updated value can affect earlier expectations when the full set of games is processed again.

Z-scores are calculated separately and written into the corresponding season game records.

## MongoDB Mental Model

The code currently selects database names directly, even though the connection URI comes from the environment.

| Database | Collection | Purpose |
| --- | --- | --- |
| `sports_data` | `temp2` | Dataset documents containing nested teams and games |
| `sports_data` | `csv_files` | Original uploaded CSV files grouped by dataset |
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

One top-level document represents one sport/gender/level dataset. Teams and games are nested inside that document rather than stored as separate MongoDB documents.

## Two Algorithm Workspaces

There are two similar but differently connected algorithm implementations:

| Location | Data source | Output | Use |
| --- | --- | --- | --- |
| `backend/api/utils/algorithm/` | MongoDB teams and stored CSVs | MongoDB updates | Running application |
| `isotests/algorithm/` | Local CSV fixtures | Generated CSVs | Isolated development and comparison |

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
| Change admin CRUD or CSV storage | `backend/api/service/admin_teams.py` |
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
- The current z-score runner replaces its DataFrame for each uploaded file and performs the final calculation after the loop, so its effective input is the last loaded file.
- [`backend/api/README.md`](../backend/api/README.md) describes an older proposed backend layout. This document and the root [`README.md`](../README.md) describe the current repository.

## Suggested Reading Order

For a first pass through the code, read:

1. [`docker-compose.yml`](../docker-compose.yml) to see the running services.
2. [`frontend/src/routes.js`](../frontend/src/routes.js) to see the available screens.
3. [`backend/api/main.py`](../backend/api/main.py) and the two files in `backend/api/routers/` to see the API surface.
4. `backend/api/service/users_teams.py` for public reads and predictions.
5. `backend/api/service/admin_teams.py` for ingestion and database updates.
6. `backend/api/service/tasks.py` and `backend/api/utils/algorithm/run.py` for queued processing.
7. The algorithm modules in order: `upload`, `data_cleaning`, `data_enrichment`, `main`, and `output`.

That path follows the same direction as a real request and avoids beginning with the densest calculation code.

## End-to-End Test Data

[`example_files/application_test/`](../example_files/application_test/) contains a fresh-database seed, team metadata, connected weekly game files, expected records, negative cases, and an HTTP smoke-test sequence. Its README describes the safe execution order and identifies the final destructive maintenance checks.

Run the automated happy-path suite from the repository root with `make test-app`. Repeat it with `make test-app-reset CONFIRM_TEST_RESET=1`, which resets only the fixture's Basketball/Men's/High School dataset before testing. Destructive maintenance endpoint checks are kept behind `make test-app-maintenance CONFIRM_DESTRUCTIVE=1`.

The test creates `sample-admin` only when no admin exists. For an existing account, provide `TEST_ADMIN_USERNAME` and `TEST_ADMIN_PASSWORD` to `make test-app`. A forgotten local-only credential can be replaced through the separately guarded `make test-admin-reset CONFIRM_ADMIN_RESET=1` target; this deletes and recreates the `admin_details.admin` account and must not be used with shared or production data.
