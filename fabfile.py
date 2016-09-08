import logging
# XXX import actual commands needed
from fabulaws.library.wsgiautoscale.api import *  # noqa
from fabulaws.library.wsgiautoscale.api import _setup_env

root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler())
root_logger.setLevel(logging.WARNING)

fabulaws_logger = logging.getLogger('fabulaws')
fabulaws_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@task
def florida(deployment_tag=env.default_deployment, answer=None):
    _setup_env(deployment_tag, 'florida')


@task
def presidential(deployment_tag=env.default_deployment, answer=None):
    _setup_env(deployment_tag, 'presidential')
