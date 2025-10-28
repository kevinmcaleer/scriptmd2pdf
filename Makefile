.PHONY: help install test lint format clean build run deploy

help:
	@echo "ScriptMD2PDF - Development and Deployment Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install dependencies in virtual environment"
	@echo "  make test       - Run all tests with coverage"
	@echo "  make lint       - Run code quality checks"
	@echo "  make format     - Auto-format code"
	@echo "  make clean      - Remove generated files"
	@echo ""
	@echo "Docker:"
	@echo "  make build      - Build Docker image"
	@echo "  make run        - Run Docker container locally"
	@echo "  make deploy     - Deploy with docker-compose"
	@echo "  make stop       - Stop docker-compose services"
	@echo "  make logs       - View docker-compose logs"
	@echo ""

install:
	python -m venv venv
	./venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed. Activate with: source venv/bin/activate"

test:
	./venv/bin/pytest test_screenmd2pdf.py test_app.py -v --cov=screenmd2pdf --cov=app --cov-report=term --cov-report=html
	@echo "✅ Tests complete. Coverage report in htmlcov/index.html"

lint:
	./venv/bin/black --check screenmd2pdf.py app.py test_screenmd2pdf.py test_app.py || true
	./venv/bin/isort --check-only screenmd2pdf.py app.py test_screenmd2pdf.py test_app.py || true
	./venv/bin/flake8 screenmd2pdf.py app.py test_screenmd2pdf.py test_app.py --max-line-length=120 --ignore=E203,W503 || true
	@echo "✅ Lint checks complete"

format:
	./venv/bin/black screenmd2pdf.py app.py test_screenmd2pdf.py test_app.py
	./venv/bin/isort screenmd2pdf.py app.py test_screenmd2pdf.py test_app.py
	@echo "✅ Code formatted"

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov *.pyc
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned up generated files"

build:
	docker buildx build --platform linux/arm64,linux/amd64 -t 192.168.2.1:5000/md2script:latest .
	@echo "✅ Docker image built for multiple platforms"

build-local:
	docker build -t 192.168.2.1:5000/md2script:latest .
	@echo "✅ Docker image built for local platform"

run:
	docker run -d --name scriptmd2pdf -p 8000:8000 192.168.2.1:5000/md2script:latest
	@echo "✅ Container running at http://localhost:8000"
	@echo "   Health check: curl http://localhost:8000/health"

deploy:
	docker-compose up -d
	@echo "✅ Services deployed with docker-compose"
	@echo "   View logs: make logs"
	@echo "   Stop: make stop"

stop:
	docker-compose down
	@echo "✅ Services stopped"

logs:
	docker-compose logs -f

push:
	docker push 192.168.2.1:5000/md2script:latest
	@echo "✅ Image pushed to private registry"

health:
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ Service not responding"

quick-test:
	@echo "Testing health endpoint..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Service not running"
	@echo ""
	@echo "Testing conversion with example file..."
	@curl -X POST -F "file=@example_screenplay.md" http://localhost:8000/convert -o /tmp/test_output.pdf 2>/dev/null && echo "✅ PDF generated successfully" || echo "❌ Conversion failed"

dev:
	./venv/bin/python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

all: install test lint build
