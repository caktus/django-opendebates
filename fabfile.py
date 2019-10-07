import json
import logging
import os.path

from fabric.api import env, local, roles, require, sudo, task
from fabric.utils import abort

root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler())
root_logger.setLevel(logging.WARNING)

fabulaws_logger = logging.getLogger("fabulaws")
fabulaws_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

env.environments = ["testing"]
env.vault_password_file = os.path.abspath(".vault_password")


@task
def testing():
    env.environment = "testing"


####################
#
# FOR KUBERNETES
#
####################

# Find an opendebates (Django) pod and return its name
def get_opendebates_pod_name():
    require("environment", provided_by=env.environments)
    output = local("kubectl get --namespace=opendebates-%s pods -o json" % env.environment, capture=True)
    data = json.loads(output)
    for i in data["items"]:
        m = i["metadata"]
        if m["labels"].get("app") == "opendebates":
            return m["name"]


def run_in_opendebates_pod(command):
    require("environment", provided_by=env.environments)
    os.chdir("kubernetes")
    pod = get_opendebates_pod_name()
    local("kubectl exec -it %s %s" % (pod, command))


@task
def create_site(name):
    # Usage: fab create_site:localhost8000
    manage_run("create_site %s" % name)


@task
def build():
    local("docker build .")


@task
def decrypt_file(filename):
    local(
        "ansible-vault decrypt --vault-password={PASSFILE} {FILENAME}".format(
            PASSFILE=env.vault_password_file, FILENAME=filename
        )
    )


@task
def encrypt_file(filename):
    local(
        "ansible-vault encrypt --vault-password={PASSFILE} {FILENAME}".format(
            PASSFILE=env.vault_password_file, FILENAME=filename
        )
    )


@task
def up():
    require("environment", provided_by=env.environments)
    os.chdir("kubernetes")
    # Note: the playbook loads vars from vars files itself.
    local(
        "ansible-playbook "
        "--vault-password-file={PASSFILE} "
        "-e ENVIRONMENT={ENVIRONMENT} "
        "playbook.yml".format(
            ENVIRONMENT=env.environment, PASSFILE=env.vault_password_file
        )
    )


@task
def manage_run(command):
    run_in_opendebates_pod("/venv/bin/python /code/manage.py %s" % command)


@task
def migrate():
    manage_run("migrate --noinput -v 0")


@task
def manage_shell():
    manage_run("shell")


@task
def createsuperuser():
    manage_run("createsuperuser")


###############################################################################


@task
@roles("db-master")
def pg_create_unaccent_ext():
    # FIXME: do we still need this?
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
