{% load ui %}
{% load static %}

(function() {
{% include "viewers_loadscripts.js" %}


var e = document.getElementById("{{ anchor_id }}");
e.innerHTML = '<iframe src="https://player.vimeo.com/video/{{ vimeo_id }}" width="640" height="360" frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>';

})();
