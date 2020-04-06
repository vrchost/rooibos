from django.contrib import admin
from .models import Storage, Media, ProxyUrl, TrustedSubnet


class StorageAdmin(admin.ModelAdmin):
    # hide the derivative fields since it can cause data loss
    # see storage.models.Storage.derivative
    list_display = ('name', 'base', 'urlbase', 'deliverybase')
    fields = ('title', 'name', 'base', 'urlbase', 'deliverybase')
    readonly_fields = ['name']


class MediaAdmin(admin.ModelAdmin):
    list_display = ('name', 'record', 'storage', 'mimetype')
    fieldsets = (
        (None, {
            'fields': ('name', 'record')
        }),
        ('Media File info', {
            'fields': (
                'media_file_path', 'delivery_url', 'width', 'height',
                'mimetype', 'bitrate'
            )
        }),
    )
    readonly_fields = [
        'delivery_url', 'media_file_path', 'mimetype', 'width',
        'height', 'bitrate'
    ]

    def delivery_url(self, obj):
        return obj.get_delivery_url()

    def media_file_path(self, obj):
        return obj.get_absolute_file_path()


class ProxyUrlAdmin(admin.ModelAdmin):
    pass


class TrustedSubnetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Storage, StorageAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(ProxyUrl, ProxyUrlAdmin)
admin.site.register(TrustedSubnet, TrustedSubnetAdmin)
