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

    var imageViewNavigate = function (imageView, jump) {
        var target = imageView.currentImgIndex + jump;
        target = Math.min(imageView.imagesList.length - 1, Math.max(0, target));
        if (target !== imageView.currentImgIndex) {
            imageView.eventEmitter.publish(
                'SET_CURRENT_CANVAS_ID.' + imageView.windowId,
                imageView.imagesList[target]['@id']
            );
        }
    };


    var countUsedCanvases = function () {
        return viewer.mirador.viewer.workspace.slots.map(function (slot) {
            return slot.window ? 1 : null;
        }).length;
    };

    var keydown = function (event) {
        var distance = countUsedCanvases();
        if (event.key === 'ArrowLeft') {
            forEachWindowAndImageViewer(function (imageView) {
                imageViewNavigate(imageView, -distance);
            });
        }
        if (event.key === 'ArrowRight') {
            forEachWindowAndImageViewer(function (imageView) {
                imageViewNavigate(imageView, distance);
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

    var getUsedCanvases = function () {
        return viewer.mirador.viewer.workspace.slots.map(function (slot) {
            return slot.window ? slot.window.canvasID : null;
        });
    };

    var getManifest = function () {
        var manifests =
            viewer.mirador.viewer.state.getStateProperty('manifests');
        for (var manifest in manifests) {
            if (!manifests.hasOwnProperty(manifest)) {
                continue;
            }
            return manifests[manifest];
        }
    };

    var getNextCanvases = function () {
        var manifest = getManifest();
        var canvases = manifest.jsonLd.sequences[0].canvases;
        var used = getUsedCanvases();
        var next = [];
        var canvasId;
        canvases.forEach(function (canvas) {
            canvasId = canvas['@id'];
            if (used.indexOf(canvasId) > -1) {
                next = [];
            } else {
                next.push(canvasId);
            }
        });
        // if no further slides found, return last one
        if (!next.length && canvasId) {
            next.push(canvasId);
        }
        return next;
    };

    var fillEmptySlots = function () {
        var next = getNextCanvases();
        var manifest = getManifest();
        viewer.mirador.viewer.workspace.slots.forEach(function (slot) {
            if (!slot.window) {
                var windowConfig = {
                    manifest: manifest,
                    canvasID: next.length === 1 ? next[0] : next.shift(),
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
