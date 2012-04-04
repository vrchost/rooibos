from django import template
from django.template.loader import render_to_string
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable
from rooibos.data.forms import get_collection_visibility_prefs_form
from rooibos.data.functions import get_collection_visibility_preferences

register = template.Library()


class MetaDataNode(template.Node):

    def __init__(self, record, fieldset):
        self.record = Variable(record)
        self.fieldset = Variable(fieldset) if fieldset else None

    def render(self, context):
        record = self.record.resolve(context)
        fieldvalues = list(record.get_fieldvalues(owner=context['request'].user,
                                                  fieldset=self.fieldset.resolve(context) if self.fieldset else None))
        if fieldvalues:
            fieldvalues[0].subitem = False
        for i in range(1, len(fieldvalues)):
            fieldvalues[i].subitem = (fieldvalues[i].field == fieldvalues[i - 1].field and
                                      fieldvalues[i].group == fieldvalues[i - 1].group and
                                      fieldvalues[i].resolved_label == fieldvalues[i - 1].resolved_label)

        return render_to_string('data_metadata.html',
                                dict(
                                    values=fieldvalues,
                                    record=record,
                                ),
                                context_instance=context)


@register.tag
def metadata(parser, token):
    try:
        tag_name, record, fieldset = token.split_contents()
    except ValueError:
        try:
            tag_name, record = token.split_contents()
            fieldset = None
        except ValueError:
            raise template.TemplateSyntaxError, "%r tag requires exactly one or two arguments" % token.contents.split()[0]
    return MetaDataNode(record, fieldset)


@register.filter
def fieldvalue(record, field):
    if not record:
        return ''
    for v in record.get_fieldvalues(hidden=True):
        if v.field.full_name == field:
            return v.value
    return ''


@register.inclusion_tag('data_collection_visibility_preferences.html',
                        takes_context=True)
def collection_visibility_preferences(context):
    user = context.get('user')
    mode, ids = get_collection_visibility_preferences(user)
    cform = get_collection_visibility_prefs_form(user)
    form = cform(initial=dict(show_or_hide=mode, collections=ids))
    return {
        'form': form,
        'request': context['request'],
    }
