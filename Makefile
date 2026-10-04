SHELL := /bin/bash
.DEFAULT_GOAL := help

APP_ENV ?= .env/development
APP_COMPOSE = docker compose --env-file $(APP_ENV)
LIGHTSAIL_ENV ?= .env/production
LIGHTSAIL_CONFIG_VARS = DOMAIN ENABLE_API_DOCS MONGO_DB_NAME MONGO_USER \
	MONGO_MAX_POOL_SIZE MONGO_PASS REDIS_PASSWORD SETUP_TOKEN SECRET_KEY \
	RANKING_DEBOUNCE_SECONDS AUTO_RANKING_ITERATIONS RANKING_TIMEZONE \
	RANKING_JOB_GUARD_SECONDS CORS_ORIGINS ALLOWED_HOSTS
LIGHTSAIL_CLEAN_ENV = env $(foreach variable,$(LIGHTSAIL_CONFIG_VARS),-u $(variable))
LIGHTSAIL_COMPOSE = $(LIGHTSAIL_CLEAN_ENV) docker compose \
	--env-file $(LIGHTSAIL_ENV) -f docker-compose.lightsail.yml

.PHONY: help app-up app-down app-logs ci ci-config test test-check test-backend \
	test-backend-service test-backend-algorithm test-backend-lint test-frontend test-frontend-app \
	test-frontend-admin test-frontend-archive test-frontend-teams test-lint test-build test-app \
	test-security test-security-python test-security-frontend test-deployment-security \
	test-app-reset test-app-maintenance test-admin-reset \
	team-id-migration-check team-id-migration-apply \
	lightsail-init lightsail-check lightsail-up lightsail-down lightsail-restart \
	lightsail-logs lightsail-status lightsail-health lightsail-backup

help:
	@echo "Packard Power Rankings development commands"
	@echo
	@echo "  make app-up                  Build and start the local stack"
	@echo "  make app-down                Stop the local stack"
	@echo "  make app-logs                Follow backend and worker logs"
	@echo "  make test                    Run backend and frontend unit tests"
	@echo "  make test-check              Run unit tests, lint, and production build"
	@echo "  make ci                      Run the same checks as GitHub CI/CD before pushing"
	@echo "  make test-backend            Run all backend tests"
	@echo "  make test-backend-service    Run backend service tests"
	@echo "  make test-backend-algorithm  Run backend algorithm tests"
	@echo "  make test-backend-lint       Check backend syntax and undefined names"
	@echo "  make test-frontend           Run all frontend tests"
	@echo "  make test-frontend-app       Run app routing and breadcrumb tests"
	@echo "  make test-frontend-admin     Run admin workflow tests"
	@echo "  make test-frontend-archive   Run public archive tests"
	@echo "  make test-frontend-teams     Run public team page tests"
	@echo "  make test-lint               Run frontend lint checks"
	@echo "  make test-build              Create the frontend production build"
	@echo "  make test-security           Run Python and JavaScript security checks"
	@echo "  make test-security-python    Scan backend code (Bandit) and audit dependencies"
	@echo "  make test-security-frontend  Scan frontend code (ESLint security) and audit dependencies"
	@echo "  make test-deployment-security Test the Caddy bot-blocking policy"
	@echo "  make test-app                Run the happy-path application smoke test"
	@echo "  make test-app-reset          Replace all local app data with full fixtures"
	@echo "  make test-app-maintenance    Run destructive maintenance endpoint checks"
	@echo "  make test-admin-reset        Replace the local admin with test credentials"
	@echo "  make team-id-migration-check Preview legacy team_num migration"
	@echo "  make team-id-migration-apply Apply migration (confirmation required)"
	@echo
	@echo "Packard Power Rankings AWS Lightsail commands"
	@echo
	@echo "  make lightsail-init DOMAIN=rankings.example.com"
	@echo "  make lightsail-check        Validate production configuration"
	@echo "  make lightsail-up           Build and start the production stack"
	@echo "  make lightsail-status       Show production container status"
	@echo "  make lightsail-logs         Follow production logs"
	@echo "  make lightsail-health       Check the public HTTPS health endpoint"
	@echo "  make lightsail-backup       Back up MongoDB, archives, and uploads"
	@echo "  make lightsail-restart      Restart production containers"
	@echo "  make lightsail-down         Stop production without deleting data"
	@echo
	@echo "Reset and maintenance targets require an explicit confirmation variable."

app-up:
	$(APP_COMPOSE) up -d --build --wait --wait-timeout 120

app-down:
	$(APP_COMPOSE) down

app-logs:
	$(APP_COMPOSE) logs -f backend arq_worker

ci: ci-config
	@$(MAKE) --no-print-directory test-check test-security test-deployment-security || { \
		echo; echo "==> CI checks failed; recent service logs:"; \
		$(APP_COMPOSE) logs --no-color --tail=200; \
		exit 1; \
	}
	@echo; echo "==> All CI checks passed"

