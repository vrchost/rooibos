# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Collection'
        db.create_table('data_collection', (
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('agreement', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(db_index=True, unique=True, max_length=50, blank=True)),
        ))
        db.send_create_signal('data', ['Collection'])

        # Adding M2M table for field children on 'Collection'
        db.create_table('data_collection_children', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_collection', models.ForeignKey(orm['data.collection'], null=False)),
            ('to_collection', models.ForeignKey(orm['data.collection'], null=False))
        ))
        db.create_unique('data_collection_children', ['from_collection_id', 'to_collection_id'])

        # Adding model 'CollectionItem'
        db.create_table('data_collectionitem', (
            ('record', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Record'])),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('collection', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Collection'])),
        ))
        db.send_create_signal('data', ['CollectionItem'])

        # Adding model 'Record'
        db.create_table('data_record', (
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Record'], null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('manager', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('next_update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('data', ['Record'])

        # Adding model 'MetadataStandard'
        db.create_table('data_metadatastandard', (
            ('prefix', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('data', ['MetadataStandard'])

        # Adding model 'Vocabulary'
        db.create_table('data_vocabulary', (
            ('origin', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('standard', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('data', ['Vocabulary'])

        # Adding model 'VocabularyTerm'
        db.create_table('data_vocabularyterm', (
            ('term', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Vocabulary'])),
        ))
        db.send_create_signal('data', ['VocabularyTerm'])

        # Adding model 'Field'
        db.create_table('data_field', (
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('vocabulary', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Vocabulary'], null=True, blank=True)),
            ('standard', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.MetadataStandard'], null=True, blank=True)),
            ('old_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('data', ['Field'])

        # Adding unique constraint on 'Field', fields ['name', 'standard']
        db.create_unique('data_field', ['name', 'standard_id'])

        # Adding M2M table for field equivalent on 'Field'
        db.create_table('data_field_equivalent', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_field', models.ForeignKey(orm['data.field'], null=False)),
            ('to_field', models.ForeignKey(orm['data.field'], null=False))
        ))
        db.create_unique('data_field_equivalent', ['from_field_id', 'to_field_id'])

        # Adding model 'FieldSet'
        db.create_table('data_fieldset', (
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('standard', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('data', ['FieldSet'])

        # Adding model 'FieldSetField'
        db.create_table('data_fieldsetfield', (
            ('fieldset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.FieldSet'])),
            ('importance', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Field'])),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('data', ['FieldSetField'])

        # Adding model 'FieldValue'
        db.create_table('data_fieldvalue', (
            ('field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Field'])),
            ('group', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('refinement', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('context_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('index_value', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('date_end', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=0, blank=True)),
            ('date_start', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=0, blank=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('numeric_value', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=18, decimal_places=4, blank=True)),
            ('record', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['data.Record'])),
            ('context_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('hidden', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('data', ['FieldValue'])

        # Adding model 'DisplayFieldValue'
        db.create_table('data_displayfieldvalue', (
            ('fieldvalue_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['data.FieldValue'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('data', ['DisplayFieldValue'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Collection'
        db.delete_table('data_collection')

        # Removing M2M table for field children on 'Collection'
        db.delete_table('data_collection_children')

        # Deleting model 'CollectionItem'
        db.delete_table('data_collectionitem')

        # Deleting model 'Record'
        db.delete_table('data_record')

        # Deleting model 'MetadataStandard'
        db.delete_table('data_metadatastandard')

        # Deleting model 'Vocabulary'
        db.delete_table('data_vocabulary')

        # Deleting model 'VocabularyTerm'
        db.delete_table('data_vocabularyterm')

        # Deleting model 'Field'
        db.delete_table('data_field')

        # Removing unique constraint on 'Field', fields ['name', 'standard']
        db.delete_unique('data_field', ['name', 'standard_id'])

        # Removing M2M table for field equivalent on 'Field'
        db.delete_table('data_field_equivalent')

        # Deleting model 'FieldSet'
        db.delete_table('data_fieldset')

        # Deleting model 'FieldSetField'
        db.delete_table('data_fieldsetfield')

        # Deleting model 'FieldValue'
        db.delete_table('data_fieldvalue')

        # Deleting model 'DisplayFieldValue'
        db.delete_table('data_displayfieldvalue')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'data.collection': {
            'Meta': {'object_name': 'Collection'},
            'agreement': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['data.Collection']", 'symmetrical': 'False', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'records': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['data.Record']", 'through': "orm['data.CollectionItem']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'data.collectionitem': {
            'Meta': {'object_name': 'CollectionItem'},
            'collection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Collection']"}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'record': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Record']"})
        },
        'data.displayfieldvalue': {
            'Meta': {'object_name': 'DisplayFieldValue', '_ormbases': ['data.FieldValue']},
            'fieldvalue_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['data.FieldValue']", 'unique': 'True', 'primary_key': 'True'})
        },
        'data.field': {
            'Meta': {'unique_together': "(('name', 'standard'),)", 'object_name': 'Field'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'equivalent': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'equivalent_rel_+'", 'null': 'True', 'to': "orm['data.Field']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'old_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'standard': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.MetadataStandard']", 'null': 'True', 'blank': 'True'}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Vocabulary']", 'null': 'True', 'blank': 'True'})
        },
        'data.fieldset': {
            'Meta': {'object_name': 'FieldSet'},
            'fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['data.Field']", 'through': "orm['data.FieldSetField']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'standard': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'data.fieldsetfield': {
            'Meta': {'object_name': 'FieldSetField'},
            'field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Field']"}),
            'fieldset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.FieldSet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'importance': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'data.fieldvalue': {
            'Meta': {'object_name': 'FieldValue'},
            'context_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'context_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'date_end': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '0', 'blank': 'True'}),
            'date_start': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '0', 'blank': 'True'}),
            'field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Field']"}),
            'group': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index_value': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'numeric_value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '18', 'decimal_places': '4', 'blank': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'record': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Record']"}),
            'refinement': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'data.metadatastandard': {
            'Meta': {'object_name': 'MetadataStandard'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'prefix': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'data.record': {
            'Meta': {'object_name': 'Record'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manager': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'next_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Record']", 'null': 'True', 'blank': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'})
        },
        'data.vocabulary': {
            'Meta': {'object_name': 'Vocabulary'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'origin': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'standard': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'data.vocabularyterm': {
            'Meta': {'object_name': 'VocabularyTerm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'term': ('django.db.models.fields.TextField', [], {}),
            'vocabulary': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['data.Vocabulary']"})
        }
    }
    
    complete_apps = ['data']
