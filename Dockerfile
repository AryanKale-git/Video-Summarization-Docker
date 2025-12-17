# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY app/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY app/ .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables (can be overridden at runtime)
ENV SECRET_KEY="a-very-secure-secret-key-for-production"

# Run app.py when the container launches using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]