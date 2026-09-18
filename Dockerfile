FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create persistent data directory with proper permissions
RUN mkdir -p /app/data

# Copy application source code
COPY . .

EXPOSE 8000

# Default entrypoint runs FastAPI through Uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

