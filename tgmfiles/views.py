import json
import re

from django.db.models import get_model, UnavailableApp
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from tgmfiles.fields import TgmFileField, TgmImageField
from tgmfiles.forms import TemporaryFileForm


class FileUploadView(View):
    http_method_names = ['post', ]
    FQ_REGEX = re.compile(r'^FQ:([\w\d]+)\.([\w\d]+)\.([\w\d]+)$')

    @staticmethod
    def json_response(response, status=200):
        return HttpResponse(json.dumps(response), status=status)


    @classmethod
    def parse_field_component(cls, component):

        if component[:3] != 'FQ:':
            raise NotImplementedError('Encrypted field path is not supported yet.')

        mat = cls.FQ_REGEX.match(component)
        if mat:
            return mat.group(1), mat.group(2), mat.group(3)

        return None

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        field_component = self.parse_field_component(request.POST.get('fq', None))
        if not field_component:
            return

        valid, field_value, errors = self.validate_fq(field_component)
        if valid:
            form = TemporaryFileForm(field_value, request.POST, request.FILES)
            if form.is_valid():
                instance = form.save()

                return self.json_response({
                    'success': True,
                    'file': {
                        'id': instance.id,
                        'md5sum': instance.md5sum,
                        'url': instance.file.url,
                        'file_name': instance.file.name,
                        'instance_type': 'image' if isinstance(field_value, TgmImageField) else 'file'
                    },
                })
            else:
                for field, error_val in form.errors.items():
                    for error_txt in error_val:
                        errors += [force_text(error_txt)]

        return self.json_response({
            'success': False,
            'errors': str(errors[0])
        }, status=403)

    @staticmethod
    def validate_fq(field_component):
        if field_component is None or len(field_component) != 3:
            return False, None, ['FQ protection validation failed.']

        try:
            model = get_model(field_component[0], field_component[1])
        except UnavailableApp as e:
            model = None

        if model is None:
            return False, None, ['FQ protection validation failed.']

        for field in model._meta.fields:
            if field.name == field_component[2]:
                if not isinstance(field, (TgmFileField, TgmImageField)):
                    raise Exception('Fields used in TGM Uploader must be instances of [TgmFileField, TgmImageField].')
                return True, field, []

        return False, None, ['FQ protection validation failed.']
