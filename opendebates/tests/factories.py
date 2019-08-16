import random

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils.timezone import now
import factory

from opendebates import models


_random = random.Random()


def _testserver_debate(obj=None):
    site = SiteFactory(domain='testserver')
    if site.debates.all():
        return site.debates.all()[0]
    return DebateFactory(site=site)


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Site
        django_get_or_create = ('domain',)

    domain = 'testserver'


class DebateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Debate

    site = factory.SubFactory(SiteFactory)
    prefix = factory.Faker('slug')
    debate_state = 'NY'


class CandidateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Candidate

    debate = factory.SubFactory(DebateFactory)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: "user%d" % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)
    password = factory.PostGenerationMethodCall('set_password', 'password')

    is_staff = False
    is_active = True

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for group in extracted:
                self.groups.add(group)


class CategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Category

    debate = factory.LazyAttribute(_testserver_debate)


class VoterFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Voter
        django_get_or_create = ('email',)

    user = factory.SubFactory(UserFactory)
    email = factory.Faker('safe_email')
    zip = factory.Faker('zipcode')


class SubmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Submission

    category = factory.SubFactory(CategoryFactory)

    headline = factory.Faker('sentence')
    followup = factory.Faker('paragraph')

    idea = factory.LazyAttribute(lambda obj: (u'%s %s' % (obj.headline, obj.followup)).strip())

    voter = factory.SubFactory(VoterFactory)
    created_at = now()
    approved = True
    votes = 1
    current_votes = 1


class VoteFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Vote

    submission = factory.SubFactory(SubmissionFactory)
    voter = factory.SubFactory(VoterFactory)
    created_at = now()


class RemovalFlagFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Flag

    to_remove = factory.SubFactory(SubmissionFactory)
    voter = factory.SubFactory(VoterFactory)


class MergeFlagFactory(RemovalFlagFactory):
    duplicate_of = factory.SubFactory(SubmissionFactory)


class TopSubmissionCategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.TopSubmissionCategory

    debate = factory.LazyAttribute(_testserver_debate)

    slug = factory.Faker('slug')
    title = factory.Faker('catch_phrase')
    caption = factory.Faker('bs')
