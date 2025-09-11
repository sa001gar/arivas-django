from django import template

register = template.Library()

@register.filter
def until_period(value):
    """
    Returns the text up to the first full stop.
    """
    if not value:
        return ""
    text = value.replace("\n", " ")
    period_index = text.find(".")
    if period_index != -1:
        return text[:period_index + 1]  # include the period
    return text  # if no full stop, return whole thing
