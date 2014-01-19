package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class RightClickMenuEvent extends Event
	{
		public static const HIDE_IMAGE: String = "hideImageEvent";
		public static const SHOW_IMAGE: String = "showImageEvent";
		public static const UNSPLIT_DISPLAY: String = "unsplitDisplayEvent";
		public static const SPLIT_DISPLAY_HORIZONTALLY: String = "splitDisplayHorizontallyEvent";
		public static const SPLIT_DISPLAY_VERTICALLY: String = "splitDisplayVerticallyEvent";
		public static const IMAGE_IS_VISIBLE: String = "imageIsVisibleEvent";
		public static const IMAGE_IS_HIDDEN: String = "imageIsHiddenEvent";
		public static const TOGGLE_FULLSCREEN: String = "toggleFullscreenEvent";
		
		private var _targetWindow:String;
		private var _targetPane:String;
		
		public function get targetWindow():String {
			return _targetWindow;
		}
		public function get targetPane():String {
			return _targetPane;
		}
		
		public function RightClickMenuEvent(type:String, targetWindow:String, targetPane:String="") {
			_targetWindow = targetWindow;
			_targetPane = targetPane;
			super(type, false, false);
		}
		override public function clone():Event {
			return new RightClickMenuEvent(type, _targetWindow, _targetPane);
		}
	}
}