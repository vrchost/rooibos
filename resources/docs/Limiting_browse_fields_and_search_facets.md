Limiting browse fields and search facets
===

Browse fields
---

By default, MDID finds all fields that are used for a collection and shows them as fields available for browsing.  

To limit the available browse fields, create a fieldset called `browse-collection-1`, where `1` is the internal identifier of the collection.

To limit the available browse fields for all collections, create a fieldset called `browse-collections`.

A `manage.py` command that creates default fieldsets for all collections is available to make this process easier.

Running

    python manage.py default_browse_fieldsets
    
will create a fieldset for each collection with the fields currently used in the respective collection.  Using these fieldsets as a starting point, the browse fields can be customized by just removing the undesired fields from a fieldset.

Re-running the command will recreate any missing fieldsets, but will not change or overwrite existing fieldsets.  It is possible to reset the browse fields for a collection by removing the corresponding fieldset and re-running the command.

Search facets
---

The above command also creates a fieldset called `facet-fields` that defaults to all Dublin Core fields except `dc.identifier`.  This fieldset is used to determine which facets are shown on the **Explore** screen.  Removing a field from this fieldset will effectively hide the corresponding search facet.
