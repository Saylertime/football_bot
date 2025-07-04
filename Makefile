.PHONY: up down

CURRENT_HOSTNAME := $(shell hostname)

ifeq ($(CURRENT_HOSTNAME), 1738991-cy22118.twc1.net)
    COMPOSE_FILE = docker-compose_prod.yml
else
    COMPOSE_FILE = docker-compose_local.yml
endif

up:
	docker-compose -f $(COMPOSE_FILE) up

build:
	docker-compose -f $(COMPOSE_FILE) up --build

down:
	docker-compose -f $(COMPOSE_FILE) down

report:
	docker exec -it report /bin/sh -c "cat bot.log"

guru:
	docker exec -it guide_guru /bin/sh -c "cat bot.log"

pg_bash:
	docker exec -it football_postgres /bin/sh -c "psql -h postgres -U sayler -d postgres"

logs_report:
	docker logs postgres


debug:
	@echo "Current Hostname: $(CURRENT_HOSTNAME)"
	@echo "Using Compose File: $(COMPOSE_FILE)"


