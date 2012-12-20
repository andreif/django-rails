# coding=utf-8
from dagny import Resource, action
from dagny.utils import camel_to_underscore, resource_name
from django.shortcuts import redirect, get_object_or_404


@action.RENDERER.html
def render_html(action, resource):
    return resource.render_html(action)


class BaseResource(Resource):

    template_path_prefix = ''
    model = None

    def get_label(self):
        return camel_to_underscore(resource_name(self))

    def get_template_name(self, action, ext='.html'):
        return "%s%s/%s%s" % (self.template_path_prefix, self.get_label(), action.name, ext)

    def get_context(self):
        return {'Self': self, '_': self}

    def render_html(self, action):
        from coffin.shortcuts import render_to_response
        return render_to_response(self.get_template_name(action, ext='.haml'), self.get_context())

    def redirect(self, to_action, *args, **kwargs):
        return redirect('%s#%s' % (resource_name(self), to_action), *args, **kwargs)

    @property
    def objects(self):
        return self.model.objects

    def get_object(self, id):
        return get_object_or_404(self.model, id=id)
