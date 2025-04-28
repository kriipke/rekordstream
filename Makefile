.PHONY: build up upd down restart logs frontend api db worker rabbitmq clean

build:
	docker compose build

up:
	docker compose up

upd:
	docker compose up -d

down:
	docker compose down

restart: down build up

logs:
	docker compose logs -f

frontend:
	docker compose logs -f frontend

api:
	docker compose logs -f api

db:
	docker compose exec db psql -U rekordboxuser rekordbox

worker:
	docker compose exec api python worker.py

rabbitmq:
	open http://localhost:15672

clean:
	docker system prune -af --volumes
