from django.template.defaultfilters import register

## tags.py
@register.simple_tag
def active_if_starts(path, pattern):
    print "xx", path, pattern
    if path.startswith(pattern):
        return 'active'
    return ''
    