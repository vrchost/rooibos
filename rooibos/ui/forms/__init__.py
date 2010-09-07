from django import forms
from rooibos.contrib.tagging.models import Tag, TaggedItem
from rooibos.contrib.tagging.forms import TagField
from rooibos.contrib.tagging.utils import parse_tag_input


class SplitTaggingWidget(forms.MultiWidget):
    """
    A Widget that displays tags as a multiple choice list and an input box
    """
    def __init__(self, attrs=None, choices=(), add_label=None, add_label_class=None):
        widgets = (forms.SelectMultiple(attrs=attrs, choices=choices), forms.TextInput(attrs=attrs))
        self.add_label = add_label
        self.add_label_class = add_label_class
        super(SplitTaggingWidget, self).__init__(widgets, attrs)

    def render(self, name, value, attrs=None):
        return super(SplitTaggingWidget, self).render(name, (value,), attrs)

    def format_output(self, rendered_widgets):
        return u'%s<label class="%s">%s</label>%s' % \
            (rendered_widgets[0], self.add_label_class, self.add_label, rendered_widgets[1])

    def decompress(self, value):
        if hasattr(value[0], '__iter__'):
            return [[isinstance(t, Tag) and t.name or t for t in value[0]], None]
        elif isinstance(value[0], (str, unicode)):
            return [parse_tag_input(value[0]), None]
        else:
            return [None, None]
    

class SplitTaggingField(forms.MultiValueField):    
    def __init__(self, choices=(), add_label='', attrs=None, *args, **kwargs):        
        self.choices = list(choices)
        fields = (
            forms.MultipleChoiceField(choices=self.choices),
            TagField(),
        )
        self.widget = SplitTaggingWidget(attrs, self.choices, add_label)
        super(SplitTaggingField, self).__init__(fields, *args, **kwargs)        

    def compress(self, data_list):
        return '"%s"' % '","'.join(data_list[0] + parse_tag_input(data_list[1]))
