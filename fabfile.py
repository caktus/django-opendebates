import logging

# XXX import actual commands needed
import requests
from fabulaws.library.wsgiautoscale.api import *  # noqa
from fabulaws.library.wsgiautoscale.api import _setup_env

root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler())
root_logger.setLevel(logging.WARNING)

fabulaws_logger = logging.getLogger("fabulaws")
fabulaws_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@task
def create_site(name):
    # Usage: fab create_site:localhost8000
    local("docker-compose run web python manage.py create_site %s" % name)


@task
def logs():
    local("docker-compose logs")
    local("docker-compose logs --follow")


@task
def up():
    local("docker-compose up --build -d")
    time.sleep(1)  # Sometimes it's not *quite* ready yet.
    smoketest()


@task
def down():
    local("docker-compose down")


@task
def migrate():
    local("docker-compose run web python manage.py migrate --noinput -v 0")


@task
def createsuperuser():
    local("docker-compose run web python manage.py createsuperuser")


@task
def smoketest():
    # Make sure we're at least serving basic http requests
    site = "localhost:8000"
    create_site(site)  # FIXME: not really the right place for this, but it works for now since "up" runs "smoketest"

    admin_url = "http://%s/admin/" % site
    login_url = "http://%s/admin/login/?next=/admin/" % site
    result = requests.get(admin_url, allow_redirects=False)
    result.raise_for_status()
    assert result.headers["Location"] == login_url
    result = requests.get(login_url, allow_redirects=False)
    result.raise_for_status()
    assert result.status_code == 200


###############################################################################


@task
def florida(deployment_tag=env.default_deployment, answer=None):
    _setup_env(deployment_tag, "florida")


@task
def presidential(deployment_tag=env.default_deployment, answer=None):
    _setup_env(deployment_tag, "presidential")


@task
def staging01(deployment_tag=env.default_deployment, answer=None):
    _setup_env(deployment_tag, "staging01")


@task
def prod01(deployment_tag=env.default_deployment, answer=None):
    _setup_env(deployment_tag, "prod01")


@task
@roles("db-master")
def pg_create_unaccent_ext():
    """
    Workaround to facilitate granting the opendebates database user
    permission to use the 'unaccent' extension in Postgres.
    """
    require("environment", provided_by=env.environments)
    sudo(
        'sudo -u postgres psql %s -c "CREATE EXTENSION IF NOT EXISTS unaccent;"'
        "" % env.database_name
    )
    for func in [
        "unaccent(text)",
        "unaccent(regdictionary, text)",
        "unaccent_init(internal)",
        "unaccent_lexize(internal, internal, internal, internal)",
    ]:
        sudo(
            'sudo -u postgres psql %s -c "ALTER FUNCTION %s OWNER TO %s;"'
            "" % (env.database_name, func, env.database_user)
        )
