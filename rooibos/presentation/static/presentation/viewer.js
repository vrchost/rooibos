/* global Mirador, jQuery */

var Viewer = function (options) {

    "use strict";
    var OpenSeadragon = Mirador.OpenSeadragon;
    Mirador.OpenSeadragon = function (options) {
        var osd = OpenSeadragon(jQuery.extend({}, options, {
            minZoomImageRatio: 0.1,
            maxZoomPixelRatio: 3.0,
            visibilityRatio: 0.2
        }));

        var goHome = osd.viewport.__proto__.goHome;
        osd.viewport.__proto__.goHome = function (immediate) {
            var world = this.viewer.world;
            var active = world._items.filter(function (item) { return item.opacity; });
            if (active.length) {
                var img = active[0];
                var rect = img.imageToViewportRectangle(0, 0, img.source.width, img.source.height);
                img.viewport.fitBounds(rect, immediate);
            } else {
                goHome.apply(this, arguments);
            }
        };

        return osd;
    };


    this.mirador = Mirador(options);
    var viewer = this;

    if (window.opener && window.opener.viewer &&
            window.opener.viewer.windows !== undefined) {
        this.windows = window.opener.viewer.windows;
        this.synced = window.opener.viewer.synced;
        this.active = window.opener.viewer.active;
    } else {
        this.windows = [window];
        this.synced = false;
        this.active = {
            window: 0,
            slot: 0
        };
    }

    this.toggleAnnotationFontSize = function () {
        forEachWindow(function (w) {
            w.viewer.mirador.viewer.element.toggleClass(
                'annotation-large-font');
        });
    };

    this.toggleViewerTitle = function () {
        forEachWindow(function (w) {
            w.viewer.mirador.viewer.element.toggleClass(
                'viewer-title');
        });
    };

    this.additionalWindow = function () {
        var next = getNextCanvases()[0];
        var url = window.location.href;
        if (url.indexOf('canvas=') === -1) {
            url += (url.indexOf('?') === -1 ? '?' : '&') + 'canvas=' + next;
        } else {
            url = url.replace(/canvas=[^&]+/, 'canvas=' + next);
        }
        viewer.windows.push(
            window.open(url, '_blank', 'height=600,width=800')
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
        jQuery('body').toggleClass('mdid-synced', synced);
    };

    var forEachWindow = function (callback) {
        viewer.windows.forEach(function (window, windowIndex) {
            if (!window.closed) {
                callback(window, windowIndex);
            }
        });
    };

    this.forEachImageView = function (callback) {
        var slots = viewer.mirador.viewer.workspace.slots;
        slots.forEach(function (slot, slotIndex) {
            var imageView = slot.window && slot.window.focusModules.ImageView;
            if (imageView) {
                callback(imageView, slotIndex);
            }
        });
    };

    var forEachWindowAndImageViewer = function (callback) {
        forEachWindow(function (w, windowIndex) {
            w.viewer.forEachImageView(function (imageView, slotIndex) {
                callback(imageView, windowIndex, slotIndex);
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
        var count = 0;
        forEachWindowAndImageViewer(function () {
            count++;
        });
        return count;
    };

    var whenActive = function (callback) {
        return function () {
            var imageView = arguments[0];
            if (viewer.synced ||
                    jQuery(imageView.element).parents('.mdid-active').length) {
                callback.apply(this, arguments);
            }
        };
    };

    var emitEvent = function (event, options) {
        var _emitEvent = function (window) {
            if (!window.closed) {
                window.viewer.mirador.eventEmitter.publish(event, options);
            }
        };
        if (viewer.synced) {
            forEachWindow(_emitEvent);
        } else {
            _emitEvent(viewer.windows[viewer.active.window]);
        }
    };

    var metaKey;

    var keydown = function (event) {
        metaKey = event.metaKey;
        var distance = viewer.synced ? countUsedCanvases() : 1;
        if (event.key === 'ArrowLeft') {
            forEachWindowAndImageViewer(whenActive(function (imageView) {
                imageViewNavigate(imageView, -distance);
            }));
        } else
        if (event.key === 'ArrowRight') {
            forEachWindowAndImageViewer(whenActive(function (imageView) {
                imageViewNavigate(imageView, distance);
            }));
        } else
        if (event.key === ' ') {
            viewer.markAsActive(event.shiftKey ? -1 : 1);
        } else
        if (event.key === 's') {
            viewer.syncViewers();
        } else
        if (event.key === 'r') {
            forEachWindowAndImageViewer(whenActive(function (imageView) {
                imageView.osd.viewport.goHome();
            }));
        } else
        if (event.key === 'h') {
            forEachWindowAndImageViewer(whenActive(function (imageView) {
                jQuery(imageView.element).toggleClass('mdid-hide-image')
            }));
        } else
        if (event.key === 'i') {
            forEachWindowAndImageViewer(whenActive(function (imageView) {
                jQuery(imageView.element)
                    .find('.mirador-canvas-metadata-toggle').click();
            }));
        } else
        if (event.key === 't') {
            viewer.toggleViewerTitle();
        } else
        if (event.key === 'ArrowUp') {
            forEachWindowAndImageViewer(whenActive(function (imageView) {
                jQuery(imageView.element)
                    .find('.mirador-osd-zoom-in').click();
            }));
        } else
        if (event.key === 'ArrowDown') {
            forEachWindowAndImageViewer(whenActive(function (imageView) {
                jQuery(imageView.element)
                    .find('.mirador-osd-zoom-out').click();
            }));
        } else
        if (event.key === 'u') {
            emitEvent('RESET_WORKSPACE_LAYOUT', {
                layoutDescription:
                    Mirador.layoutDescriptionFromGridString('1x1')
            });
            delay(viewer.markAsActive.bind(viewer));
        } else
        if (event.key === 'y') {
            emitEvent('RESET_WORKSPACE_LAYOUT', {
                layoutDescription:
                    Mirador.layoutDescriptionFromGridString('1x2')
            });
            delay(viewer.markAsActive.bind(viewer));
        } else
        if (event.key === 'x') {
            emitEvent('RESET_WORKSPACE_LAYOUT', {
                layoutDescription:
                    Mirador.layoutDescriptionFromGridString('2x1')
            });
            delay(viewer.markAsActive.bind(viewer));
        } else
        if (event.key === 'f') {
            emitEvent('TOGGLE_FULLSCREEN');
        }
    };

    var keyup = function (event) {
        metaKey = event.metaKey;
    };

    var eventWrapper = function (eventHandler, onlyWhenSynced) {
        return function (event) {
            if (!onlyWhenSynced || viewer.synced) {
                eventHandler(event);
            }
            event.stopPropagation();
        };
    };

    var mouseMove = function () {
        var mouseMoveTimeout;
        var mouseMoveHudHidden = false;
        var mouseMove = function () {
            clearTimeout(mouseMoveTimeout);
            mouseMoveTimeout = setTimeout(function () {
                jQuery('.mirador-hud,.mirador-main-menu')
                    .addClass('mdid-hud-hidden');
                mouseMoveHudHidden = true;
            }, 2000);
            if (mouseMoveHudHidden) {
                jQuery('.mirador-hud,.mirador-main-menu')
                    .removeClass('mdid-hud-hidden');
                mouseMoveHudHidden = false;
            }
        };
        mouseMove();
        return mouseMove;
    }();

    document.addEventListener('keydown', eventWrapper(keydown), true);
    document.addEventListener('keyup', keyup, true);
    document.addEventListener('mousemove', mouseMove);


    var delay = setTimeout;


    var getUsedCanvases = function () {
        return viewer.mirador.viewer.workspace.slots.map(function (slot) {
            return slot.window ? slot.window.canvasID : null;
        });
    };


    var _manifest;

    var getManifest = function () {
        if (_manifest) {
            return _manifest;
        }
        var manifests =
            viewer.mirador.viewer.state.getStateProperty('manifests');
        for (var manifest in manifests) {
            if (!manifests.hasOwnProperty(manifest)) {
                continue;
            }
            _manifest = manifests[manifest];
            return _manifest;
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
        var manifest = getManifest();
        var next = getNextCanvases();
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


    this.markAsActive = function (jump) {
        jump = jump || 0;
        var positions = [];
        var activePosition = 0;
        var active = this.active;
        forEachWindowAndImageViewer(function (imageView, windowIndex, slotIndex) {
            var element = jQuery(imageView.element)
                .parents('.slot')
                .removeClass('mdid-active')
                .removeClass('mdid-active-frame');
            positions.push({
                window: windowIndex,
                slot: slotIndex,
                element: element
            });
            if (active.window === windowIndex && active.slot === slotIndex) {
                activePosition = positions.length - 1;
            }
        });
        var count = positions.length;
        if (!count) {
            return;
        }
        activePosition = (activePosition + jump + count) % count;
        if (count > 1) {
            positions[activePosition].element.addClass('mdid-active-frame');
        }
        positions[activePosition].element.addClass('mdid-active');
        active.window = positions[activePosition].window;
        active.slot = positions[activePosition].slot;
    };

    var countSlots = function (layout) {
        return layout.children ? layout.children.map(countSlots).reduce(
            function (a, b) { return a + b; }, 0) : 1;
    };

    var showAddItemButton = function () {
        viewer.mirador.viewer.workspace.slots.forEach(function (slot) {
            if (!slot.window) {
                slot.element.find('.slotIconContainer').show();
            }
        });
    };

    this.mirador.eventEmitter.subscribe('RESET_WORKSPACE_LAYOUT',
        function () {
            if (!metaKey) {
                var newCount = countSlots(arguments[1].layoutDescription);
                var oldCount = countSlots(viewer.mirador.viewer.workspace.layoutDescription);
                if (newCount > oldCount) {
                    delay(fillEmptySlots);
                }
            } else {
                delay(showAddItemButton);
            }
        }
    );


    this.mirador.eventEmitter.subscribe('ADD_WINDOW', function () {
        delay(viewer.markAsActive.bind(viewer));
    });


    this.mirador.eventEmitter.subscribe('windowSlotAdded', function (e, w) {
        // this event is triggered on window initialization, so we use it
        // to hook up the navigation event
        viewer.mirador.eventEmitter.subscribe(
            'DESTROY_EVENTS.' + w.id,
            function () {
                var f = function () { updateSlots(e, w); };
                delay(f);
                viewer.mirador.eventEmitter.subscribe(
                    'currentCanvasIDUpdated.' + w.id, f
                );
            }
        );
    });


    this.mirador.eventEmitter.subscribe('TOGGLE_FULLSCREEN', function () {
        // Mirador hides bottom panel control in fullscreen, keep it visible
        delay(function () {
            viewer.forEachImageView(function (imageView) {
                imageView.element.find(
                    '.mirador-osd-toggle-bottom-panel').show();
            });
        }, 500);
    });


    var getImageViewById = function (id) {
        var result;
        forEachWindowAndImageViewer(function (imageView) {
            if (imageView.windowId === id) {
                result = imageView;
            }
        });
        return result;
    };


    this.mirador.eventEmitter.subscribe('ANNOTATIONS_LIST_UPDATED', function (event, data) {
        if (data && data.annotationsList && data.annotationsList.length &&
                data.annotationsList[0]) {
            var res = data.annotationsList[0].resource;
            var url = res.format === 'text/html' ? res['@id'] : undefined;
            var request = jQuery.ajax({
                url: url,
                dataType: 'html',
                async: true
            });
            request.done(function (html) {
                var imageView = getImageViewById(data.windowId);

                var embeddedViewer = function () {
                    imageView.elemAnno
                        .addClass('active')
                        .html('<div class="embedded-viewer">' + html + '</div>')
                        .on('click', function () {
                            imageView.elemAnno
                                .removeClass('active').off('click').html('');
                        });
                };

                if (imageView) {
                    var button = jQuery('<a class="hud-control embedded-viewer-button" role="button" aria-label="Show additional media"><i class="material-icons">image</i></a>');
                    button.on('click', embeddedViewer);
                    imageView.hud.element
                        .find('.mirador-canvas-metadata-controls')
                        .append(button);
                }
            });
        }
    });

    var updateSlots = function (event, data) {
        updateTitles();
        updateEmbeddedViewers(data);
    };


    var updateEmbeddedViewers = function (data) {
        var imageView = getImageViewById(data.id);
        if (imageView) {
            imageView.elemAnno
                .off('click').removeClass('active').html('');
            imageView.hud.element
                .find('.mirador-canvas-metadata-controls .embedded-viewer-button')
                .remove();
        }
    };


    var updateTitles = function () {
        var manifest = getManifest();
        var canvases = manifest.jsonLd.sequences[0].canvases;

        forEachWindowAndImageViewer(function (imageView) {
            var canvasID = imageView.canvasID;
            canvases.forEach(function (canvas) {
                if (canvas['@id'] === canvasID) {
                    imageView.element
                        .parents('.window')
                        .find('.window-manifest-title')
                        .text(canvas.label);

                    var metadata = imageView.element
                        .find('.mirador-canvas-metadata');
                    if (!metadata.draggable('instance')) {
                        metadata.append('<div class="metadata-drag-handle"><i class="fa fa-arrows-v"></i></div>');
                        metadata.draggable({
                            axis: 'y',
                            handle: '.metadata-drag-handle',
                            drag: function (event, ui) {
                                var minTop =
                                    metadata.offsetParent().height() / 4;
                                var maxTop = minTop * 4 * 95 / 100;
                                ui.position.top = Math.max(
                                    minTop, ui.position.top);
                                ui.position.top = Math.min(
                                    maxTop, ui.position.top);
                            }
                        });
                    }
                }
            });
        });
    };


    this.mirador.eventEmitter.subscribe(
        'manifestReceived', function (event, manifest) {
            // if sequence items don't have metadata, copy manifest metadata
            // into each sequence item
            var metadata = manifest.jsonLd.metadata;
            manifest.jsonLd.sequences.forEach(function (sequence) {
                sequence.canvases.forEach(function (canvas) {
                    if (!canvas.metadata || !canvas.metadata.length) {
                        canvas.metadata = metadata;
                    }
                });
            });
        }
    );

    return this;
};
