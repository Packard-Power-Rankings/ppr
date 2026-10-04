# MongoDB Data Model

This document describes the MongoDB collections currently used by Packard Power Rankings. MongoDB calls them **collections** rather than tables. The application does not install MongoDB JSON Schema validators, so the service layer enforces the shapes below and older documents may omit newer optional fields.

## Databases and Collections

| Database        | Collection          | Document unit                                  | Purpose                                                              |
| --------------- | ------------------- | ---------------------------------------------- | -------------------------------------------------------------------- |
| `sports_data`   | `temp2`             | One document per sport/gender/level            | Team metadata, rankings, season records, and ranking scheduler state |
| `sports_data`   | `games`             | One document per current-season game           | Canonical source for ranking and z-score calculations                |
| `sports_data`   | `csv_files`         | One document per sport/gender/level            | Metadata for validated source files stored on disk                   |
| `sports_data`   | `flagged_games`     | One document per sport/gender/level            | Open and resolved game issue reports                                 |
| `sports_data`   | `previous_season`   | One document per sport/gender/level            | Legacy previous-season team snapshots                                |
| `admin_details` | `admin`             | One document for the application administrator | Login identity and bcrypt password hash                              |
| `admin_details` | `execution_history` | One document per background job                | Recent ranking and z-score job status and errors                     |

Most sports documents use the same dataset key:

```javascript
{
  sport_type: "basketball", // basketball or football
  gender: "mens",          // mens or womens
  level: "high_school"     // high_school or college
}
```

The application currently supports six dataset combinations: men's football at both levels and men's and women's basketball at both levels.

## Type and Date Conventions

- MongoDB-generated identifiers and fixed dataset identifiers use `ObjectId`, except execution-history `_id`, which is the string task ID.
- `game_date` and `sports_week` are ISO date strings such as `2026-01-09`.
- Sports timestamps such as `created_at`, `reported_at`, and `ranking_completed_at` are BSON UTC datetimes.
- Execution-history timestamps are UTC ISO strings such as `2026-10-03T07:00:00Z`.
- Team and game IDs are integers. MongoDB does not enforce cross-collection foreign keys.
- Fields marked optional can be absent from older records or `null` while an operation is incomplete.

## `sports_data.temp2`

This is the main denormalized rankings collection. Each document owns one dataset and embeds all of its teams.

### Dataset Fields

| Field                     | Type          | Presence        | Meaning                                                                                               |
| ------------------------- | ------------- | --------------- | ----------------------------------------------------------------------------------------------------- |
| `_id`                     | `ObjectId`    | Required        | Fixed dataset ID from `LEVEL_CONSTANTS`; used for direct lookups                                      |
| `sport_type`              | string        | Required        | `basketball` or `football`                                                                            |
| `gender`                  | string        | Required        | `mens` or `womens`                                                                                    |
| `level`                   | string        | Required        | `high_school` or `college`                                                                            |
| `season_year`             | integer       | Optional        | Season represented by the current rankings; preserved by previous-season import and advanced by reset |
| `teams`                   | array         | Required        | Embedded team documents described below                                                               |
| `games_revision`          | integer       | Startup-managed | Incremented whenever canonical game input changes                                                     |
| `ranked_revision`         | integer       | Startup-managed | Game revision represented by the last completed ranking                                               |
| `rankings_stale`          | boolean       | Startup-managed | Whether current games are newer than published rankings                                               |
| `ranking_status`          | string        | Startup-managed | `current`, `stale`, `queued`, `in_progress`, `failed`, or `no_games`                                  |
| `ranking_requested_at`    | datetime/null | Optional        | Most recent time a game change requested recalculation                                                |
| `ranking_task_id`         | string        | Optional        | ARQ task currently or most recently associated with this dataset                                      |
| `ranking_trigger`         | string        | Optional        | `manual`, `automatic`, or `weekly`                                                                    |
| `ranking_iterations`      | integer       | Optional        | Iteration count requested for the full ranking job                                                    |
| `ranking_started_at`      | datetime      | Optional        | Time the worker began the current/last ranking job                                                    |
| `ranking_completed_at`    | datetime      | Optional        | Last time the scheduler or an import marked the dataset current or without games; reset skips it      |
| `ranking_error`           | object/null   | Optional        | Last scheduler error with `type`, `message`, and `location`                                           |
| `last_rank_snapshot_week` | string        | Optional        | Local ISO week, for example `2026-W40`, last copied into team `last_rank`                             |
| `last_rank_snapshot_at`   | datetime      | Optional        | UTC time of that weekly rank snapshot                                                                 |
| `previous_season_import`  | object        | Import-created  | Audit metadata for the most recent final-ranking CSV import; fields listed below                      |

