import os

from django.core.urlresolvers import reverse
from django.forms import widgets, CheckboxInput
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from tgmfiles.models import TemporaryFileWrapper, get_max_file_size, get_size_error


DELETE_FIELD_HTML = """
            <input type="checkbox" id="id-{clear_checkbox_name}" name="{clear_checkbox_name}" value='1' {delete_val} />
"""

HTML = """
    <div class="col-xs-12 col-md-12 well {classes}"
        data-upload-url="{upload_url}" data-max-size="{max_size}" data-size-error="{size_error}">

        <label>
            <img src="{file_url}">

            <span class="file-display">
                <i class="fa fa-file"></i>
                <span>{file_name}</span>
            </span>

            <span class="upload-link"><i class="fa fa-cloud-upload"></i></span>

            <div class="progress-area">
                Uploading...
                <div class="progress progress-striped active">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
            </div>

            <input type="file" id="{element_id}" name="{name}" />
            <input type="hidden" id="{element_id}_md5sum" name="{md5sum_field_name}" value="{md5sum_field_value}" />
            <input type="hidden" id="{element_id}_FQ" name="{fq_field_name}" value='{FQ}' />
            {delete_field}
        </label>

        <button type="button" class="close">&times;</button>
    </div>
"""


class TgmSingleUploadWidget(widgets.FileInput):
    class Media:
        js = (
            'tgm-files/js/jquery.iframe-transport.js',
            'tgm-files/js/jquery.ui.widget.js',
            'tgm-files/js/jquery.fileupload.js',
            'tgm-files/js/tgm-fileupload.js',
        )
        css = {
            'all': ('tgm-files/css/font-awesome.css', 'tgm-files/css/main.css', ),
        }

    widget_class = 'single-uploader'

    def __init__(self, fq, is_image, attrs=None):
        self.field_query = fq
        self.is_image = is_image

        super().__init__(attrs)

    @staticmethod
    def clear_checkbox_name(name):
        if '-' not in name:
            return '%s-DELETE' % name

        return '%s-DELETE' % '-'.join(name.split('-')[:-1])

    @staticmethod
    def fq_field_name(name):
        return '%s_FQ' % name

    @staticmethod
    def md5sum_field_name(name):
        return '%s_md5sum' % name

    def get_fq(self):
        return 'FQ:%s' % self.field_query

    def get_required_state(self):
        return self.is_required

    def value_from_datadict(self, data, files, name):
        upload = data.get(self.md5sum_field_name(name), None)
        fq = data.get(self.fq_field_name(name), None)

        if type(upload) == str and upload[:3] == 'id:':
            # Pre uploaded linked file.
            return TemporaryFileWrapper.get_image_from_id(upload[3:], self.field_query)

        if fq != self.get_fq():
            raise Exception('For some reason FQ value is wrong...')

        was_deleted = CheckboxInput().value_from_datadict(data, files, self.clear_checkbox_name(name))

        if not self.get_required_state() and was_deleted:
            # If isn't required and delete is checked
            if not upload:
                # False signals to clear any existing value, as opposed to just None
                return False

        if upload:
            try:
                real_file = TemporaryFileWrapper.objects.get(md5sum=upload)
            except TemporaryFileWrapper.DoesNotExist:
                pass
            else:
                upload = real_file.file

        return upload

    def render_delete_field(self, name, delete_val):
        return DELETE_FIELD_HTML.format(
            clear_checkbox_name=self.clear_checkbox_name(name),
            delete_val=delete_val
        )

    def render(self, name, value, attrs=None):
        element_id = 'id'
        md5sum_field_value = ''
        file_url = ''

        if value:
            if hasattr(value, 'instance') and isinstance(value.instance, TemporaryFileWrapper):
                # Case 1: Pre existing temporary-file in form.
                md5sum_field_value = value.instance.md5sum
                file_url = force_text(value.instance.file.url)
            elif hasattr(value, "url"):
                # Case 2: Pre existing linked-file in form.
                file_url = force_text(value.url)
                md5sum_field_value = 'id:%s' % value.instance.id

        classes = ['file-uploader', self.widget_class, 'has-image' if file_url else '']

        if file_url and not self.is_image:
            classes.append('is-file')

        upload_url = reverse('tgm-file-upload')
        delete_val = '' if file_url else 'checked="checked"'

        file_name = os.path.split(value.name)[-1] if value and hasattr(value, "name") else 'Uploaded.pdf'

        delete_field = self.render_delete_field(name, delete_val)

        output = HTML.format(
            name=name,
            file_url=file_url,
            element_id=element_id,
            classes=' '.join(classes),
            upload_url=upload_url,
            FQ=self.get_fq(),
            md5sum_field_name=self.md5sum_field_name(name),
            fq_field_name=self.fq_field_name(name),
            md5sum_field_value=md5sum_field_value,
            delete_field=delete_field,
            file_name=file_name,
            max_size=get_max_file_size(),
            size_error=get_size_error(),
        )

        return mark_safe(str(output))


class TgmMultiUploadWidget(TgmSingleUploadWidget):
    widget_class = 'multi-uploader'

    def render_delete_field(self, name, delete_val):
        return ''
