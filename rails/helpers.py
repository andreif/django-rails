# coding=utf-8
import logging
import urllib


def helper(func):
    from coffin.common import env
    env.globals[func.__name__] = func
    return func


@helper
def url_to(resource, action=None, **params):
    from django.core.urlresolvers import reverse
    try:
        extra = ''
        if isinstance(resource, basestring):
            if '.' in resource:
                name = resource
                if action and not isinstance(action, basestring):
                    params['id'] = str(action.id)
                if params:
                    for k, v in params.iteritems():
                        if isinstance(v, unicode):
                            params[k] = v.encode('utf8')
                    extra = '?' + urllib.urlencode(params)
            else:
                resource_name = resource[:-1]
                action = action or 'index'
                name = '%s.%s' % (resource_name, action)
        else:
            from . import utils
            resource_name = utils.to_underscore(resource.__class__.__name__)
            action = action or 'show'
            extra = '?' + urllib.urlencode(dict(id=resource.id))
            name = '%s.%s' % (resource_name, action.replace('#', ''))
        return reverse(name) + extra
    except Exception as e:
        logging.error('Failed rendering url_to tag: %r', e)


@helper
def markdown(text):
    import jinja2
    from .utils import markdown_urlize
    return jinja2.Markup(markdown_urlize(text))
