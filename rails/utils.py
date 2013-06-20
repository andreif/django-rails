# coding=utf-8
import re
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import find_template_loader

template_source_loaders = None


def get_template_source_loaders():
    global template_source_loaders
    if template_source_loaders is None:
        loaders = []
        for loader_name in settings.TEMPLATE_LOADERS:
            loader = find_template_loader(loader_name)
            if loader is not None:
                loaders.append(loader)
        template_source_loaders = tuple(loaders)
    return template_source_loaders


def load_template_source(name, dirs=None):
    for loader in get_template_source_loaders():
        try:
            return loader.load_template_source(template_name=name, template_dirs=dirs)
        except TemplateDoesNotExist:
            pass
    raise TemplateDoesNotExist(name)


def make_data_dict(data):
    dic = {}

    def set_dic(d, keys, value):
        k = keys.pop(0)
        if keys:
            d.setdefault(k, {})
            return set_dic(d[k], keys, value)
        else:
            d[k] = value

    for k in data.keys():
        if k.endswith('[]'):
            v = data.getlist(k)
        else:
            v = data.get(k)
        set_dic(dic, k.split('-'), v)

    return dic


def to_underscore(camelcase):
    return re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', r'_\1', camelcase).lower().strip('_')


try:
    from django.contrib.markup.templatetags.markup import markdown
except ImportError:
    markdown = lambda x: x


try:
    from django.utils.html import urlize
except ImportError:
    urlize = lambda x: x


def markdown_urlize(node):
    return markdown(urlize(node)).replace('href="www.', 'href="http://www.')


def remove_indent(text):
    lines = text.split('\n')
    min_indent = None
    for i in range(0, len(lines)):
        if re.match(r'^\s*$', lines[i]):
            lines[i] = ''
        else:
            m = re.search(r'^(\s+)', lines[i])
            if m:
                if min_indent is None or len(m.group(0)) < min_indent:
                    min_indent = len(m.group(0))
    if min_indent:
        for i in range(1, len(lines) - 1):
            if lines[i].startswith(' ' * min_indent):
                lines[i] = lines[i][min_indent:]
    return '\n'.join(lines).strip()
