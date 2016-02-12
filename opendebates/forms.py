from urlparse import urlparse

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import resolve, Resolver404
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _
from localflavor.us.forms import USZipCodeField
from registration.forms import RegistrationForm

from .models import Category, Flag, Submission

VALID_SUBMISSION_DETAIL_URL_NAMES = ['vote', 'show_idea']


class VoterForm(forms.Form):

    email = forms.EmailField()
    zipcode = USZipCodeField()


class QuestionForm(forms.Form):
    category = forms.ModelMultipleChoiceField(queryset=Category.objects.all())
    question = forms.CharField()
    citation = forms.URLField(required=False)

display_name_help_text = _("How your name will be displayed on the site. If you "
                           "are an expert in a particular field or have a professional "
                           "affiliation that is relevant to your ideas, feel free to "
                           "mention it here alongside your name! If you leave this "
                           "blank, your first name and last initial will be used "
                           "instead.")  # @@TODO
display_name_label = (u"Display name <span data-toggle='tooltip' title='%s' "
                      "class='glyphicon glyphicon-question-sign'></span>" % display_name_help_text)
twitter_handle_help_text = _("Fill in your Twitter username (without the @) if you "
                             "would like to be @mentioned on Twitter when people "
                             "tweet your ideas.")  # @@TODO
twitter_handle_label = (u"Twitter handle <span data-toggle='tooltip' title='%s' "
                        "class='glyphicon glyphicon-question-sign'></span>"
                        % twitter_handle_help_text)


class OpenDebatesRegistrationForm(RegistrationForm):

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    display_name = forms.CharField(max_length=255,
                                   label=mark_safe(display_name_label),
                                   required=False)
    twitter_handle = forms.CharField(max_length=255,
                                     label=mark_safe(twitter_handle_label),
                                     required=False)
    zip = USZipCodeField()

    def clean_twitter_handle(self):
        if self.cleaned_data.get("twitter_handle", "").startswith("@"):
            return self.cleaned_data['twitter_handle'].lstrip("@")
        if self.cleaned_data.get("twitter_handle", "").startswith("https://twitter.com/"):
            return self.cleaned_data['twitter_handle'][20:]
        if self.cleaned_data.get("twitter_handle", "").startswith("http://twitter.com/"):
            return self.cleaned_data['twitter_handle'][19:]
        if self.cleaned_data.get("twitter_handle", "").startswith("twitter.com/"):
            return self.cleaned_data['twitter_handle'][12:]
        return self.cleaned_data.get("twitter_handle", "").strip() or None

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.

        """
        User = get_user_model()
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError("This email address is already in use. Please supply "
                                        "a different email address.")
        return self.cleaned_data['email']

    def save(self, commit=True):
        user = super(OpenDebatesRegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class OpenDebatesAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=254,
                               label="Username or Email")


class MergeFlagForm(forms.ModelForm):
    duplicate_of_url = forms.URLField()

    class Meta:
        model = Flag
        fields = ('duplicate_of_url', )

    def __init__(self, *args, **kwargs):
        self.idea = kwargs.pop('idea')
        self.voter = kwargs.pop('voter')
        super(MergeFlagForm, self).__init__(*args, **kwargs)

    def clean_duplicate_of_url(self):
        # parse the URL and use Django's resolver to find the urlconf entry
        path = urlparse(self.cleaned_data['duplicate_of_url']).path
        try:
            url_match = resolve(path)
        except Resolver404:
            url_match = None

        if not url_match or url_match.url_name not in VALID_SUBMISSION_DETAIL_URL_NAMES:
            raise forms.ValidationError('That is not the URL of a question.')

        duplicate_of_pk = url_match.kwargs.get('id')
        if duplicate_of_pk == unicode(self.idea.pk):
            raise forms.ValidationError('Please enter the URL of the submission that this '
                                        'submission appears to be a duplicate of, not the '
                                        'URL of this submission.')

        self.duplicate_of = Submission.objects.filter(pk=duplicate_of_pk, approved=True) \
                                              .first()
        if not self.duplicate_of:
            raise forms.ValidationError('Invalid Question URL.')
        return self.cleaned_data['duplicate_of_url']

    def save(self, commit=True):
        flag = super(MergeFlagForm, self).save(commit=False)
        flag.to_remove = self.idea
        flag.voter = self.voter
        flag.duplicate_of = self.duplicate_of
        if commit:
            flag.save()
        return flag


class ModerationForm(forms.Form):
    to_remove = forms.IntegerField(label="ID of submission to remove")
    duplicate_of = forms.IntegerField(required=False,
                                      label="(Optional) ID of submission it is a duplicate of")

    def clean_to_remove(self):
        to_remove_pk = self.cleaned_data['to_remove']
        if to_remove_pk:
            try:
                self.cleaned_data['to_remove_obj'] = Submission.objects.get(
                    pk=to_remove_pk, approved=True)
            except Submission.DoesNotExist:
                raise forms.ValidationError('That submission does not exist or is not approved.')
        return to_remove_pk

    def clean_duplicate_of(self):
        duplicate_of_pk = self.cleaned_data['duplicate_of']
        if duplicate_of_pk:
            try:
                self.cleaned_data['duplicate_of_obj'] = Submission.objects.get(
                    pk=duplicate_of_pk, approved=True)
            except Submission.DoesNotExist:
                raise forms.ValidationError('That submission does not exist or is not approved.')
        return duplicate_of_pk

    def clean(self):
        to_remove_pk = self.cleaned_data.get('to_remove')
        duplicate_of_pk = self.cleaned_data.get('duplicate_of')
        if to_remove_pk and duplicate_of_pk and to_remove_pk == duplicate_of_pk:
            raise forms.ValidationError('Cannot merge a submission into itself.')
        return self.cleaned_data
