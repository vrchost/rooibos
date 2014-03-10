package org.mdid.MediaViewer.controllers
{
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.models.vo.User;
	import org.mdid.MediaViewer.services.IMessageService;
	import org.robotlegs.mvcs.Command;
	
	public class KeepSessionAliveCommand extends Command
	{
		[Inject]
		public var event:LoginEvent;
		
		[Inject]
		public var service:IMessageService;
				
		override public function execute():void
		{
			service.keepSessionAlive();
		}
	}
}