package org.mdid.MediaViewer.controllers
{
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.services.IMessageService;
	import org.robotlegs.mvcs.Command;
	
	public class GetSlideshowCommand extends Command
	{
		[Inject]
		public var event:SlideshowsEvent;
		
		[Inject]
		public var service:IMessageService;
		
		override public function execute():void {
			service.getSlideshow(event.selectedSlideshow == null ? -1 : (event.selectedSlideshow.id == null ? -1 : event.selectedSlideshow.id));
		}
	}
}