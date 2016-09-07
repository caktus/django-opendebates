import logging
# XXX import actual commands needed
from fabulaws.library.wsgiautoscale.api import *  # noqa

root_logger = logging.getLogger()
root_logger.addHandler(logging.StreamHandler())
root_logger.setLevel(logging.WARNING)

fabulaws_logger = logging.getLogger('fabulaws')
fabulaws_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@task
@roles('db-master')
def pg_create_unaccent_ext():
    """
    Workaround to facilitate granting the opendebates database user
    permission to use the 'unaccent' extension in Postgres.
    """
    require('environment', provided_by=env.environments)
    sudo('sudo -u postgres psql %s -c "CREATE EXTENSION IF NOT EXISTS unaccent;"'
         '' % env.database_name)
    for func in [
        'unaccent(text)',
        'unaccent(regdictionary, text)',
        'unaccent_init(internal)',
        'unaccent_lexize(internal, internal, internal, internal)',
    ]:
        sudo('sudo -u postgres psql %s -c "ALTER FUNCTION %s OWNER TO %s;"'
             '' % (env.database_name, func, env.database_user))
