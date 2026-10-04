# Previous-Season CSV Migration

This workflow imports a final ranking snapshot from the legacy application into the current rankings dataset. It is intentionally separate from game ingestion: it prepares the previous season for review and archiving, after which the administrator starts the next season with the normal reset action.

## Workflow

For each sport, gender, and level:

1. Select the dataset in the admin header.
2. Open **Add Teams** and import the team metadata CSV first.
3. Return to the dashboard and open **Import Previous Season**.
4. Select the legacy final ranking export and review the confirmation.
5. Complete the import and review any flagged team rows or recent-opponent warnings.
6. Return to the dashboard and choose **Archive Selected Sport**. The archive year defaults to the selected dataset's `season_year` (or the current year if unset) and can be changed before publishing.
7. Verify the public archive, then choose **Reset Selected Sport** to begin the next season.

The import does not delete teams, games, uploads, or archives. Reset remains a separate, explicitly confirmed operation.

## Matching Rule

The legacy season export uses `team_id` as a team name. It is not the current numeric team identifier.

```text
legacy season team_id -> current MongoDB teams[].short_name
```

Matching ignores capitalization and repeated whitespace but does not fall back to `team_name` or `long_name`. A row with no unique `short_name` match is flagged, skipped, and returned in the import result. Other valid rows continue importing.

## Required Headers

Column order does not matter and extra columns such as the legacy `id` are ignored.

```text
team_id
wins
losses
ties
power
overall_rank
recent_opponent_1
recent_opponent_2
recent_opponent_3
recent_opponent_4
recent_opponent_5
div_rank
```

The CSV filename must contain the selected gender, level, and sport names in any order; matching is case-insensitive. Only the headers listed above are required. Any other columns, including `week_id`, are ignored. The admin dataset selection is verified against the filename.

## Stored Fields

For every matched team, the importer preserves team identity and metadata from the earlier Teams import and replaces these final-season values:

| Legacy column                                   | MongoDB team field              |
| ----------------------------------------------- | ------------------------------- |
| `wins`                                          | `wins`                          |
| `losses`                                        | `losses`                        |
| `ties`                                          | `ties`                          |
| `power`                                         | Latest entry in `power_ranking` |
| `overall_rank`                                  | `overall_rank`                  |
| `div_rank`                                      | `division_rank`                 |
| `recent_opponent_1` through `recent_opponent_5` | `recent_opp`                    |

`team_id` is used only to match the existing team's `short_name`; it does not replace the team's numeric ID. The snapshot is keyed by its import timestamp, and importing does not change the dataset's `season_year`. A successful import removes obsolete `week_id`, `actual_change`, `total_score`, and `num_games` fields from the selected dataset's team records, and clears old top-level source-week metadata. Active fields such as `last_rank`, `win_ratio`, and `season_initial_power` are preserved. An unknown recent-opponent numeric ID is replaced with `0` and reported as a warning because MongoDB does not enforce foreign keys.

At the dataset level, the application records the filename, import time, row counts, and snapshot key. The imported ranking is marked current so it can be reviewed and archived without running the ranking algorithm.

## Reset Result

After the archive is verified, **Reset Selected Sport**:

- Advances `season_year` by one.
- Preserves team identity, metadata, power, overall rank, division rank, and last rank.
- Uses the imported final power as `season_initial_power` for the next ranking cycle.
- Clears wins, losses, ties, win ratio, and legacy calculation counters.
- Removes canonical games and upload records according to the normal reset workflow.
- Preserves no more than the final five existing `season_opp` game records.

The legacy ranking export contains opponent IDs but not enough score, date, home/away, and z-score information to reconstruct `season_opp` records.
