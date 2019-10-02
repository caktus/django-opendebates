import json
import logging

# XXX import actual commands needed
from pprint import pprint

from fabric.api import (abort, cd, env, execute, hide, hosts, local, parallel,
    prompt, put, roles, require, run, runs_once, settings, sudo, task)
from fabric.colors import red
from fabric.contrib.files import exists, upload_template, append, uncomment, sed
from fabric.exceptions import NetworkError
from fabric.network import disconnect_all

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
def kubernetes():
    env.world = 'kubernetes'
@task
def docker():
    env.world = 'docker'
@task
def creds(filename):
    if not os.path.exists(filename):
        print("Invalid value for credentials filename %s" % filename)
        print("Does not exist")
        abort()
    env.creds = filename
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = filename

####################
#
# FOR KUBERNETES
#
####################

# Find an opendebates pod
def get_opendebates_pod_name():
    require("environment", provided_by=env.environments)
    require("creds", provided_by=['creds'])
    local("kubectl config set-context --current --namespace=opendebates-%s" % env.environment)
    output = local("kubectl get pods -o json", capture=True)
    data = json.loads(output)
    for i in data["items"]:
        # pprint(i)
        m = i["metadata"]
        if m["labels"].get("app") == "opendebates":
            return m["name"]

#############################
#
# FOR DOCKER OR KUBERNETES
#
#############################


@task
def create_site(name):
    # Usage: fab create_site:localhost8000
    require("world", provided_by=['kubernetes', 'docker'])
    require("environment", provided_by=env.environments)
    if env.world == 'docker':
        local("docker-compose run web python manage.py create_site %s" % name)
    elif env.world == 'kubernetes':
        require("creds", provided_by=['creds'])
        os.chdir('kubernetes')
        pod = get_opendebates_pod_name()
        local(
            "kubectl exec %s /venv/bin/python /code/manage.py create_site %s" % (pod, name)
        )


@task
def logs():
    local("docker-compose logs")
    local("docker-compose logs --follow")


@task
def build():
    local("docker-compose build")


@task
def up():
    require("world", provided_by=['kubernetes', 'docker'])
    require("environment", provided_by=env.environments)
    if env.world == 'docker':
        # local("docker-compose up --build -d")
        local("docker-compose up -d")
        time.sleep(1)  # Sometimes it's not *quite* ready yet.
        smoketest()
    elif env.world == 'kubernetes':
        require("creds", provided_by=['creds'])
        os.chdir('kubernetes')
        #local("kubectl apply -f kubernetes")
        local("ansible-playbook -e ENVIRONMENT=%s playbook.yml" % env.environment)

@task
def down():
    local("docker-compose down")


@task
def migrate():
    require("world", provided_by=['kubernetes', 'docker'])
    require("environment", provided_by=env.environments)
    if env.world == 'docker':
        local("docker-compose run web python manage.py migrate --noinput -v 0")
    elif env.world == 'kubernetes':
        require("creds", provided_by=['creds'])
        os.chdir('kubernetes')
        pod = get_opendebates_pod_name()
        local("kubectl exec %s /venv/bin/python /code/manage.py migrate" % pod)


@task
def createsuperuser():
    require("world", provided_by=['kubernetes', 'docker'])
    require("environment", provided_by=env.environments)
    if env.world == 'docker':
        local("docker-compose run web python manage.py createsuperuser")
    elif env.world == 'kubernetes':
        require("creds", provided_by=['creds'])
        os.chdir('kubernetes')
        pod = get_opendebates_pod_name()
        local("kubectl exec -it %s /venv/bin/python /code/manage.py createsuperuser" % pod)


@task
def smoketest():
    # Make sure we're at least serving basic http requests
    site = "localhost:8000"
    create_site(
        site
    )  # FIXME: not really the right place for this, but it works for now since "up" runs "smoketest"

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
def testing(deployment_tag=env.default_deployment, answer=None):
    _setup_env(deployment_tag, "testing")


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
