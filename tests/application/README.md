# Full Application Test Fixtures

This directory contains two complementary test-data workflows:

- `make test-app` exercises ingestion and ranking from an empty Basketball/Men's/High School dataset.
- `make test-app-reset CONFIRM_TEST_RESET=1` replaces the complete local application database with a deterministic, fully populated baseline and verifies it.

Use both workflows only with an isolated local development database.

## Test Admin

The default test account is:

```text
username: test-admin
password: test-admin-password
```

`test-app` creates this account only when no admin exists. The full reset always replaces the existing `admin_details.admin` contents with this account. Override the defaults for an isolated test environment by setting `TEST_ADMIN_USERNAME` and `TEST_ADMIN_PASSWORD` on the Make command.

To replace only the local admin account:

```bash
make test-admin-reset CONFIRM_ADMIN_RESET=1
```

## Fixture Inventory

| File | Purpose |
| --- | --- |
| `full-database-fixture.json` | Compact specification for all six supported datasets, with 10 teams and 10 games per dataset |
| `load_full_fixture.mongodb.js` | Builds complete MongoDB documents from the specification and replaces the application collections |
| `seed-empty-datasets.json` | Empty documents for manually preparing the six supported dataset keys |
| `seed-flagged-games.json` | Empty flagged-game documents for manual setup |
| `teams.json` | Seven Basketball/Men's/High School teams used by the ingestion smoke test |
| `week-01.csv` through `week-04.csv` | Thirteen connected games used by the ingestion and ranking smoke test |
| `expected-records.json` | Expected records after the ingestion smoke test runs the algorithm |
| `api-smoke-test.http` | Reusable API requests for manually stepping through the workflow |
| `negative-cases/` | Intentionally invalid upload files for error-path checks |

The full fixture covers these dataset combinations:

| Sport | Gender | Level |
| --- | --- | --- |
| Football | Men's | High School |
| Football | Men's | College |
| Basketball | Men's | High School |
| Basketball | Men's | College |
| Basketball | Women's | High School |
| Basketball | Women's | College |

For each combination, the loader creates 10 current teams, 10 unique games stored as reciprocal team records, one uploaded CSV containing those games, one flagged game, and a 10-team previous-season dataset. In total, the fixture contains 60 current teams and 60 unique current-season games.

## Full Database Reset

Run this from the repository root:

```bash
make test-app-reset CONFIRM_TEST_RESET=1
```

The confirmation is required because the command replaces every document in:

- `sports_data.temp2`
- `sports_data.csv_files`
- `sports_data.flagged_games`
- `sports_data.previous_season`
- `admin_details.admin`

After loading, the runner logs in as the test admin and verifies collection counts plus public team and protected flagged-game API responses for all six datasets. A successful run ends with:

```text
[application-test] PASS: full fixture reset and application verification
```

Never run the reset against shared, staging, or production data.

## Ingestion Smoke Test

On an empty Basketball/Men's/High School fixture dataset, run:

```bash
make test-app
```

This path creates missing dataset documents, authenticates the test admin, adds seven teams through the API, uploads four CSV files containing 13 games, runs the ranking and z-score jobs, and verifies team records, details, predictions, and the flagged-game lifecycle. It intentionally refuses to overwrite populated data.

The test reads `SETUP_TOKEN`, `MONGO_USER`, and `MONGO_PASS` from `.env/development`. Optional settings are `BASE_URL`, `JOB_TIMEOUT_SECONDS`, and `POLL_INTERVAL_SECONDS`.

## CSV Contract

Application CSV uploads are headerless and contain exactly six columns:

```text
date,home_team,away_team,home_score,away_score,neutral_site
```

Use `0` for a normal home game and `999` for a neutral-site game. Team names must exactly match their MongoDB records.

## Maintenance Checks

After loading the full fixture or completing the ingestion smoke test, destructive endpoint checks can run against Basketball/Men's/High School:

```bash
make test-app-maintenance CONFIRM_DESTRUCTIVE=1
```

The maintenance suite updates a score, renames and restores a team, deletes a game, deletes a team, and clears the season. Reload the full baseline afterward with the guarded reset command.

## Troubleshooting

### Admin Login Failed

An ordinary `make test-app` does not replace an existing account. Supply its credentials or recreate the local test account:

```bash
TEST_ADMIN_USERNAME=existing-name \
TEST_ADMIN_PASSWORD='existing-password' \
make test-app

make test-admin-reset CONFIRM_ADMIN_RESET=1
```

### Fixture Dataset Is Not Empty

The ingestion smoke test requires an empty Basketball/Men's/High School dataset. Use the full reset when you want a populated UI baseline, or clear that dataset in a disposable database before rerunning the ingestion workflow.

### Background Job Failed or Timed Out

Inspect FastAPI and ARQ output with `make app-logs`. On a slow machine, increase the timeout:

```bash
JOB_TIMEOUT_SECONDS=300 make test-app
```

The upload endpoint stores CSV bytes before background validation. Keep files under `negative-cases/` out of the happy-path dataset.
