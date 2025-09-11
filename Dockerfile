#  base image
FROM python:3.11-slim

# CWD
WORKDIR /app

# preparing env
RUN apt-get update && apt-get install -y git build-essential curl && rm -rf /var/lib/apt/lists/*

# copy and install requirements (no need to copy src code if there's issue with installation)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy code
COPY . .

#  expose FastAPI port 
EXPOSE 8000

CMD ["python", "main.py", "--serve"]