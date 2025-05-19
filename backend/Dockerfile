# Use an official Python runtime as a parent image
FROM python:3-slim

# Set the working directory
WORKDIR /app

# Upgrade pip
RUN python -m pip install --upgrade pip

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code into the container
COPY . .

ENV PYTHONPATH=/app

# Create a non-root user and switch to it

# Expose the port FastAPI will run on
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
