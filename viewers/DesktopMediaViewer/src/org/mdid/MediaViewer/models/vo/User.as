package org.mdid.MediaViewer.models.vo
{
	public class User
	{
		private var _username:String;
		private var _password:String;
		private var _sessiontoken:String;
		private var _userid:String;
		
		public function User(username:String="", password:String="", sessiontoken:String = "", userid:String = "") {
			_username = username;
			_password = password;
			_sessiontoken = sessiontoken;
		}
		
		public function get username():String {
			return _username;
		}		
		public function set username(value:String):void {
			_username = value;
		}
		
		public function get password():String {
			return _password;
		}
		public function set password(value:String):void {
			_password = value;
		}
		
		public function get sessiontoken():String {
			return _sessiontoken;
		}
		public function set sessiontoken(value:String):void {
			_sessiontoken = value;
		}
		
		public function get userid():String {
			return _userid;
		}
		public function set userid(value:String):void {
			_userid = value;
		}
		
		public function clone():User {
			return new User(_username, _password, _sessiontoken, _userid);
		}
		
	}
}