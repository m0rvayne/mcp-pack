# Base Python image for containerized deployment
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variable placeholder (set at runtime)
ENV FATHOM_API_KEY=""

CMD ["fastmcp", "run", "server.py"]
