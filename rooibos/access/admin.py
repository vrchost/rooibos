from django.contrib import admin
from django import forms
from django.forms.models import inlineformset_factory
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin
from .models import AccessControl, Attribute, AttributeValue, ExtendedGroup, \
    Subnet


class AccessControlAdmin(admin.ModelAdmin):
    pass


class ExtendedGroupAdmin(admin.ModelAdmin):
    pass


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue


class AttributeAdmin(admin.ModelAdmin):
    inlines = [AttributeValueInline]


class SubnetAdmin(admin.ModelAdmin):
    pass


admin.site.register(AccessControl, AccessControlAdmin)
admin.site.register(ExtendedGroup, ExtendedGroupAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Subnet, SubnetAdmin)


class UsernameField(forms.CharField):

    def prepare_value(self, value):
        try:
            return User.objects.get(id=value).username
        except:
            return super(UsernameField, self).prepare_value(value)

    def clean(self, value):
        try:
            return User.objects.get(username=value)
        except:
            raise forms.ValidationError('Invalid or non-existent username.')


class MemberReadOnlyForm(forms.ModelForm):
    class Meta:
        model = User.groups.through
        fields = ['user']

    user = UsernameField()


MemberReadOnlyFormSet = inlineformset_factory(
    Group,
    User.groups.through,
    form=MemberReadOnlyForm,
)


class MembershipInline(admin.TabularInline):
    model = User.groups.through
    form = MemberReadOnlyForm
    formset = MemberReadOnlyFormSet


class CustomGroupAdmin(GroupAdmin):
    inlines = [
        MembershipInline
    ]


admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
