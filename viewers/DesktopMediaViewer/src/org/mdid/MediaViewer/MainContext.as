package org.mdid.MediaViewer
{
	import com.adobe.air.preferences.Preference;
	
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
	
	public class MainContext extends ModuleContext
	{
		public function MainContext(contextView:DisplayObjectContainer, injector:IInjector) {
			super(contextView, true, injector);
		}
		
		override public function startup():void {

			//map values
			injector.mapValue(String, SlideshowCursor.MAIN_WINDOW, "windowname");
			
			//map commands

			//map view
			mediatorMap.mapView(AppHolder, ControlBarTopBarMediator);
			mediatorMap.mapView(ImageHolder, ImageHolderMediator);
			mediatorMap.mapView(EdgeControls, EdgeControlsMediator);
			
			// And away we go!
			//dispatchEvent(new ContextEvent(ContextEvent.STARTUP));
		}
		
		override public function dispose():void {
			mediatorMap.removeMediatorByView(contextView);
			super.dispose();
		}
	}
}