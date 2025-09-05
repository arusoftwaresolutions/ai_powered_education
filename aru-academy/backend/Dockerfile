# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY . .

# Create storage directories
RUN mkdir -p storage/departments/computer_science \
    && mkdir -p storage/departments/electrical_engineering \
    && mkdir -p storage/departments/mechanical_engineering \
    && mkdir -p storage/departments/business_administration

# Create migrations directory
RUN mkdir -p migrations

# Set permissions for storage
RUN chmod -R 755 storage/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting ARU Academy..."\n\
echo "🔄 Running database migrations..."\n\
python -c "from app import app; from models.base import db; app.app_context().push(); db.create_all(); print(\"✅ Database tables created/verified\")"\n\
echo "🌱 Checking and seeding database if needed..."\n\
python -c "from app import app, seed_database_if_empty; app.app_context().push(); seed_database_if_empty()"\n\
echo "🌐 Starting web server..."\n\
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 app:app' > /app/start.sh

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
