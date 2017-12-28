FROM python:3.6-alpine3.6

ENV TZ Europe/Paris
RUN set -ex \
    && apk --no-cache add tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

ENV PYTHONUNBUFFERED 1

RUN addgroup -S django \
    && adduser -S -g '' -G django django \
    && apk add --no-cache 'su-exec>=0.2'

WORKDIR /app

COPY Pipfile Pipfile.lock ./

ENV PIPENV_VERSION 9.0.1

ARG development
RUN set -ex \
    && apk add --no-cache --virtual .build-deps \
           gcc \
           linux-headers \
           ${development:+make} \
           musl-dev \
           postgresql-dev \
           python3-dev \
    && pip install --no-cache-dir --upgrade "pipenv==${PIPENV_VERSION}" \
    && pipenv install --deploy --system "${development:+--dev}" \
    && apk add --no-cache \
           libpq \
    && apk del .build-deps

COPY . ./

RUN python -m compileall .

ENV PORT 8000
EXPOSE $PORT

ENTRYPOINT [ "./docker-entrypoint.sh" ]

CMD [ "gunicorn", "home_web.wsgi", \
      "--bind", "0.0.0.0:$PORT", \
      "--name", "home_web", \
      "--access-logfile", "-", \
      "--error-logfile", "-" ]
