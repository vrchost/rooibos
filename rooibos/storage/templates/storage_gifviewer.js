{% load ui %}
{% load static %}

(function() {
{% include "viewers_loadscripts.js" %}


var e = document.getElementById("{{ anchor_id }}");
e.style.maxWidth = "{{ selectedmedia.width|default:"520" }}px";
e.style.maxHeight = "{{ selectedmedia.height|default:"330" }}px";
e.innerHTML = '<img src="{{ server_url }}{{ selectedmedia.get_absolute_url }}" />';

})();
