package org.mdid.MediaViewer
{
	import flash.display.DisplayObjectContainer;
	
	import org.mdid.MediaViewer.models.vo.SlideshowCursor;
	import org.mdid.MediaViewer.views.components.AppHolder;
	import org.mdid.MediaViewer.views.components.EdgeControls;
	import org.mdid.MediaViewer.views.components.ImageHolder;
	import org.mdid.MediaViewer.views.mediators.ControlBarTopBarMediator;
	import org.mdid.MediaViewer.views.mediators.EdgeControlsMediator;
	import org.mdid.MediaViewer.views.mediators.ImageHolderMediator;
	import org.robotlegs.core.IInjector;
	import org.robotlegs.utilities.modular.mvcs.ModuleContext;
	
	public class SecondContext extends ModuleContext
	{
		public function SecondContext(contextView:DisplayObjectContainer, injector:IInjector) {
			super(contextView, true, injector);
		}
		
		override public function startup():void {
			//map value
			injector.mapValue(String, SlideshowCursor.SECOND_WINDOW, "windowname");

			//map commands

			//injector.mapSingletonOf(ICachingService, CachingService);
			mediatorMap.mapView(AppHolder, ControlBarTopBarMediator);
			mediatorMap.mapView(ImageHolder, ImageHolderMediator);
			mediatorMap.mapView(EdgeControls, EdgeControlsMediator);
		}
		
		override public function dispose():void {
			mediatorMap.removeMediatorByView(contextView);
			super.dispose();
		}
	}
}