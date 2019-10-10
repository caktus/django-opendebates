# https://www.caktusgroup.com/blog/2017/03/14/production-ready-dockerfile-your-python-django-app/
# https://pythonspeed.com/articles/base-image-python-docker-images/ (July 2019)
# FIXME: update for Python 3
FROM python:2.7.16-slim-buster

# Install packages needed to run your application (not build deps):
#   mime-support -- for mime types when serving static files
#   postgresql-client -- for running database commands
# We need to recreate the /usr/share/man/man{1..8} directories first because
# they were clobbered by a parent image.
RUN set -ex \
    && RUN_DEPS=" \
        libpcre3 \
        mime-support \
        postgresql-client \
        curl \
        nodejs \
        npm \
    " \
    && seq 1 8 | xargs -I{} mkdir -p /usr/share/man/man{} \
    && apt-get update && apt-get install -y --no-install-recommends $RUN_DEPS \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --gid 9999 debates \
  && adduser --no-create-home --disabled-password --uid 9999 --gid 9999 debates

RUN set -ex && npm install -g yuglify less

RUN set -ex \
    && pip install virtualenv \
    && virtualenv -p python2.7 /venv \
    && /venv/bin/pip install --no-cache-dir -U pip wheel

# "Activate" virtualenv
ENV PATH=/venv/bin:$PATH

# Copy in your requirements file
ADD requirements.txt /requirements.txt

# OR, if you’re using a directory for your requirements, copy everything (comment out the above and uncomment this if so):
# ADD requirements /requirements

# Install build deps, then run `pip install`, then remove unneeded build deps all in a single step.
# Correct the path to your production requirements file, if needed.
RUN set -ex \
    && BUILD_DEPS=" \
        build-essential \
        libpcre3-dev \
        libpq-dev \
    " \
    && apt-get update && apt-get install -y --no-install-recommends $BUILD_DEPS \
    && pip install --no-cache-dir -r /requirements.txt \
    \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
    && rm -rf /var/lib/apt/lists/*

# Copy your application code to the container (make sure you create a .dockerignore file if any large files or directories should be excluded)
RUN mkdir /code/
WORKDIR /code/
ADD . /code/

# We will listen on this port
EXPOSE 8000

# Add any static environment variables needed by Django or your settings file here:
# Settings can look at DJANGO_ENV to customize settings for prod vs. other environments.
# "prod" really just means deployed vs. running locally. It could still be staging or testing.
ENV DJANGO_ENV=prod
ENV DOCKER_CONTAINER=1
ENV PYTHONUNBUFFERED=1

# Call collectstatic (customize the following line with the minimal environment variables needed for manage.py to run):
RUN DATABASE_URL='' python manage.py collectstatic --noinput -v 0

# Note: to run migrations, see "fab migrate" after this is up.

# By default run gunicorn, but if command-line arguments
# are given run those instead:
ENTRYPOINT ["./docker-entrypoint.sh"]
# https://pythonspeed.com/articles/gunicorn-in-docker/
CMD ["gunicorn", "opendebates_deploy.wsgi", "--pythonpath", "/code/opendebates", "--log-file",  "-", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--worker-tmp-dir", "/dev/shm"]