### `previous_season_import` Fields

| Field             | Type              | Meaning                                                           |
| ----------------- | ----------------- | ----------------------------------------------------------------- |
| `source_filename` | string            | Imported CSV filename                                             |
| `snapshot_key`    | ISO UTC string    | Timestamp key used for the imported power snapshot                |
| `imported_at`     | BSON UTC datetime | Time the import completed                                         |
| `rows_total`      | integer           | Number of valid rows in the CSV                                   |
| `teams_updated`   | integer           | Number of rows matched to existing teams                          |
| `teams_flagged`   | integer           | Number of rows skipped because no unique short-name match existed |

### `teams[]` Fields

| Field                  | Type              | Presence             | Meaning                                                                                                                                              |
| ---------------------- | ----------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `team_id`              | integer           | Required             | Canonical positive team identifier; unique within the dataset by application validation                                                              |
| `team_name`            | string            | Required             | Canonical display and game-matching name; normally the short name                                                                                    |
| `short_name`           | string            | Current imports      | Short display name and source of `team_name`                                                                                                         |
| `long_name`            | string            | Current imports      | Full school or organization name                                                                                                                     |
| `city`                 | string            | Optional             | Team city; new imports currently initialize it to an empty string                                                                                    |
| `state`                | string/null       | Optional             | State name or code supplied by team metadata                                                                                                         |
| `division`             | string/null       | Optional             | Division/classification used for division rankings                                                                                                   |
| `conference`           | string/null       | Optional             | Conference used for conference rankings                                                                                                              |
| `ranked`               | boolean           | Current imports      | Team ranking-eligibility metadata supplied by the administrator                                                                                      |
| `power_ranking`        | array of objects  | Required             | Ordered power history, beginning with `{initial: number}`; algorithm entries use game dates and previous-season imports use an ISO UTC timestamp key |
| `overall_rank`         | integer           | Imported/derived     | Current overall position; lower numbers are better                                                                                                   |
| `last_rank`            | integer           | Derived              | Overall rank captured by the Sunday scheduler for weekly movement comparison                                                                         |
| `division_rank`        | integer           | Imported/derived     | Position among teams with the same division                                                                                                          |
| `conference_rank`      | integer           | Derived              | Position among teams with the same conference                                                                                                        |
| `wins`                 | integer           | Imported/derived     | Wins from the previous-season import or calculated from canonical current-season games                                                               |
| `losses`               | integer           | Imported/derived     | Losses from the previous-season import or calculated from canonical current-season games                                                             |
| `ties`                 | integer           | Imported/reset       | Final tie count from previous-season import; reset clears it                                                                                         |
| `win_ratio`            | number            | Derived              | `wins / (wins + losses)`, or `0.0` when no games exist                                                                                               |
| `date`                 | string            | Derived              | Latest game date represented by the ranking calculation                                                                                              |
| `recent_opp`           | array of integers | Imported/derived     | Up to five opponent team IDs used by ranking propagation; zero pads unused positions                                                                 |
| `season_opp`           | array             | Derived              | Reciprocal materialized game views for this team                                                                                                     |
| `season_initial_power` | object/null       | Reset-created        | Last power entry captured as the seed for the next season                                                                                            |
| `actual_change`        | number            | Legacy/reset-created | Reset initializes this unused legacy counter to `0.0`; successful previous-season import removes it                                                  |
| `total_score`          | number            | Legacy/reset-created | Reset initializes this unused legacy counter to `0.0`; successful previous-season import removes it                                                  |
| `num_games`            | number            | Legacy/reset-created | Reset initializes this unused legacy counter to `0.0`; successful previous-season import removes it                                                  |

