# coding=utf-8
"""
urlpatterns = patterns('',
    (r'^accounts', AccountsController.routes()),
)

class AccountsController(BaseController):
    simple_actions = 'index profile'.split()

    @action('get', 'post', 'put', 'delete', 'patch') # CRUD - create, read, update, delete
    def login(self):
        if self._is_authenticated():
            return self._redirect(to='.index')
        if self._request.POST.get('remember_me'):
            self._request.session.set_expiry(365*24*60*60) # 1 year
        return self._auth_proxy(authentication_form=AccountLoginForm)

    @action
    def logout(self):
        return self._auth_proxy(next_page=self._reverse('.login'))

"""
import json
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django import http
from django.template import TemplateDoesNotExist
from django.views.generic import View
import urllib
import re
from . import utils


def action(*args, **kwargs):
    func = args[0] if len(args) == 1 and callable(args[0]) else None

    def decorator(fn):
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        wrapper.responds_to = (None if func else args) or ['get', 'post']
        return wrapper
    if func:
        return decorator(func)
    else:
        return decorator


class Context(dict):

    def __setattr__(self, key, value):
        if isinstance(key, basestring) and key.startswith('_'):
            super(Context, self).__setattr__(key, value)
        else:
            self[key] = value

    def __getattribute__(self, item):
        try:
            return super(Context, self).__getattribute__(item)
        except AttributeError as e:
            if isinstance(item, basestring):
                return self.get(item)
            else:
                raise e

    def update(self, E=None, **F):
        super(Context, self).update(**F)
        return self

    def __call__(self, *args, **kwargs):
        if args:
            raise
        return self.update(**kwargs)


class Request(object):

    def __init__(self, request):
        self.request = request

    def is_ajax(self):
        return self.request.is_ajax()

    def is_post(self):
        return self.request.method == 'POST'

    def is_get(self):
        return self.request.method == 'GET'

    def is_authenticated(self):
        return self.request.user and self.request.user.is_authenticated()

    def is_staff(self):
        return self.is_authenticated() and self.request.user.is_staff

    def is_superuser(self):
        return self.is_authenticated() and self.request.user.is_superuser

    def data(self, *keys):
        if self.is_get():
            data = self.request.GET
        elif self.is_post():
            data = self.request.POST
        else:
            raise
        if keys:
            values = [data.get(k) for k in keys]
            if len(values) == 1:
                return values[0]
            else:
                return values
        else:
            return data

    def data_dict(self):
        return utils.make_data_dict(self.data())


class Router(object):

    def __init__(self, controller_class):
        if isinstance(controller_class, BaseController):
            self.controller_class = controller_class.__class__
        else:
            self.controller_class = controller_class
        self.controller_name = self.controller_class._controller_name()

    def get_routes(self):
        cls = self.controller_class
        actions = cls._actions() + cls.simple_actions
        routes = [self.get_route(name) for name in actions]
        if 'index' in actions:
            routes.append(self.get_route('index', regex=r'^/?$'))

        class urlconf_module(object):
            urlpatterns = patterns('', *routes)
        return urlconf_module, cls.app_name, cls.namespace
        #import collections
        #urlconf_module = collections.namedtuple('urlconf_module', 'urlpatterns')
        #return urlconf_module(urlpatterns = patterns('', *routes)), 'x', ''

    def get_view(self, name, *args, **kwargs):
        def view(request, *args, **kwargs):
            return self.controller_class(request, name)._render()
        return view

    def get_route(self, name, regex=None):
        return url(
            regex or r'^/%s(\.[a-z]+)?/?$' % name.replace('_', '-'),
            self.get_view(name),
            name='%s.%s' % (self.controller_name, name),
        )

    def reverse(self, url):
        if '/' not in url:
            if url.startswith('.'):
                url = self.controller_name + url
            elif url.startswith('#'):
                url = self.controller_name + '.' + url[1:]
            url = reverse(url)
        return url


class Renderer(object):

    allowed_extensions = ('html', 'haml')

    def __init__(self, controller):
        self.controller = controller

    def render_to_response(self, template_name):
        from coffin.shortcuts import render_to_response
        from coffin.template import RequestContext
        return render_to_response(template_name, self.controller.cx, RequestContext(self.controller.rq.request))

    def find_template(self, template_name):
        for ext in self.allowed_extensions:
            try:
                utils.load_template_source(template_name + '.' + ext)
                return template_name + '.' + ext
            except TemplateDoesNotExist:
                continue
        raise TemplateDoesNotExist(template_name + '.%s' % str(self.allowed_extensions))


class Inspector(object):

    def __init__(self, controller_class):
        self.controller_class = controller_class


class BaseController(View):

    simple_actions = []
    template_name_prefix = ''
    app_name = None
    namespace = None

    def __init__(self, request, action):
        super(BaseController, self).__init__()
        self.cx = Context()
        self.rq = Request(request)
        self.router = Router(self.__class__)
        self.renderer = Renderer(self)
        self._current_action = action
        self.cx.current_action = action

    def _redirect(self, to='/', params=None):
        if to == ':back':
            url = self.rq.request.META['HTTP_REFERER']
        else:
            url = self.router.reverse(to)
            if isinstance(params, dict):
                url += '?' + urllib.urlencode(params)
            elif params and hasattr(params, 'id'):
                url += '?' + urllib.urlencode(dict(id=params.id))
        return http.HttpResponseRedirect(redirect_to=url)

    def _template(self, name=None):
        name = self.cx.action_template or name or self._current_action
        if '/' in name:
            template_name = name
        else:
            name = name or self._current_action
            template_name = '%s%s/%s' % (self.template_name_prefix, self._controller_name(), name)
        return self.renderer.find_template(template_name)

    def _before_render(self):
        pass

    def _render(self, name=None):
        name = name or self._current_action
        self.cx(
            current_action=self._current_action,
            current_controller=self._controller_name(),
            title='%s | %s' % (self._controller_name(), name)
        )
        if name in self._actions():
            response = self._before_render() or getattr(self, name)()
            if isinstance(response, http.HttpResponse):
                return response
        elif name not in self.simple_actions:
            return http.HttpResponseNotFound('Unknown route')
        return self.renderer.render_to_response(self._template(name))

    def _render_json(self, data):
        return http.HttpResponse(json.dumps(data), mimetype='application/json')

    def _render_error(self, status=403):
        return http.HttpResponse(status=status)

    def render(self, action):
        self.cx.update(action_template=action)

    @classmethod
    def _controller_name(cls):
        return re.sub(r'([A-Z]+)', '_\\1', cls.__name__).lower()[1:-11]

    @classmethod
    def _is_action(cls, name):
        return not name.startswith('_') and hasattr(getattr(cls, name), 'responds_to')

    @classmethod
    def _actions(cls):
        return [name for name in dir(cls) if cls._is_action(name)]

    @classmethod
    def routes(cls):
        return Router(cls).get_routes()

    @classmethod
    def render_view(cls, name, request, *args, **kwargs):
        return Router(cls).get_view(name)(request, *args, **kwargs)
