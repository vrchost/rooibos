package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class SlideshowCursorChangeEvent extends Event
	{
		public static const POSITION_CHANGED: String = "positionChangedEvent";
		
		public var targetWindow:String;
		public var targetPane:String;
		public var newPosition:int;
		public var numPositions:int;


		public function SlideshowCursorChangeEvent(type:String)
		{
			super(type, false, false);
		}
		override public function clone():Event
		{
			var event:SlideshowCursorChangeEvent = new SlideshowCursorChangeEvent(type);
			event.targetWindow = targetWindow;
			event.targetPane = targetPane;
			event.newPosition = newPosition;
			event.numPositions = numPositions;
			return event;
		}
	}
}