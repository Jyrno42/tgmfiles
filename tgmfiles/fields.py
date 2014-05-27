import os

from django import forms
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import get_model

from tgmfiles.forms import allowed_type
from tgmfiles.models import get_upload_path, TemporaryFileWrapper
from tgmfiles.widgets import TgmSingleUploadWidget, TgmMultiUploadWidget


class TgmFormFileField(forms.FileField):
    def __init__(self, allowed_types, fq, widget, *args, **kwargs):
        self.field_query = fq
        self.allowed_types = allowed_types
        self.widget = widget(fq=self.field_query, is_image=False)

        super().__init__(*args, **kwargs)

    @staticmethod
    def get_content_type(file):
        import magic
        return magic.from_file(file.path, mime=True)

    def to_python(self, data):
        if type(data) == str and data[:3] == 'id:':
            # Pre uploaded linked file.
            return TemporaryFileWrapper.get_image_from_id(data[3:], self.field_query)

        data = super().to_python(data)

        if data:
            content_type = TgmFormFileField.get_content_type(data)
            if not allowed_type(content_type, self.allowed_types):
                # TODO: i18n and handle plurar form.
                raise forms.ValidationError("File %s should be one of the following types [%s]" % (
                    content_type,
                    ', '.join(self.allowed_types)))

        return data


class TgmFormImageField(forms.ImageField):
    def __init__(self, allowed_types, fq, widget, *args, **kwargs):
        self.field_query = fq
        self.allowed_types = allowed_types
        self.widget = widget(fq=self.field_query, is_image=True)

        super().__init__(*args, **kwargs)

    def to_python(self, data):
        if type(data) == str and data[:3] == 'id:':
            # Pre uploaded linked file.
            return TemporaryFileWrapper.get_image_from_id(data[3:], self.field_query)

        data = super().to_python(data)

        if data:
            content_type = TgmFormFileField.get_content_type(data)
            if not allowed_type(content_type, self.allowed_types):
                # TODO: i18n and handle plurar form.
                raise forms.ValidationError("File %s should be one of the following types [%s]" % (
                    content_type,
                    ', '.join(self.allowed_types)))

        return data


class TgmFileField(models.FileField):
    DEFAULT_FILE_TYPES = ['pdf', 'rar', 'zip']

    def __init__(self, fq, memory=None, allowed_types=None, widget=None, **kwargs):
        self.memory = memory
        self.widget = widget or self.get_widget_class()
        self.field_query = fq
        self.max_length = 128

        # Used for validators
        self.allowed_types = self.handle_allowed_types(allowed_types or self.DEFAULT_FILE_TYPES)

        super(TgmFileField, self).__init__(**kwargs)

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

        if defaults['widget'] is not TgmSingleUploadWidget and defaults['widget'] is not TgmMultiUploadWidget:
            del defaults['allowed_types']
            del defaults['form_class']
            del defaults['fq']

        return super(TgmFileField, self).formfield(**defaults)

    def get_file_path_pointer(self, model_instance):
        field_name = self.field_query.split('.')[-1]

        for field in model_instance._meta.fields:
            if field.name == field_name:
                if not isinstance(field, (TgmFileField, TgmImageField)):
                    raise Exception('Fields used in TGM Uploader must be instances of [TgmFileField, TgmImageField].')

                return field.upload_to

        return None

    def pre_save(self, model_instance, add):
        print('instance', model_instance)

        file = super(models.FileField, self).pre_save(model_instance, add)

        # If the file provided resides in the temporary files directory.
        if file and get_upload_path() in file.name:
            new_pointer = self.get_file_path_pointer(model_instance)
            if new_pointer is not None:
                # This currently replaces the filename generator function
                # with the correct one for the model field and then restores it after.
                #
                # FIXME: I know this is insane, but i have no idea how to do it better
                # (or why the function points to tgm_upload_file_name) so i'll let this
                #  one slide for now.
                old_pointer = file.field.generate_filename
                file.field.generate_filename = new_pointer

                path, filename = os.path.split(file.name)

                image_file = ContentFile(file.file.read(), file.name)
                file.save(filename, image_file, save=False)

                file.field.generate_filename = old_pointer
        return file


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