Team import creates each new team entry with `overall_rank`, `division_rank`, `conference_rank`, and `last_rank` set to `0`, `wins`/`losses` set to `0`, `win_ratio` set to `0.0`, `date` set to an empty string, `recent_opp` set to five zeros, and an empty `season_opp`. These placeholders stay until a ranking run or previous-season import replaces them.

Previous-season CSV imports require only `team_id`, `wins`, `losses`, `ties`, `power`, `overall_rank`, `recent_opponent_1` through `recent_opponent_5`, and `div_rank`. `team_id` matches `teams[].short_name`; the remaining values map to the correspondingly named fields, with `power` stored as the latest `power_ranking` entry, `div_rank` mapped to `division_rank`, and the five opponents stored as `recent_opp`. Extra CSV columns, including `week_id`, are ignored and no `week_id` is stored. On a successful import, old `week_id`, `actual_change`, `total_score`, and `num_games` fields are removed from all team entries in the selected dataset, along with obsolete top-level week/source metadata. Active fields such as `last_rank`, `win_ratio`, and `season_initial_power` are preserved.

### `teams[].season_opp[]` Fields

| Field           | Type         | Meaning                                                      |
| --------------- | ------------ | ------------------------------------------------------------ |
| `opponent_id`   | integer      | Canonical ID of the opposing team                            |
| `opponent_name` | string       | Denormalized opponent name kept in sync by rename operations |
| `home_team`     | integer/bool | `1`/true when this team was home, otherwise `0`/false        |
| `home_score`    | integer      | Home team's score                                            |
| `away_score`    | integer      | Away team's score                                            |
| `home_z_score`  | number       | Derived z-score for the home performance                     |
| `away_z_score`  | number       | Derived z-score for the away performance                     |
| `game_date`     | string       | ISO game date                                                |
| `game_id`       | string       | Canonical ordered game ID shared with `games.game_id`        |

Season reset advances `season_year`, preserves ranking fields and the final five `season_opp` entries, sets wins/losses/ties/win ratio and legacy calculation counters to zero, and removes the canonical current-season games. It also increments `games_revision`, sets `ranked_revision` to that new value, sets `ranking_status` to `no_games` with `rankings_stale` false, and clears `ranking_requested_at` and `ranking_error`. Reset does not update `ranking_completed_at`, so that field keeps the time of the last completed ranking or import.

## `sports_data.games`

This is the canonical current-season game store. Ranking jobs read this collection rather than reparsing uploaded CSV files.

| Field              | Type       | Presence | Meaning                                                          |
| ------------------ | ---------- | -------- | ---------------------------------------------------------------- |
| `_id`              | `ObjectId` | Required | MongoDB document identifier                                      |
| `sport_type`       | string     | Required | Dataset sport                                                    |
| `gender`           | string     | Required | Dataset gender                                                   |
| `level`            | string     | Required | Dataset level                                                    |
| `identity`         | string     | Required | Rename-safe duplicate key: `date\|lower_team_id\|higher_team_id` |
| `game_id`          | string     | Required | Ordered ID: `home_team_id_away_team_id_date`                     |
| `game_date`        | string     | Required | Normalized ISO date                                              |
| `home_team_id`     | integer    | Required | Canonical home-team ID                                           |
| `home_team`        | string     | Required | Denormalized home-team name                                      |
| `away_team_id`     | integer    | Required | Canonical away-team ID                                           |
| `away_team`        | string     | Required | Denormalized away-team name                                      |
| `home_score`       | integer    | Required | Nonnegative home score                                           |
| `away_score`       | integer    | Required | Nonnegative away score                                           |
| `neutral_site`     | integer    | Required | `0` for normal home advantage or `999` for a neutral site        |
| `home_z_score`     | number     | Derived  | Home performance z-score; starts at `0.0`                        |
| `away_z_score`     | number     | Derived  | Away performance z-score; starts at `0.0`                        |
| `source_upload_id` | string     | Required | Links to an entry in `csv_files[].upload_id`                     |
| `source_filename`  | string     | Required | Original or generated manual-entry filename                      |
| `created_at`       | datetime   | Required | Initial ingestion time                                           |
| `updated_at`       | datetime   | Required | Last score update time                                           |

