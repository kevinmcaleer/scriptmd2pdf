# Multi-stage build for smaller image size
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for Pillow and ReportLab
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 scriptmd2pdf && \
    chown -R scriptmd2pdf:scriptmd2pdf /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/scriptmd2pdf/.local

# Copy application code
COPY --chown=scriptmd2pdf:scriptmd2pdf screenmd2pdf.py .
COPY --chown=scriptmd2pdf:scriptmd2pdf app.py .

# Switch to non-root user
USER scriptmd2pdf

# Add user's local bin to PATH
ENV PATH=/home/scriptmd2pdf/.local/bin:$PATH

# Environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV MAX_FILE_SIZE=1048576
ENV RATE_LIMIT=5/minute
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
