# Season Archive Mental Model

The season archive is a collection of public, read-only snapshots of rankings. Each
snapshot belongs to one calendar year and is stored separately from the live season
data in MongoDB.

The central idea is:

```text
Live MongoDB rankings
        |
        | Admin archives one selected dataset or all sports
        v
Filesystem snapshot for one year
        |
        +--> React archive pages at /archives/...
        `--> Standalone HTML pages at /archive/<year>/...
```

An archive is a snapshot, not another live view. Changes to teams, games, or rankings
after publication do not change an existing archive unless an administrator explicitly
overwrites that dataset or the complete year.

## Where This Directory Fits

This source directory is intentionally almost empty. At runtime, Docker mounts the
persistent `archive_data` volume here as read-only data for the development frontend:

```text
archive_data volume -> /app/public/archive
```

In the Lightsail deployment, the same volume is mounted read-only into the frontend
container at `/srv/archive`, where Caddy serves it under `/archive/`.

The backend mounts the volume read-write at `/var/lib/ppr-archives`. Therefore:

- FastAPI owns archive creation and replacement.
- The frontend can read and serve archives but cannot modify them.
- Container rebuilds do not remove archives because the files live in a named volume.
- `docker compose down --volumes` does remove the archive volume and must not be used
  when the archive data needs to be preserved.

This `README.md` documents the directory in source control. The IDE reads that host
directory, so seeing only this README is expected even when a generated `2026/` archive
exists. The runtime volume mount does not copy generated files back into the repository.
Inside the running frontend container, `/app/public/archive/2026/` contains the generated
files instead.

For local development, open the archive through either presentation:

```text
http://localhost:3000/archives/2026
http://localhost:3000/archive/2026/index.html
```

## Runtime Components

| Component | Responsibility |
| --- | --- |
| MongoDB `sports_data.temp2` | Holds the current teams, games, records, and rankings |
| Admin dashboard | Checks archive status and requests archive creation or overwrite |
| FastAPI `ArchiveService` | Reads current rankings and generates the snapshot files |
| Docker `archive_data` volume | Persists all published years |
| React archive view | Presents archive data through normal application routes |
| React dev server or Caddy | Serves the generated standalone HTML files |

The public filesystem archive is separate from the MongoDB `previous_season`
collection. Creating an archive does not write to `previous_season`, and resetting a
season does not copy data into it or alter an existing public archive.

## Creating Archives

The admin dashboard provides two archive scopes.

### Selected Sport

```text
GET /archive-season/status/selected?sport_type=...&gender=...&level=...
        |
        +--> Dataset is not archived
        |       `--> POST /archive-season/selected/?year=<year>&overwrite=false&...
        |
        `--> Dataset is already archived
                `--> Ask for dataset overwrite confirmation
                     `--> POST /archive-season/selected/?year=<year>&overwrite=true&...
```

This action snapshots only the selected sport, gender, and level. When the year already
contains other datasets, FastAPI merges the new snapshot into that archive and preserves
the others. Only replacing the same selected dataset requires overwrite confirmation.

### All Sports

```text
GET /archive-season/status
        |
        +--> Year does not exist
        |       `--> POST /archive-season/all/?year=<year>&overwrite=false
        |
        `--> Year already exists, even as a partial archive
                `--> Ask for full-year overwrite confirmation
                     `--> POST /archive-season/all/?year=<year>&overwrite=true
```

This action reads every current dataset and produces a complete archive for the year.
It replaces any partial or complete archive for that year after explicit confirmation.

The dashboard defaults to the current UTC calendar year. All archive endpoints require
admin authentication.

When FastAPI receives an archive request, it:

1. Reads the selected dataset or every dataset from `sports_data.temp2`.
2. Normalizes the fields needed by the public rankings pages.
3. Sorts teams with ranked teams first, using stored overall rank and current power.
4. Merges selected-sport data with any other datasets already archived for the year.
5. Generates a year index and one standalone HTML page per dataset.
6. Writes everything into a temporary directory.
7. Replaces only the requested year directory after generation succeeds.
8. Refreshes the top-level archive catalog.

Using a temporary directory prevents visitors from seeing a partially generated year
while files are still being written.

## Runtime File Layout

After archiving 2025 and 2026, the volume resembles:

```text
/var/lib/ppr-archives/
|-- index.json
|-- 2025/
|   |-- data.json
|   |-- index.html
|   |-- basketball-mens-college.html
|   |-- basketball-mens-high-school.html
|   |-- basketball-womens-college.html
|   |-- basketball-womens-high-school.html
|   |-- football-mens-college.html
|   `-- football-mens-high-school.html
`-- 2026/
    |-- data.json
    |-- index.html
    `-- ...dataset HTML pages...
```

