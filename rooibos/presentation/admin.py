from django.contrib import admin
from rooibos.data.models import FieldSet
from models import Presentation, PresentationItem, PresentationItemInfo


#class fieldset_inline(admin.TabularInline):
#    model = 'FieldSet'

class PresentationItem_inline(admin.StackedInline):
    model = PresentationItem
    extra = 1
    #fk_name = 'presentation'

class PresentationAdmin(admin.ModelAdmin):
    list_display = ('title', 'slides', 'owner', 'created', 'modified', 'hidden', 'hide_default_data')
    list_filter = ('hidden', 'hide_default_data')
    search_fields = ['title', 'name']
    ordering = ('created', 'modified')
    raw_id_fields = ('owner', )
    date_hierarchy = ('created')
    readonly_fields = ('name', 'created', 'modified')
    inlines = [
        PresentationItem_inline,
    ]

    def slides(self, obj):
        return obj.visible_item_count() + obj.hidden_item_count()


#class PresentationItemAdmin(admin.ModelAdmin):
#    pass


#class PresentationItemInfoAdmin(admin.ModelAdmin):
#    pass



#    def eq_fields(self, obj):
#        return ", ".join([f.full_name for f in obj.get_equivalent_fields()])
#
#
#class PresentationItemInline(admin.TabularInline):
#    model = PresentationItem


admin.site.register(Presentation, PresentationAdmin)
#admin.site.register(PresentationItem, PresentationItemAdmin)
#admin.site.register(PresentationItemInfo, PresentationItemInfoAdmin)
