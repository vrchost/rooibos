package org.mdid.MediaViewer.views.mediators
{
	import com.adobe.air.preferences.Preference;
	import com.adobe.utils.XMLUtil;
	
	import flash.desktop.NativeApplication;
	import flash.desktop.Updater;
	import flash.events.BrowserInvokeEvent;
	import flash.events.Event;
	import flash.events.MouseEvent;
	import flash.events.ProgressEvent;
	import flash.events.TimerEvent;
	import flash.filesystem.File;
	import flash.filesystem.FileMode;
	import flash.filesystem.FileStream;
	import flash.geom.Point;
	import flash.net.URLLoader;
	import flash.net.URLRequest;
	import flash.net.URLRequestDefaults;
	import flash.net.URLStream;
	import flash.system.Capabilities;
	import flash.ui.Mouse;
	import flash.ui.MouseCursor;
	import flash.utils.ByteArray;
	import flash.utils.Timer;
	
	import mx.controls.Alert;
	import mx.events.AIREvent;
	import mx.events.CloseEvent;
	import mx.events.FlexEvent;
	import mx.events.MoveEvent;
	import mx.events.ResizeEvent;
	import mx.events.StateChangeEvent;
	import mx.managers.CursorManager;
	import mx.managers.PopUpManager;
	import mx.utils.Base64Decoder;
	import mx.utils.URLUtil;
	import mx.utils.XMLUtil;
	
	import org.mdid.MediaViewer.MainContext;
	import org.mdid.MediaViewer.SecondContext;
	import org.mdid.MediaViewer.events.ControlBarEvent;
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.events.NavigationEvent;
	import org.mdid.MediaViewer.events.SlideshowCursorChangeEvent;
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.events.TopBarEvent;
	import org.mdid.MediaViewer.models.LoginModel;
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.models.vo.SlideshowCursor;
	import org.mdid.MediaViewer.views.components.LoginWindow;
	import org.mdid.MediaViewer.views.components.SecondWindow;
	import org.mdid.MediaViewer.views.components.SlideshowList;
	import org.robotlegs.base.ContextEvent;
	import org.robotlegs.core.IInjector;
	import org.robotlegs.mvcs.Mediator;
	import org.robotlegs.utilities.modular.mvcs.ModuleMediator;
	
	public class ApplicationMediator extends ModuleMediator
	{
		[Inject]
		public var view:DesktopMediaViewer;
		
		[Inject]
		public var loginModel:LoginModel;
		
		[Inject]
		public var slideshow:SlideshowModel;
		
		[Inject]
		public var prefs:Preference;
		
		[Inject]
		public var parentContextIInjector:IInjector;
				
		private var _latestVersion:String;
		private var _airFileUrl:String;
		private var loginwindowPopup:LoginWindow;
		private var isLoginWindowPopped:Boolean = false;
		private var slideshowlistPopup:SlideshowList;
		private var isSlideshowListWindowPopped:Boolean = false;
		private var isLoggedIn:Boolean = false;
		private var isMouseShowing:Boolean = true;
		private var isMouseOverStage:Boolean = true;
		private var topBarReadyDelay:Timer = new Timer(5, 1);
		private var keepAliveTimer:Timer = new Timer(1000 * 60 * 10, 0);//run every ten minutes
		private const IDLETIME:int = 5; //Seconds
		
		protected function get baseURL():String {
			if (!prefs.isLatestDataLoaded) prefs.load();
			var value:String = prefs.getValue("mdid_url");
			if (value == null || value.length < 1) return "";
			if (value.charAt(value.length - 1) != "/") value += "/";
			return value;
		}
		
		public function ApplicationMediator() {
		}
		
		override public function onRegister():void {
			NativeApplication.nativeApplication.idleThreshold = this.IDLETIME;
			flash.net.URLRequestDefaults.idleTimeout = 1000 * 60 * 2; //two minutes
			if (!Capabilities.isDebugger) {
				var isUpdateNotificationDisabled:Boolean = false;
				trace(isUpdateNotificationDisabled);
				//first, check to see if "Upgrade is available" notification has been disabled locally
				var updatePrefsFile:File;
				updatePrefsFile = File.applicationStorageDirectory;
				updatePrefsFile = updatePrefsFile.resolvePath("update_prefs.xml");
				if (updatePrefsFile.exists) {
					var stream:FileStream = new FileStream();
					var updatePrefsXML:XML;
					stream.open(updatePrefsFile, FileMode.READ);
					updatePrefsXML = XML(stream.readUTFBytes(stream.bytesAvailable));
					stream.close();
					isUpdateNotificationDisabled = (updatePrefsXML.disableUpdateIsAvailableNotification.toLowerCase() == "true");
				}
				if (!isUpdateNotificationDisabled) {
					var versionLoader:URLLoader = new URLLoader();
					versionLoader.addEventListener(Event.COMPLETE, versionLoaderCompleteHandler);
					versionLoader.load(new URLRequest(baseURL + "static/dmvinstaller/latestversion.txt"));
					NativeApplication.nativeApplication.addEventListener(BrowserInvokeEvent.BROWSER_INVOKE, browserInvokeHandler);
				}
			}
			var descriptor:XML = NativeApplication.nativeApplication.applicationDescriptor;
			var air:Namespace = descriptor.namespaceDeclarations()[0];
			loginwindowPopup = new LoginWindow();
			slideshowlistPopup = new SlideshowList();
			keepAliveTimer.addEventListener(TimerEvent.TIMER, handleKeepAlive);
			topBarReadyDelay.addEventListener(TimerEvent.TIMER, updateTopBarTitles);
			eventMap.mapListener(eventDispatcher, LoginEvent.PROMPT_FOR_LOGIN, handleLoginWindowPopupAdd);
			eventMap.mapListener(view.mainview.appholder.appmenu.login, MouseEvent.CLICK, handleLoginWindowPopupAdd)
			eventMap.mapListener(view.mainview.appholder.appmenu.slideshows, MouseEvent.CLICK, handleSlideshowPopupAdd)
			eventMap.mapListener(eventDispatcher, SlideshowsEvent.SELECT_SLIDESHOW, handleSlideshowPopupAdd);
			eventMap.mapListener(eventDispatcher, SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_SUCCESSFUL, handleLoadSelectedSlideshowSuccess);
			eventMap.mapListener(view.mainview.appholder.controlbar.dualmonitors, MouseEvent.CLICK, handleOpenSecondWindow);
			eventMap.mapListener(view, Event.CLOSING, handleApplicationClosing);
			eventMap.mapListener(eventDispatcher, LoginEvent.LOGIN_SUCCESSFUL, handleLoginMessageEvent);
			eventMap.mapListener(eventDispatcher, LoginEvent.LOGIN_FAILED, handleLoginMessageEvent);
			eventMap.mapListener(eventDispatcher, LoginEvent.LOGOUT, handleLoginMessageEvent);
			eventMap.mapListener(eventDispatcher, SlideshowsEvent.UNLOAD_CURRENT_SLIDESHOW, handleUnloadCurrentSlideshow);
			eventMap.mapListener(view, ControlBarEvent.TOGGLE_WINDOW_ORDER, handleToggleWindowOrder);
			view.mainview.appholder.appmenu.smoothbitmap.addEventListener(Event.CHANGE, handleSmoothBitmapChangeEvent);
		}
		protected function handleSmoothBitmapChangeEvent(e:Event):void {
			view.isSmoothBitmap = e.currentTarget.selected;
			if (view.secondWindow != null) {
				view.secondWindow.isSmoothBitmap = view.isSmoothBitmap;	
			}
		}
		private function browserInvokeHandler(e:BrowserInvokeEvent):void {
			var base64Dec:Base64Decoder = new Base64Decoder();
			base64Dec.decode(e.arguments[0]);
			var mdidURL:String = base64Dec.toByteArray().toString();
			if (mdidURL == null || mdidURL.length < 5) return;
			if (!prefs.isLatestDataLoaded) prefs.load();
			var storedURL:String = prefs.getValue("mdid_url");
			if (storedURL == null || storedURL.length < 5) {
				this.prefs.setValue("mdid_url", mdidURL);
				this.prefs.save();
				if (this.loginwindowPopup != null) {
					this.loginwindowPopup.urlinput.text = mdidURL;
					this.loginwindowPopup.savebutton.enabled = false;
					this.loginwindowPopup.loginButton.enabled = true;
				}
			}
		}
		private function versionLoaderCompleteHandler(e:Event):void {
			var loader:URLLoader = e.target as URLLoader;
			_latestVersion = loader.data.split(",")[0];
			var descriptor:XML = NativeApplication.nativeApplication.applicationDescriptor;
			var air:Namespace = descriptor.namespaceDeclarations()[0];
			var currentVersion:String = descriptor.air::versionNumber;
			if (_latestVersion != currentVersion) {
				_airFileUrl = loader.data.split(",")[1];
				var message:String = "You are running version " + currentVersion + " of the Desktop MediaViewer. However, version " + _latestVersion + " is available. Please click the Update button or click Canel to perform the update later.";
				Alert.yesLabel = "Update";
				Alert.show(message, "New version of MediaViewer available", Alert.YES|Alert.CANCEL, view, alertUpdateClickHandler);
			} else {
				trace("You appear to be running the latest version of the Desktop MediaViewer");
			}
		}
		private function alertUpdateClickHandler(e:CloseEvent):void {
			if (e.detail == Alert.YES) updateApplication();
		}
		private function updateApplication():void {
			var stream:URLStream = new URLStream();
			stream.addEventListener(ProgressEvent.PROGRESS, updateProgressHandler);
			stream.addEventListener(Event.COMPLETE, updateDownloadCompleteHandler);
			stream.load(new URLRequest(_airFileUrl));
			handleCloseLoginWindowPopup();
			view.setCurrentState("updateapplication");
			view.updateWindow.closeButton.visible = false;
			view.updateMessage.text = "Initiating update download...";
		}
		private function updateProgressHandler(e:ProgressEvent):void {
			view.updateMessage.text = "Downloading update: " + Math.round(e.bytesLoaded/1024.0).toString() + " of " + Math.round(e.bytesTotal/1024.0).toString() + " megabytes";
		}
		private function updateDownloadCompleteHandler(e:Event):void {
			view.updateMessage.text = "Download complete. Beginning update...";
			var urlStream:URLStream = e.target as URLStream;
			var f:File = File.applicationStorageDirectory.resolvePath("DesktopMediaViewer.air");
			var fs:FileStream = new FileStream();
			fs.open(f, FileMode.WRITE);
			var bytes:ByteArray = new ByteArray();
			urlStream.readBytes(bytes);
			fs.writeBytes(bytes);
			fs.close();
			var updater:Updater = new Updater();
			updater.update(f, _latestVersion);
		}
		private function handleToggleWindowOrder(e:ControlBarEvent):void {
			if (view.secondWindow == null || view.secondWindow.closed) {
				view.nativeWindow.orderToFront();
				view.nativeWindow.activate();
				return;
			}
			if (e.targetWindow == SlideshowCursor.MAIN_WINDOW) {
				view.secondWindow.nativeWindow.orderToFront();
				view.secondWindow.nativeWindow.activate();					
			} else if (e.targetWindow == SlideshowCursor.SECOND_WINDOW) {
				view.nativeWindow.orderToFront();
				view.nativeWindow.activate();
			}
		}
		private function updateMouseOverStage(e:Event):void {
			this.isMouseOverStage = (e.type != Event.MOUSE_LEAVE);
			if (this.isMouseOverStage) {
				eventMap.unmapListener(view.stage, MouseEvent.MOUSE_OVER, updateMouseOverStage);
			} else {
				eventMap.mapListener(view.stage, MouseEvent.MOUSE_OVER, updateMouseOverStage);
			}
		}
		private function handleUnloadCurrentSlideshow(e:SlideshowsEvent):void {
			view.mainview.appholder.dispatchEvent(new SlideshowsEvent(SlideshowsEvent.UNLOAD_CURRENT_SLIDESHOW));
			if (view.secondWindow != null) { 
				eventMap.unmapListener(view.secondWindow, ControlBarEvent.TOGGLE_WINDOW_ORDER, handleToggleWindowOrder);
				view.secondWindow.close();
				view.secondWindow = null;
			}
		}
		private function handleLoginMessageEvent(e:LoginEvent):void {
			this.isLoggedIn = (e.type == LoginEvent.LOGIN_SUCCESSFUL);
			view.mainview.appholder.topbar.status.source = (this.isLoggedIn) ? view.mainview.appholder.topbar.connected : view.mainview.appholder.topbar.disconnected;
			if (view.secondWindow != null) {
				view.secondWindow.appholder.topbar.status.source = (this.isLoggedIn) ? view.secondWindow.appholder.topbar.connected : view.secondWindow.appholder.topbar.disconnected;				
			}
			if (e.type == LoginEvent.LOGIN_SUCCESSFUL) {
				view.mainview.appholder.appmenu.status.text = "Logged in as: " + e.user.username + ".";
				NativeApplication.nativeApplication.addEventListener(Event.USER_IDLE, onIdle);
				NativeApplication.nativeApplication.addEventListener(Event.USER_PRESENT, onPresent);
				userPresentOffset = 0;
				keepAliveTimer.start();
			} else if (e.type == LoginEvent.LOGOUT) {
				view.mainview.appholder.appmenu.status.text = "Not logged in.";
				NativeApplication.nativeApplication.removeEventListener(Event.USER_IDLE, onIdle);
				NativeApplication.nativeApplication.removeEventListener(Event.USER_PRESENT, onPresent);
				keepAliveTimer.stop();
			}
		}
		private function handleLoadSelectedSlideshowSuccess(e:SlideshowsEvent):void {
			view.mainview.appholder.appmenu.visible = false;
			view.mainview.appholder.dispatchEvent(new SlideshowsEvent(SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_SUCCESSFUL));
			view.titlesSubmenu.@version = (parseInt(view.titlesSubmenu.@version) + 1).toString();
			view.titlesSubmenu.setChildren(new XMLList());
			for(var i:int=0; i < this.slideshow.cacheService.thumbFilePaths.length; i++) {
				var node:XML = <menuitem id="" label="" menutype="submenu" enabled="true"/>
				node.@id = i.toString();
				node.@label = (i+1).toString() + ". " + truncate(this.slideshow.cacheService.thumbFilePaths.getItemAt(i).title, 65, " …");
				view.titlesSubmenu.appendChild(node);
			}
			var menu:XML = view.mainview.appholder.singlepane.imageHolder.menuData;
			menu.menuitem.(@id=='goto').setChildren(new XMLList());
			for(i=0; i < view.titlesSubmenu.children().length(); i++) {
				menu.menuitem.(@id=='goto').appendChild(view.titlesSubmenu.children()[i]);
			}
			menu.menuitem.(@id=='goto').@submenuversion = view.titlesSubmenu.@version;
			menu.menuitem.(@id=='goto').@enabled = true;
		}
		private function handleApplicationClosing(e:Event):void {
			if (view.secondWindow != null && !view.secondWindow.closed) {
				e.preventDefault();
				Alert.yesLabel = "Quit";
				Alert.show("Two MediaViewer windows are open. Are you sure you want to close both windows?", "Exit MediaViewer?", Alert.YES|Alert.CANCEL, view, alertQuitClickHandler);
			}
		}
		private function alertQuitClickHandler(e:CloseEvent):void {
			if (e.detail == Alert.YES) {
				eventMap.unmapListener(view, Event.CLOSING, handleApplicationClosing);
				if (view.secondWindow != null && !view.secondWindow.closed) {
					view.secondWindow.close();
				}
				view.close();
			}
		}
		private function handleSecondWindowComplete(e:Event):void {
			view.secondWindow.appholder.singlepane.imageHolder.addEventListener(FlexEvent.CREATION_COMPLETE, handleSecondWindowMediatorsReady);
			view.secondWindow.appholder.topbar.addEventListener(FlexEvent.CREATION_COMPLETE, handleTopbarReady);
			eventMap.mapListener(view.secondWindow, ControlBarEvent.TOGGLE_WINDOW_ORDER, handleToggleWindowOrder);
		}
		private function handleTopbarReady(e:FlexEvent):void {
			view.secondWindow.appholder.topbar.removeEventListener(FlexEvent.CREATION_COMPLETE, handleTopbarReady);
			view.secondWindow.appholder.topbar.status.source = (view.mainview.appholder.topbar.status.source == view.mainview.appholder.topbar.connected) ? view.secondWindow.appholder.topbar.connected : view.secondWindow.appholder.topbar.disconnected;				
			view.secondWindow.appholder.topbar.info.enabled = true;
			view.secondWindow.appholder.controlbar.initProgressBar(slideshow.numSlides, view.mainview.appholder.controlbar.progressArray);
			topBarReadyDelay.reset();
			topBarReadyDelay.start();
		}
		private function updateTopBarTitles(e:TimerEvent):void {
			this.topBarReadyDelay.stop();
			view.secondWindow.appholder.dispatchEvent(new TopBarEvent(TopBarEvent.SECOND_WINDOW_TOPBAR_IS_READY, SlideshowCursor.SECOND_WINDOW, SlideshowCursor.FIRST_PANE));
		}
		private function handleSecondWindowMediatorsReady(e:Event):void {
			slideshow.cursor.setCursor(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.FIRST_PANE, -1);
			var navEvent:NavigationEvent = new NavigationEvent(NavigationEvent.GOTO_X);
			navEvent.targetWindow = SlideshowCursor.SECOND_WINDOW;
			navEvent.targetPane = SlideshowCursor.FIRST_PANE;
			navEvent.targetPosition = slideshow.getCurrentPosition(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.FIRST_PANE);
			dispatchToModules(navEvent);
			view.secondWindow.appholder.controlbar.initSecondWindowControls(navEvent.targetPosition, slideshow.numSlides);
			view.secondWindow.appholder.appmenu.visible = false;
			view.secondWindow.appholder.singlepane.imageHolder.removeEventListener(FlexEvent.CREATION_COMPLETE, handleSecondWindowMediatorsReady);
		}
		private function handleSecondWindowClosing(e:Event):void {
			view.secondWindow.context.dispose();
		}
		private function handleOpenSecondWindow(e:MouseEvent):void {
			if (view.secondWindow == null || view.secondWindow.closed) {
				view.secondWindow = new SecondWindow();
				view.secondWindow.mdidSupportURL = view.mdidSupportURL;
				view.secondWindow.context = new SecondContext(view.secondWindow, this.parentContextIInjector);
				view.secondWindow.addEventListener(AIREvent.WINDOW_COMPLETE, handleSecondWindowComplete);
				view.secondWindow.addEventListener(Event.CLOSING, handleSecondWindowClosing);
				view.secondWindow.isSmoothBitmap = view.isSmoothBitmap
				view.secondWindow.open();
				view.secondWindow.appholder.handleResize();
			}
			//view.secondWindow.orderToFront();
		}
		private var userPresentOffset:int;
		private function handleKeepAlive(e:TimerEvent):void {
			
			if (view.mainview.appholder.controlbar.isPlaying) {
				userPresentOffset = NativeApplication.nativeApplication.timeSinceLastUserInput;
			} else if (view.secondWindow != null && !view.secondWindow.closed && view.secondWindow.appholder.controlbar.isPlaying) {
				userPresentOffset = NativeApplication.nativeApplication.timeSinceLastUserInput;
			}
			var timeSinceLastUserInputAdjusted:int = NativeApplication.nativeApplication.timeSinceLastUserInput - userPresentOffset;
			if (this.isLoggedIn && timeSinceLastUserInputAdjusted > 60*60) { //no user input for last 60 minutes
				if (this.loginwindowPopup != null) handleCloseLoginWindowPopup();
				if (this.slideshowlistPopup != null) handleCloseSlideshowlistPopup();
				dispatch(new LoginEvent(LoginEvent.LOGOUT, this.loginModel.user, "Your session has expired due to lack of activity within last 30 minutes."));
				Mouse.show();
			} else if (this.isLoggedIn) {
				dispatch(new LoginEvent(LoginEvent.KEEP_SESSION_ALIVE));
			}
		}
		private function onIdle(e:Event):void {
			if (isMouseShowing && !this.isLoginWindowPopped && !this.isSlideshowListWindowPopped) {
				if (CursorManager.currentCursorID == CursorManager.NO_CURSOR) {
					Mouse.hide();	
				} else {
					CursorManager.hideCursor();
				}
				if (view.secondWindow != null && !view.secondWindow.closed) {
					if (view.secondWindow.cursorManager.currentCursorID == CursorManager.NO_CURSOR) {
						Mouse.hide();
					} else {
						view.secondWindow.cursorManager.hideCursor();
					}
				}
				isMouseShowing = false;
			}
		}
		private function onPresent(e:Event):void {
			if (!isMouseShowing) {
				if (CursorManager.currentCursorID == CursorManager.NO_CURSOR) {
					Mouse.show();	
				} else {
					CursorManager.showCursor();
				}
				if (view.secondWindow != null && !view.secondWindow.closed) {
					if (view.secondWindow.cursorManager.currentCursorID == CursorManager.NO_CURSOR) {
						Mouse.show();
					} else {
						view.secondWindow.cursorManager.showCursor();
					}
				}
				isMouseShowing = true;
			}
		}
		private function handleLoginWindowPopupAdd(e:Event = null):void {
			eventMap.mapListener(loginwindowPopup, StateChangeEvent.CURRENT_STATE_CHANGE, handleLoginWindowStateChange);
			eventMap.mapListener(loginwindowPopup, CloseEvent.CLOSE, handleCloseLoginWindowPopup);
			view.addEventListener(ResizeEvent.RESIZE, recenterLoginWindow);
			mediatorMap.createMediator(loginwindowPopup);
			PopUpManager.addPopUp(loginwindowPopup, view, true);
			this.isLoginWindowPopped = true;
			PopUpManager.centerPopUp(loginwindowPopup);
			if (this.isLoggedIn) loginwindowPopup.currentState = "loggedin";
		}
		private function recenterLoginWindow(e:ResizeEvent):void {
			PopUpManager.centerPopUp(loginwindowPopup);
		}
		private function handleSlideshowPopupAdd(e:Event = null):void {
			eventMap.mapListener(slideshowlistPopup, StateChangeEvent.CURRENT_STATE_CHANGE, handleSlideshowlistWindowStateChange);
			eventMap.mapListener(slideshowlistPopup, CloseEvent.CLOSE, handleCloseSlideshowlistPopup);
			view.addEventListener(ResizeEvent.RESIZE, recenterSlideshowlistPopup);
			mediatorMap.createMediator(slideshowlistPopup);
			PopUpManager.addPopUp(slideshowlistPopup, view, true);
			this.isSlideshowListWindowPopped = true;
			PopUpManager.centerPopUp(slideshowlistPopup);
		}
		private function recenterSlideshowlistPopup(e:ResizeEvent):void {
			PopUpManager.centerPopUp(slideshowlistPopup);
		}
		private function handleCloseLoginWindowPopup(e:CloseEvent = null):void {
			eventMap.unmapListener(loginwindowPopup, StateChangeEvent.CURRENT_STATE_CHANGE, handleLoginWindowStateChange);
			eventMap.unmapListener(loginwindowPopup, CloseEvent.CLOSE, handleCloseLoginWindowPopup);
			view.removeEventListener(ResizeEvent.RESIZE, recenterLoginWindow);
			PopUpManager.removePopUp(loginwindowPopup);
			this.isLoginWindowPopped = false;
			mediatorMap.removeMediatorByView(loginwindowPopup);
			view.focusManager.setFocus(view.mainview.appholder.dummyFocusHolder);
		}
		private function handleCloseSlideshowlistPopup(e:CloseEvent = null):void {
			eventMap.unmapListener(slideshowlistPopup, StateChangeEvent.CURRENT_STATE_CHANGE, handleSlideshowlistWindowStateChange);
			eventMap.unmapListener(slideshowlistPopup, CloseEvent.CLOSE, handleCloseSlideshowlistPopup);
			view.removeEventListener(ResizeEvent.RESIZE, recenterSlideshowlistPopup);
			PopUpManager.removePopUp(slideshowlistPopup);
			this.isSlideshowListWindowPopped = false;
			mediatorMap.removeMediatorByView(slideshowlistPopup);
			view.focusManager.setFocus(view.mainview.appholder.dummyFocusHolder);
		}
		private function handleLoginWindowStateChange(e:StateChangeEvent):void {
			PopUpManager.centerPopUp(loginwindowPopup);
		}
		private function handleSlideshowlistWindowStateChange(e:StateChangeEvent):void {
			PopUpManager.centerPopUp(slideshowlistPopup);
		}
		private function truncate(str:String, numChars:uint, symbol:String = "..." ):String {
			// Don't do anything if the string is shorter than the maximum value.
			if (str.length <= numChars) return str;
			// Search backwards for a space in the string, starting with
			// the character position that was requested.
			var charPosition:uint = numChars-1;
			
			while (str.charAt(charPosition) != " " && charPosition != 0) {
				charPosition--;
			}
			var truncateAt:uint = charPosition == 0 ? numChars : charPosition;
			
			// If the space is right before a punctuation mark, crop the
			// punctuation mark also (or else it looks weird.)
			var charBefore:String = str.charAt(truncateAt-1);
			if (charBefore == ":" || charBefore == ";" || charBefore == "." || charBefore == ",") {
				truncateAt--;
			}
			
			// Truncate the string
			var newString:String = str.substr(0, truncateAt);
			newString += symbol;
			
			// Return the truncated string
			return newString;
		}
	}
}