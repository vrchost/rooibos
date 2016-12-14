{% load ui %}
{% load staticfiles %}

(function() {
{% include "viewers_loadscripts.js" %}
var clip;
{% if streaming_server and streaming_media %}
clip = {
{% if flowplayer_key %}
    key: '{{ flowplayer_key }}',
{% endif %}
    clip: {
        autoPlay: {{ autoplay|yesno:"true,false" }},
        url: '{{ streaming_media|escapejs }}',
{% if idevice_streaming_url %}
        ipadUrl: '{{ idevice_streaming_url }}',
{% endif %}
        provider: 'influxis',
        scaling: 'fit'
    },
    plugins: {
        influxis: {
            url: "{{ server_url }}{% static 'flowplayer/flowplayer.rtmp-3.2.3.swf' %}",
            netConnectionUrl: '{{ streaming_server|escapejs }}'
            {% if audio %} ,
            durationFunc: 'getStreamLength'
            {% endif %}
        }
        {% if audio %} ,
        controls: {
            fullscreen: false,
            height: 30,
            autoHide: false
        }
        {% endif %}
    }
};
{% else %}
clip = {
{% if flowplayer_key %}
    key: '{{ flowplayer_key }}',
{% endif %}
    clip: {
        autoPlay: {{ autoplay|yesno:"true,false" }},
        url: '{{ delivery_url|escapejs }}'
        {% if audio %} ,
        type: 'audio'
        {% else %} ,
        scaling: 'fit'
        {% endif %}
    }
    {% if audio %} ,
    plugins: {
        audio: {
            url: "{{ server_url }}{% static 'flowplayer/flowplayer.audio-3.2.1.swf' %}"
        },
        controls: {
            fullscreen: false,
            height: 30,
            autoHide: false
        }
    }
    {% endif %}
};
{% endif %}

function insert_flowplayer() {
    var e = document.getElementById("{{ anchor_id }}");
    e.style.width = "{{ selectedmedia.width|default:"520" }}px";
    e.style.height = "{% if audio %}30{% else %}{{ selectedmedia.height|default:"330" }}{% endif %}px";
    $f("{{ anchor_id }}",
        "{{ server_url }}{% if flowplayer_key %}{% static 'flowplayer/flowplayer.commercial-3.2.5.swf' %}{% else %}{% static 'flowplayer/flowplayer-3.2.5.swf' %}{% endif %}", clip).ipad();
}

if (typeof(flowplayer) == "function") {
    insert_flowplayer();
} else {
    load_scripts([
        "{{ server_url }}{% static 'flowplayer/flowplayer-3.2.4.modified.js' %}",
        "{{ server_url }}{% static 'flowplayer/flowplayer.ipad-3.2.1.min.js' %}"
        ], insert_flowplayer);
}
})();
