FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y curl unzip gcc g++ && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install "poetry>=2.0.0"

# Copy dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy frontend source
COPY frontend ./frontend
COPY .env .

WORKDIR /app/frontend

ENV REFLEX_ENV=prod

EXPOSE 3000

CMD ["reflex", "run", "--env", "prod", "--frontend-port", "3000", "--backend-port", "8000"]
