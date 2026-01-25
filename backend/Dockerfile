# Use Playwright image to ensure browser deps are present
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Install system dependencies if any additional needed
# RUN apt-get update && apt-get install -y ...

# Install Python dependencies
COPY pyproject.toml .
# We don't have a lock file yet, so we install from pyproject.toml or requirements.txt
# Assuming pyproject.toml has everything. 
# We need to install the project itself or just deps.
# Let's check pyproject.toml content again to see if it's poetry or just pip.
# It looked like standard setuptools/pip or hatch.
# We'll use pip to install the dependencies listed in pyproject.toml
RUN pip install --no-cache-dir .[dev] 
RUN pip install pytest-asyncio  # Ensure this is present as it was added manually

# Install playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Create directory for data and uploads
RUN mkdir -p data uploads

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite:///data/coinstack.db

# Run command
CMD ["uvicorn", "src.infrastructure.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
