function flickrSelection(ids, checked) {
    if (!ids.length) ids = [ids];
    $.ajax({
        mode: 'queue',
        type: 'POST',
        url: '/flickr/select-flickr/',
        data: {'id': ids, 'checked': checked},
        dataType: 'json',
        success: function(r) {
                $("#selected-flickrs div[id^=selected-flickr-]").remove();
                for (i in r.flickrs) {
                    addSelectedFlickr(r.flickrs[i].id, r.flickrs[i].title);
                }
                $("#session-status").html(r.status);
            }
    })
}

function updateSelectedFlickrs() {
    flickrSelection(0, false);
}

function addSelectedFlickr(id, title) {
    var a = $("<a>").attr('href', 'javascript:flickrDeselect(\''+id+'|'+title+'\')').append('x');
    var div = $("<div>").attr('id', 'selected-flickr-' + id + '|' + title);
    $("#selected-flickrs").append(div);
    document.getElementById('selected-flickr-' + id + '|' + title).appendChild(document.createTextNode(title+" ("));
    div.append(a);
    document.getElementById('selected-flickr-' + id + '|' + title).appendChild(document.createTextNode(")"));
}

function flickrSelectAllOnPage() {
    ids = Array();
    $(".flickr-select").each(function (i) { ids[i] = this.value; }).val(ids);
    flickrSelection(ids, true);
}

function flickrDeselect(id) {
    $(".flickr-select[value='" + id + "']").removeAttr("checked");
	flickrSelection(id, false);
}

function flickrDeselectAll() {
    var ids = Array();
    $("#selected-flickrs div[id^=selected-flickr-]").each(function(i) {
        ids[i] = this.id.substring(16);
        $(".flickr-select[value='" + ids[i] + "']").removeAttr("checked");
    }).remove();
    flickrSelection(ids, false);
}

function importAll() {
    document.location = "/flickr/import-photo-list"
}

function bindSelectFlickrCheckboxes() {
    $(".flickr-select").click(function() { 
        flickrSelection($(this).attr('value'), $(this).attr('checked'));
    });
}

$(document).ready(function() {
    bindSelectFlickrCheckboxes()
    updateSelectedFlickrs()
    $("#submit_flickr_selections").replaceWith($("<input type='button' value='Select all on page'>").click(flickrSelectAllOnPage));
    $("#submit_flickr_deselections").replaceWith($("<input type='button' value='Deselect All'>").click(flickrDeselectAll));
});
