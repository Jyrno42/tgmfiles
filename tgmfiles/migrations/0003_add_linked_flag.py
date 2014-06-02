# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'TemporaryFileWrapper.linked'
        db.add_column(u'tgmfiles_temporaryfilewrapper', 'linked',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'TemporaryFileWrapper.linked'
        db.delete_column(u'tgmfiles_temporaryfilewrapper', 'linked')


    models = {
        u'tgmfiles.temporaryfilewrapper': {
            'Meta': {'object_name': 'TemporaryFileWrapper'},
            'content_type': ('django.db.models.fields.CharField', [], {'default': "'application/unknown'", 'max_length': '128'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'md5sum': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['tgmfiles']