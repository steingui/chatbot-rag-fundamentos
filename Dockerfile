FROM python:3.11-slim

# Evita que o Python escreva arquivos .pyc e força flush do stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código para o container
COPY . .

# Expor a porta 7860 exigida pelo Hugging Face Spaces
EXPOSE 7860

# Configura o PYTHONPATH para rodar módulos a partir do diretório raiz
ENV PYTHONPATH=/app

# Comando de inicialização
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
