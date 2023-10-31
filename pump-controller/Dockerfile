FROM alpine:latest

RUN apk update && apk add python3 py3-pip gcc libc-dev python3-dev
RUN pip install pymodbus rpi.gpio click

EXPOSE 502

CMD python app.py