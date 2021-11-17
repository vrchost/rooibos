{% load ui %}
{% load static %}

(function() {
{% include "viewers_loadscripts.js" %}


var e = document.getElementById("{{ anchor_id }}");
e.innerHTML = '<iframe id="ytplayer" type="text/html" width="640" height="360" src="{{ embed_url }}" frameborder="0" allowFullScreen></iframe>';

})();
