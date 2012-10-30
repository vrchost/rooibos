# This is old code without access controls

#from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
#from rooibos.data.models import Collection, Record
#from rooibos.util import get_full_url
#
#class GroupFeed(Feed):
#
#    def get_object(self, bits):
#        if len(bits) != 1:
#            raise ObjectDoesNotExist
#        return Collection.objects.get(name=bits[0])
#
#    def title(self, collection):
#        return collection.title
#
#    def link(self, collection):
#        if not collection:
#            raise FeedDoesNotExist
#        return collection.get_absolute_url()
#
#    def description(self, collection):
#        return collection.description
#
#    def items(self, collection):
#        return Record.objects.filter(collection=collection).order_by('groupmembership__order')
#
#    def item_enclosure_url(self, record):
#        return record.get_thumbnail_url()
#
#    def item_enclosure_mime_type(self, record):
#        return 'image/jpeg'
#
#    def item_enclosure_length(self, record):
#        return 0
#
