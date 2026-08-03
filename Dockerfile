FROM python:3.12-slim
WORKDIR /app

# Install runtime dependencies
RUN pip install --no-cache-dir python-telegram-bot python-dotenv aiosqlite apscheduler

# Copy application source
COPY . /app

# Ensure bot data directory exists
RUN mkdir -p /app/bot/data

EXPOSE 3000
CMD ["python", "-m", "bot.main"]
