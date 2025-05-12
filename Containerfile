FROM python:3.11-slim

# Skapa en icke-root-användare
RUN useradd -m appuser

# Installera beroenden
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Lägg in appkod + startskript
COPY . /app
COPY start.sh /start.sh
WORKDIR /app

# Gör startscriptet körbart
RUN chmod +x /start.sh

# Byt till icke-root
USER appuser

# Starta via skript
CMD ["/start.sh"]