`identity` sorts the two team IDs, so reversing home and away does not bypass duplicate detection. `game_id` preserves home/away order for team views and admin operations.

## `sports_data.csv_files`

Each dataset document contains metadata for its uploaded or manually generated source files. CSV bytes are stored under `UPLOAD_DIR`, not in MongoDB.

### Upload Metadata Document Fields

| Field        | Type       | Meaning                        |
| ------------ | ---------- | ------------------------------ |
| `_id`        | `ObjectId` | MongoDB document identifier    |
| `sport_type` | string     | Dataset sport                  |
| `gender`     | string     | Dataset gender                 |
| `level`      | string     | Dataset level                  |
| `csv_files`  | array      | Source upload metadata entries |

### `csv_files[]` Fields

| Field          | Type          | Presence              | Meaning                                                                                    |
| -------------- | ------------- | --------------------- | ------------------------------------------------------------------------------------------ |
| `upload_id`    | string        | Required              | UUID-like identifier referenced by canonical games                                         |
| `filename`     | string        | Required              | Original filename or generated manual-game filename                                        |
| `storage_path` | string        | Required              | Relative path below `UPLOAD_DIR`                                                           |
| `upload_date`  | datetime      | Required              | UTC ingestion time                                                                         |
| `sports_week`  | string        | Required              | Normalized date associated with the first game in the upload                               |
| `game_count`   | integer       | Required              | Number of canonical games created from the file                                            |
| `migrated_at`  | datetime      | Legacy migration only | Time an old Mongo-stored file was moved to disk                                            |
| `filedata`     | binary/string | Legacy only           | Old embedded CSV payload; startup migration removes it after successful filesystem storage |

Resetting a dataset deletes its `games` documents, this metadata document, and the referenced files on disk.

## `sports_data.flagged_games`

Each dataset document embeds its public game issue reports. Resolved issues remain as review history.

### Flagged-Game Document Fields

| Field           | Type       | Meaning                         |
| --------------- | ---------- | ------------------------------- |
| `_id`           | `ObjectId` | MongoDB document identifier     |
| `sport_type`    | string     | Dataset sport                   |
| `gender`        | string     | Dataset gender                  |
| `level`         | string     | Dataset level                   |
| `flagged_games` | array      | Open and resolved issue entries |

### `flagged_games[]` Fields

| Field         | Type     | Presence      | Meaning                                                                          |
| ------------- | -------- | ------------- | -------------------------------------------------------------------------------- |
| `issue_id`    | string   | Required      | Unique issue UUID used by the resolve endpoint                                   |
| `game_id`     | string   | Required      | Reported canonical game ID                                                       |
| `team1_id`    | integer  | Required      | Canonical home-team ID at report time                                            |
| `team1_name`  | string   | Required      | Denormalized home-team name                                                      |
| `team2_id`    | integer  | Required      | Canonical away-team ID at report time                                            |
| `team2_name`  | string   | Required      | Denormalized away-team name                                                      |
| `description` | string   | Required      | User-provided problem description; legacy records receive a fallback description |
| `reported_at` | datetime | Required      | UTC report time                                                                  |
| `status`      | string   | Required      | `open` or `resolved`                                                             |
| `resolved_at` | datetime | Resolved only | UTC time an administrator resolved the issue                                     |

Only one unresolved report for the same `game_id` is accepted at a time. This is enforced atomically by the service, not by a MongoDB unique index.

## `sports_data.previous_season`

Documents use the same dataset fields and embedded `teams[]` shape as `temp2`. This collection is retained for legacy previous-season snapshots and is still updated when teams are renamed or deleted.

The current archive and reset workflows do **not** write here. Public season archives are immutable JSON and HTML files in `ARCHIVE_DIR`/the `archive_data` volume. A reset also does not copy current data into `previous_season`.

## `admin_details.admin`

The current application supports one administrator account.

| Field      | Type       | Meaning                                                    |
| ---------- | ---------- | ---------------------------------------------------------- |
| `_id`      | `ObjectId` | MongoDB document identifier                                |
| `username` | string     | Login username; uniquely indexed                           |
| `password` | string     | bcrypt password hash; plaintext passwords are never stored |

