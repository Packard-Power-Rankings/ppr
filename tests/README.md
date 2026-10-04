# Test Suites

All automated tests, application smoke fixtures, and the standalone algorithm harness live under this directory.

## Layout

| Path | Purpose |
| --- | --- |
| `backend/service/` | FastAPI service and datastore behavior tests |
| `backend/algorithm/` | Production algorithm unit tests |
| `frontend/` | React component, routing, and admin workflow tests |
| `application/` | End-to-end API smoke runner and its fixtures |
| `deployment/` | Caddy edge-security behavior tests |
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

Before pushing, run the same checks as the GitHub CI/CD workflow: Compose configuration validation for both `.env/development.example` and your `.env/development`, `make test-check`, `make test-security`, and the deployment security policy test. Recent service logs are printed if any step fails. Unlike CI, it reuses your running stack and does not delete volumes:

```bash
make ci
```

Focused targets are available when working on one area:

```bash
make test-backend
make test-backend-service
make test-backend-algorithm
make test-backend-lint
make test-frontend
make test-frontend-app
make test-frontend-admin
make test-frontend-archive
make test-frontend-teams
make test-lint
make test-build
make test-security
make test-security-python
make test-security-frontend
make test-deployment-security
```

These targets build and start the local Docker Compose stack when needed. `make test-security` runs Bandit and `pip-audit` for the backend (`make test-security-python`), and `eslint-plugin-security` and `npm audit` for the frontend (`make test-security-frontend`); the audits require access to current advisory databases. `make test-deployment-security` starts a disposable Caddy container and verifies browser access, bot rejection, probe-path rejection, health-check exemption, and structured detection logs. Run `make help` for the complete command list.

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
