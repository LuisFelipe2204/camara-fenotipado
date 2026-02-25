FROM python:3.11

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgpiod-dev \
    python3-libgpiod \
    i2c-tools \
    libsm6 libxext6 libxrender1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --verbose

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]