FROM alpine:latest

RUN apk update && apk add python3 py3-pip
RUN pip install pymodbus

CMD python app.py