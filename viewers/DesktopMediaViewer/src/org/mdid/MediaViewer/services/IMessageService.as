package org.mdid.MediaViewer.services
{
	import org.mdid.MediaViewer.models.vo.User;
	
	public interface IMessageService
	{
		function get loggedIn():Boolean;
		function logIn(user:User):void;
		function logOut():void;
		function getSlideshowList():void;
		function getSlideshow(id:int):void;
		function keepSessionAlive():void;
	}
}