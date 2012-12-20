# coding=utf-8
from django import template
from django.core.urlresolvers import reverse
import logging
import urllib


register = template.Library()


@register.tag
def url_to(resource, action=None):
    try:
        if isinstance(resource, basestring):
            resource_name = resource[:-1]
            action = action or 'index'
            extra = ''
        else:
            resource_name = resource.__class__.__name__.lower()
            action = action or 'show'
            extra = '?' + urllib.urlencode(dict(id=resource.id))
        return reverse('%s.%s' % (resource_name, action)) + extra
    except Exception as e:
        logging.error('Failed rendering url_to tag: %r', e)
