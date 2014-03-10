package org.mdid.MediaViewer.controllers
{
	import org.mdid.MediaViewer.services.IMessageService;
	import org.robotlegs.mvcs.Command;
	
	public class SlideshowsLoadCommand extends Command
	{
		[Inject]
		public var service:IMessageService;
				
		override public function execute():void {
			service.getSlideshowList();
		}

	}
}