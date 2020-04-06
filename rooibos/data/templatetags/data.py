from django import template
from django.template import Variable
from rooibos.data.forms import get_collection_visibility_prefs_form
from rooibos.data.functions import get_collection_visibility_preferences, \
    get_fields_for_set
from rooibos.access.functions import filter_by_access
from rooibos.util.markdown import markdown


register = template.Library()


class MetaDataNode(template.Node):

    def __init__(self, record, fieldset, crosslinks):
        self.record = Variable(record)
        self.fieldset = Variable(fieldset) if fieldset else None
        self.crosslinks = Variable(crosslinks) if crosslinks else None

    def render(self, context):
        record = self.record.resolve(context)
        fieldset = self.fieldset.resolve(context) if self.fieldset else None
        fieldvalues = list(
            record.get_fieldvalues(
                owner=context['request'].user,
                fieldset=fieldset
            )
        )

        crosslinks = self.crosslinks and self.crosslinks.resolve(context)

        if crosslinks:
            crosslink_fields = get_fields_for_set('crosslinks')
        else:
            crosslink_fields = dict()

        markdown_fields = get_fields_for_set('markdown')

        for i in range(0, len(fieldvalues)):
            if not fieldvalues[i].value:
                continue
            field_id = fieldvalues[i].field_id
            if crosslinks:
                fieldvalues[i].crosslinked = field_id in crosslink_fields
            if field_id in markdown_fields:
                fieldvalues[i].markdown_html = markdown(fieldvalues[i].value)

        collections = filter_by_access(
            context['request'].user, record.collection_set.all())

        context.update(dict(
            values=fieldvalues,
            record=record,
            collections=collections,
        ))

        t = context.template.engine.get_template('data_metadata.html')
        return t.render(context)


@register.tag
def metadata(parser, token):
    args = (token.split_contents() + [None, None])[1:4]
    record, fieldset, crosslinks = args
    return MetaDataNode(record, fieldset, crosslinks)


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
