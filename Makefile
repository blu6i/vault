# Окружение: nginx + python + PostgreSQL

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Подгружаем .env для подстановки переменных в make
ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: help
help:
	@echo "make init         — создать .env из .env.example (с UID/GID текущего пользователя)"
	@echo "make build        — собрать образы"
	@echo "make up           — поднять контейнеры (в фоне)"
	@echo "make down         — остановить и удалить контейнеры"
	@echo "make restart      — перезапустить контейнеры"
	@echo "make ps           — статус контейнеров"
	@echo "make logs         — логи всех сервисов (follow)"
	@echo "make clean        — down -v: остановить и удалить volume pgdata"
	@echo "make sync         — установить зависимости python (uv sync)"
	@echo "make lock         — зафиксировать зависимости (uv lock)"
	@echo "make lint         — проверить стиль кода (ruff check)"
	@echo "make format       — автоформатирование кода (ruff format + fix)"
	@echo "make test         — запуск тестов (pytest)"
	@echo "make test-db-init — создать и накатить схему тестовой БД (PostgreSQL)"
	@echo "make migrate      — применить миграции базы данных (alembic upgrade head)"
	@echo "make migration    — создать авто-миграцию (make migration msg=\"...\")"
	@echo "make migrate-down — откатить последнюю миграцию (alembic downgrade -1)"
	@echo "make sh           — bash в контейнере приложения"
	@echo "make psql         — консоль psql к postgres"
	@echo "make gen_secret   — генератор секрета"

.PHONY: init
init:
	@if [ -f .env ]; then \
		echo ".env уже существует, пропускаю"; \
	else \
		cp .env.example .env; \
		CURRENT_UID=$$(id -u); \
		CURRENT_GID=$$(id -g); \
		sed -i.bak "s/^UID=.*/UID=$$CURRENT_UID/" .env; \
		sed -i.bak "s/^GID=.*/GID=$$CURRENT_GID/" .env; \
		rm -f .env.bak; \
		echo ".env создан (UID=$$CURRENT_UID, GID=$$CURRENT_GID)"; \
	fi

.PHONY: build
build:
	docker compose build

.PHONY: up
up:
	docker compose up -d

.PHONY: down
down:
	docker compose down

.PHONY: restart
restart: down up

.PHONY: ps
ps:
	docker compose ps

.PHONY: logs
logs:
	docker compose logs -f $(service)

.PHONY: clean
clean:
	docker compose down -v

.PHONY: sync
sync:
	docker compose exec app uv sync

.PHONY: lock
lock:
	docker compose exec app uv lock

.PHONY: lint
lint:
	docker compose exec app ruff check src/

.PHONY: format
format:
	docker compose exec app ruff format src/
	docker compose exec app ruff check --fix src/

.PHONY: test
test:
	docker compose exec app pytest

.PHONY: test-db-init
test-db-init:
	@echo "Создание тестовой базы данных PostgreSQL..."
	docker compose exec postgres psql -U $${DB__POSTGRES_USER:-admin} -c "CREATE DATABASE $${DB__POSTGRES_DB:-app}_test;" || true
	docker compose exec -e DB__POSTGRES_DB=$${DB__POSTGRES_DB:-app}_test app alembic upgrade head
	@echo "Тестовая база данных готова к тестам."

.PHONY: migrate
migrate:
	docker compose exec app alembic upgrade head

.PHONY: migration
migration:
	@if [ -z "$(msg)" ]; then \
		echo "Ошибка: укажите описание миграции через msg='...'"; \
		exit 1; \
	fi
	docker compose exec app alembic revision --autogenerate -m "$(msg)"

.PHONY: migrate-down
migrate-down:
	docker compose exec app alembic downgrade -1

.PHONY: sh
sh:
	docker compose exec app bash

.PHONY: psql
psql:
	docker compose exec postgres psql -U $${POSTGRES_USER:-admin} -d $${POSTGRES_DB:-app}

.PHONY: gen_secret
gen_secret:
	python -c "import secrets; print(secrets.token_urlsafe(32))"
