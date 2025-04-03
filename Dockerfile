# Dockerfile.airflow
FROM python:3.9

# Upgrade pip first
RUN python -m pip install --upgrade pip
