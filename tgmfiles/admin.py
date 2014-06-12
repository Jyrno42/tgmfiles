from django.contrib import admin
from tgmfiles.models import TemporaryFileWrapper, show_in_admin

if show_in_admin():
    admin.site.register(TemporaryFileWrapper)
