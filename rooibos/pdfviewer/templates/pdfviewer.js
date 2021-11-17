{% load ui %}
{% load static %}

(function() {
{% include "viewers_loadscripts.js" %}



function insert_pdfviewer() {
    var myPDF = new PDFObject({
        url: "{{ server_url }}{{ media_url }}"
    });
    myPDF.embed("{{ anchor_id }}");
}

if (typeof(PDFObject) != "undefined") {
    insert_pdfviewer();
} else {
    load_scripts([
        "{{ server_url }}{% static 'pdf/pdfobject.js' %}",
        ], insert_pdfviewer);
}
})();
