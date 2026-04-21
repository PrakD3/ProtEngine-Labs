# ProtEngine Labs Backend - Production Dockerfile
FROM condaforge/mambaforge:latest

WORKDIR /app

# Install system dependencies & bio-tools
RUN mamba install -y -c conda-forge \
    python=3.11 \
    vina \
    fpocket \
    openbabel \
    rdkit \
    wget \
    && mamba clean -afy

# Install Gnina binary (Deep Learning Scoring Engine)
RUN wget https://github.com/gnina/gnina/releases/download/v1.1/gnina -O /usr/local/bin/gnina && \
    chmod +x /usr/local/bin/gnina

# Copy requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 7860

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
