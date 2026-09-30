# Full Application Test Fixtures

This fixture pack exercises the Packard Power Rankings application from initial database setup through public ranking views and admin maintenance operations.

The happy-path data uses this dataset key:

```text
sport_type=basketball
gender=mens
level=high_school
```

Use these files only with a local development database. Some of the later smoke-test requests intentionally update or delete test data.

## Files

| File | Purpose |
| --- | --- |
| `seed-empty-datasets.json` | Creates the six dataset documents required by `LEVEL_CONSTANTS` |
| `seed-flagged-games.json` | Creates the documents required by the flagged-game endpoints |
| `teams.json` | Ordered request body for adding seven sample teams |
| `week-01.csv` through `week-04.csv` | Headerless game uploads with home and neutral-site games |
| `expected-records.json` | Expected records after one successful algorithm run |
| `api-smoke-test.http` | Reusable API requests for the complete workflow |
| `negative-cases/` | Intentionally invalid files for error-path checks |

## CSV Contract

Application CSV uploads must have no header and exactly six columns:

```text
date,home_team,away_team,home_score,away_score,neutral_site
```

Use `0` for a normal home game and `999` for a neutral-site game. Every team name must match the corresponding MongoDB team name, including spaces and spelling.

## Prepare a Fresh Database

The automated workflow requires Docker, `curl`, and `jq`. From the repository root, run:

```bash
make test-app
```

This command builds and starts the application, waits for FastAPI, safely creates missing dataset documents, and runs the complete happy-path test. It refuses to continue when the fixture dataset already contains teams or uploaded CSVs.

To repeat the test, explicitly allow the script to reset only the Basketball/Men's/High School fixture data:

```bash
make test-app-reset CONFIRM_TEST_RESET=1
```

The reset replaces that one dataset document and removes its CSV and flagged-game documents. It does not drop a database or affect the other sport/gender/level datasets.

The test reads `SETUP_TOKEN`, `MONGO_USER`, and `MONGO_PASS` from the root `.env`. It tries to create this default test admin:

```text
username: sample-admin
password: sample-password-change-me
```

If the application already has a different admin account, supply its credentials:

```bash
TEST_ADMIN_USERNAME=my-admin \
TEST_ADMIN_PASSWORD=my-password \
make test-app
```

If the local admin password is unavailable, replace the local admin account with the default test account:

```bash
make test-admin-reset CONFIRM_ADMIN_RESET=1
make test-app
```

`test-admin-reset` deletes the existing documents in `admin_details.admin` and creates one local test account. It does not affect MongoDB connection credentials, but it should never be used against a shared or production database. Override `TEST_ADMIN_USERNAME` and `TEST_ADMIN_PASSWORD` on the reset command to choose different test credentials.

Other optional settings are `BASE_URL`, `JOB_TIMEOUT_SECONDS`, and `POLL_INTERVAL_SECONDS`.

The JSON seed files remain available for manual database initialization across all supported datasets, but the automated test only creates or resets its selected dataset.

## Troubleshooting

### Admin Login Failed

The database supports one admin account. If setup finds an existing account, it will not create `sample-admin`. The runner now reports the existing username.

Use the existing credentials:

```bash
TEST_ADMIN_USERNAME=existing-name \
TEST_ADMIN_PASSWORD='existing-password' \
make test-app
```

For a disposable local database where the password is unavailable, use the guarded `test-admin-reset` command shown above.

### Fixture Dataset Is Not Empty

A previous test run leaves its teams and uploaded files in MongoDB. Use:

```bash
make test-app-reset CONFIRM_TEST_RESET=1
```

This reset is limited to the Basketball/Men's/High School fixture dataset.

### Background Job Failed or Timed Out

Inspect FastAPI and ARQ output:

```bash
make app-logs
```

For a slow machine, increase the polling timeout:

```bash
JOB_TIMEOUT_SECONDS=300 make test-app
```

## Happy-Path Test

The Make target runs [`scripts/application_smoke_test.sh`](../../scripts/application_smoke_test.sh), which performs and verifies the same requests as [`api-smoke-test.http`](api-smoke-test.http). The HTTP file remains useful for inspecting individual responses or debugging a failed stage.

The equivalent UI-oriented workflow is:

1. Create the initial admin through `/setup/admin/`, then log in.
2. Select Basketball, Men's, High School in the application controls.
3. Upload `week-01.csv` from the Add Teams page.
4. When prompted for missing teams, use the values from `teams.json`. The first week contains six teams.
5. Upload `week-02.csv` and `week-03.csv`; neither should introduce another team.
6. Upload `week-04.csv` and add `QA Reserve` when prompted.
7. Run the main algorithm once from Calculate Values and wait for completion.
8. Run the z-score calculation and wait for completion.
9. Open Teams, a team detail page, and Predictions to verify public reads.
10. Use the admin screens to test score updates, renaming, game deletion, and team deletion.

For an exact and deterministic team-ID order, post `teams.json` through the smoke-test request before uploading the game files. The UI missing-team list is created from a set, so its insertion order and generated team IDs can vary.

## Expected Happy-Path Results

After all four files are uploaded and the main algorithm completes once:

- Seven teams should appear in the team list.
- Each game should appear on both participating team pages.
- The win/loss records should match `expected-records.json`.
- Power-ranking values should differ from their `initial` values.
- A prediction between any two sample teams should return two decimal scores.
- The neutral-site games in weeks 1, 2, 3, and 4 should be calculated without home-field advantage.
- A flagged game should appear in `/retrieve-flagged/` and disappear after `/clear-flagged`.

The expected records are calculated from 13 games. There must be 13 total wins and 13 total losses across the seven teams.

## Destructive Checks

Run the maintenance checks only after a successful happy-path test:

```bash
make test-app-maintenance CONFIRM_DESTRUCTIVE=1
```

This target performs requests that mutate or remove data:

- Correct a game's score.
- Rename `QA Reserve` and restore its original name.
- Find and delete one game.
- Delete the QA team.
- Clear the season.

Team IDs in that section assume `teams.json` was inserted into a fresh empty dataset in its listed order. Call `/teams-ids/` and adjust the variables at the top of the HTTP file if teams were created through the UI or already existed.

## Negative Cases

Run negative files against a disposable dataset after finishing the happy path:

| File | Intended check |
| --- | --- |
| `wrong-column-count.csv` | The algorithm rejects rows that do not contain six columns |
| `header-included.csv` | Demonstrates why production uploads must be headerless |
| `non-numeric-score.csv` | Shows current score cleaning, which coerces invalid scores to zero |
| `not-a-csv.txt` | The upload endpoint rejects a non-`.csv` filename |

The upload endpoint stores CSV bytes before the algorithm performs full row validation. An invalid CSV can therefore upload successfully and fail only when the background job processes it. Keep negative cases out of the happy-path dataset.

## Current Behaviors These Fixtures Expose

- The first upload into a new `csv_files` document may report `files_uploaded: 0` even though MongoDB performed an upsert and stored the file.
- The current z-score runner calculates after iterating through stored files while retaining only the final file's DataFrame.
- Game update and delete operations should be checked in both MongoDB and the UI; their CSV lookup and generated game-ID paths currently use different assumptions.
- Flagging requires a dataset document in `flagged_games`; that is why a separate seed file is included.

These are application behaviors, not special requirements of the sample data.
