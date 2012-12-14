# my_filters.py
# Some custom filters for dictionary lookup.
from django.template.defaultfilters import register

@register.filter(name='lookup')
def lookup(dict, index):
    if index in dict:
        return dict[index]
    return ''