The single-account restriction is enforced by checking for any existing document before insertion.

## `admin_details.execution_history`

This collection stores recent ARQ ranking and z-score jobs. The application retains the latest five records per process and dataset.

| Field         | Type                | Presence | Meaning                                                |
| ------------- | ------------------- | -------- | ------------------------------------------------------ |
| `_id`         | string              | Required | ARQ task ID                                            |
| `task_id`     | string              | Required | Same task ID exposed to the frontend and Redis         |
| `process`     | string              | Required | `algorithm` or `z_scores`                              |
| `sport_type`  | string              | Required | Dataset sport                                          |
| `gender`      | string              | Required | Dataset gender                                         |
| `level`       | string              | Required | Dataset level                                          |
| `iterations`  | integer/null        | Required | Ranking iterations; null for z-score-only jobs         |
| `trigger`     | string              | Required | Usually `manual`, `automatic`, or `weekly`             |
| `status`      | string              | Required | `queued`, `in_progress`, `complete`, or `failed`       |
| `queued_at`   | ISO UTC string      | Required | Time the job record was created                        |
| `started_at`  | ISO UTC string/null | Required | Worker start time when known                           |
| `finished_at` | ISO UTC string/null | Required | Completion/failure time when known                     |
| `updated_at`  | ISO UTC string      | Required | Last status transition time                            |
| `error`       | object/null         | Required | Failure details with `type`, `message`, and `location` |

## Indexes

Indexes are created or repaired during FastAPI startup.

| Collection          | Index                                 | Keys                              | Purpose                                  |
| ------------------- | ------------------------------------- | --------------------------------- | ---------------------------------------- |
| `temp2`             | `uq_dataset_key`                      | `sport_type`, `gender`, `level`   | One current team document per dataset    |
| `csv_files`         | `uq_dataset_key`                      | `sport_type`, `gender`, `level`   | One upload container per dataset         |
| `flagged_games`     | `uq_dataset_key`                      | `sport_type`, `gender`, `level`   | One issue container per dataset          |
| `previous_season`   | `uq_dataset_key`                      | `sport_type`, `gender`, `level`   | One legacy snapshot per dataset          |
| `games`             | `uq_game_identity`                    | dataset key plus `identity`       | Prevent duplicate games within a dataset |
| `games`             | `ix_games_dataset_date`               | dataset key plus `game_date`      | Ordered ranking input and date lookup    |
| `games`             | `ix_games_dataset_game_id`            | dataset key plus `game_id`        | Admin update/delete and issue lookup     |
| `admin`             | `uq_admin_username`                   | `username`                        | Prevent duplicate usernames              |
| `execution_history` | `ix_execution_history_process_queued` | `process`, `queued_at` descending | Recent job-history queries               |

The four dataset-key indexes and the admin username index are unique and sparse. Team IDs are embedded inside `temp2.teams`, so their per-dataset uniqueness is enforced by ingestion and migration code rather than by an index.

## Relationships and Write Ownership

```text
temp2.teams[].team_id
  <- games.home_team_id / games.away_team_id
  <- temp2.teams[].season_opp[].opponent_id
  <- flagged_games[].team1_id / team2_id

csv_files[].upload_id
  <- games.source_upload_id

games.game_id
  <- temp2.teams[].season_opp[].game_id
  <- flagged_games[].game_id

execution_history.task_id
  <-> Redis/ARQ job ID
```

These are application-managed relationships, not MongoDB foreign keys. Team rename and delete services deliberately update denormalized names and references across the related collections.

## Data Lifecycle Summary

1. Team import creates or extends the dataset document in `temp2`.
2. Game ingestion validates a file, writes its reference file to disk, inserts canonical `games`, appends `csv_files` metadata, and marks `temp2` stale.
3. The ranking worker reads `games`, replaces derived team ranking and season fields in `temp2`, and writes z-scores to both canonical and materialized game records.
4. Public issue reporting appends to `flagged_games`; resolution updates status without deleting history.
5. Reset deletes current `games`, upload metadata, and source files while retaining teams and selected ranking history.
6. Archive generation reads `temp2` and writes static files outside MongoDB.
