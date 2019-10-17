# This fabfile is written for Fabric3
#
# (Fabric3 is the fork of Fabric v1 that runs on Python 3.
# Not to be confused with Fabric 2, the incompatible complete
# rewrite of Fabric v1 that also runs on Python 3.)

import datetime
import os.path

from fabric.api import env, local, require, task
from fabric.utils import abort

env.vault_password_file = os.path.abspath(".vault_password")
env.docker_hub_account = "caktus"

ENVIRONMENTS = {
    'testing': {  # see also kubernetes/testing_vars.yml
        'gcloud': {
            "cluster": "opendebates-cluster",
            "region": "us-east1",
            "project": "open-debates-2019-deployment",
        }
    },
    'testing111': {  # see also kubernetes/testing111_vars.yml
        'gcloud': {
            "cluster": "opendebates-cluster",
            "region": "us-east1",
            "project": "open-debates-2019-deployment",
        }
    }
}
env.environments = list(ENVIRONMENTS.keys())


@task
def testing():
    env.environment = "testing"
    env.update(ENVIRONMENTS[env.environment])
    auth_gcloud()


@task
def testing111():
    """A testing environment running Django1.11."""
    env.environment = "testing111"
    env.update(ENVIRONMENTS[env.environment])
    auth_gcloud()


####################
#
# FOR KUBERNETES
#
####################


def auth_gcloud():
    require("gcloud", provided_by=env.environments)
    local(
        "gcloud beta container clusters get-credentials {cluster} --region {region} --project {project}".format(
            **env.gcloud
        )
    )
    local("kubectl cluster-info")


def run_in_opendebates_pod(command):
    require("environment", provided_by=env.environments)
    os.chdir("kubernetes")
    namespace = "opendebates-%s" % env.environment
    local(
        "kubectl exec -it --namespace=%s deployment/opendebates %s"
        % (namespace, command)
    )


@task
def create_site(name):
    # Usage: fab create_site:localhost8000
    manage_run("create_site %s" % name)


@task
def docker_hub(account_name):
    """Set name of account to use on docker hub"""
    env.docker_hub_account = account_name


@task
def build():
    """BUILD the docker image"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    print(timestamp)
    tag = "docker.io/%s/opendebates:%s" % (env.docker_hub_account, timestamp)
    local("docker build . --tag=%s" % tag)


@task
def publish():
    """PUBLISH the most recent docker image"""
    # Find the most recent
    tag = local(
        "docker images %s/opendebates --format '{{.Tag}}' | head -1"
        % env.docker_hub_account,
        capture=True,
    )
    if tag == "":
        abort("No docker image found, have you run 'fab build' yet?")
    print(tag)
    local("docker push %s/opendebates:%s" % (env.docker_hub_account, tag))


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
