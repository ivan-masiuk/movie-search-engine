# Use Python 3.11 slim image
FROM python:3.11-slim

WORKDIR /app

# System deps (gcc/g++ are enough for spaCy wheels; add others only if you really need them)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml uv.lock ./

# Install uv and sync deps
RUN python -m pip install --upgrade pip uv && uv sync --frozen

# >>> Ensure pip in the uv-managed venv BEFORE spaCy's downloader tries to use it
RUN uv run python -m ensurepip && \
    uv run python -m pip install --upgrade pip && \
    uv run python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Data setup
RUN mkdir -p data && \
    curl -L -o data/movies.csv.gz https://github.com/metarank/msrd/raw/master/dataset/movies.csv.gz && \
    gunzip data/movies.csv.gz && \
    mv data/movies.csv data/movies_metadata.csv

# Env
ENV SESSION_SECRET=your-secret-key-change-in-production
ENV PYTHONPATH=/app

EXPOSE 5000

# Run the app with uv - using new architecture
CMD ["uv", "run", "python", "app.py"]
