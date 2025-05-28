# Makefile

PROJECT_NAME = logi

check:
	lsof -i :27017 && echo "❌ Port 27017 zajęty. Przerwij działającą instancję!" && exit 1 || echo "✅ Port 27017 wolny"

up: check
	docker-compose -p $(PROJECT_NAME) up --build

down:
	docker-compose -p $(PROJECT_NAME) down -v --remove-orphans

reset: down up

