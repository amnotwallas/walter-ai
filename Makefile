.PHONY: help install dev test clean sync export

help:
	@echo "🛠️ WALTER-AI API (UV Optimized) - Available commands:"
	@echo "  make install  - Install and sync all dependencies"
	@echo "  make dev      - Run the development server with hot-reload"
	@echo "  make test     - Run unit tests with pytest"
	@echo "  make export   - Export dependencies to requirements.txt (for Vercel)"
	@echo "  make clean    - Remove python cache and virtual environment"

install:
	uv sync
	@echo "✅ Project synced and dependencies installed."

dev:
	@echo "🚀 Starting FastAPI server on http://localhost:8000"
	uv run uvicorn main:app --reload

test:
	@echo "🧪 Running unit tests..."
	uv run pytest tests/

export:
	uv export --format requirements-txt > requirements.txt
	@echo "✅ requirements.txt updated for Vercel."

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	@echo "🧹 Cleaned up environment and cache."
