# Production Ranking Pipeline

This directory contains the calculation pipeline used by the FastAPI ARQ worker. CSV is an ingestion format only. By the time this pipeline starts, every game has already been validated and normalized into `sports_data.games`.

## Data Flow

```text
Add Games
  -> validate CSV or individual form
  -> store canonical games in sports_data.games
  -> retain source CSV under UPLOAD_DIR

Run Rankings
  -> query canonical games in date/game-ID order
  -> load each team's initial ranking seed
  -> calculate the requested iterations in memory
  -> replace derived team rankings and season_opp records
  -> calculate z-scores from the same canonical game set
  -> write z-scores to games and both reciprocal team views
```

The original source upload is an immutable reference. The algorithm never opens it. Score corrections, team renames, and deletions update canonical game records, after which a ranking run rebuilds the derived views.

## Modules

| Module | Responsibility |
| --- | --- |
| `run.py` | Query MongoDB, adapt games to a DataFrame, coordinate iterations, persistence, and z-scores |
| `data_cleaning.py` | Normalize score and team values for calculations |
| `data_enrichment.py` | Add constants and current in-memory team rankings |
| `main.py` | Calculate score adjustments, expected performance, power changes, propagation, and z-scores |
| `output.py` | Replace derived team records, ranks, histories, and z-scores in MongoDB |
| `upload.py` | Legacy/isolated file adapter; not used by the production runner |

## Repeatability

Every ranking invocation starts from the first value in each team's `power_ranking` history. The worker then processes all canonical games for each requested iteration and writes one final snapshot. Running the same dataset with the same iteration count therefore produces the same rankings rather than adding the changes again.

`POST /run_algorithm/{iterations}` accepts 1 through 100 iterations and runs rankings plus z-scores. `POST /calc_z_scores/` only refreshes z-scores using current rankings.

## Tests

From the repository root:

```bash
make test-backend-algorithm
make test-backend-service
make test-app-reset CONFIRM_TEST_RESET=1
```

The full fixture reset creates 60 canonical games and six filesystem source references. The algorithm tests verify Mongo-backed loading, full pipeline sequencing, bounded iterations, and z-score scaling.
