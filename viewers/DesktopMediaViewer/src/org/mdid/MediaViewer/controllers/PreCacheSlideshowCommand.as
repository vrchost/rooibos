package org.mdid.MediaViewer.controllers
{
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.services.ICachingService;
	import org.robotlegs.mvcs.Command;
	
	public class PreCacheSlideshowCommand extends Command
	{
		[Inject]
		public var service:ICachingService;

		[Inject]
		public var model:SlideshowModel;
		
		override public function execute():void {
			service.preCacheImageThumbnails(model.currentShow.slides);
			service.preCacheImages(model.currentShow.slides);
		}
	}
}