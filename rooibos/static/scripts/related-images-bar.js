var relatedImagesEnabled = false;

function showRelatedImages(querystring, element) {
    if (relatedImagesEnabled) {
        ajaxManager.add({
            type: 'GET',
            url: '/explore/api/search/?' + querystring + "&s=random_" + (new Date().getTime()) + "+asc&ps=" + Math.floor($("#related-images-bar").width() / 170),
            dataType: 'json',
            success: function(r) {
                    $("#related-images-bar-content").html(r.html);
                    $("#related-images-bar-all").empty().append(
                        $("<a>Explore these records</a>").attr("href", "/explore/search/?" + querystring));                    
                    bindSelectRecordCheckboxes();
                    if ($("#related-images-bar").height() < 100)
                    {
                        if (element) {
                            var p = $("#related-images-bar").position().top - $(element).position().top - 166;
                            if (p < 20) $("html,body").animate({scrollTop: "+=" + (-p + 20)}, 500);
                        }
                        toggleRelatedImages();
                    }
                }
        });
    }
}

function clearRelatedImages() {
    if (relatedImagesEnabled) {
        $("#related-images-bar-content").empty();
    }
}

function toggleRelatedImages() {
    var h = $("#related-images-bar").height();
    $("#related-images-bar, #related-images-bar-placeholder").animate({height: 202 - h}, 500);
    $("#related-images-bar-hide").html(h < 100 ? "Hide" : "Show");
}

function enableRelatedImages(hint) {    
    var adjust = function() { $("#related-images-bar").width($(window).width()); };
    $(window).resize(adjust);
    $(window).scroll(adjust);
    adjust();
    $("#related-images-bar-hint").html(hint);
    $("#related-images-bar-toggle").click(toggleRelatedImages);
    $("#related-images-bar").show()
    $("#related-images-bar-placeholder").height($("#related-images-bar").height());
    relatedImagesEnabled = true;
    var t;
    $("a.related-images").hover(
        function() {
            var e = this;
            var q = e.href.substring(this.href.indexOf('?') + 1);
            t = setTimeout(function() { showRelatedImages(q, e) }, 1000); },
       function() { clearTimeout(t); });
}
