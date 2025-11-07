# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10.11
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install locales package and configure locale
RUN apt-get update && apt-get install -y locales && \
    sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=de_DE.UTF-8 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the locale environment variables
ENV LANG=de_DE.UTF-8  
ENV LANGUAGE=de_DE.UTF-8  
ENV LC_ALL=de_DE.UTF-8 

# Copy dependency list and install dependencies
COPY ./requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy application files
COPY ./secrets.json /app/secrets.json
COPY ./src /app

# Expose the port that the application listens on.
EXPOSE 80

# Run the application.
CMD ["python", "main.py"]
