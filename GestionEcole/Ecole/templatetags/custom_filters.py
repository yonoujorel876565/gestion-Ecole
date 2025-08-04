from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtre personnalisé pour accéder aux éléments d'un dictionnaire dans les templates
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key) 