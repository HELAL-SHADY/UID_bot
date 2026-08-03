FROM python:3.12-slim
WORKDIR /app

# Install system deps needed by psycopg2-binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Ensure bot data directory exists
RUN mkdir -p /app/bot/data

EXPOSE 3000
CMD ["python", "-m", "bot.main"]
