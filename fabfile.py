import logging
import os.path

from fabric.api import env, local, roles, require, sudo, task

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


def run_in_opendebates_pod(command):
    require("environment", provided_by=env.environments)
    os.chdir("kubernetes")
    namespace = "opendebates-%s" % env.environment
    local("kubectl exec -it --namespace=%s deployment/opendebates %s" % (namespace, command))


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
def encrypt_string(text):
    local(
        "ansible-vault encrypt_string --vault-password={PASSFILE} {TEXT}".format(
            PASSFILE=env.vault_password_file, TEXT=text
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
