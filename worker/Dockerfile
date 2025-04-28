# Use a slim official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install needed system packages if necessary (optional for lightweight)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the worker code
COPY . .

# Default command
CMD ["python", "worker.py"]
