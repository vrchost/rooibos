{% load ui %}
{% load static %}

(function() {
{% include "viewers_loadscripts.js" %}

function insert_player() {
    var e = document.getElementById("{{ anchor_id }}");
    e.style.width = '{{ selectedmedia.width|default:"520" }}px';
    e.style.height = '{% if audio %}30{% else %}{{ selectedmedia.height|default:"330" }}{% endif %}px';
    e.innerHTML = '<video id="{{ anchor_id }}-video" controls ' +
{% if autoplay %}
        'autoplay ' +
{% endif %}
        'class="video-js" ' +
        'style="width: {{ selectedmedia.width|default:"520" }}px; height: {% if audio %}30{% else %}{{ selectedmedia.height|default:"330" }}{% endif %}px;"' +
        'width="{{ selectedmedia.width|default:"520" }}" ' +
        'height="{% if audio %}30{% else %}{{ selectedmedia.height|default:"330" }}{% endif %}">' +
{% if streaming_server and streaming_media %}
        '<source src="{{ streaming_media }}" type="{{ selectedmedia.mimetype }}">' +
{% else %}
        '<source src="{{ delivery_url }}" type="{{ selectedmedia.mimetype }}">' +
{% endif %}
        '</video>';
    videojs("{{ anchor_id }}");
}

if (typeof(videojs) == "function") {
    insert_player();
} else {

    var stylesheet = document.createElement("link");
    stylesheet.type = "text/css";
    stylesheet.rel = "stylesheet";
    stylesheet.href = "{{ server_url }}{% static 'video-js-6.5.1/video-js.css' %}";
    document.getElementsByTagName("head")[0].appendChild(stylesheet);

    load_scripts([
        "{{ server_url }}{% static 'video-js-6.5.1/video.js' %}"
        ], insert_player);
}
})();
