# Workout Tracker - Docker Management Commands

.PHONY: help build up down restart logs shell db-shell clean prune

# Default target
help:
	@echo "Workout Tracker - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build      Build Docker images"
	@echo "  up         Start all containers (detached)"
	@echo "  up-dev     Start with live reload for development"
	@echo "  down       Stop all containers"
	@echo "  restart    Restart all containers"
	@echo "  logs       View container logs (follow mode)"
	@echo "  logs-web   View web container logs only"
	@echo "  logs-db    View database container logs only"
	@echo "  shell      Open shell in web container"
	@echo "  db-shell   Open psql shell in database"
	@echo "  status     Show container status"
	@echo "  clean      Stop containers and remove volumes"
	@echo "  prune      Remove all unused Docker resources"
	@echo "  backup     Backup database to file"
	@echo "  restore    Restore database from file"

# Build the Docker images
build:
	docker compose build

# Start containers in detached mode
up:
	docker compose up -d

# Start with development mode (uncomment volume mount in docker-compose.yml)
up-dev:
	FLASK_ENV=development docker compose up

# Stop all containers
down:
	docker compose down

# Restart containers
restart:
	docker compose restart

# View all logs
logs:
	docker compose logs -f

# View web container logs
logs-web:
	docker compose logs -f web

# View database logs
logs-db:
	docker compose logs -f db

# Open shell in web container
shell:
	docker compose exec web /bin/bash

# Open psql shell
db-shell:
	docker compose exec db psql -U $${POSTGRES_USER:-workout} -d $${POSTGRES_DB:-workout_tracker}

# Show container status
status:
	docker compose ps

# Stop and remove everything including volumes
clean:
	docker compose down -v --remove-orphans

# Remove unused Docker resources
prune:
	docker system prune -f

# Backup database
backup:
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	docker compose exec -T db pg_dump -U $${POSTGRES_USER:-workout} $${POSTGRES_DB:-workout_tracker} > backups/backup_$$TIMESTAMP.sql && \
	echo "Backup saved to backups/backup_$$TIMESTAMP.sql"

# Restore database (usage: make restore FILE=backups/backup_XXXXXX.sql)
restore:
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore FILE=backups/backup_XXXXXX.sql"; exit 1; fi
	docker compose exec -T db psql -U $${POSTGRES_USER:-workout} -d $${POSTGRES_DB:-workout_tracker} < $(FILE)
	@echo "Database restored from $(FILE)"

# Create a new user (interactive)
create-user:
	docker compose exec web flask create-user

# Initialize database (run schema)
init-db:
	docker compose exec web flask init-db
