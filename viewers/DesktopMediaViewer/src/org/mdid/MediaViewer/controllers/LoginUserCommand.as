package org.mdid.MediaViewer.controllers
{
	import com.adobe.air.preferences.Preference;
	
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.models.vo.User;
	import org.mdid.MediaViewer.services.IMessageService;
	import org.robotlegs.mvcs.Command;
	
	public class LoginUserCommand extends Command
	{
		[Inject]
		public var event:LoginEvent;
		
		[Inject]
		public var service:IMessageService;
				
		override public function execute():void
		{
			service.logIn(event.user);
		}
	}
}