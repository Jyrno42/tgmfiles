import os
from django.db.models.fields.files import FieldFile
import six

from django import forms
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import get_model
from django.utils.translation import ungettext

from tgmfiles.forms import allowed_type
from tgmfiles.models import get_upload_path, TemporaryFileWrapper, human_readable_types
from tgmfiles.widgets import TgmSingleUploadWidget, TgmMultiUploadWidget


class TgmFormFileField(forms.FileField):
    def __init__(self, allowed_types, fq, widget, *args, **kwargs):
        self.field_query = fq
        self.allowed_types = allowed_types
        self.widget = widget(fq=self.field_query, is_image=False)

        super(TgmFormFileField, self).__init__(*args, **kwargs)

    @staticmethod
    def get_content_type(the_file):
        try:
            temporary = TemporaryFileWrapper.objects.get(file=the_file)
            return temporary.content_type

        except TemporaryFileWrapper.DoesNotExist:
            return 'application/unknown'

    @staticmethod
    def file_type_error(content_type, allowed_types):
        raise forms.ValidationError(ungettext("File should be a %s.",
                                              "File should be one of the following types [%s]",
                                              len(allowed_types)) % (human_readable_types(allowed_types)))

    def to_python(self, data):
        if isinstance(data, six.string_types) and data[:3] == 'id:':
            # Pre uploaded linked file.
            return TemporaryFileWrapper.get_image_from_id(data[3:], self.field_query)

        data = super(TgmFormFileField, self).to_python(data)

        if data:
            content_type = TgmFormFileField.get_content_type(data)
            if not allowed_type(content_type, self.allowed_types):
                self.file_type_error(content_type, self.allowed_types)

        return data


class TgmFormImageField(forms.ImageField):
    def __init__(self, allowed_types, fq, widget, *args, **kwargs):
        self.field_query = fq
        self.allowed_types = allowed_types
        self.widget = widget(fq=self.field_query, is_image=True)

        super(TgmFormImageField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        if isinstance(data, six.string_types) and data[:3] == 'id:':
            # Pre uploaded linked file.
            return TemporaryFileWrapper.get_image_from_id(data[3:], self.field_query)

        data = super(TgmFormImageField, self).to_python(data)
        if data:
            content_type = TgmFormFileField.get_content_type(data)
            if not allowed_type(content_type, self.allowed_types):
                TgmFormFileField.file_type_error(content_type, self.allowed_types)

        return data


class TgmFileField(models.FileField):
    DEFAULT_FILE_TYPES = ['application/pdf', 'application/x-rar-compressed', 'application/zip']

    def __init__(self, post_link=None, allowed_types=None, widget=None, get_upload_image=None, **kwargs):
        self.widget = widget or self.get_widget_class()
        self.field_query = None
        self.max_length = 128
        self.get_upload_image = get_upload_image

        # Used for validators
        self.allowed_types = self.handle_allowed_types(allowed_types or self.DEFAULT_FILE_TYPES)

        if post_link is not None and callable(post_link):
            setattr(self, 'post_link', post_link)

        super(TgmFileField, self).__init__(**kwargs)

    def contribute_to_class(self, cls, name):
        self.field_query = [cls, name]

        super(TgmFileField, self).contribute_to_class(cls, name)


    def post_link(self, real_instance, temporary_instance, raw_file):
        """ This function is used to provide a way for
            developers to do some needed post processing for files.

        :param real_instance: An instance of the model that will be saved to the database.
        :param temporary_instance: An instance of TemporaryImageWrapper.
        :param raw_file: The raw file which was uploaded, can be None.

        :returns: bool True if you want to mark this temporary file linked (linked files are cleaned up more often).
        """
        return True

    @staticmethod
    def handle_allowed_types(allowed_types):

        image_types = {'image/gif', 'image/jpeg', 'image/jpg', 'image/png'}

        if 'type:image' in allowed_types:
            # Add image types to the allowed types list
            allowed_types.pop(allowed_types.index('type:image'))
            allowed_types = list(set(allowed_types + list(image_types)))

        return allowed_types

    @staticmethod
    def get_widget_class():
        return TgmSingleUploadWidget

    @staticmethod
    def get_form_class():
        return TgmFormFileField

    def formfield(self, **kwargs):
        defaults = {
            'allowed_types': self.allowed_types,
            'form_class': self.get_form_class(),
            'widget': self.widget,
            'fq': self.field_query,
        }
        defaults.update(kwargs)

        if not getattr(defaults['widget'], 'is_tgm_widget', False):
            del defaults['allowed_types']
            del defaults['form_class']
            del defaults['fq']

        return super(TgmFileField, self).formfield(**defaults)

    def get_file_path_pointer(self, model_instance):
        field = self.get_field_pointer(model_instance)
        if field is not None:
            return field.upload_to
        else:
            return None

    def get_field_pointer(self, model_instance):
        for field in model_instance._meta.fields:
            if field.name == self.field_query[1]:
                if not isinstance(field, (TgmFileField, TgmImageField)):
                    raise Exception('Fields used in TGM Uploader must be instances of [TgmFileField, TgmImageField].')

                return field

        return None

    def pre_save(self, model_instance, add):
        the_file = super(models.FileField, self).pre_save(model_instance, add)
        real_file = the_file

        # If the file provided is a Temporary One
        if the_file and hasattr(the_file, 'instance') and isinstance(the_file.instance, TemporaryFileWrapper):
            path, filename = os.path.split(the_file.name)
            new_file = FieldFile(model_instance, self.get_field_pointer(model_instance), filename)

            image_file = ContentFile(the_file.file.read(), the_file.name)
            new_file.save(filename, image_file, save=False)

            real_file = new_file

        elif the_file and not the_file._committed and not getattr(self.widget, 'is_tgm_widget', False):
            # Commit the file to storage prior to saving the model
            # This makes this model work correctly with other widgets
            # (e.g. a plain image upload in admin)
            the_file.save(the_file.name, the_file, save=False)

        if self.post_link(model_instance, the_file.instance if the_file else the_file, real_file):
            if the_file and isinstance(the_file.instance, TemporaryFileWrapper):
                the_file.instance.linked = True
                the_file.instance.save()

        return real_file


class TgmImageField(TgmFileField):
    DEFAULT_FILE_TYPES = ['type:image']

    @staticmethod
    def get_widget_class():
        return TgmSingleUploadWidget

    @staticmethod
    def get_form_class():
        return TgmFormImageField

    def formfield(self, **kwargs):
        return super(TgmImageField, self).formfield(**kwargs)


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^tgmfiles\.fields\.TgmFileField"])
    add_introspection_rules([], ["^tgmfiles\.fields\.TgmImageField"])
except ImportError:
    pass
