import random
import string

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils.timezone import now
import factory
import factory.fuzzy

from opendebates import models


_random = random.Random()


def _testserver_site_mode(obj):
    site = Site.objects.get_or_create(domain='testserver')[0]
    return models.SiteMode.objects.get_or_create(site=site)[0]


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Site

    domain = factory.Sequence(lambda n: 'site-{0}.example.com'.format(n))


class SiteModeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SiteMode

    site = factory.SubFactory(SiteFactory)


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

    site_mode = factory.LazyAttribute(_testserver_site_mode)


class FuzzyEmail(factory.fuzzy.FuzzyText):
    def fuzz(self):
        chars = [_random.choice(self.chars) for _i in range(self.length)]
        return "%s@example.com" % ''.join(chars)


class VoterFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Voter

    site_mode = factory.LazyAttribute(_testserver_site_mode)
    user = factory.SubFactory(UserFactory)
    email = FuzzyEmail()
    zip = factory.fuzzy.FuzzyText(length=5, chars=string.digits)


class SubmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Submission

    category = factory.SubFactory(CategoryFactory)

    headline = factory.fuzzy.FuzzyText()
    followup = factory.fuzzy.FuzzyText()

    idea = factory.LazyAttribute(lambda obj: (u'%s %s' % (obj.headline, obj.followup)).strip())

    voter = factory.SubFactory(VoterFactory)
    created_at = now()
    approved = True
    votes = 1


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
