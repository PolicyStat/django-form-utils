# -*- coding: utf-8 -*-
"""
widgets for django-form-utils

parts of this code taken from http://www.djangosnippets.org/snippets/934/
 - thanks baumer1122

"""
from __future__ import unicode_literals

import posixpath

import django
from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .settings import JQUERY_URL

try:
    from sorl.thumbnail import get_thumbnail

    def thumbnail(image_path, width, height):
        geometry_string = 'x'.join([str(width), str(height)])
        t = get_thumbnail(image_path, geometry_string)
        return u'<img src="%s" alt="%s" />' % (t.url, image_path)
except ImportError:
    try:
        from easy_thumbnails.files import get_thumbnailer

        def thumbnail(image_path, width, height):
            thumbnail_options = dict(size=(width, height), crop=True)
            thumbnail = get_thumbnailer(image_path).get_thumbnail(
                thumbnail_options)
            return u'<img src="%s" alt="%s" />' % (thumbnail.url, image_path)
    except ImportError:
        def thumbnail(image_path, width, height):
            absolute_url = posixpath.join(settings.MEDIA_URL, image_path)
            return u'<img src="%s" alt="%s" />' % (absolute_url, image_path)


class ImageWidget(forms.FileInput):
    template = '%(input)s<br />%(image)s'

    def __init__(self, attrs=None, template=None, width=200, height=200):
        if template is not None:
            self.template = template
        self.width = width
        self.height = height
        super(ImageWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        input_html = super(ImageWidget, self).render(name, value, attrs)
        if hasattr(value, 'width') and hasattr(value, 'height'):
            image_html = thumbnail(value.name, self.width, self.height)
            output = self.template % {'input': input_html,
                                      'image': image_html}
        else:
            output = input_html
        return mark_safe(output)


class ClearableFileInputRenderer(object):
    def __init__(self, template_string):
        self.template_string = template_string

    def set_value(self, value):
        self.input_value = value

    def render(self, template_name, context, request=None):

        input_context = dict(widget={})
        input_context['widget'].update(context['widget']['subwidgets'][0])

        checkbox_context = dict(widget={})
        checkbox_context['widget'].update(context['widget']['subwidgets'][1])

        input_html = render_to_string(
            context['widget']['subwidgets'][0]['template_name'],
            input_context,
            request,
        )

        checkbox_html = render_to_string(
            context['widget']['subwidgets'][1]['template_name'],
            checkbox_context,
            request,
        )

        return self.get_clearable_file_input(
            [
                input_html,
                checkbox_html,
            ]
        )

    def get_clearable_file_input(self, rendered_widgets):
        # Only show the clear checkbox if the input has a value
        if self.input_value:
            return self.template_string % {
                'input': rendered_widgets[0],
                'checkbox': rendered_widgets[1]
            }

        return rendered_widgets[0]


class ClearableFileInput(forms.MultiWidget):
    default_file_widget_class = forms.FileInput
    template = '%(input)s Clear: %(checkbox)s'

    def __init__(self, file_widget=None, attrs=None, template=None):
        if template is not None:
            self.template = template

        file_widget = file_widget or self.default_file_widget_class()

        self.renderer = ClearableFileInputRenderer(self.template)

        super(ClearableFileInput, self).__init__(
            widgets=[file_widget, forms.CheckboxInput()],
            attrs=attrs)

    def render(self, name, value, attrs=None):
        if isinstance(value, list):
            self.value = value[0]
        else:
            self.value = value

        self.renderer.set_value(value)

        render_kwargs = dict()
        render_kwargs['renderer'] = self.renderer
        if django.VERSION < (1, 11, 0):
            del render_kwargs['renderer']
        return super(ClearableFileInput, self).render(
            name,
            value,
            attrs,
            **render_kwargs
        )

    def decompress(self, value):
        # The clear checkbox is never initially checked
        return [value, None]

    def format_output(self, rendered_widgets):
        # Only show the clear checkbox if the input has a value
        if self.value:
            return self.template % {'input': rendered_widgets[0],
                                    'checkbox': rendered_widgets[1]}
        return rendered_widgets[0]


def root(path):
    return posixpath.join(settings.STATIC_URL, path)


class AutoResizeTextarea(forms.Textarea):
    """
    A Textarea widget that automatically resizes to accomodate its contents.
    """
    class Media:
        js = (JQUERY_URL,
              root('form_utils/js/jquery.autogrow.js'),
              root('form_utils/js/autoresize.js'))

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        try:
            attrs['class'] = "%s autoresize" % (attrs['class'],)
        except KeyError:
            attrs['class'] = 'autoresize'
        attrs.setdefault('cols', 80)
        attrs.setdefault('rows', 5)
        super(AutoResizeTextarea, self).__init__(*args, **kwargs)


class InlineAutoResizeTextarea(AutoResizeTextarea):
    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        try:
            attrs['class'] = "%s inline" % (attrs['class'],)
        except KeyError:
            attrs['class'] = 'inline'
        attrs.setdefault('cols', 40)
        attrs.setdefault('rows', 2)
        super(InlineAutoResizeTextarea, self).__init__(*args, **kwargs)
