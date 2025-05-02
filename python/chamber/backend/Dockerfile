FROM python:3.11-slim

WORKDIR /camara

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install latest pip and setuptools
RUN pip install --upgrade pip setuptools

# Clone and install Dynamixel SDK
RUN git clone https://github.com/ROBOTIS-GIT/DynamixelSDK.git /camara/lib/dynamixel-sdk \
    && cd /camara/lib/dynamixel-sdk/python \
    && python setup.py install

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

CMD ["python", "main.py"]
