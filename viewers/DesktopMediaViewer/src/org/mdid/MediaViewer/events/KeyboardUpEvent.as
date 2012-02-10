package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class KeyboardUpEvent extends Event
	{
		public static const KEY_UP: String = "theKeyUpEvent";
		
		private var _targetWindow:String;
		private var _targetPane:String;
		private var _keyCode:uint;
		private var _shiftKey:Boolean;
		
		public function get targetWindow():String {
			return _targetWindow;
		}
		public function get targetPane():String {
			return _targetPane;
		}
		public function get keyCode():uint {
			return _keyCode;
		}
		public function get shiftKey():Boolean {
			return _shiftKey;
		}
		
		public function KeyboardUpEvent(type:String, targetWindow:String, targetPane:String, theKeyCode:uint, theShiftKey:Boolean) {
			_targetWindow = targetWindow;
			_targetPane = targetPane;
			_keyCode = theKeyCode;
			_shiftKey = theShiftKey;
			super(type, false, false);
		}
		override public function clone():Event {
			return new KeyboardUpEvent(type, _targetWindow, _targetPane, _keyCode, _shiftKey);
		}
	}
}