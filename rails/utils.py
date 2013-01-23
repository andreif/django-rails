# coding=utf-8
import logging
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