ci-config:
	@test -f "$(APP_ENV)" || \
		(echo "Missing $(APP_ENV). Create it with: cp .env/development.example $(APP_ENV)"; exit 1)
	docker compose version
	docker compose --env-file .env/development.example config --quiet
	$(APP_COMPOSE) config --quiet

test: test-backend test-frontend

test-check: test test-backend-lint test-lint test-build

test-backend: app-up
	$(APP_COMPOSE) exec -T backend pytest -q tests

test-backend-service: app-up
	$(APP_COMPOSE) exec -T backend pytest -q tests/service

test-backend-algorithm: app-up
	$(APP_COMPOSE) exec -T backend pytest -q tests/algorithm

test-backend-lint: app-up
	$(APP_COMPOSE) exec -T backend flake8 api tests \
		--count --select=E9,F63,F7,F82 --show-source --statistics

test-frontend: app-up
	$(APP_COMPOSE) exec -T frontend npm test -- --watchAll=false --runInBand

test-frontend-app: app-up
	$(APP_COMPOSE) exec -T frontend npm test -- --watchAll=false --runInBand \
		--runTestsByPath tests/App.test.js tests/navigation.test.js \
		tests/components/AppBreadcrumb.test.js

test-frontend-admin: app-up
	$(APP_COMPOSE) exec -T frontend npm test -- --watchAll=false --runInBand tests/views/admin

test-frontend-archive: app-up
	$(APP_COMPOSE) exec -T frontend npm test -- --watchAll=false --runInBand \
		tests/views/archive tests/views/admin/dashboard/AdminDashboard.test.js

test-frontend-teams: app-up
	$(APP_COMPOSE) exec -T frontend npm test -- --watchAll=false --runInBand tests/views/teams

test-lint: app-up
	$(APP_COMPOSE) exec -T frontend npm run lint -- --quiet

test-build: app-up
	$(APP_COMPOSE) exec -T frontend npm run build

test-security: test-security-python test-security-frontend

test-security-python: app-up
	$(APP_COMPOSE) exec -T backend bandit -r api -q
	$(APP_COMPOSE) exec -T backend pip-audit -r requirements.txt

test-security-frontend: app-up
	$(APP_COMPOSE) exec -T frontend npm run lint:security
	$(APP_COMPOSE) exec -T frontend npm audit --omit=dev --audit-level=high

test-deployment-security:
	./tests/deployment/test_caddy_bot_policy.sh

test-app: app-up
	APP_ENV="$(APP_ENV)" ./tests/application/application_smoke_test.sh

test-app-reset: app-up
	APP_ENV="$(APP_ENV)" CONFIRM_TEST_RESET="$(CONFIRM_TEST_RESET)" ./tests/application/application_smoke_test.sh --reset

test-app-maintenance: app-up
	APP_ENV="$(APP_ENV)" CONFIRM_DESTRUCTIVE="$(CONFIRM_DESTRUCTIVE)" ./tests/application/application_smoke_test.sh --maintenance

test-admin-reset: app-up
	APP_ENV="$(APP_ENV)" CONFIRM_ADMIN_RESET="$(CONFIRM_ADMIN_RESET)" ./tests/application/application_smoke_test.sh --reset-admin

team-id-migration-check: app-up
	$(APP_COMPOSE) exec -T backend python -m api.migrate_team_ids

team-id-migration-apply: app-up
	@test "$(CONFIRM_TEAM_ID_MIGRATION)" = "1" || \
		(echo "Migration refused. Re-run with CONFIRM_TEAM_ID_MIGRATION=1"; exit 1)
	$(APP_COMPOSE) exec -T backend python -m api.migrate_team_ids --apply

lightsail-init:
	./scripts/init_lightsail_env.sh "$(LIGHTSAIL_ENV)" "$(DOMAIN)"

lightsail-check:
	./scripts/validate_lightsail_env.sh "$(LIGHTSAIL_ENV)"
	$(LIGHTSAIL_COMPOSE) config --quiet

lightsail-up: lightsail-check
	$(LIGHTSAIL_COMPOSE) up -d --build --remove-orphans

lightsail-down:
	$(LIGHTSAIL_COMPOSE) down

lightsail-restart: lightsail-check
	$(LIGHTSAIL_COMPOSE) restart

lightsail-logs:
	$(LIGHTSAIL_COMPOSE) logs -f --tail=200

lightsail-status:
	$(LIGHTSAIL_COMPOSE) ps

lightsail-health:
	LIGHTSAIL_ENV="$(LIGHTSAIL_ENV)" ./scripts/lightsail_health.sh

lightsail-backup:
	LIGHTSAIL_ENV="$(LIGHTSAIL_ENV)" ./scripts/lightsail_backup.sh
