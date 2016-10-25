import itertools

from django.contrib.admin import ModelAdmin, register
from django.shortcuts import render
from django.utils.timezone import now
from djangohelpers.export_action import admin_list_export

from . import models
from opendebates_emails.models import send_email


@register(models.Category)
class CategoryAdmin(ModelAdmin):
    list_display = [f.name for f in models.Category._meta.fields]
    actions = [admin_list_export]


@register(models.Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = [f.name for f in models.Submission._meta.fields]
    list_filter = ('approved', )
    search_fields = ('idea', )
    actions = [admin_list_export, 'remove_submissions']
    raw_id_fields = ['voter', 'duplicate_of']

    def remove_submissions(self, request, queryset):
        "Custom action to mark submissions 'unapproved' and to notify users by email."
        if request.POST.get('post'):
            count = 0
            removal_time = now()
            # only email user if submission changes status, hence the filter
            for submission in queryset.filter(approved=True):
                count += 1
                submission.approved = False
                submission.moderated_removal = True
                submission.moderated_at = removal_time
                submission.removal_flags.all().update(reviewed=True)
                submission.save()
                send_email("idea_is_removed", {"idea": submission})
            if count == 1:
                msg = "Removed 1 submission"
            else:
                msg = "Removed {} submissions".format(count)
            self.message_user(request, msg)
            return None  # returning None causes us to return to changelist
        context = {'queryset': queryset}
        return render(request, 'opendebates/admin/remove_submissions.html', context)
    remove_submissions.short_description = 'Remove selected submissions'

    def get_actions(self, request):
        # Remove the default 'Delete selected...' action
        actions = super(SubmissionAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@register(models.Voter)
class VoterAdmin(ModelAdmin):
    list_display = [f.name for f in models.Voter._meta.fields]
    actions = [admin_list_export]
    raw_id_fields = ['user']
    search_fields = ('email',)


@register(models.Vote)
class VoteAdmin(ModelAdmin):
    list_display = [f.name for f in models.Vote._meta.fields]
    actions = [admin_list_export]
    raw_id_fields = ['submission', 'voter', 'original_merged_submission']


@register(models.Candidate)
class CandidateAdmin(ModelAdmin):
    list_display = [f.name for f in models.Candidate._meta.fields]
    actions = [admin_list_export]


@register(models.Flag)
class FlagAdmin(ModelAdmin):
    list_display = [f.name for f in models.Flag._meta.fields]
    actions = [admin_list_export]
    raw_id_fields = ['to_remove', 'duplicate_of', 'voter']


@register(models.TopSubmissionCategory)
class TopSubmissionCategoryAdmin(ModelAdmin):
    list_display = ['slug', 'title']


@register(models.SiteMode)
class SiteModeAdmin(ModelAdmin):
    list_display = ['debate_time', 'previous_debate_time', 'show_question_votes',
                    'show_total_votes', 'allow_sorting_by_votes']
    actions = ['reset_current_votes']
    _fields = [f.name for f in models.SiteMode._meta.get_fields() if f.name != 'id']
    fieldsets = [
        ('General Settings', {
            'fields': ['show_question_votes', 'show_total_votes',
                       'allow_sorting_by_votes',
                       'allow_voting_and_submitting_questions',
                       'inline_css']
        }),
        ('Debate Details', {
            'fields': [f for f in _fields if 'debate_' in f],
        }),
        ('Announcement Details', {
            'fields': [f for f in _fields if f.startswith('announcement_')],
        }),
        ('Site Content', {
            'fields': ['hashtag', 'banner_header_title', 'banner_header_copy',
                       'popup_after_submission_text'],
        }),
        ('Email Share', {
            'fields': [f for f in _fields if f.startswith('email_')],
        }),
        ('Facebook Meta Data', {
            'fields': ['facebook_image'],
        }),
        ('Facebook Share of the Whole Site', {
            'fields': ['facebook_site_title', 'facebook_site_description'],
        }),
        ('Facebook Share of Individual Questions', {
            'fields': ['facebook_question_title', 'facebook_question_description'],
        }),
        ('Twitter Meta Data', {
            'fields': ['twitter_image', 'twitter_site_description',
                       'twitter_question_description'],
        }),
        ('Twitter Share of the Whole Site', {
            'fields': ['twitter_site_title', 'twitter_site_text'],
        }),
        ('Twitter Share of Individual Questions', {
            'fields': ['twitter_question_title',
                       'twitter_question_text_with_handle',
                       'twitter_question_text_no_handle'],
        }),
    ]
    _used_fields = [fieldset[1]['fields'] for fieldset in fieldsets]
    _used_fields = set(itertools.chain.from_iterable(_used_fields))
    _missed_fields = set(_fields) - _used_fields
    if _missed_fields:
        fieldsets.append(('Other', {'fields': sorted(list(_missed_fields))}))

    def reset_current_votes(self, request, queryset):
        # Note, currently all submissions are under the one and only SiteMode.
        models.Submission.objects.update(current_votes=0)
    reset_current_votes.short_description = "Reset vote counts since the last debate"


@register(models.FlatPageMetadataOverride)
class FlatPageMetadataOverrideAdmin(ModelAdmin):
    list_display = ['flatpage_url']

    def flatpage_url(self, obj):
        return obj.page.url

    def get_queryset(self, request):
        return super(FlatPageMetadataOverrideAdmin, self).get_queryset(
            request).select_related("page")
