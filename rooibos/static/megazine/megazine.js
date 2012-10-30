/*
 * Copyright (C) 2007-2010 Florian Nuecke
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/**
 * Interface for calling functions in the MegaZine engine.
 * For more info see API of the respective plugins.
 *
 * Usage: onxxx="javascript:MegaZine.yyy(zzz);"
 * where xxx is the event type, yyy is the function to call, and zzz are
 * possible parameters.
 * 
 * Example: onclick="javascript:MegaZine.nextPage();"
 */
MegaZine = {
	// Name of the movie (flash object). This should be the value of the id set in the embedSWF call.
	moviename : "megazine",
	
	/*
	 * Adjust the following functions to handle events.
	 */
	
	// ---------------------- JavaScript Plugin ------------------ //
	
	// Called when the current page changes. page will always be an even number.
	onPageChange			: function(newPage, oldPage) {
	},
	// Called when the current page changes. page will always be an even number.
	onPageChangeDelayed		: function(newPage, oldPage) {
	},
	// Called when the current page scaling changes.
	onZoomChange			: function(newZoom, oldZoom) {
	},
	// Called when the current page scaling changes.
	onZoomChangeDelayed		: function(newZoom, oldZoom) {
	},
	// Called when sounds should be muted.
	onMute					: function() {
	},
	// Called when sounds are no longer muted.
	onUnmute				: function() {
	},
	// Called when the MegaZine instance is ready for JavaScript interaction.
	onJSInit				: function() {
	},
	// Called when the MegaZine instance's flip status changes (pages moving or not).
	onFlipStateChange		: function(state, prevstate) {
	},
	
	// ---------------------- PrintPDF Plugin -------------------- //
	
	// Called when a print job is about to start. If this function
	// returns TRUE, the job is cancelled. This can be used to handle
	// the printing via JS, for example.
	// pages is an array with the numbers of the pages to print.
	onPrintPdf				: function(pages) {
	},
	
	// ---------------------- Gallery Plugin --------------------- //
	
	// Called when the displayed image in a gallery changes.
	// page is the number of the page containing the now displayed image.
	// element is the number of the element on the page that belongs to the
	// displayed image.
	onGalleryElementChange	: function(page, element) {
	},
	// Called when the gallery is opened.
	onGalleryOpen			: function() {
	},
	// Called when the gallery is closed.
	onGalleryClose			: function() {
	},
	
	// ---------------------- SlideShow Plugin ------------------- //
	
	// Called when the automatic page turning (slideshow) is started.
	onSlideStart			: function() {
	},
	// Called when the automatic page turning (slideshow) is stopped.
	onSlideStop				: function() {
	},
	
	
	
	/*
	 * !!! Do not change the following functions, just call them !!!
	 */
	
	/* This utility function resolves the string movie to a Flash object reference based on browser type. */
	getMovie : function() { return document.getElementById([MegaZine.moviename]); },
	
	// ---------------------- JavaScript Plugin ------------------ //
	
	// Returns current page number (always an even number).
	getCurrentPage			: function() { return MegaZine.getMovie().getCurrentPage(); },
	// Returns number of pages in the book.
	getPageCount			: function() { return MegaZine.getMovie().getPageCount(); },
	// Returns page height.
	getPageHeight			: function() { return MegaZine.getMovie().getPageHeight(); },
	// Return page width.
	getPageWidth			: function() { return MegaZine.getMovie().getPageWidth(); },
	// Return flip state (page moving or not).
	getFlipState			: function() { return MegaZine.getMovie().getFlipState(); },
	// Return state (loading, ready).
	getLoadState			: function() { return MegaZine.getMovie().getLoadState(); },
	// Navigate to a page in the book.
	gotoPage				: function(page, instant) { if (instant == null) instant = false; MegaZine.getMovie().gotoPage(page, instant); },
	// Navigate to the first page in the book.
	gotoFirstPage			: function(instant) { if (instant == null) instant = false; MegaZine.getMovie().gotoFirstPage(instant); },
	// Navigate to the last page in the book.
	gotoLastPage			: function(instant) { if (instant == null) instant = false; MegaZine.getMovie().gotoLastPage(instant); },
	// Navigate to the next page.
	gotoNextPage			: function(instant) { if (instant == null) instant = false; MegaZine.getMovie().gotoNextPage(instant); },
	// Navigate to the previous page.
	gotoPreviousPage		: function(instant) { if (instant == null) instant = false; MegaZine.getMovie().gotoPreviousPage(instant); },
	// Returns whether shadows are enabled.
	hasShadows				: function() { return MegaZine.getMovie().hasShadows(); },
	// Returns whether reflections are enabled.
	hasReflection			: function() { return MegaZine.getMovie().hasReflection(); },
	// Return whether corner hinting is enabled.
	isCornerHintingEnabled	: function() { return MegaZine.getMovie().isCornerHintingEnabled(); },
	// Get the number of maximum pages to be jumped over before not animating the page change.
	getInstantJumpCount		: function() { return MegaZine.getMovie().getInstantJumpCount(); },
	// Return whether mouse interaction with pages is enabled.
	isDraggingEnabled		: function() { return MegaZine.getMovie().isDraggingEnabled(); },
	// Return whether the given page side may be turned.
	isTurningEnabled		: function(pageside) { return MegaZine.getMovie().isTurningEnabled(pageside); },
	// Return whether sounds are muted.
	isMuted					: function() { return MegaZine.getMovie().isMuted(); },
	// Set whether corner hinting should be enabled. Setting to true will fail if user is dragging.
	setCornerHintingEnabled	: function(enable) { MegaZine.getMovie().setCornerHintingEnabled(enable); },
	// Set whether mouse interaction with pages is enabled.
	setDraggingEnabled		: function(enable) { MegaZine.getMovie().setDraggingEnabled(enable); },
	// Set whether the given page side may be turned.
	setTurningEnabled		: function(pageside, enabled) { return MegaZine.getMovie().setTurningEnabled(pageside, enabled); },
	// Set the number of maximum pages to be jumped over before not animating the page change.
	setInstantJumpCount		: function(value) { MegaZine.getMovie().setInstantJumpCount(value); },
	// Set muted state for sounds.
	setMuted				: function(mute) { MegaZine.getMovie().setMuted(mute); },
	// Sets shadow usage.
	setShadows				: function(enabled) { MegaZine.getMovie().setShadows(enabled); },
	// Sets reflection usage.
	setReflection			: function(enabled) { MegaZine.getMovie().setReflection(enabled); },
	// The current book rotation.
	getRotation				: function() { return MegaZine.getMovie().getRotation(); },
	// Sets book rotation.
	setRotation				: function(rotation) { MegaZine.getMovie().setRotation(rotation); },
	// Get current zoom level
	getZoom					: function() { return MegaZine.getMovie().getZoom(); },
	// Set zoom to the given level
	setZoom					: function(value) { MegaZine.getMovie().setZoom(value); },
	// Get whether liquid scaling is currently used / active.
	getLiquidScaling		: function() { return MegaZine.getMovie().getLiquidScaling(); },
	// Set whether to use liquid scaling or not (this does not completely disable it! Just until it's re-enabled e.g. via user zooming)).
	setLiquidScaling		: function(enabled) { MegaZine.getMovie().setLiquidScaling(enabled); },
	// Zoom in the actual book
	zoomIn					: function(amount) { if (amount == null) amount = 0.1; MegaZine.getMovie().zoomIn(amount); },
	// Zoom out the actual book
	zoomOut					: function(amount) { if (amount == null) amount = 0.1; MegaZine.getMovie().zoomOut(amount); },
	// Zoom to liquid scaling size (i.e. reenable use of liquid scaling manually)
	zoomFit					: function() { MegaZine.getMovie().zoomFit(); },
	// Add a chapter to the book
	addChapter				: function(xml) { MegaZine.getMovie().addChapter(xml); },
	// Add a chapter at a certain position to the book
	addChapterAt			: function(xml, index) { MegaZine.getMovie().addChapterAt(xml, index); },
	// Add a page to the book
	addPage					: function(xml) { MegaZine.getMovie().addPage(xml); },
	// Add a page to a chapter in the book
	addPageIn				: function(xml, chapter) { if (chapter === null) chapter = -1; console.log(chapter); MegaZine.getMovie().addPageIn(xml, chapter); },
	// Add a page at a certain position to the book
	addPageAt				: function(xml, index, prevChapter) { MegaZine.getMovie().addPageAt(xml, index, prevChapter); },
	// Removes a chapter from the book
	removeChapter			: function(chapter) { MegaZine.getMovie().removeChapter(chapter); },
	// Removes a page from the book
	removePage				: function(page) { MegaZine.getMovie().removePage(page); },
	// Get currently used language
	getLanguage				: function() { return MegaZine.getMovie().getLanguage(); },
	// Set language to use
	setLanguage				: function(lang) { if (lang == null) return; MegaZine.getMovie().setLanguage(lang); },
	// Get a list of all available languages
	getAllLanguages			: function() { return MegaZine.getMovie().getAllLanguages(); },
	
	// ---------------------- Anchors Plugin --------------------- //
	
	// Returns current anchor. Can be null.
	getCurrentAnchor		: function() { return MegaZine.getMovie().getCurrentAnchor(); },
	// Returns anchor of the given page in the book.
	getPageAnchor			: function(page, exact) { if (exact == null) exact = false; return MegaZine.getMovie().getPageAnchor(page, exact); },
	// Navigate to an anchor in the book.
	gotoAnchor				: function(id, instant) { if (instant == null) instant = false; MegaZine.getMovie().gotoAnchor(id, instant); },
	
	// ---------------------- Gallery Plugin --------------------- //
	
	// Return whether the gallery is currently open.
	isGalleryOpen			: function() { return MegaZine.getMovie().isGalleryOpen(); },
	// Opens the gallery for the given page (and if given, element)
	openGallery				: function(page, element) { if (element == null) element = -1; return MegaZine.getMovie().openGallery(page, element); },
	// Rotate the current image counterclockwise if gallery is open (else returns false).
	galleryRotateLeft		: function() { return MegaZine.getMovie().galleryRotateRight(); },
	// Rotate the current image clockwise if gallery is open (else returns false).
	galleryRotateRight		: function() { return MegaZine.getMovie().galleryRotateRight(); },
	// Zoom in if gallery is open (else returns false).
	galleryZoomIn			: function() { return MegaZine.getMovie().galleryZoomIn(); },
	// Zoom out if gallery is open (else returns false).
	galleryZoomOut			: function() { return MegaZine.getMovie().galleryZoomOut(); },
	// Goes to the next image if gallery is open (else returns false).
	galleryNextImage		: function() { return MegaZine.getMovie().galleryNextImage(); },
	// Goes to the previous image if gallery is open (else returns false).
	galleryPreviousImage	: function() { return MegaZine.getMovie().galleryPreviousImage(); },
	// Goes to the first image if gallery is open (else returns false).
	galleryFirstImage		: function() { return MegaZine.getMovie().galleryFirstImage(); },
	// Goes to the last image if gallery is open (else returns false).
	galleryLastImage		: function() { return MegaZine.getMovie().galleryLastImage(); },

	// ---------------------- Index Plugin ----------------------- //
	
	// Whether the index frame (page overview) is currently open or not.
	getIndexOpen			: function() { return MegaZine.getMovie().getIndexOpen(); },
	// Sets visibility state of the index frame.
	setIndexOpen			: function(open) { MegaZine.getMovie().setIndexOpen(open); },
	
	// ---------------------- Print Plugin ----------------------- //
	
	// Prints a given set of pages (array of page numbers to print)
	print					: function(pages) { MegaZine.getMovie().print(pages); },
	// Whether a print job is currently in progress (loading data).
	getPrinting				: function() { return MegaZine.getMovie().getPrinting(); },
	// Whether the print frame (page selection) is currently open or not.
	getPrintOpen			: function() { return MegaZine.getMovie().getPrintOpen(); },
	// Sets visibility state of the print frame.
	setPrintOpen			: function(open) { MegaZine.getMovie().setPrintOpen(open); },
	
	// ---------------------- Search Plugin ---------------------- //
	
	// Search for the given query inside the book.
	search					: function(query) { MegaZine.getMovie().search(query); },
	
	// ---------------------- Sidebar Plugin --------------------- //
	
	// Checks whether the sidebar is currently open
	getSidebarOpen			: function() { return MegaZine.getMovie().getSidebarOpen(); },
	// Sets whether the sidebar is currently open
	setSidebarOpen			: function(open) { MegaZine.getMovie().setSidebarOpen(open); },
	// Checks whether the sidebar is currently in manual mode
	getSidebarManualMode	: function() { return MegaZine.getMovie().getSidebarManualMode(); },
	// Sets whether the sidebar is currently in manual mode
	setSidebarManualMode	: function(enabled) { MegaZine.getMovie().setSidebarManualMode(enabled); },
	
	// ---------------------- Slideshow Plugin ------------------- //
	
	// Start slideshow / automatic page turning.
	slideStart				: function(skipFirstIfLongerThan) { if (skipFirstIfLongerThan == null) skipFirstIfLongerThan = 1000; MegaZine.getMovie().slideStart(skipFirstIfLongerThan); },
	// Stop slideshow / automatic page turning.
	slideStop				: function() { MegaZine.getMovie().slideStop(); },
	
	// ---------------------- MouseWheel workaround ------------------- //
	
	// Mouse wheel workaround for set wmode
	// see http://cookbooks.adobe.com/index.cfm?event=showdetails&postId=13086
	handleWheel				: function(event) { MegaZine.getMovie().handleWheel({x : event.screenX, y : event.screenY, delta : event.detail || -event.wheelDelta, ctrlKey : event.ctrlKey, altKey : event.altKey, shiftKey : event.shiftKey}); }
};

// Part of mouse wheel workaround.
// Add a leading slash in the next line to enable (i.e. make it read //*).
/*
if(!(document.attachEvent)) {
	// Firefox
	window.addEventListener("DOMMouseScroll", MegaZine.handleWheel, false);
	// Chrome
	document.onmousewheel = MegaZine.handleWheel;
}
//*/