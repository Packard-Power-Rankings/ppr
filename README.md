# Packard Power Rankings

Packard Power Rankings is a full-stack sports rankings application. The backend exposes a FastAPI API for team data, admin workflows, predictions, CSV uploads, and algorithm runs. The frontend is a CoreUI React app that consumes those API endpoints. MongoDB stores application data, Redis backs the async worker queue, and the ranking algorithm also exists as a standalone CSV pipeline for isolated testing.

## Project Structure

```text
.
|-- backend/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- api/
|       |-- main.py                  # FastAPI app entry point
|       |-- routers/                 # Admin and public/user API routes
|       |-- schemas/                 # Pydantic request/response models
|       |-- service/                 # Business logic, database access, ARQ tasks
|       |-- config/                  # Constants for sports, divisions, states, etc.
|       |-- external_services/       # Placeholder for integrations
|       `-- utils/
|           |-- algorithm/           # Backend-integrated ranking pipeline
|           |-- dependencies.py
|           |-- json_helper.py
|           `-- update_algo_vals.py
|-- frontend/
|   |-- Dockerfile
|   |-- Dockerfile.production       # React build served by Caddy
|   |-- package.json
|   |-- public/                      # Static CRA assets
|   `-- src/
|       |-- api.js                   # Frontend API client
|       |-- routes.js                # React route registration
|       |-- components/              # Shared layout/header/sidebar components
|       |-- layout/                  # CoreUI layout shell
|       |-- services/                # Auth and client-side services
|       |-- views/                   # Dashboard, teams, predictions, admin pages
|       |-- assets/                  # Images, avatars, and brand helpers
|       `-- scss/                    # CoreUI/custom styles
|-- tests/
|   |-- backend/                     # Backend service and algorithm tests
|   |-- frontend/                    # React component and workflow tests
|   |-- application/                 # End-to-end runner, requests, and fixtures
|   `-- isolation/algorithm/         # Standalone algorithm test workspace
|-- docs/
|   `-- README.md                    # Architecture and workflow mental model
|-- deploy/
|   `-- lightsail/                   # AWS host bootstrap, Caddy, and runbook
|-- scripts/                         # AWS setup, health, and backup helpers
|-- uploads/                         # Validated source game files (runtime, ignored)
|-- example_files/                   # Sample CSV/text inputs
|-- databases/                       # SQLite database snapshots/reference files
|-- old_db/                          # Older database snapshots
|-- archived_files/                  # Older model/algorithm references
|-- Contract/                        # Project contract and notes
|-- Makefile                         # Development and smoke-test commands
|-- docker-compose.yml               # MongoDB, Redis, backend, worker, frontend
|-- docker-compose.lightsail.yml     # HTTPS production stack for AWS Lightsail
|-- .env/
|   |-- development.example          # Local environment template
|   `-- production.example           # Production environment template
|-- workflow_requirements.txt
`-- README.md
```

Generated local runtime data may also appear under `data/db/` for MongoDB and `uploads/` for validated source game files. Upload contents are ignored by Git; only `uploads/.gitkeep` is tracked.

For a detailed explanation of how requests, data, background jobs, and ranking calculations move through the system, see the [project mental model](docs/README.md).

## Development Workflow

Local development requires Docker Compose. The automated smoke test also uses `curl` and `jq`. Run `make help` from the repository root to list the available commands.

Build and start the complete application:

```bash
make app-up
```

The frontend container compares `package-lock.json` with its persisted `node_modules` volume at startup. When the lockfile changes or dependencies are incomplete, it runs `npm ci` automatically before starting React; that startup can take a few extra seconds.

After the containers start:

- Public frontend: <http://localhost:3000/>
- Admin login: <http://localhost:3000/admin/login>
- Protected admin area: <http://localhost:3000/admin>
- FastAPI docs: <http://localhost:8000/docs>
- MongoDB: <http://localhost:27017>
- Redis: <http://localhost:6379>

The frontend uses normal browser paths rather than hash URLs. Current rankings use sport-first paths such as `/football/mens/college` and `/basketball/womens/high_school`. The complete team directory remains at `/teams`, predictions are at `/predictions`, and all administration pages live under `/admin`. Opening an admin URL while signed out redirects to `/admin/login`, then returns to the originally requested page after a successful login. Legacy `/teams/<sport>/<gender>/<level>` links redirect to the shorter sport-first paths, and `/login` redirects to `/admin/login`.

Live ranking headings and rank, power, and division-rank labels automatically display the current calendar year. Archived ranking views use the year stored in their season snapshot instead.

Published season rankings are available through `/archives`. The `/admin` dashboard offers **Archive Selected Sport** for one chosen sport/gender/level dataset and **Archive All Sports** for a complete current-year snapshot. Archiving a selected sport merges it into that year's archive without removing other archived datasets; replacing the same selected dataset requires explicit overwrite confirmation. Archiving all sports replaces the complete year only after confirmation. Both actions create self-contained public pages under `/archive/<year>/` without changing current teams or games.

Generated archives are runtime data stored in Docker's named `archive_data` volume, not files copied into the Git working tree. Therefore, `frontend/public/archive/` normally shows only its documentation in the IDE even when an archive such as `2026/` exists. Inside the running containers, the backend writes the volume at `/var/lib/ppr-archives`, and the development frontend reads it at `/app/public/archive`. View a year through the React page at `http://localhost:3000/archives/<year>` or its standalone snapshot at `http://localhost:3000/archive/<year>/index.html`. See the [archive mental model](frontend/public/archive/README.md) for the runtime layout and persistence rules.

The `/admin` dashboard also provides guarded season reset actions. **Reset Selected Sport** opens a dataset picker and verifies that exact dataset is archived before resetting it. **Reset All Sports** has a separate confirmation and checks for a complete all-sports archive. A reset sets wins, losses, and win ratio to zero; removes canonical current-season games and source uploads; and preserves overall rank, division rank, power history, ranking date, recent opponents, and each team's five most recent game records. If the required archive is missing, the administrator must explicitly confirm that they want to proceed without archiving. Resetting does not copy data to `previous_season` or modify an existing public archive.

Follow backend and worker logs while debugging:

```bash
make app-logs
```

Stop the stack without deleting its persisted data:

```bash
make app-down
```

The equivalent direct startup command remains available:

```bash
docker compose --env-file .env/development up -d --build
```

## Automated Tests

All test code and fixtures are organized under [`tests/`](tests/README.md). Run the backend and frontend unit suites with:

```bash
make test
```

Run unit tests, frontend lint, and a production frontend build together with:

```bash
make test-check
```

Focused targets are available for backend service tests, backend algorithm tests, frontend app/routing tests, admin workflows, and public team views. Run `make help` for the complete list.

## Application Test Workflow

The end-to-end smoke test uses the fixture data under `tests/application/` and targets Basketball/Men's/High School. On an empty fixture dataset, run:

```bash
make test-app
```

This command:

1. Builds and starts the Docker Compose stack.
2. Waits for FastAPI to become available.
3. Creates missing MongoDB dataset and flagged-game documents without overwriting existing data.
4. Creates or authenticates the test admin.
5. Adds seven teams and uploads four weeks containing 13 games.
6. Queues the ranking and z-score jobs and waits for ARQ to finish them.
7. Verifies records, ranking updates, team details, predictions, and the flagged-game lifecycle.

A successful run ends with:

```text
[application-test] PASS: application happy-path smoke test
```

The test refuses to run over an already populated fixture dataset. To replace the complete local test database with deterministic fixtures, run:

```bash
make test-app-reset CONFIRM_TEST_RESET=1
```

This guarded reset replaces all documents in `sports_data.temp2`, `sports_data.games`, `sports_data.csv_files`, `sports_data.flagged_games`, `sports_data.previous_season`, and `admin_details.admin`. It also replaces local fixture references under `uploads/`. It loads all six supported datasets with 10 teams and 10 games each, then verifies the database and API responses. Do not point it at shared or production data.

### Test Admin

On a database with no admin, the test attempts to create:

```text
username: test-admin
password: test-admin-password
```

If a local admin already exists, pass its credentials without storing them in the repository:

```bash
TEST_ADMIN_USERNAME=custom-test-admin \
TEST_ADMIN_PASSWORD='custom-test-password' \
make test-app
```

If the password is unavailable and the database is strictly local, replace the existing admin with the default fixture account:

```bash
make test-admin-reset CONFIRM_ADMIN_RESET=1
make test-app
```

`test-admin-reset` deletes the documents in `admin_details.admin`. Never run it against a shared or production database.

### Maintenance Checks

After the happy-path test passes, the destructive maintenance suite checks score updates, team renaming, game deletion, team deletion, and season clearing:

```bash
make test-app-maintenance CONFIRM_DESTRUCTIVE=1
```

The confirmation variables are deliberate safeguards. The reset and maintenance targets modify or remove fixture data.

### Canonical Team IDs

Team metadata must be loaded before games. Its CSV contract is:

```text
state,short_name,team_id,long_name,division,conference,ranked
```

The supplied positive `team_id` is the identifier used by teams, games, opponent history, flagged games, and previous-season records. Game uploads reject unknown teams instead of generating IDs.

The manual Add Team form suggests one greater than the highest `team_id` in the selected dataset, or `1` when the dataset is empty. The suggestion remains editable, and the backend rechecks uniqueness when the form is submitted.

If data was uploaded during the temporary `team_num` implementation, back up MongoDB and preview the controlled migration:

```bash
make team-id-migration-check
```

After reviewing the counts, apply it during a maintenance window:

```bash
make team-id-migration-apply CONFIRM_TEAM_ID_MIGRATION=1
```

For request-by-request debugging, use [`api-smoke-test.http`](tests/application/api-smoke-test.http). See the [fixture guide](tests/application/README.md) for expected records, negative inputs, optional environment variables, and known application behavior exposed by the tests.

## Environment

Environment files are grouped under `.env/`. Copy the tracked development template when setting up a new checkout:

