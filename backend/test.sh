#!/bin/bash

# Backend CI test script for local development

set -e

echo "🔧 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "🧪 Running tests with coverage..."
DATABASE_URL="mongodb://test:test@localhost:27017/test" python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo "✅ Tests completed! Check htmlcov/index.html for detailed coverage report."