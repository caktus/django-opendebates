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
