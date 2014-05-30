from django import forms
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext_lazy as _

from tgmfiles.models import TemporaryFileWrapper, get_max_file_size, get_size_error


def allowed_type(file_type, allowed_types):
    if '*' in allowed_types:
        return True

    if type(file_type) is not str:
        file_type = str(file_type, 'utf8')

    return file_type in allowed_types


class TemporaryFileForm(forms.ModelForm):
    class Meta:
        model = TemporaryFileWrapper

        fields = ('file', )

    def __init__(self, real_field, *args, **kwargs):
        self.allowed_types = real_field.allowed_types
        self.content_type = 'application/unknown'

        super(TemporaryFileForm, self).__init__(*args, **kwargs)

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file', False)
        if uploaded_file:
            if uploaded_file._size > get_max_file_size():
                raise forms.ValidationError(get_size_error())
        else:
            raise forms.ValidationError(smart_unicode(_("Couldn't read uploaded file")))

        if not allowed_type(uploaded_file.content_type, self.allowed_types):
            from tgmfiles.fields import TgmFormFileField
            TgmFormFileField.file_type_error(uploaded_file.content_type, self.allowed_types)

        if uploaded_file:
            self.content_type = uploaded_file.content_type

        return uploaded_file

    def save(self, commit=True):
        inst = super(TemporaryFileForm, self).save(commit=False)
        inst.content_type = self.content_type

        return super(TemporaryFileForm, self).save(commit=True)
