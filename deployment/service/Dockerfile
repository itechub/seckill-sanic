FROM python:3.7-alpine

ADD requirements.txt /service/

WORKDIR /service

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories
RUN apk add --no-cache --virtual .build-deps build-base linux-headers libc-dev libffi libffi-dev openssl-dev\
    && pip install -r requirements.txt \
    && apk del .build-deps


ARG service

ADD ${service}/. /service

COPY ./deployment/service/entrypoint.sh  /service

RUN chmod +x /service/entrypoint.sh

ENTRYPOINT ["/service/entrypoint.sh"]

ADD config /service/config
