package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class NavigationEvent extends Event
	{
		public static const NEXT: String = "gotoNextSlideEvent";
		public static const LAST: String = "gotoLastSlideEvent";
		public static const PREVIOUS: String = "gotoPreviousSlideEvent";
		public static const FIRST: String = "gotoFirstSlideEvent";
		public static const GOTO_X: String = "gotoSlideXEvent";
		public static const UNLOAD_ALL_SLIDES: String = "unloadAllSlidesEvent";
		
		public var targetWindow:String;
		public var targetPane:String;
		public var targetPosition:int;


		public function NavigationEvent(type:String)
		{
			super(type, false, false);
		}
		override public function clone():Event
		{
			var event:NavigationEvent = new NavigationEvent(type);
			event.targetWindow = targetWindow;
			event.targetPane = targetPane;
			event.targetPosition = targetPosition;
			return event;
		}
	}
}