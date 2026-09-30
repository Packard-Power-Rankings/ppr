SHELL := /bin/bash
.DEFAULT_GOAL := help

LIGHTSAIL_ENV ?= .env.production
LIGHTSAIL_COMPOSE = docker compose --env-file $(LIGHTSAIL_ENV) -f docker-compose.lightsail.yml

.PHONY: help app-up app-down app-logs test-app test-app-reset test-app-maintenance test-admin-reset \
	lightsail-init lightsail-check lightsail-up lightsail-down lightsail-restart \
	lightsail-logs lightsail-status lightsail-health lightsail-backup

help:
	@echo "Packard Power Rankings development commands"
	@echo
	@echo "  make app-up                  Build and start the local stack"
	@echo "  make app-down                Stop the local stack"
	@echo "  make app-logs                Follow backend and worker logs"
	@echo "  make test-app                Run the happy-path application smoke test"
	@echo "  make test-app-reset          Reset only fixture data, then run the test"
	@echo "  make test-app-maintenance    Run destructive maintenance endpoint checks"
	@echo "  make test-admin-reset        Replace the local admin with test credentials"
	@echo
	@echo "Packard Power Rankings AWS Lightsail commands"
	@echo
	@echo "  make lightsail-init DOMAIN=rankings.example.com"
	@echo "  make lightsail-check        Validate production configuration"
	@echo "  make lightsail-up           Build and start the production stack"
	@echo "  make lightsail-status       Show production container status"
	@echo "  make lightsail-logs         Follow production logs"
	@echo "  make lightsail-health       Check the public HTTPS health endpoint"
	@echo "  make lightsail-backup       Create a private MongoDB archive"
	@echo "  make lightsail-restart      Restart production containers"
	@echo "  make lightsail-down         Stop production without deleting data"
	@echo
	@echo "Reset and maintenance targets require an explicit confirmation variable."

app-up:
	docker compose up -d --build

app-down:
	docker compose down

app-logs:
	docker compose logs -f backend arq_worker

test-app: app-up
	./scripts/application_smoke_test.sh

test-app-reset: app-up
	CONFIRM_TEST_RESET="$(CONFIRM_TEST_RESET)" ./scripts/application_smoke_test.sh --reset

test-app-maintenance: app-up
	CONFIRM_DESTRUCTIVE="$(CONFIRM_DESTRUCTIVE)" ./scripts/application_smoke_test.sh --maintenance

test-admin-reset: app-up
	CONFIRM_ADMIN_RESET="$(CONFIRM_ADMIN_RESET)" ./scripts/application_smoke_test.sh --reset-admin

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
