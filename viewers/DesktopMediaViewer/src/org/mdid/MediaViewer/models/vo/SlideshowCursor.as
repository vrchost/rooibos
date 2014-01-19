package org.mdid.MediaViewer.models.vo
{
	public class SlideshowCursor
	{
		public static const MAIN_WINDOW:String = "theMainWindow";
		public static const SECOND_WINDOW:String = "theSecondOrCompanionWindow";
		public static const FIRST_PANE:String = "theFirstPane";
		public static const SECOND_PANE:String = "theSecondPane";
		
		private var _cursorWindow1FirstPane:int = -1;
		private var _cursorWindow1SecondPane:int = -1;
		private var _cursorWindow2FirstPane:int = -1;
		private var _cursorWindow2SecondPane:int = -1;
		
		public function getCursor(windowname:String, panename:String):int {
			if (windowname == MAIN_WINDOW) {
				return (panename == FIRST_PANE) ? _cursorWindow1FirstPane : _cursorWindow1SecondPane;
			} else if (windowname == SECOND_WINDOW) {
				return (panename == FIRST_PANE) ? _cursorWindow2FirstPane : _cursorWindow2SecondPane;
			} else {
				return -1;
			}
		}
		
		public function setCursor(windowname:String, panename:String, val:int):void {
			if (windowname == MAIN_WINDOW) {
				if (panename == FIRST_PANE) {
					_cursorWindow1FirstPane = val;
				} else if (panename == SECOND_PANE) {
					_cursorWindow1SecondPane = val;
				}
			} else if (windowname == SECOND_WINDOW) {
				if (panename == FIRST_PANE) {
					_cursorWindow2FirstPane = val;
				} else if (panename == SECOND_PANE) {
					_cursorWindow2SecondPane = val;
				}
			}
		}
		public function initialize(initVal:int = -1):void {
			_cursorWindow1FirstPane = initVal;
			_cursorWindow1SecondPane = initVal;
			_cursorWindow2FirstPane = initVal;
			_cursorWindow2SecondPane = initVal;	
		}
		public function SlideshowCursor(initVal:int = -1) {
			initialize(initVal);
		}
	}
}