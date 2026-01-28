# Use Playwright image to ensure browser deps are present
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install deps from lockfile (reproducible), then project
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev

# Playwright browsers in base image; ensure chromium
RUN uv run playwright install chromium

RUN mkdir -p data uploads
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///data/coinstack.db

CMD ["uv", "run", "uvicorn", "src.infrastructure.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
