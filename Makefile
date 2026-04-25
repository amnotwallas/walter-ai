# Variables
PYTHON = python3
PIP = .venv/bin/pip
UVICORN = .venv/bin/uvicorn
VENV = .venv
PYTEST = .venv/bin/pytest

.PHONY: help install dev clean lint test

help:
	@echo "🛠️ WALTER_AI API - Available commands:"
	@echo "  make install  - Create virtual environment and install dependencies"
	@echo "  make dev      - Run the development server with hot-reload"
	@echo "  make test     - Run unit tests with pytest"
	@echo "  make clean    - Remove virtual environment and python cache"
	@echo "  make lint     - Run basic syntax check"

$(VENV):
	$(PYTHON) -m venv $(VENV)
	@echo "✅ Virtual environment created."

install: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed."

dev:
	@echo "🚀 Starting FastAPI server on http://localhost:8000"
	@export PYTHONPATH=$${PYTHONPATH}:$(shell pwd) && $(UVICORN) main:app --reload

test:
	@echo "🧪 Running unit tests..."
	@export PYTHONPATH=$${PYTHONPATH}:$(shell pwd) && $(PYTEST) tests/

clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "🧹 Cleaned up environment and cache."

lint:
	$(PIP) install ruff
	.venv/bin/ruff check .