```bash
cp .env/development.example .env/development
```

The ignored `.env/development` file should define:

```env
MONGO_DB_NAME=ppr
MONGO_USER=ppr
MONGO_PASS=ppr-dev-password
MONGO_PORT=27017
SETUP_TOKEN=change-this-local-setup-token
SECRET_KEY=change-this-local-secret-key
```

These values are used by the MongoDB container, the FastAPI backend, and the admin setup/auth flow.

## AWS Lightsail Deployment

The repository includes a separate production stack for a single AWS Lightsail instance. It compiles React into a Caddy image, serves the application over automatic HTTPS, proxies `/api` to FastAPI, authenticates Redis, runs the backend as a non-root user, and keeps MongoDB and Redis off the public network.

Start by reading the [AWS Lightsail deployment guide](deploy/lightsail/README.md). The main commands are:

```bash
make lightsail-init DOMAIN=packardpowerrankings.com
make lightsail-check
make lightsail-up
make lightsail-status
make lightsail-health
make lightsail-backup
```

Production configuration lives in the ignored `.env/production` file created by `make lightsail-init` using `.env/production.example` as its reference. Local development uses `.env/development` and `docker-compose.yml`. Override either location with `APP_ENV=/path/to/file` or `LIGHTSAIL_ENV=/path/to/file` when needed.

## Backend

The backend lives in `backend/api` and starts from `api.main:app`.

- `routers/admin_routes.py` handles protected admin operations such as login, setup, CSV upload, adding/updating/deleting teams and games, and queueing algorithm work.
- `routers/user_routes.py` exposes public team lists, team detail, prediction team names, and game predictions.
- `service/admin_service.py`, `service/admin_teams.py`, and `service/users_teams.py` contain the main application logic. `service/upload_storage.py` owns source-file persistence.
- `service/tasks.py` defines ARQ worker jobs for running the algorithm and calculating z-scores.
- `utils/algorithm/` contains the backend version of the ranking pipeline.

See [`backend/api/README.md`](backend/api/README.md) and [`backend/api/utils/algorithm/README.md`](backend/api/utils/algorithm/README.md) for more focused backend and algorithm notes.

## Frontend

The frontend lives in `frontend/` and is a Create React App/CoreUI application.

- `src/views/` contains the user-facing pages, including teams, team detail, predictions, dashboard, login/register, and admin tools.
- `src/components/` and `src/layout/` define the shared application chrome.
- `src/api.js` and `src/services/authService.js` centralize frontend API calls and authentication helpers.
- `src/_nav.js` defines sidebar navigation.
- `src/routes.js` defines public and protected admin routes; `src/components/RequireAdmin.js` enforces the admin boundary after validating the stored token.

Useful local commands from `frontend/`:

```bash
npm install
npm start
npm run build
```

Run the centralized frontend suite from the repository root with `make test-frontend`.

## Algorithm Workspaces

There are two algorithm workspaces:

- `backend/api/utils/algorithm/` is the version wired into the backend service layer.
- `tests/isolation/algorithm/` is a standalone CSV-based workspace for experimenting with inputs and comparing outputs.

The production flow is:

1. Add Games validates CSV input once and writes normalized records to `sports_data.games`.
2. The validated source file is retained under `uploads/`; Mongo stores only its metadata and path.
3. `run.py` reads canonical games from Mongo and starts from each team's initial ranking.
4. `data_cleaning.py`, `data_enrichment.py`, and `main.py` calculate rankings.
5. `output.py` replaces derived team records, ranking order, and z-scores.
6. Repeating a run with the same games and iteration count produces the same result.

The standalone `tests/isolation/algorithm/` workspace continues to use local CSV files for experiments. It is not the production application's data path.

## About the Ranking Algorithm

The algorithm models how teams should move in power ranking after games are played. It considers margin of victory, total score context, home-field advantage, current power ranking, and connected opponent performance. A team can still gain power after a closer-than-expected win because winning itself carries value, but larger surprises create larger shifts.

At the start of a season, rankings can be seeded from the previous season. As scores are added, the algorithm repeats calculations over the season so rankings stabilize as more connected results become available.

The application can also estimate hypothetical game scores between two teams. These predictions are decimal approximations rather than exact final scores.

## Z-Scores

Team pages use z-scores to show how impactful a game was relative to average game performance in the current ranking context. Positive z-scores improve a team's ranking, negative z-scores lower it, and values beyond roughly `-2` or `2` indicate especially impactful games. Because rankings change as more games are processed, historical game z-scores can also change over time.

## Legacy and Reference Files

- `archived_files/` keeps older model and algorithm references.
- `databases/` and `old_db/` contain database snapshots used for reference or migration work.
- `example_files/` contains sample source data.
- `tests/application/` contains a documented end-to-end fixture pack for the current API and UI workflows.
- `Contract/` contains project contract documents and notes.

## Git Branch Management & Best Practices

GitHub hooks and workflow ideas were adapted from <https://github.com/rambasnet/course-container>.
