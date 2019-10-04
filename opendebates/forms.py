from urlparse import urlparse

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import resolve, Resolver404
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _
from localflavor.us.forms import USZipCodeField
from nocaptcha_recaptcha.fields import NoReCaptchaField
from phonenumber_field.formfields import PhoneNumberField
from registration.forms import RegistrationForm

from .models import Category, Flag, Submission, TopSubmissionCategory, TopSubmission

VALID_SUBMISSION_DETAIL_URL_NAMES = ['vote', 'show_idea']


class VoterForm(forms.Form):

    email = forms.EmailField()
    zipcode = USZipCodeField()
    captcha = NoReCaptchaField(
        gtag_attrs={'data-size': 'compact'}
    )

    def __init__(self, *args, **kwargs):
        super(VoterForm, self).__init__(*args, **kwargs)

    def ignore_captcha(self):
        del self.fields['captcha']


class QuestionForm(forms.Form):
    category = forms.ModelMultipleChoiceField(queryset=Category.objects.none())
    headline = forms.CharField(required=True)
    question = forms.CharField(required=False)
    citation = forms.URLField(required=False, max_length=255)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['category'].error_messages['invalid_pk_value'] = _("You must select a category")
        self.fields['category'].queryset = Category.objects.filter(debate=request.debate)

display_name_help_text = _("How your name will be displayed on the site. If you "
                           "are an expert in a particular field or have a professional "
                           "affiliation that is relevant to your ideas, feel free to "
                           "mention it here alongside your name! If you leave this "
                           "blank, your first name and last initial will be used "
                           "instead.")  # @@TODO
display_name_label = (u"Display name <span data-toggle='tooltip' title='%s' "
                      "data-placement='bottom' "
                      "class='glyphicon glyphicon-question-sign'></span>" % display_name_help_text)
twitter_handle_help_text = _("Fill in your Twitter username (without the @) if you "
                             "would like to be @mentioned on Twitter when people "
                             "tweet your ideas.")  # @@TODO
twitter_handle_label = (u"Twitter handle <span data-toggle='tooltip' title='%s' "
                        "data-placement='bottom' "
                        "class='glyphicon glyphicon-question-sign'></span>"
                        % twitter_handle_help_text)
phone_number_help_text = _("We will be inviting some participants to "
                           "attend the event live or read their question "
                           "via video. Enter your phone number for a "
                           "chance to participate!")  # @@TODO
phone_number_label = (u"Phone number <span data-toggle='tooltip' title='%s' "
                      "data-placement='bottom' "
                      "class='glyphicon glyphicon-question-sign'></span>" % phone_number_help_text)


class OpenDebatesRegistrationForm(RegistrationForm):

    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    # Additional fields which we want to add in __init__, *after* adding
    # the phone number and display name fields (if enabled). In Django 1.8,
    # SortedDict is deprecated and the only way to modify the order of fields
    # (collections.OrderedDict) on Python 2.7 is to create an entirely new
    # dictionary. Django 1.9 adds a 'field_order' attribute on forms, but
    # we're not using that yet. This attempts to maintain proper field order
    # while doing as little as possible at runtime.
    additional_fields = [
        ('twitter_handle', forms.CharField(max_length=255,
                                           label=mark_safe(twitter_handle_label),
                                           required=False)),
        ('zip', USZipCodeField()),
        ('captcha', NoReCaptchaField(label=_("Are you human?"))),
    ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(OpenDebatesRegistrationForm, self).__init__(*args, **kwargs)
        if settings.ENABLE_USER_PHONE_NUMBER:
            self.fields['phone_number'] = PhoneNumberField(
                label=mark_safe(phone_number_label),
                required=False,
            )
        if settings.ENABLE_USER_DISPLAY_NAME:
            self.fields['display_name'] = forms.CharField(
                max_length=255,
                label=mark_safe(display_name_label),
                required=False,
            )
        for name, field in self.additional_fields:
            self.fields[name] = field

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

    def save(self, commit=True):
        user = super(OpenDebatesRegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

    def ignore_captcha(self):
        del self.fields['captcha']


class OpenDebatesAuthenticationForm(AuthenticationForm):
    username = forms.CharField(max_length=254,
                               label="Email")


class MergeFlagForm(forms.ModelForm):
    duplicate_of_url = forms.URLField(label=_("Enter URL here"))

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
            # Override and use the full urlconf, so that we can handle
            # non-existent questions differently from questions on a
            # different sub-site.
            url_match = resolve(path, urlconf=settings.ROOT_URLCONF)
        except Resolver404:
            url_match = None

        if not url_match or url_match.url_name not in VALID_SUBMISSION_DETAIL_URL_NAMES:
            raise forms.ValidationError('That is not the URL of a question.')

        duplicate_of_pk = url_match.kwargs.get('id')
        if duplicate_of_pk == unicode(self.idea.pk):
            raise forms.ValidationError('Please enter the URL of the submission that this '
                                        'submission appears to be a duplicate of, not the '
                                        'URL of this submission.')

        self.duplicate_of = Submission.objects.filter(
            pk=duplicate_of_pk, approved=True, category__debate=self.idea.debate
        ).first()
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
        if to_remove_pk and duplicate_of_pk:
            if to_remove_pk == duplicate_of_pk:
                raise forms.ValidationError('Cannot merge a submission into itself.')
            remove_obj = self.cleaned_data['to_remove_obj']
            duplicate_obj = self.cleaned_data['duplicate_of_obj']
            if remove_obj.debate != duplicate_obj.debate:
                self.add_error(
                    'duplicate_of',
                    forms.ValidationError('That submission does not exist or is not approved.')
                )
        return self.cleaned_data


class TopSubmissionForm(forms.ModelForm):
    class Meta:
        model = TopSubmission
        fields = ('category', 'submission', 'rank')

    def __init__(self, *args, **kwargs):
        debate = kwargs.pop('debate')
        super(TopSubmissionForm, self).__init__(*args, **kwargs)
        self.fields['submission'].widget = forms.NumberInput()
        self.fields['category'].queryset = TopSubmissionCategory.objects.filter(
            debate=debate)

    def clean(self):
        cleaned_data = super(TopSubmissionForm, self).clean()
        category = cleaned_data.get('category')
        submission = cleaned_data.get('submission')
        if submission.debate != category.debate:
            self.add_error(
                'submission',
                forms.ValidationError("This submission does not exist or is not in this debate.")
            )
        return cleaned_data

    def save(self, commit=True):
        top = super(TopSubmissionForm, self).save(commit=False)
        submission = top.submission

        top.headline = submission.headline
        top.followup = submission.followup
        top.votes = submission.votes
        top.current_votes = submission.current_votes
        if commit:
            top.save()
        return top
