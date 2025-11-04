.PHONY: install dev test clean format lint build publish help

help:
	@echo "gcallm - Google Calendar + LLM CLI"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    Install gcallm (non-editable, production)"
	@echo "  make dev        Install in development mode (editable)"
	@echo "  make test       Run tests"
	@echo "  make format     Format code with black"
	@echo "  make lint       Lint code with ruff"
	@echo "  make build      Build package for PyPI"
	@echo "  make publish    Publish to PyPI (requires authentication)"
	@echo "  make clean      Remove build artifacts"
	@echo "  make uninstall  Uninstall gcallm"

install:
	@echo "📦 Installing gcallm (production mode)..."
	uv tool install .
	@echo "✅ Installation complete! Try: gcallm verify"

dev:
	@echo "📦 Installing gcallm in development mode (editable)..."
	uv tool install --editable .
	@echo "✅ Development installation complete!"

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

format:
	@echo "🎨 Formatting code..."
	black gcallm/ tests/
	@echo "✅ Code formatted!"

lint:
	@echo "🔍 Linting code..."
	ruff check gcallm/ tests/
	@echo "✅ Linting complete!"

build: clean
	@echo "📦 Building package for PyPI..."
	uv build
	@echo "✅ Package built! Files in dist/"

publish: build
	@echo "🚀 Publishing to PyPI..."
	@echo "⚠️  Make sure you have PyPI credentials configured!"
	twine upload dist/*
	@echo "✅ Published to PyPI!"

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned!"

uninstall:
	@echo "🗑️  Uninstalling gcallm..."
	uv tool uninstall gcallm
	@echo "✅ Uninstalled!"
