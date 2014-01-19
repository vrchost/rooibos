package org.mdid.MediaViewer
{
	import com.adobe.air.preferences.Preference;
	
	import flash.display.DisplayObjectContainer;
	import flash.system.ApplicationDomain;
	
	import org.mdid.MediaViewer.controllers.*;
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.models.LoginModel;
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.models.SlideshowsModel;
	import org.mdid.MediaViewer.models.vo.SlideshowCursor;
	import org.mdid.MediaViewer.services.CachingService;
	import org.mdid.MediaViewer.services.ICachingService;
	import org.mdid.MediaViewer.services.IMessageService;
	import org.mdid.MediaViewer.services.Mdid3MessageService;
	import org.mdid.MediaViewer.views.components.EdgeControls;
	import org.mdid.MediaViewer.views.components.ImageHolder;
	import org.mdid.MediaViewer.views.components.LoginWindow;
	import org.mdid.MediaViewer.views.components.MainView;
	import org.mdid.MediaViewer.views.components.SecondWindow;
	import org.mdid.MediaViewer.views.components.SlideshowList;
	import org.mdid.MediaViewer.views.mediators.*;
	import org.robotlegs.base.ContextEvent;
	import org.robotlegs.core.IInjector;
	import org.robotlegs.utilities.modular.mvcs.ModuleContext;
	
	public class ParentContext extends ModuleContext
	{
		override public function startup():void {
			//map injector
			injector.mapValue(IInjector, injector);
			
			//map the modules so that instances will be properly supplied (injected) with an injector.
			viewMap.mapType(MainView);
			viewMap.mapType(SecondWindow);
			
			//map commands
			commandMap.mapEvent(ContextEvent.STARTUP, StartupCommand, ContextEvent, true);
			commandMap.mapEvent(LoginEvent.LOGIN_USER, LoginUserCommand, LoginEvent);
			commandMap.mapEvent(LoginEvent.LOGOUT, LogoutUserCommand, LoginEvent);
			commandMap.mapEvent(LoginEvent.KEEP_SESSION_ALIVE, KeepSessionAliveCommand, LoginEvent);
			commandMap.mapEvent(SlideshowsEvent.LOAD_SLIDESHOWS, SlideshowsLoadCommand, SlideshowsEvent);
			commandMap.mapEvent(SlideshowsEvent.UNLOAD_CURRENT_SLIDESHOW, SlideshowsUnLoadCommand, SlideshowsEvent);
			commandMap.mapEvent(SlideshowsEvent.LOAD_SELECTED_SLIDESHOW, GetSlideshowCommand, SlideshowsEvent);
			commandMap.mapEvent(SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_SUCCESSFUL, PreCacheSlideshowCommand, SlideshowsEvent);
			
			//map model
			injector.mapSingleton(LoginModel);
			injector.mapSingleton(SlideshowsModel);
			injector.mapSingleton(SlideshowModel);
			
			
			//map values
			var prefs:Preference = new Preference("prefs.obj");
			injector.mapValue(Preference, prefs);
			var cursor:SlideshowCursor = new SlideshowCursor(-1);
			injector.mapValue(SlideshowCursor, cursor);
			
			//map service
			injector.mapSingletonOf(IMessageService, Mdid3MessageService);
			injector.mapSingletonOf(ICachingService, CachingService);
			
			//map view
			mediatorMap.mapView(SlideshowList, SlideshowListMediator, null, false, false );
			mediatorMap.mapView(LoginWindow, LoginWindowMediator, null, false, false );
			mediatorMap.mapView(DesktopMediaViewer, ApplicationMediator);
			
			// And away we go!
			dispatchEvent(new ContextEvent(ContextEvent.STARTUP));
		}
	}
}