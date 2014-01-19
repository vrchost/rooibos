package org.mdid.MediaViewer.models
{
	import org.mdid.MediaViewer.models.vo.User;
	import org.robotlegs.mvcs.Actor;
	
	public class LoginModel extends Actor
	{
		private var _user:User;
		
		public function LoginModel() { }
		
		public function get user():User
		{
			return _user;
		}
		public function set user(value:User):void {
			_user = value;
		}
		public function get isLoggedIn():Boolean {
			return (_user != null && _user.sessiontoken != null && _user.sessiontoken.length > 0);
		}		
	}
}