from django.contrib import admin
from models import Storage, Media, ProxyUrl, TrustedSubnet

class StorageAdmin(admin.ModelAdmin):
    pass

class MediaAdmin(admin.ModelAdmin):
    pass

class ProxyUrlAdmin(admin.ModelAdmin):
    pass

class TrustedSubnetAdmin(admin.ModelAdmin):
    pass


admin.site.register(Storage, StorageAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(ProxyUrl, ProxyUrlAdmin)
admin.site.register(TrustedSubnet, TrustedSubnetAdmin)