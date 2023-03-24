FROM python:3.10-slim-buster
WORKDIR /app
RUN apt update && apt upgrade -y
RUN pip install --upgrade pip
RUN apt install git -y

COPY requirements.txt requirements.txt
RUN pip3 install -U pip && pip3 install -U -r requirements.txt

COPY . .

CMD python3 bot.py
