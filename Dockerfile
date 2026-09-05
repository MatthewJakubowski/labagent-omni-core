# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Ustawienia środowiska Pythona
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalacja zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu aplikacji
COPY . .

# Uruchamianie z uprawnieniami użytkownika bez praw roota (Standard ISO 27001 / Cybersecurty)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Wystawienie portu Streamlit
EXPOSE 8501

# Healthcheck do weryfikacji żywotności kontenera w klastrze
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Punkt startowy kontenera
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
