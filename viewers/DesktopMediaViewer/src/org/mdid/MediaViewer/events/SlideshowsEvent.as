package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class SlideshowsEvent extends Event
	{
		public static const LOAD_SLIDESHOWS:String = "loadSlideshowsEvent";
		public static const LOAD_SLIDESHOWS_SUCCESSFUL:String = "loadSlideshowsSuccessfulEvent";
		public static const LOAD_SLIDESHOWS_FAILED:String = "loadFailedEvent";
		public static const INVALIDATE_ALL_IMAGES:String = "invalidateAllImagesEvent";
		public static const UNLOAD_CURRENT_SLIDESHOW:String = "unloadCurrentSlideshowEvent";
		public static const SELECT_SLIDESHOW:String = "selectSlideshowEvent";
		public static const LOAD_SELECTED_SLIDESHOW:String = "loadSelectedSlideshowEvent";
		public static const LOAD_SELECTED_SLIDESHOW_SUCCESSFUL:String = "loadSelectedSlideshowSuccessfulEvent";
		public static const LOAD_SELECTED_SLIDESHOW_FAILED:String = "loadSelectedSlideshowFailedEvent";
		public static const FILTER_LIST:String = "filterListEvent";

		public var errorMessage:String;
		public var selectedSlideshow:Object;

		public function SlideshowsEvent(type:String, errMsg:String = "") {
			errorMessage = errMsg;
			super(type, false, false);
		}
		override public function clone():Event
		{
			var event:SlideshowsEvent = new SlideshowsEvent(type, errorMessage);
			event.selectedSlideshow = selectedSlideshow;
			return event;
		}
	}
}