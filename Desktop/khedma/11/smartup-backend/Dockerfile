# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
# Turns off buffering for easier container logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update image dependencies
RUN apt-get update
RUN apt-get upgrade -y

# Download and install wkhtmltopdf START
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y build-essential xorg libssl-dev libxrender-dev wget

# Install container dependencies
RUN apt-get install -y --no-install-recommends xvfb libfontconfig xfonts-75dpi fontconfig curl

RUN wget --no-check-certificate http://archive.ubuntu.com/ubuntu/pool/main/libj/libjpeg-turbo/libjpeg-turbo8_2.0.3-0ubuntu1_amd64.deb && \
    dpkg -i libjpeg-turbo8_2.0.3-0ubuntu1_amd64.deb && \
    rm libjpeg-turbo8_2.0.3-0ubuntu1_amd64.deb

RUN wget --no-check-certificate https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb && \
    dpkg -i wkhtmltox_0.12.5-1.bionic_amd64.deb && \
    rm wkhtmltox_0.12.5-1.bionic_amd64.deb
# Download and install wkhtmltopdf END

# Install app dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# Copy app files 
WORKDIR /backend
COPY . /backend
