#!/bin/sh
set -e

myname="$(basename $0)"

msg(){
    echo "$myname: $1"
}

if [ "$1" = "gunicorn" ]; then
    msg "start migrating database models"
    ./manage.py migrate

    msg "start collecting static files"
    ./manage.py collectstatic --noinput

    msg "launching $1"
    exec su-exec django "$@"
fi

if [ "$1" = "celery" ]; then
    msg "launching $1 $2"
    exec su-exec django "$@"
fi

msg "executing $@"
exec "$@"
