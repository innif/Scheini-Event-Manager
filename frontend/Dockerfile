# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.10.11
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install locales package
RUN apt-get update && apt-get install -y locales

# Uncomment the de_DE.UTF-8 locale in /etc/locale.gen and generate the locale
RUN sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=de_DE.UTF-8

# Set the locale environment variables
ENV LANG de_DE.UTF-8  
ENV LANGUAGE de_DE.UTF-8  
ENV LC_ALL de_DE.UTF-8 

COPY ./requirements.txt ./requirements.txt

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Copy the source code into the container.
COPY ./secrets.json ./secrets.json
COPY ./src /app

# Expose the port that the application listens on.
EXPOSE 80

# Run the application.
CMD ["python", "main.py"]
