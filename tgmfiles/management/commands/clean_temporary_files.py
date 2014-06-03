import datetime
import logging

from django.core.management.base import NoArgsCommand
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import smart_unicode

from tgmfiles.models import TemporaryFileWrapper, get_linked_expiry_time, get_expiry_time


class Command(NoArgsCommand):
    help = 'Cleans up TemporaryFileWrapper objects by deleting the ' \
           'ones that are older than the timedelta defined in TGM_EXPIRE_TIME.'

    @staticmethod
    def clean_temporary_files():
        linked_stale_delta = timezone.now() - datetime.timedelta(seconds=get_linked_expiry_time())
        stale_delta = timezone.now() - datetime.timedelta(seconds=get_expiry_time())

        files = TemporaryFileWrapper.objects.filter(Q(linked=True, modified__lte=linked_stale_delta) |
                                                    Q(linked=False, modified__lte=stale_delta))

        logging.info('clean_temporary_files: Removing %d TemporaryFileWrapper objects from DB.', files.count())
        logging.debug('clean_temporary_files: Removing TemporaryFileWrapper objects [%s].',
                      ', '.join([smart_unicode(x) for x in files.values_list('id', flat=True)]))

        files.delete()

    def handle(self, *args, **options):
        self.clean_temporary_files()
