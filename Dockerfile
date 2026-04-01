FROM python:3.10-slim

LABEL description="Medical Imaging Coursework — reproducible environment"

WORKDIR /app

# Install system dependencies for scikit-image and matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt pyproject.toml ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy source code and install the package in editable mode
COPY . .
RUN python -m pip install --no-cache-dir -e .

# Default: open a shell; override with e.g.:
#   docker run --rm medical-imaging pytest tests/ -v
CMD ["bash"]
