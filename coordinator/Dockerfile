FROM alpine:latest

RUN apk update && apk add python3 py3-pip nodejs npm
RUN pip install pymodbus click flask

WORKDIR /opt/csci498
COPY app.py /opt/csci498/app.py
COPY hmi /opt/csci498/hmi-src
RUN cd /opt/csci498/hmi-src && npm install && npm run build && mv build /opt/csci498/hmi
RUN rm -rf /opt/csci498/hmi-src

CMD python /opt/csci498/app.py