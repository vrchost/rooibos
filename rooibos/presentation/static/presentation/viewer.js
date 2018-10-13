var Viewer = function (options) {

    var mirador = Mirador(options);
    var viewer = this;

    if (window.opener && window.opener.viewer) {
        this.windows = window.opener.viewer.windows;
    } else {
        this.windows = [window];
    }

    this.additionalWindow = function () {
        viewer.windows.push(
            window.open(window.location.href)
        );
    };

    var forEachWindow = function (callback) {
        viewer.windows.forEach(function (w) {
            if (!w.closed) {
                callback(w);
            }
        });
    };

    this.forEachImageViewer = function (callback) {
        var slots = mirador.viewer.workspace.slots;
        slots.forEach(function (slot) {
            var imageView = slot.window && slot.window.focusModules.ImageView;
            if (imageView) {
                callback(imageView);
            }
        });
    };

    var forEachWindowAndImageViewer = function (callback) {
        forEachWindow(function (w) {
            w.viewer.forEachImageViewer(function (imageViewer) {
                callback(imageViewer);
            });
        });
    };


    var keydown = function (event) {

        if (event.key === 'ArrowLeft') {
            forEachWindowAndImageViewer(function (imageView) {
                imageView.previous();
            });
        }

        if (event.key === 'ArrowRight') {
            forEachWindowAndImageViewer(function (imageView) {
                imageView.next();
            });
        }

        event.stopPropagation();
    };

    var keyup = function (event) { };

    var stopPropagationWrapper = function (eventHandler) {
        return function (event) {
            eventHandler(event);
            event.stopPropagation();
        };
    };

    document.addEventListener('keydown', stopPropagationWrapper(keydown), true);
    document.addEventListener('keyup', stopPropagationWrapper(keyup), true);

    return this;
};
