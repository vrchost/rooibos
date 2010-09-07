from django import forms
from models import FieldSet

    
class FieldSetChoiceField(forms.ChoiceField):
    
    def __init__(self, *args, **kwargs):
        self._for_user = kwargs.pop('user', None)
        kwargs['choices'] = [
                ('0', kwargs.pop('default_label', None) or '-' * 10),
                ('Default field sets', list(FieldSet.for_user(self._for_user).filter(owner=None).values_list('id', 'title')))
            ]
        if self._for_user:
            user_fieldsets = list(FieldSet.for_user(self._for_user).filter(owner=self._for_user).values_list('id', 'title'))
            if user_fieldsets:
                kwargs['choices'].insert(1, ('Your field sets', user_fieldsets))
        super(FieldSetChoiceField, self).__init__(*args, **kwargs)
    
    def clean(self, value):
        value = super(FieldSetChoiceField, self).clean(value)
        return None if not value or value == '0' else FieldSet.for_user(self._for_user).get(id=value)
