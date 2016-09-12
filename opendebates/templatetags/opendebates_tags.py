from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def provide_site_mode_to(context, obj):
    """
    Convenience method to add the SiteMode object available in the template
    context to a model object (such as Submission). Helps avoid a call out to
    the cache for each Submission in opendebates/list_ideas.html.
    """
    obj._cached_site_mode = context['SITE_MODE']
    return ''
