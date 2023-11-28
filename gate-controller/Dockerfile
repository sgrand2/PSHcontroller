FROM alpine:latest

RUN apk update && apk add python3 py3-pip gcc libc-dev python3-dev
RUN pip install pymodbus rpi.gpio click

EXPOSE 502

WORKDIR /opt/csci498
COPY app.py /opt/csci498/app.py

CMD python /opt/csci498/app.py