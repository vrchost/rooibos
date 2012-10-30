package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class TopBarEvent extends Event
	{
		public static const SHOW_TOPBAR: String = "showTopBarEvent";
		public static const HIDE_TOPBAR: String = "hideTopBarEvent";
		public static const LEFT_EDGE_BLOCK: String = "theLeftEdgeBlock";
		public static const RIGHT_EDGE_BLOCK: String = "theRightEdgeBlock";
		public static const SECOND_WINDOW_TOPBAR_IS_READY: String = "secondWindowTopbarIsReadyEvent";
		
		private var _targetWindow:String;
		private var _targetPane:String;
		private var _edgeBlock:String;
		
		public function get targetWindow():String {
			return _targetWindow;
		}
		public function get targetPane():String {
			return _targetPane;
		}
		public function get edgeBlock():String {
			return _edgeBlock;
		}

		public function TopBarEvent(type:String, targetWindow:String, targetPane:String, edgeBlock:String = "") {
			_targetWindow = targetWindow;
			_targetPane = targetPane;
			_edgeBlock = edgeBlock;
			super(type, false, false);
		}
		override public function clone():Event {
			return new TopBarEvent(type, _targetWindow, _targetPane, _edgeBlock);
		}
	}
}