`data.json` is the canonical snapshot for a year. A year counts as an available archive
only when that file exists and contains readable JSON.

## Year, Scope, and Overwrite Rules

Different years are independent:

```text
Archive 2025 -> creates or replaces only /2025
Archive 2026 -> creates or replaces only /2026
```

Creating the 2026 archive does not overwrite, merge with, or move the 2025 archive.
Both years remain available, and the archive catalog displays newer years first.

The overwrite behavior is scoped to one year and, for selected archiving, one dataset:

| Situation | Result |
| --- | --- |
| Selected dataset and requested year do not exist | A partial year archive is created |
| Requested year exists but selected dataset does not | The dataset is added; existing datasets remain |
| Selected dataset exists and `overwrite=false` | The API returns a conflict and changes nothing |
| Selected dataset exists and `overwrite=true` | Only that dataset is refreshed; others remain |
| Archive All Sports targets an existing year with `overwrite=false` | The API returns a conflict and changes nothing |
| Archive All Sports uses `overwrite=true` | The complete year is rebuilt from current rankings |
| Another year already exists | That other year remains unchanged |

Overwriting is useful when rankings were archived too early or corrected before the
season was reset. Once live data has been reset, the prior ranking state cannot be
reconstructed from the current-season database.

## Reading an Archive

There are two public presentations of the same snapshot.

### React Application

```text
/archives
/archives/<year>
/archives/<year>/<dataset-slug>
```

The React view calls:

```text
GET /archives/
GET /archives/<year>
```

FastAPI scans the available year directories and reads each year's `data.json`.

### Standalone Static HTML

```text
/archive/<year>/index.html
/archive/<year>/<dataset-slug>.html
```

These pages contain their own styling and ranking table. They do not need React or a
live MongoDB query after generation, which makes them suitable as durable public season
records.

## Reset Interaction

Archive and reset are deliberately separate actions:

```text
Archive Selected Sport -> saves one dataset; live data is unchanged
Archive All Sports     -> saves a complete snapshot; live data is unchanged
Reset Selected Sport   -> starts a selected dataset's new season; archive is unchanged
Reset All Sports       -> starts every dataset's new season; archive is unchanged
```

Before resetting a selected sport, the dashboard checks whether that exact dataset is
in the current-year archive. Before resetting all sports, it checks whether the year is
marked as a complete all-sports archive. A partial archive does not satisfy the second
check. If the required snapshot is missing, the dashboard warns the administrator and
asks whether to proceed without archiving. The administrator may continue, but doing so
can permanently discard the only current copy of the affected rankings.

A season reset preserves each team's overall rank, division rank, power history, ranking
date, recent-opponent IDs, and five most recent materialized game records. It resets wins,
losses, and win ratio to zero, then deletes canonical current-season games and their source
upload references so those old games cannot be included in a new ranking calculation.

## Persistence and Recovery

The named volume survives normal container recreation, image rebuilds, and application
deployments. The backend startup entrypoint repairs archive-volume ownership and then
runs the API as the unprivileged `app` user.

The archive volume is independent of the MongoDB volume. Backing up MongoDB alone does
not back up these generated files. Preserve `archive_data` separately when the static
snapshots are the historical record, especially before removing Docker volumes or
moving the application to another server.

## Key Source Files

- [`ArchiveService`](../../../backend/api/service/archive_service.py) creates, reads,
  lists, and replaces archive snapshots.
- [`admin_routes.py`](../../../backend/api/routers/admin_routes.py) exposes protected
  archive creation and status endpoints.
- [`user_routes.py`](../../../backend/api/routers/user_routes.py) exposes public archive
  read endpoints.
- [`AdminDashboard.js`](../../src/views/admin/dashboard/AdminDashboard.js) owns the
  archive and reset confirmation workflow.
- [`Archive.js`](../../src/views/archive/Archive.js) renders the public React archive.
- [`docker-compose.yml`](../../../docker-compose.yml) shares the archive volume in local
  development.
- [`docker-compose.lightsail.yml`](../../../docker-compose.lightsail.yml) shares it with
  the production backend and Caddy frontend.
