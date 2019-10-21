FROM python:3.7-alpine

COPY . /opt/fwd-app

WORKDIR /opt/fwd-app

RUN apk --no-cache add gcc libc-dev \
    && pip3 install -r requirements.txt \
    && apk del gcc libc-dev \
    && find / -type d -name  __pycache__ | xargs rm -rf \
    && mkdir /data

ENV FWD_KEYS_PATH=/data
ENV FWD_LISTEN_ADDR=0.0.0.0
ENV FWD_LISTEN_PORT=8080

VOLUME [ "/data" ]

EXPOSE 8080/tcp

CMD ["python3", "main.py"]
