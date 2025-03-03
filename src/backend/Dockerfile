# Use a multi-stage build to reduce the final image size
# Builder stage: Install dependencies and build the application
FROM python:3.11-slim as builder # version specified in Technical Specifications/3.1 PROGRAMMING LANGUAGES

# Set working directory
WORKDIR /app # Specified in JSON file

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Install system dependencies for building Python packages
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        gcc \
        python3-dev \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Final stage: Create the production image
FROM python:3.11-slim # version specified in Technical Specifications/3.1 PROGRAMMING LANGUAGES

# Set working directory
WORKDIR /app # Specified in JSON file

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Copy system dependencies for running the application
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000 # Specified in JSON file

# Health check endpoint
HEALTHCHECK --interval=5m --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run gunicorn
CMD ["gunicorn", "--conf", "gunicorn.conf.py", "wsgi:application", "--bind", "0.0.0.0:5000"]