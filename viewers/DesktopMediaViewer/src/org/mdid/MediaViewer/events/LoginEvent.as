package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	import org.mdid.MediaViewer.models.vo.User;
	
	public class LoginEvent extends Event
	{		
		public static const LOGIN_USER: String = "loginUser";
		public static const PROMPT_FOR_LOGIN:String = "promptForLoginEvent";
		public static const LOGOUT: String = "logoutEvent";
		public static const LOGIN_SUCCESSFUL:String = "loginSuccessfulEvent";
		public static const LOGIN_FAILED:String = "loginFailedEvent";
		public static const KEEP_SESSION_ALIVE:String = "keepAliveEvent";
		
		private var _user:User;
		public var errorMessage:String;
		
		public function get user():User {
			return _user;
		}
		
		public function LoginEvent(type:String, user:User = null, errMsg:String = "") {
			_user = user;
			errorMessage = errMsg;
			super(type,false,false);
		}
		override public function clone():Event
		{
			return new LoginEvent(type, _user, errorMessage);
		}
	}
}