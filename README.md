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
|-- isotests/
|   `-- algorithm/                   # Standalone algorithm test workspace
|-- docs/
|   `-- README.md                    # Architecture and workflow mental model
|-- deploy/
|   `-- lightsail/                   # AWS host bootstrap, Caddy, and runbook
|-- scripts/
|   `-- application_smoke_test.sh   # Automated end-to-end API workflow
|-- example_files/                   # Sample CSV/text inputs
|   `-- application_test/            # End-to-end fixtures and API smoke tests
|-- databases/                       # SQLite database snapshots/reference files
|-- old_db/                          # Older database snapshots
|-- archived_files/                  # Older model/algorithm references
|-- Contract/                        # Project contract and notes
|-- Makefile                         # Development and smoke-test commands
|-- docker-compose.yml               # MongoDB, Redis, backend, worker, frontend
|-- docker-compose.lightsail.yml     # HTTPS production stack for AWS Lightsail
|-- .env.production.example          # Production environment template
|-- workflow_requirements.txt
`-- README.md
```

Generated local runtime data may also appear under `data/db/` when MongoDB is run through Docker Compose.

For a detailed explanation of how requests, data, background jobs, and ranking calculations move through the system, see the [project mental model](docs/README.md).

## Development Workflow

Local development requires Docker Compose. The automated smoke test also uses `curl` and `jq`. Run `make help` from the repository root to list the available commands.

Build and start the complete application:

```bash
make app-up
```

After the containers start:

- Frontend: <http://localhost:3000>
- FastAPI docs: <http://localhost:8000/docs>
- MongoDB: `localhost:27017`
- Redis: `localhost:6379`

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
docker compose up -d --build
```

## Application Test Workflow

The end-to-end smoke test uses the fixture data under `example_files/application_test/` and targets Basketball/Men's/High School. On an empty fixture dataset, run:

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

The test refuses to run over an already populated fixture dataset. To reset only that dataset and rerun:

```bash
make test-app-reset CONFIRM_TEST_RESET=1
```

### Test Admin

On a database with no admin, the test attempts to create:

```text
username: sample-admin
password: sample-password-change-me
```

If a local admin already exists, pass its credentials without storing them in the repository:

```bash
TEST_ADMIN_USERNAME=admin \
TEST_ADMIN_PASSWORD='your-password' \
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

For request-by-request debugging, use [`api-smoke-test.http`](example_files/application_test/api-smoke-test.http). See the [fixture guide](example_files/application_test/README.md) for expected records, negative inputs, optional environment variables, and known application behavior exposed by the tests.

## Environment

Docker Compose expects a `.env` file in the repository root. A local development file should define:

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
make lightsail-init DOMAIN=rankings.example.com
make lightsail-check
make lightsail-up
make lightsail-status
make lightsail-health
make lightsail-backup
```

Production configuration lives in the ignored `.env.production` file created from `.env.production.example`. Local development continues to use `.env` and `docker-compose.yml`.

## Backend

The backend lives in `backend/api` and starts from `api.main:app`.

- `routers/admin_routes.py` handles protected admin operations such as login, setup, CSV upload, adding/updating/deleting teams and games, and queueing algorithm work.
- `routers/user_routes.py` exposes public team lists, team detail, prediction team names, and game predictions.
- `service/admin_service.py`, `service/admin_teams.py`, and `service/users_teams.py` contain the main application logic.
- `service/tasks.py` defines ARQ worker jobs for running the algorithm and calculating z-scores.
- `utils/algorithm/` contains the backend version of the ranking pipeline.

See [`backend/api/README.md`](backend/api/README.md) and [`backend/api/utils/algorithm/README.md`](backend/api/utils/algorithm/README.md) for more focused backend and algorithm notes.

## Frontend

The frontend lives in `frontend/` and is a Create React App/CoreUI application.

- `src/views/` contains the user-facing pages, including teams, team detail, predictions, dashboard, login/register, and admin tools.
- `src/components/` and `src/layout/` define the shared application chrome.
- `src/api.js` and `src/services/authService.js` centralize frontend API calls and authentication helpers.
- `src/_nav.js` defines sidebar navigation.

Useful local commands from `frontend/`:

```bash
npm install
npm start
npm test
npm run build
```

## Algorithm Workspaces

There are two copies of the algorithm pipeline:

- `backend/api/utils/algorithm/` is the version wired into the backend service layer.
- `isotests/algorithm/` is a standalone CSV-based workspace for experimenting with inputs and comparing outputs.

Both follow the same general flow:

1. `upload.py` loads and validates CSV input.
2. `data_cleaning.py` normalizes incoming game data.
3. `data_enrichment.py` adds ranking inputs and derived fields.
4. `main.py` performs the ranking and prediction calculations.
5. `output.py` formats the results.
6. `run.py` ties the pipeline together.

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
- `example_files/application_test/` contains a documented end-to-end fixture pack for the current API and UI workflows.
- `Contract/` contains project contract documents and notes.

## Git Branch Management & Best Practices

GitHub hooks and workflow ideas were adapted from <https://github.com/rambasnet/course-container>.
