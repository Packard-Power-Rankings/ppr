# FastAPI Backend

The backend exposes the public rankings API, protected admin operations, MongoDB access, and Redis-backed ranking jobs. It runs as `api.main:app` from the backend container.

For the complete system architecture, see [`../../docs/README.md`](../../docs/README.md). For local startup and automated test commands, see the root [`../../README.md`](../../README.md).

## Structure

```text
backend/
|-- Dockerfile
|-- requirements.txt
`-- api/
    |-- main.py                  FastAPI application entry point
    |-- routers/
    |   |-- user_routes.py      Public teams and predictions
    |   `-- admin_routes.py     Authentication, ingestion, jobs, and CRUD
    |-- schemas/
    |   `-- items.py            Pydantic request and response models
    |-- service/
    |   |-- users_teams.py      Public queries and score predictions
    |   |-- admin_service.py    Admin setup, passwords, and JWTs
    |   |-- admin_teams.py      CSV storage and team/game operations
    |   `-- tasks.py            ARQ worker functions
    |-- config/
    |   `-- constants.py        Dataset IDs and ranking constants
    `-- utils/
        |-- algorithm/          MongoDB-integrated ranking pipeline
        |-- dependencies.py
        |-- json_helper.py
        `-- update_algo_vals.py
```

## Request Model

Most endpoints require three query parameters:

```text
sport_type=football|basketball
gender=mens|womens
level=high_school|college
```

Together they form the dataset key `(sport_type, gender, level)`. `config/constants.py` maps supported keys to a MongoDB document ID and the algorithm's `k_value`, home advantage, average game score, and game-set length.

Routes have no source-code prefix. With the default development Compose configuration, the API root is `http://localhost:8000` and interactive documentation is available at `http://localhost:8000/docs`. The Lightsail deployment sets `ROOT_PATH=/api`, and Caddy exposes the same routes at `https://<domain>/api` with documentation under `/api/docs`.

## Public Routes

| Method and path                                            | Purpose                                       |
| ---------------------------------------------------------- | --------------------------------------------- |
| `GET /teams/`                                              | List teams and current rankings for a dataset |
| `GET /teams/{team_name}/`                                  | Return one team's ranking and game history    |
| `GET /predictions/`                                        | Return team names for the prediction form     |
| `GET /predictions/{team_one}/{team_two}/{home_field_adv}/` | Calculate predicted scores                    |
| `POST /flagged-game/`                                      | Report a game for admin review                |
| `GET /check-flagged/{game_id}`                             | Check whether a game was already reported     |

Public queries are implemented in `service/users_teams.py` and read from `sports_data.temp2`.

## Admin Routes

Authentication routes are `/setup/admin/`, `/token/`, `/validate-token/`, and `/logout/`. Protected routes require a Bearer JWT signed with `SECRET_KEY`.

Admin operations include:

- Retrieving valid sport metadata
- Validating and uploading game CSVs through `POST /games/upload/`
- Validating and importing team metadata CSVs through `POST /teams/upload/`
- Adding individual games through `POST /games/`
- Automatically creating teams referenced by new games
- Queueing ranking and z-score calculations
- Polling job status
- Retrieving the five most recent executions for each calculation type
- Updating team names and game scores
- Deleting games or teams
- Reviewing and clearing flagged games
- Archiving seasons and resetting selected or all datasets without modifying existing archives

The current model permits one admin account. `/setup/admin/` requires the `X-Setup-Token` header and refuses to create another account when one already exists.

## CSV Ingestion

Game files are headerless and contain six columns:

```text
date,home_team,away_team,home_score,away_score,neutral_site
```

`neutral_site=999` disables home-field advantage; normal home games use `0`. Dates may use `YYYY-MM-DD` or `MM/DD/YYYY`, and scores must be nonnegative integers. The ingestion service rejects headers, malformed rows, same-team games, duplicate games within a file, and games already present in uploaded or processed data.

Both the CSV endpoint and individual-game endpoint use the same validator. Team metadata must be imported first. A game containing an unknown team is rejected with `422` and an `unknown_teams` list; the endpoint never invents a team identifier. Valid games are normalized into documents in `sports_data.games`. The validated source file is stored under `UPLOAD_DIR` for reference; `sports_data.csv_files` contains only upload metadata such as its filename, relative storage path, game count, and upload date. CSV bytes are never retained in MongoDB.

