from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.formats import date_format

from opendebates.forms import TopSubmissionForm
from opendebates.models import TopSubmission
from .factories import (SubmissionFactory,
                        TopSubmissionCategoryFactory,
                        UserFactory,
                        )


class TopArchiveTest(TestCase):

    def setUp(self):
        self.url = lambda slug: reverse('top_archive', args=[slug])
        self.mod_url = reverse('moderation_add_to_top_archive')

        self.categories = [TopSubmissionCategoryFactory()
                           for i in range(3)]
        self.ideas = [SubmissionFactory() for i in range(10)]

    def test_form_copies_submission(self):
        idea = self.ideas[0]
        original_headline = idea.headline

        form = TopSubmissionForm(data={'category': self.categories[0].id,
                                       'submission': idea.id,
                                       'rank': 1})
        archive = form.save()
        id = archive.id

        # The archive gets a copy of the idea's headline, followup,
        # and vote count at the moment of its creation:
        self.assertEqual(archive.headline, original_headline)
        self.assertEqual(archive.followup, idea.followup)
        self.assertEqual(archive.votes, idea.votes)

        # These are just copies; if the underlying idea changes
        # because of additional platform use or moderator edits,
        # the archive remains frozen:
        idea.headline = "An entirely new headline"
        idea.followup = "Some totally different followup text"
        idea.votes += 1500

        archive = TopSubmission.objects.get(id=id)
        self.assertNotEqual(archive.headline, idea.headline)
        self.assertEqual(archive.headline, original_headline)
        self.assertNotEqual(archive.followup, idea.followup)
        self.assertEqual(archive.votes, idea.votes - 1500)

        # Even if the idea is deleted altogether, the archive remains.
        idea.delete()
        archive = TopSubmission.objects.get(id=id)
        self.assertEqual(archive.submission, None)
        self.assertEqual(archive.headline, original_headline)

    def test_top_archive_view(self):
        self.ideas[0].votes = 1000
        self.ideas[0].save()
        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[0].id,
                                'rank': 1}).save()

        self.ideas[3].votes = 4000
        self.ideas[3].save()
        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[3].id,
                                'rank': 2}).save()

        self.ideas[2].votes = 5000
        self.ideas[2].save()
        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[2].id,
                                'rank': 2}).save()

        # The "Top Questions" view will contain archived submissions
        rsp = self.client.get(self.url(self.categories[0].slug))
        self.assertContains(rsp, self.ideas[0].headline)
        self.assertNotContains(rsp, self.ideas[1].headline)

        # Submissions will appear in rank order, regardless of vote count
        self.assertLess(rsp.content.find(self.ideas[0].headline),
                        rsp.content.find(self.ideas[3].headline))

        # If two submissions have the same rank, the one that was archived
        # earlier in time will appear first
        self.assertLess(rsp.content.find(self.ideas[3].headline),
                        rsp.content.find(self.ideas[2].headline))

    def test_top_archive_view_does_not_link(self):
        """The archive view does not link to its individual entries"""
        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[2].id,
                                'rank': 2}).save()
        rsp = self.client.get(self.url(self.categories[0].slug))
        self.assertNotContains(rsp, self.ideas[2].get_absolute_url())

    def test_top_archive_view_has_metadata_iff_idea_exists(self):
        """
        As long as the original submission still exists, the archive
        will display info on its author, submission date, and category
        """
        self.ideas[2].voter.display_name = 'George Washington'
        self.ideas[2].voter.save()

        self.ideas[2].category.name = 'Environmental Issues'
        self.ideas[2].category.save()

        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[2].id,
                                'rank': 2}).save()
        rsp = self.client.get(self.url(self.categories[0].slug))
        self.assertContains(rsp, self.ideas[2].voter.user_display_name())
        self.assertContains(rsp, self.ideas[2].category.name)
        self.assertContains(rsp, date_format(self.ideas[2].created_at))

        self.ideas[2].delete()
        rsp = self.client.get(self.url(self.categories[0].slug))
        self.assertNotContains(rsp, self.ideas[2].voter.user_display_name())
        self.assertNotContains(rsp, self.ideas[2].category.name)
        self.assertNotContains(rsp, date_format(self.ideas[2].created_at))
        self.assertContains(rsp, self.ideas[2].headline)

    def test_multiple_archives(self):
        # An idea can appear in multiple archive categories
        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[2].id,
                                'rank': 1}).save()
        TopSubmissionForm(data={'category': self.categories[1].id,
                                'submission': self.ideas[2].id,
                                'rank': 2}).save()

        rsp0 = self.client.get(self.url(self.categories[0].slug))
        rsp1 = self.client.get(self.url(self.categories[1].slug))

        self.assertContains(rsp0, self.ideas[2].headline)
        self.assertContains(rsp1, self.ideas[2].headline)

        # Each archive category has an entirely independent list
        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[3].id,
                                'rank': 2}).save()

        TopSubmissionForm(data={'category': self.categories[1].id,
                                'submission': self.ideas[4].id,
                                'rank': 1}).save()

        rsp0 = self.client.get(self.url(self.categories[0].slug))
        rsp1 = self.client.get(self.url(self.categories[1].slug))

        self.assertContains(rsp0, self.ideas[3].headline)
        self.assertContains(rsp1, self.ideas[4].headline)

        self.assertNotContains(rsp1, self.ideas[3].headline)
        self.assertNotContains(rsp0, self.ideas[4].headline)

    def test_idea_once_per_category(self):
        TopSubmissionForm(data={'category': self.categories[0].id,
                                'submission': self.ideas[0].id,
                                'rank': 1}).save()

        form = TopSubmissionForm(data={'category': self.categories[0].id,
                                       'submission': self.ideas[0].id,
                                       'rank': 2})
        self.assertFalse(form.is_valid())
        self.assertEquals(
            form.non_field_errors(),
            [u'Top submission with this Category and Submission already exists.'])

    def test_moderator_view_only_accessible_to_superusers(self):
        self.client.logout()
        rsp = self.client.get(self.mod_url)
        self.assertEqual(rsp.status_code, 404)

        password = 'secretpassword'

        user = UserFactory(password=password,
                           is_staff=False, is_superuser=False)
        self.client.login(username=user.username, password=password)
        rsp = self.client.get(self.mod_url)
        self.assertEqual(rsp.status_code, 404)

        user = UserFactory(password=password,
                           is_staff=True, is_superuser=False)
        self.client.login(username=user.username, password=password)
        rsp = self.client.get(self.mod_url)
        self.assertEqual(rsp.status_code, 404)

        user = UserFactory(password=password,
                           is_staff=True, is_superuser=True)
        self.client.login(username=user.username, password=password)
        rsp = self.client.get(self.mod_url)
        self.assertEqual(rsp.status_code, 200)

    def test_moderator_view(self):
        password = 'secretpassword'
        user = UserFactory(password=password,
                           is_staff=True, is_superuser=True)
        self.client.login(username=user.username, password=password)
        data = {
            'category': self.categories[0].id,
            'submission': self.ideas[0].id,
            'rank': 1,
        }
        rsp = self.client.post(self.mod_url, data=data)
        self.assertRedirects(rsp, self.url(self.categories[0].slug))
        self.assertContains(self.client.get(
            self.url(self.categories[0].slug)),
                            self.ideas[0].headline)
