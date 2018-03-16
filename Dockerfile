FROM alpine:3.7
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY ./requirements.txt /usr/src/app
RUN apk update && \
 apk add python3 postgresql-libs && \
 apk add --virtual .build-deps gcc python3-dev musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps
COPY ./merchantcustomer /usr/src/app
COPY ./deployment/wait-for.sh /usr/local/bin/wait-for.sh
CMD ["python3", "app.py"]
EXPOSE 8888
