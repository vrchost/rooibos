from django.contrib import admin
from models import AccessControl, Attribute, AttributeValue, ExtendedGroup, Subnet

class AccessControlAdmin(admin.ModelAdmin):
    pass


class ExtendedGroupAdmin(admin.ModelAdmin):
    pass


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    
class AttributeAdmin(admin.ModelAdmin):
    inlines = [AttributeValueInline,]

class SubnetAdmin(admin.ModelAdmin):
    pass

admin.site.register(AccessControl, AccessControlAdmin)
admin.site.register(ExtendedGroup, ExtendedGroupAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Subnet, SubnetAdmin)
