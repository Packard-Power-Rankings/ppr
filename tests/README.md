# Test Suites

All automated tests, application smoke fixtures, and the standalone algorithm harness live under this directory.

## Layout

| Path | Purpose |
| --- | --- |
| `backend/service/` | FastAPI service and datastore behavior tests |
| `backend/algorithm/` | Production algorithm unit tests |
| `frontend/` | React component, routing, and admin workflow tests |
| `application/` | End-to-end API smoke runner and its fixtures |
| `isolation/algorithm/` | Standalone CSV algorithm comparison workspace |

Docker Compose mounts `tests/backend/` and `tests/frontend/` at `/app/tests` in their respective development containers. The production stack does not include these mounts.

## Make Targets

Run the normal backend and frontend suites:

```bash
make test
```

Run the complete non-destructive verification set, including lint and a production frontend build:

```bash
make test-check
```

Focused targets are available when working on one area:

```bash
make test-backend
make test-backend-service
make test-backend-algorithm
make test-frontend
make test-frontend-app
make test-frontend-admin
make test-frontend-archive
make test-frontend-teams
make test-lint
make test-build
```

These targets build and start the local Docker Compose stack when needed. Run `make help` for the complete command list.

## Application Smoke Test

The application suite uses MongoDB fixture data and is intentionally separate from `make test`:

```bash
make test-app
```

It can create and mutate data in the Basketball/Men's/High School fixture dataset. The guarded full reset seeds every supported dataset and every application collection:

```bash
make test-app-reset CONFIRM_TEST_RESET=1
```

See [`application/README.md`](application/README.md) for the reset scope, fixture inventory, credentials, and maintenance targets.

The request file [`application/api-smoke-test.http`](application/api-smoke-test.http) uses relative fixture paths, so run individual requests with that file as the working context.

## Standalone Algorithm Harness

The isolated CSV pipeline is not part of the automated unit suite. Run it from its own directory so its relative input paths resolve:

```bash
cd tests/isolation/algorithm
python run.py
```
