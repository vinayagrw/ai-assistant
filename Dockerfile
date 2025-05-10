FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    build-essential \
    wget curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && curl -L https://ollama.ai/install.sh | sh

ENV PATH="/usr/local/bin:${PATH}"

EXPOSE 8000
EXPOSE 11434
# Command to run the application
CMD ["sh", "-c", "ollama serve & python run.py"]
