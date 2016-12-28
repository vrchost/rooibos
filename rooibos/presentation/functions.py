"""
Functions for presentation app
"""

from rooibos.access.functions import sync_access
from tagging.models import Tag
from rooibos.util.models import OwnedWrapper


def duplicate_presentation(presentation, owner=None, title_suffix=' - Copy'):
    """
    Duplicates an existing presentation, optionally into a new user's account
    """
    dup = presentation.duplicate()
    if title_suffix:
        dup.title = dup.title + title_suffix
    dup.owner = owner or presentation.owner
    dup.save()

    # Duplicate presentation items
    for item in presentation.items.all():
        dupitem = item.duplicate()
        dupitem.presentation = dup
        dupitem.save()

    # Duplicate access controls
    sync_access(presentation, dup)

    # Duplicate tags
    wrapper = OwnedWrapper.objects.get_for_object(user=presentation.owner,
                                                  object=presentation)
    tags = Tag.objects.get_for_object(wrapper).values_list('name', flat=True)
    dup_wrapper = OwnedWrapper.objects.get_for_object(user=dup.owner,
                                                      object=dup)
    Tag.objects.update_tags(dup_wrapper, '"%s"' % '","'.join(tags))

    return dup
