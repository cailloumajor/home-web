FROM cailloumajor/python-armhf:alpine

RUN mkdir /static

ENV PYTHONUNBUFFERED=1 \
    DJANGO_STATIC_ROOT=/static/

WORKDIR /app

COPY requirements.txt .
RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
           gcc \
           linux-headers \
           musl-dev \
           postgresql-dev \
           python3-dev \
    && pip install -r requirements.txt \
    && apk add --no-cache \
           libpq \
    && apk del .build-deps

COPY home_web ./home_web
COPY heating ./heating
COPY manage.py .
COPY gunicorn_config.py .

EXPOSE 8000

COPY docker-entrypoint.sh .
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["./manage.py", "runserver", "0.0.0.0:8000"]