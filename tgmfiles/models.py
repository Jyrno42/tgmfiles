import hashlib
import os
import uuid

from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models import get_model
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


def get_upload_path():
    return getattr(settings, 'TGM_UPLOAD_TO', 'temp-files')


def get_expiry_time():
    return getattr(settings, 'TGM_EXPIRE_TIME', 60*60*24)


def get_max_file_size():
    return getattr(settings, 'TGM_MAX_FILE_SIZE', 2*1024*1024)


def get_size_error():
    # TODO: i18n
    return "Uploaded file too large ( > %s )" % filesizeformat(get_max_file_size())


def tgm_upload_file_name(instance, filename):
    if len(filename) > 40:
        filename = filename[-40:]

    return os.path.join(get_upload_path(), uuid.uuid4().hex, filename)


def human_readable_types(types):
    ret = ['.%s' % (x.split('/')[-1] if "/" in x else x) for x in types]
    return ', '.join(ret)


class TemporaryFileWrapper(models.Model):
    """ Holds an arbitrary file and notes when it was last accessed
    """
    file = models.FileField(upload_to=tgm_upload_file_name)

    # session = models.ForeignKey(Session, blank=True, null=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    modified = models.DateTimeField(auto_now=True)
    md5sum = models.CharField(max_length=36, unique=True)

    def get_hash(self):
        md5 = hashlib.md5()
        for chunk in self.file.chunks():
            md5.update(chunk)

        return md5.hexdigest()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.md5sum = self.get_hash()

        if not self.pk or TemporaryFileWrapper.objects.exclude(id=self.pk).filter(md5sum=self.md5sum).exists():
            try:
                self.pk = TemporaryFileWrapper.objects.exclude(id=self.pk).get(md5sum=self.md5sum).pk
            except TemporaryFileWrapper.DoesNotExist:
                pass

        return super(TemporaryFileWrapper, self).save(force_insert, force_update, using, update_fields)

    @staticmethod
    def get_image_from_id(img_id, field_query):
        try:
            img_id = int(img_id)
        except (ValueError, TypeError):
            return None
        else:
            field_component = field_query.split('.')
            model = get_model(field_component[0], field_component[1])

            try:
                instance = model.objects.get(id=img_id)
            except model.DoesNotExist:
                return None
            else:
                return getattr(instance, field_component[2])


@receiver(post_delete, sender=TemporaryFileWrapper)
def cleanup_temporary_files(sender, instance, **kwargs):
    instance.uploaded_file.close()
    storage, path = instance.uploaded_file.storage, instance.uploaded_file.path
    try:
        storage.delete(path)
    except IOError:
        pass

