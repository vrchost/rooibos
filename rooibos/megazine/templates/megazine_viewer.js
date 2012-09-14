{% load ui %}
(function() {
{% include "viewers_loadscripts.js" %}

var flashvars = {
    /* This is the ABSOLUTE base that to use for all path resolving. This has an effect on ALL paths (including GUI, sounds etc). */
    //basePath: "http://www.example.com/megazine/",

    /* Used to pass the name of the xml file to use. Path is RELATIVE to basePath, or, if not set, to the megazine.swf file. */
    xmlFile: "{{ server_url }}{% url megazine-content presentation.id %}?width={{ width }}"

    /* When set to true, log messages are printed to the JavaScript console (using the console.log() function) */
    //logToJsConsole: "true"
};
var params = {
    /* Determines whether to enable transparency (show HTML background). Not recommended (slow). Use book/background instead. */
    //wmode: "transparent",
    wmode: "opaque",
    menu: "false",
    /* Necessary for proper scaling of the content. */
    scale: "noScale",
    /* Necessary for fullscreen mode. */
    allowFullscreen: "true",
    /* Necessary for SWFAddress and other JavaScript interaction. */
    allowScriptAccess: "always",
    /* This is the background color used for the Flash element. */
    bgcolor: "#FFFFFF"
};
var attributes = {
    /* This must be the same as the ID of the HTML element that will contain the Flash element. */
    id: "{{ anchor_id }}"
};


function insert_megazine() {
    swfobject.embedSWF("{{ server_url }}{% url static 'megazine/preloader.swf' %}",
                       "{{ anchor_id }}",
                       "{{ width }}",
                       "{{ height }}",
                       "9.0.115",
                       "{{ server_url }}{% url static 'js/expressInstall.swf' %}",
                       flashvars,
                       params,
                       attributes);
}

if (typeof(MegaZine) != "undefined") {
    insert_megazine();
} else {
    load_scripts([
        "{{ server_url }}{% url static 'megazine/swfobject.js' %}",
        "{{ server_url }}{% url static 'megazine/swfaddress.js' %}",
        "{{ server_url }}{% url static 'megazine/megazine.js' %}"
        ], insert_megazine);
}
})();
