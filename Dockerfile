FROM python:3.10-slim

# Instala ffmpeg e dependências do sistema
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para iniciar a aplicação
CMD ["python", "main.py"]