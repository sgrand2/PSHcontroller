FROM alpine:latest

RUN apk update && apk add python3 py3-pip
RUN pip install pymodbus click

WORKDIR /opt/csci498
COPY app.py /opt/csci498/app.py

CMD python /opt/csci498/app.py