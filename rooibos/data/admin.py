from django.contrib import admin
from .models import MetadataStandard, Field, FieldSet, FieldSetField, \
    Record, FieldValue, Collection, Vocabulary, VocabularyTerm, \
    RemoteMetadata


class MetadataStandardAdmin(admin.ModelAdmin):
    list_display = ('title', 'name', 'prefix')


class FieldAdmin(admin.ModelAdmin):
    list_display = ('label', 'full_name', 'standard', 'eq_fields')
    list_filter = ('standard', )
    search_fields = ['name', ]
    ordering = ('standard',)
    filter_horizontal = ("equivalent",)

    def eq_fields(self, obj):
        return ", ".join([f.full_name for f in obj.get_equivalent_fields()])


class FieldSetFieldInline(admin.TabularInline):
    model = FieldSetField


class FieldSetAdmin(admin.ModelAdmin):
    list_display = ('title', 'name', 'fields_count', 'standard', )
    inlines = [FieldSetFieldInline, ]
    raw_id_fields = ('owner', )

    def fields_count(self, obj):
        return obj.fields.count()


class FieldValueInline(admin.TabularInline):
    model = FieldValue
    raw_id_fields = ['owner', 'context_type', ]


class RecordAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'title', 'owner', 'get_image_url', 'get_absolute_url',
        'shared',
    )
    inlines = [FieldValueInline, ]
    raw_id_fields = ('owner', )


class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'name', 'records_in_collection', 'owner', 'hidden',
    )
    raw_id_fields = ('owner', )

    def records_in_collection(self, obj):
        return obj.records.count()


class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('title', 'name', 'origin', 'standard', )


class VocabularyTermAdmin(admin.ModelAdmin):
    list_display = ('term', 'vocabulary', )
    list_display_links = ('vocabulary', )


class RemoteMetadataAdmin(admin.ModelAdmin):
    list_display = ('collection', 'storage', 'url', 'last_modified', )


admin.site.register(Collection, CollectionAdmin)
admin.site.register(MetadataStandard, MetadataStandardAdmin)
admin.site.register(Field, FieldAdmin)
admin.site.register(FieldSet, FieldSetAdmin)
admin.site.register(Record, RecordAdmin)
admin.site.register(Vocabulary, VocabularyAdmin)
admin.site.register(VocabularyTerm, VocabularyTermAdmin)
admin.site.register(RemoteMetadata, RemoteMetadataAdmin)
