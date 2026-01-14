FROM python:3.10-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory inside container
WORKDIR /app

# Copy requirements from server folder
COPY server/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code into /app/server
COPY server /app/server

# Copy client code into /app/client
COPY client /app/client

# Make sure Python can import the client module and server module
ENV PYTHONPATH="/app/server:/app/client:${PYTHONPATH}"

# Expose port for Cloud Run
EXPOSE 8080

# Run the Flask app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "server.server:app"]
