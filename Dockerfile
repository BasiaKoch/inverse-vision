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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Make modules importable without installing as a package
ENV PYTHONPATH=/app

CMD ["bash"]
