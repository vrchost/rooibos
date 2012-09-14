package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class ControlBarEvent extends Event
	{
		public static const SHOW_CONTROLBAR: String = "showControlBarEvent";
		public static const HIDE_CONTROLBAR: String = "hideControlBarEvent";
		public static const SHOW_CATALOGDATA_WINDOW: String = "showCatalogdataWindowEvent";
		public static const HIDE_CATALOGDATA_WINDOW: String = "hideCatalogdataWindowEvent";
		public static const MOVE_WINDOW_TO_TOPLEFT: String = "moveWindowToTopLeftEvent";
		public static const SPLIT_DISPLAY_V: String = "splitDisplayVEvent";
		public static const SPLIT_DISPLAY_H: String = "splitDisplayHEvent";
		public static const UNSPLIT_DISPLAY: String = "unSplitDisplayEvent";
		public static const DISPLAY_CHANGED: String = "displayChangedEvent";
		public static const LEFT_EDGE_BLOCK: String = "theLeftEdgeBlock";
		public static const RIGHT_EDGE_BLOCK: String = "theRightEdgeBlock";
		public static const TOGGLE_WINDOW_ORDER: String = "toggleWindowOrderEvent";
		public static const SECOND_PANE_IS_REGISTERED: String = "secondPaneIsRegisteredEvent";
		
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

		public function ControlBarEvent(type:String, targetWindow:String, targetPane:String, edgeBlock:String = "") {
			_targetWindow = targetWindow;
			_targetPane = targetPane;
			_edgeBlock = edgeBlock;
			super(type, false, false);
		}
		override public function clone():Event {
			return new ControlBarEvent(type, _targetWindow, _targetPane, _edgeBlock);
		}
	}
}