Team metadata CSV files require the headers `state`, `short_name`, `team_id`, `long_name`, `division`, `conference`, and `ranked`. Header order is flexible and extra columns are ignored. `team_id` is the canonical application identifier: every row must contain a positive whole number, IDs must be unique within the file and selected dataset, and the importer stores the supplied value directly without generating another ID. The importer maps `short_name` to the canonical `team_name` field and rejects files with missing headers, invalid rows, or duplicate IDs inside the file. IDs or names that already exist in the selected dataset are listed in `teams_failed`; successfully added team names are not listed. `ranked` accepts `yes`/`no` (also `true`/`false` or `1`/`0`).

### Legacy Team ID Migration

Deploy the new code, back up MongoDB, and preview any records created under the temporary `team_num` contract:

```bash
make team-id-migration-check
```

The dry run validates canonical-ID and game-identity uniqueness without writing. Apply the migration during a maintenance window only after reviewing the counts:

```bash
make team-id-migration-apply CONFIRM_TEAM_ID_MIGRATION=1
```

The migration rewrites current and previous-season teams, canonical games, opponent references, recent-opponent IDs, flagged games, and derived game IDs, then removes `team_num`. It is idempotent: datasets without `teams[].team_num` are ignored.

## Background Jobs

`POST /run_algorithm/{iterations}` and `POST /calc_z_scores/` enqueue ARQ jobs in Redis and immediately return a `task_id`. The ranking action accepts 1 through 100 iterations. The worker starts from `api.service.tasks.WorkerSettings` and invokes `AdminTeamsService`, which connects the job to the production algorithm under `utils/algorithm/`.

The ranking job reads only `sports_data.games`, fully rebuilds derived team season data from initial rankings, and calculates z-scores before completing. The separate z-score job remains available for refreshing z-scores without rerunning rankings.

The frontend and smoke-test script poll `GET /task-status/{task_id}` until the job completes or fails.
`GET /execution-history/` returns the five most recent ranking and z-score executions, including their dataset, queue time, iteration count when applicable, and persisted status. MongoDB retains at most five records per calculation type in `admin_details.execution_history`; new records prune older entries, and backend startup trims any excess records left by earlier versions.

## Data Storage

| Database        | Collection          | Responsibility                                               |
| --------------- | ------------------- | ------------------------------------------------------------ |
| `sports_data`   | `temp2`             | Teams plus derived rankings and reciprocal season-game views |
| `sports_data`   | `games`             | Canonical normalized current-season games                    |
| `sports_data`   | `csv_files`         | Source-upload metadata and filesystem paths; no file bytes   |
| `sports_data`   | `flagged_games`     | Games reported for review                                    |
| `sports_data`   | `previous_season`   | Archived season data                                         |
| `admin_details` | `admin`             | Admin username and bcrypt password hash                      |
| `admin_details` | `execution_history` | Persisted ranking and z-score job history                    |

The MongoDB connection comes from `MONGO_URI`, while the Python services currently select the `sports_data` and `admin_details` database names directly. ARQ reads `REDIS_HOST`, `REDIS_PORT`, `REDIS_DATABASE`, `REDIS_PASSWORD`, and `REDIS_SSL`; local development uses their defaults, while production enables Redis authentication.

The backend shares one Motor connection pool across its services and creates indexes during FastAPI startup. Dataset collections have a unique compound `(sport_type, gender, level)` index. Canonical games have a unique `(sport_type, gender, level, identity)` index and a dataset/date query index. `admin_details.admin` has a unique `username` index. Set `MONGO_MAX_POOL_SIZE` to override the default pool maximum of 50 connections per backend process.

Local Docker stores references in the root `uploads/` directory. Lightsail stores them in the persistent `upload_data` volume mounted at `/var/lib/ppr-uploads`. Backend startup performs a one-time migration of legacy `csv_files.filedata` blobs into this directory and removes the blob fields after canonical games are created.

## Local Workflow

From the repository root:

```bash
make app-up
make app-logs
make app-down
```

Run the automated API and algorithm workflow with:

```bash
make test-app
```

To replace all local application collections with the complete fixture baseline:

```bash
make test-app-reset CONFIRM_TEST_RESET=1
```

The reset creates 10 teams and 10 games for each supported dataset and also seeds uploaded CSV, flagged-game, previous-season, and test-admin records. It is destructive and is intended only for isolated local development.

If a disposable local database has an unknown admin password:

```bash
make test-admin-reset CONFIRM_ADMIN_RESET=1
make test-app
```

The default local test account is `test-admin` / `test-admin-password`. The admin reset deletes the existing `admin_details.admin` account and recreates that account. It is intended only for isolated local development.

See [`../../tests/application/README.md`](../../tests/application/README.md) for fixtures, assertions, maintenance checks, and troubleshooting.
