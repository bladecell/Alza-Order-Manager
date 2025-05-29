# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all necessary files into the container
COPY AlzaAuth.py .
COPY AlzaOrderManager.py .
COPY alzaOrder.py .
COPY credentials.json .
COPY fakeBrnoAddress.py .
COPY run.py .

# Create a directory for logs
RUN mkdir /app/logs

COPY proxy.txt /app/logs/

# Set the default run period (in seconds) as an environment variable
ENV RUN_PERIOD=10

# Use Python script instead of watch command
CMD ["python", "run.py"]