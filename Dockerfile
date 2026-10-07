# Use the official Python 3.11 Alpine image
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy the dependency manifests and install dependencies from pyproject.toml
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

# Copy the application source into the container at /app
COPY src /app

# Expose the port that the app will run on
EXPOSE 5000

# Allows user to customize threads and bind inside the container
ENV GUNICORN_THREADS=4
ENV GUNICORN_BIND=0.0.0.0:5000
ENV PATH="/app/.venv/bin:$PATH"

# Command to run the application with Gunicorn and selected parameters
CMD gunicorn app:app --workers 1 --threads ${GUNICORN_THREADS} --bind ${GUNICORN_BIND}