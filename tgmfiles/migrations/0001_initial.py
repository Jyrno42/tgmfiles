# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TemporaryFileWrapper'
        db.create_table('tgmfiles_temporaryfilewrapper', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('md5sum', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
        ))
        db.send_create_signal('tgmfiles', ['TemporaryFileWrapper'])


    def backwards(self, orm):
        # Deleting model 'TemporaryFileWrapper'
        db.delete_table('tgmfiles_temporaryfilewrapper')


    models = {
        'tgmfiles.temporaryfilewrapper': {
            'Meta': {'object_name': 'TemporaryFileWrapper'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5sum': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['tgmfiles']