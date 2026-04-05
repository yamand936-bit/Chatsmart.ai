FROM python:3.11-slim

# Create a non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Change ownership to appuser
RUN chown -R appuser:appgroup /app
RUN chmod +x prestart.sh

# Switch to non-root user
USER appuser

CMD ["./prestart.sh"]
