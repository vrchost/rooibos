from django import template
from django.template.loader import render_to_string
from django.template import Variable
from rooibos.data.forms import get_collection_visibility_prefs_form
from rooibos.data.functions import get_collection_visibility_preferences
from rooibos.data.models import FieldSet
from rooibos.access.functions import filter_by_access


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

        crosslink_fields = dict()
        if crosslinks:
            try:
                crosslink_fields.update(
                    (field.id, None)
                    for field in
                    FieldSet.objects.get(
                        name='metadata-crosslinks'
                    ).fields.all()
                )
            except FieldSet.DoesNotExist:
                pass

        for i in range(0, len(fieldvalues)):
            fieldvalues[i].crosslinked = (
                crosslinks and
                fieldvalues[i].value and
                fieldvalues[i].field_id in crosslink_fields
            )

        collections = filter_by_access(
            context['request'].user, record.collection_set.all())

        return render_to_string('data_metadata.html',
                                dict(
                                    values=fieldvalues,
                                    record=record,
                                    collections=collections,
                                ),
                                context_instance=context)


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
