from django import template
from opendebates.models import FlatPageMetadataOverride


register = template.Library()


@register.simple_tag(takes_context=True)
def provide_debate_to(context, obj):
    """
    Convenience method to add the Debate object available in the template
    context to a model object (such as Submission). Helps avoid a call out to
    the cache for each Submission in opendebates/list_ideas.html.
    """
    obj._cached_debate = context['DEBATE']
    return ''


@register.filter
def flatpage_metadata(flatpage):
    try:
        return flatpage.metadata
    except FlatPageMetadataOverride.DoesNotExist:
        return None
