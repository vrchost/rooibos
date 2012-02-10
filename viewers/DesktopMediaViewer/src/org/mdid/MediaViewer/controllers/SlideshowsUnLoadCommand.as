package org.mdid.MediaViewer.controllers
{
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.models.SlideshowsModel;
	import org.mdid.MediaViewer.services.IMessageService;
	import org.robotlegs.mvcs.Command;
	
	public class SlideshowsUnLoadCommand extends Command
	{
		[Inject]
		public var slideshow:SlideshowModel;
				
		override public function execute():void {
			slideshow.unloadCurrentShow();
		}

	}
}