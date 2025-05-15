FROM python:3.11-slim

WORKDIR /backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools

RUN git clone https://github.com/ROBOTIS-GIT/DynamixelSDK.git /camara/lib/dynamixel-sdk \
    && cd /camara/lib/dynamixel-sdk/python \
    && python setup.py install

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["python", "main.py"]
