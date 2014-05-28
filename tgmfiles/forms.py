import os

from django import forms
from django.template.defaultfilters import filesizeformat

from tgmfiles.models import TemporaryFileWrapper, get_max_file_size, human_readable_types, get_size_error


def allowed_type(file_type, allowed_types):
    if type(file_type) is not str:
        file_type = str(file_type, 'utf8')

    return file_type in allowed_types


class TemporaryFileForm(forms.ModelForm):
    class Meta:
        model = TemporaryFileWrapper

        fields = ('file', )

    def __init__(self, real_field, *args, **kwargs):
        self.allowed_types = real_field.allowed_types

        super().__init__(*args, **kwargs)

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file', False)
        if uploaded_file:
            if uploaded_file._size > get_max_file_size():
                # TODO: Correct size for error.
                raise forms.ValidationError(get_size_error())
        else:
            raise forms.ValidationError("Couldn't read uploaded file")

        if not allowed_type(uploaded_file.content_type, self.allowed_types):
            # TODO: i18n and handle plurar form.
            raise forms.ValidationError("File should be one of the following types [%s]" % (
                human_readable_types(self.allowed_types)))

        return uploaded_file
