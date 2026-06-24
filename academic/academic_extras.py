from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    """Acceso a dict por clave variable: {{ mi_dict|dict_get:clave }}"""
    if isinstance(d, dict):
        return d.get(key)
    return None

@register.filter
def get(d, key):
    """Alias de dict_get para dicts anidados: {{ tabla|get:alumno_id|get:asig_id }}"""
    if isinstance(d, dict):
        return d.get(key)
    return None