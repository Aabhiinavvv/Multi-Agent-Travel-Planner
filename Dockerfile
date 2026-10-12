FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBITECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    git\
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade zip
RUN python -m pip install -r requirements.txt

COPY . . 


EXPOSE 8000

CMD ["uvicorn" , "app.app", "--host","0.0.0.0","--port","8080"]





