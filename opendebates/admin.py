import itertools

from django.contrib.admin import ModelAdmin, register
from djangohelpers.export_action import admin_list_export

from . import models


@register(models.Category)
class CategoryAdmin(ModelAdmin):
    list_display = [f.name for f in models.Category._meta.fields]
    actions = [admin_list_export]


@register(models.Submission)
class SubmissionAdmin(ModelAdmin):
    list_display = [f.name for f in models.Submission._meta.fields]
    actions = [admin_list_export]
    raw_id_fields = ['voter', 'duplicate_of']


@register(models.Voter)
class VoterAdmin(ModelAdmin):
    list_display = [f.name for f in models.Voter._meta.fields]
    actions = [admin_list_export]
    raw_id_fields = ['user', ]


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


@register(models.SiteMode)
class SiteModeAdmin(ModelAdmin):
    list_display = ['debate_time', 'show_question_votes', 'show_total_votes',
                    'allow_sorting_by_votes']
    _fields = [f.name for f in models.SiteMode._meta.get_fields() if f.name != 'id']
    fieldsets = [
        ('General Settings', {
            'fields': ['show_question_votes', 'show_total_votes', 'allow_sorting_by_votes',
                       'allow_voting_and_submitting_questions']
        }),
        ('Debate Details', {
            'fields': [f for f in _fields if f.startswith('debate_')],
        }),
        ('Announcement Details', {
            'fields': [f for f in _fields if f.startswith('announcement_')],
        }),
        ('Site Content', {
            'fields': ['hashtag', 'banner_header_title', 'banner_header_copy',
                       'popup_after_submission_text'],
        }),
        ('Email Sharing Defaults', {
            'fields': [f for f in _fields if f.startswith('email_')],
        }),
        ('Facebook Sharing Defaults', {
            'fields': [f for f in _fields if f.startswith('facebook_')],
        }),
        ('Twitter Sharing Defaults', {
            'fields': [f for f in _fields if f.startswith('twitter_')],
        }),
    ]
    _used_fields = [fieldset[1]['fields'] for fieldset in fieldsets]
    _used_fields = set(itertools.chain.from_iterable(_used_fields))
    _missed_fields = set(_fields) - _used_fields
    if _missed_fields:
        fieldsets.append(('Other', {'fields': sorted(list(_missed_fields))}))
