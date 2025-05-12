
FROM python:3.11-slim

# Skapa en icke-root-användare
RUN useradd -m appuser

# Installera beroenden
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Lägg in appkod
COPY . /app
WORKDIR /app

# Byt användare
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3083"]
