FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système (sans libatlas-base-dev)
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    gcc g++ \
    libffi-dev \
    libssl-dev \
    curl \
    libblas-dev \
    liblapack-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer pip + wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Installer wheels précompilés
RUN pip install --no-cache-dir numpy --only-binary=:all:
RUN pip install --no-cache-dir onnxruntime --only-binary=:all:

# Installer le reste
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Exposer le port par défaut
EXPOSE 8000

# Démarrage dynamique
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]