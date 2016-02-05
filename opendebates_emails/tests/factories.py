import factory
import factory.fuzzy

from opendebates_emails.models import EmailTemplate


class EmailTemplateFactory(factory.DjangoModelFactory):
    class Meta:
        model = EmailTemplate
