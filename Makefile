# Makefile dla Multi-Agent System

.PHONY: help install run test clean setup

# Domyślna komenda
help:
	@echo "📋 Dostępne komendy:"
	@echo "  make install  - Zainstaluj zależności"
	@echo "  make setup    - Pełny setup projektu"
	@echo "  make run      - Uruchom aplikację Streamlit"
	@echo "  make test     - Uruchom testy"
	@echo "  make clean    - Wyczyść pliki tymczasowe"

# Instalacja zależności
install:
	pip install -r requirements.txt

# Pełny setup
setup:
	python3 setup.py

# Uruchom aplikację
run:
	streamlit run multi_agent_ui.py

# Uruchom testy
test:
	python3 -m pytest tests/ -v || python3 tests/test_system.py

# Wyczyść pliki tymczasowe
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete