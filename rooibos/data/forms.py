from django import forms
from .models import FieldSet, Collection
from rooibos.access.functions import filter_by_access


class FieldSetChoiceField(forms.ChoiceField):

    def __init__(self, *args, **kwargs):
        self._for_user = kwargs.pop('user', None)
        if self._for_user and not self._for_user.is_authenticated():
            self._for_user = None
        kwargs['choices'] = [
            (
                '0',
                kwargs.pop('default_label', None) or '-' * 10
            ),
            (
                'Default field sets',
                list(
                    FieldSet.for_user(self._for_user)
                    .filter(owner=None).values_list('id', 'title')
                )
            )
        ]
        if self._for_user:
            user_fieldsets = list(
                FieldSet
                .for_user(self._for_user)
                .filter(owner=self._for_user)
                .values_list('id', 'title')
            )
            if user_fieldsets:
                kwargs['choices'].insert(
                    1, ('Your field sets', user_fieldsets))
        super(FieldSetChoiceField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(FieldSetChoiceField, self).clean(value)
        return None if not value or value == '0' else int(value)


def get_collection_visibility_prefs_form(user):

    collection_choices = (
        (c.id, c.title)
        for c in filter_by_access(user, Collection)
    )

    class CollectionVisibilityPreferencesForm(forms.Form):
        show_or_hide = forms.ChoiceField(
            widget=forms.RadioSelect,
            label='When searching and browsing,',
            initial='show',
            choices=(
                (
                    'show',
                    'Show all collections except the ones selected below'
                ),
                (
                    'hide',
                    'Hide all collections except the ones selected below'
                ),
            ),
        )
        collections = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            choices=collection_choices,
            required=False,
        )

    return CollectionVisibilityPreferencesForm
