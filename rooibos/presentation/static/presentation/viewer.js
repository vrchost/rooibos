var Viewer = function (options) {

    this.mirador = Mirador(options);
    var viewer = this;

    if (window.opener && window.opener.viewer) {
        this.windows = window.opener.viewer.windows;
        this.synced = window.opener.viewer.synced;
    } else {
        this.windows = [window];
        this.synced = false;
    }

    this.additionalWindow = function () {
        viewer.windows.push(
            window.open(window.location.href)
        );
    };

    this.syncViewers = function () {
        var synced = !viewer.synced;
        forEachWindow(function (w) {
            w.viewer.setSynced(synced);
        });
    };

    this.setSynced = function (synced) {
        this.synced = synced;
        jQuery('#sync-viewers span')
            .toggleClass('fa-link', !synced)
            .toggleClass('fa-unlink', synced);
    };

    var forEachWindow = function (callback) {
        viewer.windows.forEach(function (w) {
            if (!w.closed) {
                callback(w);
            }
        });
    };

    this.forEachImageViewer = function (callback) {
        var slots = viewer.mirador.viewer.workspace.slots;
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
    };

    var keyup = function (event) { };

    var eventWrapper = function (eventHandler, onlyWhenSynced) {
        return function (event) {
            if (!onlyWhenSynced || viewer.synced) {
                eventHandler(event);
            }
            event.stopPropagation();
        };
    };

    document.addEventListener('keydown', eventWrapper(keydown, true), true);
    document.addEventListener('keyup', eventWrapper(keyup, true), true);


    var delayWrapper = function (callback) {
        return function () {
            setTimeout(callback);
        };
    };

    var fillEmptySlots = function () {
        viewer.mirador.viewer.workspace.slots.forEach(function (slot) {
            if (!slot.window) {

                var manifests =
                    viewer.mirador.viewer.state.getStateProperty('manifests');
                for (var manifest in manifests) { }
                manifest = manifests[manifest];
                var canvases = manifest.jsonLd.sequences[0].canvases;
                var windowConfig = {
                  manifest: manifest,
                  canvasID: canvases[1]['@id'],
                  viewType: 'ImageView'
                };
                viewer.mirador.eventEmitter.publish(
                    'ADD_WINDOW', windowConfig);
            }
        });
    };


    this.mirador.eventEmitter.subscribe(
        'RESET_WORKSPACE_LAYOUT', delayWrapper(fillEmptySlots));

    return this;
};
