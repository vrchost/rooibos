package org.mdid.MediaViewer.views.mediators
{
	
	import com.rialvalue.layouts.CoverflowLayout;
	import com.rictus.reflector.Reflector;
	
	import flash.display.DisplayObject;
	import flash.display.NativeWindow;
	import flash.display.StageDisplayState;
	import flash.events.Event;
	import flash.events.FullScreenEvent;
	import flash.events.KeyboardEvent;
	import flash.events.MouseEvent;
	import flash.events.NativeWindowDisplayStateEvent;
	import flash.events.TimerEvent;
	import flash.ui.Mouse;
	import flash.utils.Timer;
	
	import flashx.textLayout.events.UpdateCompleteEvent;
	import flashx.textLayout.formats.Direction;
	
	import mx.charts.HitData;
	import mx.containers.BoxDirection;
	import mx.containers.DividedBox;
	import mx.controls.LinkButton;
	import mx.core.Application;
	import mx.core.FlexGlobals;
	import mx.core.IVisualElement;
	import mx.events.DividerEvent;
	import mx.events.EffectEvent;
	import mx.events.FlexEvent;
	import mx.events.ResizeEvent;
	import mx.events.SliderEvent;
	import mx.events.StateChangeEvent;
	import mx.managers.SystemManager;
	
	import org.mdid.MediaViewer.events.CacheEvent;
	import org.mdid.MediaViewer.events.ControlBarEvent;
	import org.mdid.MediaViewer.events.EdgeEvent;
	import org.mdid.MediaViewer.events.KeyboardUpEvent;
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.events.NavigationEvent;
	import org.mdid.MediaViewer.events.RightClickMenuEvent;
	import org.mdid.MediaViewer.events.SlideshowCursorChangeEvent;
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.events.TopBarEvent;
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.models.SlideshowsModel;
	import org.mdid.MediaViewer.models.vo.Slideshow;
	import org.mdid.MediaViewer.models.vo.SlideshowCursor;
	import org.mdid.MediaViewer.views.components.AppHolder;
	import org.mdid.MediaViewer.views.components.CoverFlow;
	import org.robotlegs.utilities.modular.mvcs.ModuleMediator;
	
	public class ControlBarTopBarMediator extends ModuleMediator
	{
		[Inject]
		public var view:AppHolder;
		
		[Inject]
		public var slideShow:SlideshowModel;
		
		[Inject(name="windowname")]
		public var windowName:String;
		
		public static const LIGHT_BLUE:String = "lightBlueColor";
		public static const SALMON:String = "salmonColor";
		private var isProgressBarInitialized:Boolean;
		private var displayRefreshDelay:Timer = new Timer(5, 1);
		private var displayRefreshDelay2:Timer = new Timer(5, 1);
		private var coverFlowList:CoverFlow = new CoverFlow();
		
		public function ControlBarTopBarMediator() {
			super();
		}
		override public function onRegister():void {
			isProgressBarInitialized = (this.windowName == SlideshowCursor.SECOND_WINDOW);
			if (windowName == SlideshowCursor.MAIN_WINDOW) {
				eventMap.mapListener(view.controlbar.menubutton, MouseEvent.CLICK, handleToggleAppMenu);
				view.appmenu.visible = true;
			} else if (windowName == SlideshowCursor.SECOND_WINDOW) {
				view.controlbar.menubutton.enabled = false;
			}
			displayRefreshDelay.addEventListener(TimerEvent.TIMER, moveWindowToTopLeft);
			displayRefreshDelay2.addEventListener(TimerEvent.TIMER, handleInvalidateMainTitleReflector);
			addModuleListener(CacheEvent.ITEM_CACHED, handleProgressBarUpdate);
			addModuleListener(CacheEvent.ITEM_DOWNLOAD_FAILED, handleProgressBarUpdate);
			addModuleListener(CacheEvent.ITEM_DOWNLOAD_PROGRESS_UPDATE, handleProgressBarUpdate);
			addModuleListener(SlideshowCursorChangeEvent.POSITION_CHANGED, handleSlideNavigationChange);
			eventMap.mapListener(view.controlbar.pinbutton, MouseEvent.CLICK, handleToggleControlBarPinning);
			eventMap.mapListener(view.topbar.smallpinbutton, MouseEvent.CLICK, handleToggleTopBarPinning);
			eventMap.mapListener(view.controlbar.previous, MouseEvent.CLICK, handleNavigationEvent);
			eventMap.mapListener(view.controlbar.first, MouseEvent.CLICK, handleNavigationEvent);
			eventMap.mapListener(view.controlbar.next, MouseEvent.CLICK, handleNavigationEvent);
			eventMap.mapListener(view.controlbar.last, MouseEvent.CLICK, handleNavigationEvent);
			eventMap.mapListener(view.controlbar.surfaceHolder, MouseEvent.CLICK, handleProgressBarClickEvent);
			eventMap.mapListener(view.controlbar.scrubBar, SliderEvent.THUMB_RELEASE, handleSliderReleaseEvent);
			eventMap.mapListener(view.controlbar.scrubBar, SliderEvent.THUMB_PRESS, handleSliderPressEvent);
			eventMap.mapListener(view.controlbar.scrubBar, SliderEvent.CHANGE, handleSliderChangeEvent);
			eventMap.mapListener(view.controlbar.blankscreen, MouseEvent.CLICK, handleToggleBlankScreenEvent);
			eventMap.mapListener(view.controlbar.blankscreen, MouseEvent.CLICK, handleToggleBlankScreenEvent);
			addModuleListener(RightClickMenuEvent.HIDE_IMAGE, handleToggleBlankScreenEvent);
			addModuleListener(RightClickMenuEvent.SHOW_IMAGE, handleToggleBlankScreenEvent);
			addModuleListener(RightClickMenuEvent.UNSPLIT_DISPLAY, handleDisplaySplitEvent);
			addModuleListener(RightClickMenuEvent.SPLIT_DISPLAY_HORIZONTALLY, handleDisplaySplitEvent);
			addModuleListener(RightClickMenuEvent.SPLIT_DISPLAY_VERTICALLY, handleDisplaySplitEvent);
			addModuleListener(RightClickMenuEvent.TOGGLE_FULLSCREEN, handleFullScreenToggle);
			addModuleListener(ControlBarEvent.SECOND_PANE_IS_REGISTERED, stateChangeToDoublePane);
			eventMap.mapListener(view.appmenu.closebutton, MouseEvent.CLICK, handleToggleAppMenu);
			eventMap.mapListener(view.rollDownAppMenu, EffectEvent.EFFECT_END, handleRollDownAppMenuEffectEnd);
			eventMap.mapListener(view.controlbar.playTimer, TimerEvent.TIMER, handlePlayNextSlide);
			eventMap.mapListener(eventDispatcher, ControlBarEvent.SHOW_CONTROLBAR, handleShowControlBarEvent);
			eventMap.mapListener(eventDispatcher, TopBarEvent.SHOW_TOPBAR, handleShowTopBarEvent);
			eventMap.mapListener(view.controlbar.singlescreen, MouseEvent.CLICK, handleDisplaySplitEvent);
			eventMap.mapListener(view.controlbar.singleHsplit, MouseEvent.CLICK, handleDisplaySplitEvent);
			eventMap.mapListener(view.controlbar.singleVsplit, MouseEvent.CLICK, handleDisplaySplitEvent);
			eventMap.mapListener(view.controlbar.paneControl, MouseEvent.CLICK, handlePaneControlToggle);
			eventMap.mapListener(view.controlbar.pairwiseLinker, MouseEvent.CLICK, handlePairWiseLinkerToggle);
			eventMap.mapListener(view.topbar.info, MouseEvent.CLICK, handleToggleCatalogWindow);
			eventMap.mapListener(view.topbar.fullscreen, MouseEvent.CLICK, handleFullScreenToggle);
			eventMap.mapListener(view.systemManager.stage, FullScreenEvent.FULL_SCREEN, handleFullScreenEvent);
			eventMap.mapListener(view.stage, KeyboardEvent.KEY_DOWN, handleKeyboardPressEvent);
			eventMap.mapListener(view, SlideshowsEvent.UNLOAD_CURRENT_SLIDESHOW, handleUnloadCurrentSlideshowEvent);
			eventMap.mapListener(view, SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_SUCCESSFUL, handleLoadCurrentSlideshowEvent);
			eventMap.mapListener(view, TopBarEvent.SECOND_WINDOW_TOPBAR_IS_READY, handleSecondWindowTopbarIsReady);
			eventMap.mapListener(view.controlbar.dualmonitors, MouseEvent.CLICK, handleToggleWindowOrder);
		}
		private function handleLoadCurrentSlideshowEvent(e:SlideshowsEvent):void {
			if (slideShow.currentShow != null && slideShow.currentShow.numSlides < 1) {
				if (view.currentState == "singlePane") {
					view.singlepane.imageHolder.bitmap.source = slideShow.cacheService.fetchEmptySlideshowImage();
				} else {
					view.doublepane.imageHolder.bitmap.source = slideShow.cacheService.fetchEmptySlideshowImage();					
					view.doublepane.imageHolder2.bitmap.source = slideShow.cacheService.fetchEmptySlideshowImage();					
				}
			}
		}
		private function handleToggleWindowOrder(e:MouseEvent=null):void {
			view.parentApplication.dispatchEvent(new ControlBarEvent(ControlBarEvent.TOGGLE_WINDOW_ORDER, this.windowName, SlideshowCursor.FIRST_PANE));
		}
		private function handleUnloadCurrentSlideshowEvent(e:SlideshowsEvent):void {
			this.coverFlowList = new CoverFlow();
			//unload menudata goto slide children here
			if (view.currentState != "singlePane") {
				this.handleDisplaySplit(view.controlbar.singlescreen);
			} else {
				//view.singlepane.imageHolder.bitmap.source = first image will appear here...
			}
			if (view.controlbar.isPlaying) view.controlbar.stopSlideshow();
			view.topbar.XofY.text = "";
			view.topbar.XofYReflector.invalidateDisplayList();
			view.topbar.slideshowTitle.text = "";
			view.topbar.slideTitle.text = "";
			view.topbar.hideShowTitle.visible = false;
			view.topbar.hideShowTitle.includeInLayout = false;
			view.topbar.mainTitleReflector.invalidateDisplayList();
			view.topbar.info.enabled = false;
			isProgressBarInitialized = false;
			view.controlbar.initProgressBar(0);
			view.controlbar.dualmonitors.enabled = false;
			view.controlbar.singleHsplit.enabled = false;
			view.controlbar.singleVsplit.enabled = false;
			view.controlbar.singlescreen.enabled = false;
			view.controlbar.blankscreen.enabled = false;
			view.controlbar.previous.enabled = false;
			view.controlbar.first.enabled = false;
			view.controlbar.next.enabled = false;
			view.controlbar.last.enabled = false;
			view.controlbar.play.enabled = false;
			moduleDispatcher.dispatchEvent(new NavigationEvent(NavigationEvent.UNLOAD_ALL_SLIDES));
		}
		private function handleFullScreenEvent(e:FullScreenEvent):void {
			view.topbar.fullscreen.styleName = (view.systemManager.stage.displayState == StageDisplayState.FULL_SCREEN_INTERACTIVE) ? "ExitFullscreen" : "Fullscreen";
			view.topbar.fullscreen_refl.invalidateDisplayList();
			
		}
		private function handleKeyboardPressEvent(e:KeyboardEvent):void {
			if (!this.isProgressBarInitialized || view.parentApplication.systemManager.numModalWindows > 0) return;
			//trace(e.charCode);
			switch (e.keyCode) {
				//* indicates that control is available in web browser full-screen mode
				//  (other controls are disabled...this is a flash player security feature)
				case 9 : //*tab -- toggle main window/companion window window order
					view.focusManager.setFocus(view.dummyFocusHolder);
					handleToggleWindowOrder();
					break;
				case 32 : //*space -- toggle scrubbar pane association
					if (view.currentState == "doublePane") {
						view.focusManager.setFocus(view.dummyFocusHolder);
						handlePaneControlToggle();
					}
					break;
				case 38 : //*up arrow -- enlarge image
					if (view.currentState == "singlePane") {
						view.singlepane.imageHolder.edges.dispatchEvent(new EdgeEvent(e.shiftKey ? EdgeEvent.ZOOMINMAX : EdgeEvent.ZOOMIN));
					} else {
						if (view.controlbar.paneUnderControl == SlideshowCursor.FIRST_PANE) {
							view.doublepane.imageHolder.edges.dispatchEvent(new EdgeEvent(e.shiftKey ? EdgeEvent.ZOOMINMAX : EdgeEvent.ZOOMIN));
						} else {
							view.doublepane.imageHolder2.edges.dispatchEvent(new EdgeEvent(e.shiftKey ? EdgeEvent.ZOOMINMAX : EdgeEvent.ZOOMIN));
						}
					}
					break;
				case 40 : //*down arrow -- shrink image
					if (view.currentState == "singlePane") {
						view.singlepane.imageHolder.edges.dispatchEvent(new EdgeEvent(e.shiftKey ? EdgeEvent.ZOOMOUTMAX : EdgeEvent.ZOOMOUT));
					} else {
						if (view.controlbar.paneUnderControl == SlideshowCursor.FIRST_PANE) {
							view.doublepane.imageHolder.edges.dispatchEvent(new EdgeEvent(e.shiftKey ? EdgeEvent.ZOOMOUTMAX : EdgeEvent.ZOOMOUT));
						} else {
							view.doublepane.imageHolder2.edges.dispatchEvent(new EdgeEvent(e.shiftKey ? EdgeEvent.ZOOMOUTMAX : EdgeEvent.ZOOMOUT));
						}
					}
					break;
				case 66 : //b -- toggle controlbar pinning
					var bEvent:MouseEvent = new MouseEvent(MouseEvent.CLICK);
					bEvent.shiftKey = e.shiftKey;
					handleToggleControlBarPinning(bEvent, true);
					break;
				case 70 : //f -- toggle fullscreen mode
					handleFullScreenToggle();
					break;
				case 72 : //h -- toggle hide images
					handleToggleBlankScreenEvent();
					break;
				case 73 : //i
					handleToggleCatalogWindow();
					break;
				case 77 : //m -- minimize window
					view.stage.nativeWindow.minimize();
					break;
				case 80 : //p -- pin/unpin both windows at the same time
					var topEvent:MouseEvent = new MouseEvent(MouseEvent.CLICK);
					topEvent.shiftKey = false;
					var bottomEvent:MouseEvent = new MouseEvent(MouseEvent.CLICK);
					bottomEvent.shiftKey = false;
					if (view.topbar.smallpinbutton.styleName == "SmallPinButton" || view.controlbar.pinbutton.styleName == "PinButton") { //pin both
						if (view.topbar.smallpinbutton.styleName == "SmallPinButton" ) {
							handleToggleTopBarPinning(topEvent, true);
						}
						if (view.controlbar.pinbutton.styleName == "PinButton") {
							handleToggleControlBarPinning(bottomEvent, true);							
						}
					} else { //unpin both
						if (view.topbar.smallpinbutton.styleName != "SmallPinButton" ) {
							handleToggleTopBarPinning(topEvent, true);
						}
						if (view.controlbar.pinbutton.styleName != "PinButton") {
							handleToggleControlBarPinning(bottomEvent, true);							
						}
					}
					break;
				case 83 : //s -- fit image to screen
					if (view.currentState == "singlePane") {
						view.singlepane.imageHolder.imageViewer.zoomToCenterView();
					} else {
						if (view.controlbar.paneUnderControl == SlideshowCursor.FIRST_PANE) {
							view.doublepane.imageHolder.imageViewer.zoomToCenterView();
						} else {
							view.doublepane.imageHolder2.imageViewer.zoomToCenterView();
						}
					}
					break;
				case 84 : //t -- toggle topbar pinning
					var tEvent:MouseEvent = new MouseEvent(MouseEvent.CLICK);
					tEvent.shiftKey = e.shiftKey;
					handleToggleTopBarPinning(tEvent, true);
					break;
				case 85 : //u -- undo split screen
					if (view.currentState != "singlePane") {
						this.handleDisplaySplit(view.controlbar.singlescreen);
					}
					break;
				case 88 : //x -- split display horizontally (x-axis)
					if (view.currentState == "singlePane" || view.doublepane.direction == BoxDirection.HORIZONTAL) {
						this.handleDisplaySplit(view.controlbar.singleVsplit);
					}
					break;
				case 89 : //y -- split display vertically (y-axis)
					if (view.currentState == "singlePane" || view.doublepane.direction == BoxDirection.VERTICAL) {
						this.handleDisplaySplit(view.controlbar.singleHsplit);
					}
					break;
				case 35 : //end -- go to last slide
					dispatchNavigationEvent(NavigationEvent.FIRST, view.controlbar.paneUnderControl);
					break;
				case 36 : //home -- go to first slide
					dispatchNavigationEvent(NavigationEvent.LAST, view.controlbar.paneUnderControl);
					break;
				case 37 : //*left arrow -- go to previous slide (shift + left = go to first slide? no.)
					dispatchNavigationEvent(e.shiftKey ? NavigationEvent.FIRST : NavigationEvent.PREVIOUS, view.controlbar.paneUnderControl);
					break;
				case 39 : //*right arrow -- go to next slide (shift + left = go to first last? no.)
					dispatchNavigationEvent(e.shiftKey ? NavigationEvent.LAST : NavigationEvent.NEXT, view.controlbar.paneUnderControl);
					break;
			}
		}
		private function handleRollDownAppMenuEffectEnd(e:EffectEvent):void {
			if (view.controlbar.pinbutton.styleName == "PinButton" && !view.controlbar.hitTestPoint(view.stage.mouseX, view.stage.mouseY)) {
				view.controlbarRollOutHandler();
			}
		}
		private function handleToggleAppMenu(e:MouseEvent):void {
			if (this.windowName == SlideshowCursor.SECOND_WINDOW) return;
			view.appmenu.visible = !view.appmenu.visible;
		}
		private function handleFullScreenToggle(e:Event=null):void {
			if (e.type == RightClickMenuEvent.TOGGLE_FULLSCREEN) {
				var rcEvent:RightClickMenuEvent = e as RightClickMenuEvent;
				if (this.windowName != rcEvent.targetWindow) return;
			}
			if (view.systemManager.stage.displayState == StageDisplayState.NORMAL) {
				view.systemManager.stage.displayState = StageDisplayState.FULL_SCREEN_INTERACTIVE;
			} else if (view.systemManager.stage.displayState == StageDisplayState.FULL_SCREEN_INTERACTIVE) {
				view.systemManager.stage.displayState = StageDisplayState.NORMAL;
			}
			if (view.currentState == "singlePane") {
				view.singlepane.imageHolder.imageViewer.centerView();
			} else {
				view.doublepane.imageHolder.imageViewer.centerView();
				view.doublepane.imageHolder2.imageViewer.centerView();					
			}
		}
		private function handleToggleCatalogWindow(e:MouseEvent=null):void {
			if (view.currentState == "singlePane") {
				dispatchToModules(new ControlBarEvent(view.singlepane.imageHolder.isCatalogWindowVisible ? ControlBarEvent.HIDE_CATALOGDATA_WINDOW : ControlBarEvent.SHOW_CATALOGDATA_WINDOW, this.windowName, SlideshowCursor.FIRST_PANE ));
			} else {
				if (view.doublepane.imageHolder.isCatalogWindowVisible || view.doublepane.imageHolder2.isCatalogWindowVisible) {
					dispatchToModules(new ControlBarEvent(ControlBarEvent.HIDE_CATALOGDATA_WINDOW, this.windowName, SlideshowCursor.FIRST_PANE ));
					dispatchToModules(new ControlBarEvent(ControlBarEvent.HIDE_CATALOGDATA_WINDOW, this.windowName, SlideshowCursor.SECOND_PANE ));
				} else {
					dispatchToModules(new ControlBarEvent(ControlBarEvent.SHOW_CATALOGDATA_WINDOW, this.windowName, SlideshowCursor.FIRST_PANE ));
					dispatchToModules(new ControlBarEvent(ControlBarEvent.SHOW_CATALOGDATA_WINDOW, this.windowName, SlideshowCursor.SECOND_PANE ));
				}
			}
		}
		
		private var addedElement:IVisualElement;
		private var cfItemWidth:int = 0;
		private var cfDataProviderUpdateRequired:Boolean = true;
		private function handleSliderPressEvent(e:SliderEvent):void {
			if (this.coverFlowList.dataProvider == null) {
				this.coverFlowList.dataProvider = slideShow.cacheService.thumbFilePaths;
				coverFlowList.x = 0;
				coverFlowList.height = 165 + 5;
				cfItemWidth = 110 + coverFlowList.hLayout.gap;
				cfDataProviderUpdateRequired = !slideShow.cacheService.isThumbCachingComplete;
			} else if (cfDataProviderUpdateRequired) {
				cfDataProviderUpdateRequired = !slideShow.cacheService.isThumbCachingComplete;
				this.coverFlowList.dataProvider = null;
				this.coverFlowList.dataProvider = slideShow.cacheService.thumbFilePaths;
			}
			coverFlowList.y = view.controlbar.y - 155;
			addedElement = view.addElement(coverFlowList);
			coverFlowList.maxWidth = coverFlowList.dataProvider.length * cfItemWidth;
			coverFlowList.scroller.maxWidth = coverFlowList.maxWidth;
			coverFlowList.width = coverFlowList.maxWidth;
			coverFlowList.selectedIndex = e.value - 1;
			coverFlowList.x = (view.width / 2) - (coverFlowList.selectedIndex * cfItemWidth) - 55;
		}
		private function handleSliderChangeEvent(e:SliderEvent):void {
			coverFlowList.selectedIndex = e.value - 1;
			coverFlowList.x = (view.width / 2) - (coverFlowList.selectedIndex * cfItemWidth) - 55;
		}
		private function handleSliderReleaseEvent(e:SliderEvent):void {
			if (this.coverFlowList != null && addedElement != null) {
				view.removeElement(addedElement);
				addedElement = null;
			}
			var position:int = slideShow.getCurrentPosition(this.windowName, view.controlbar.paneUnderControl);
			if (position != e.currentTarget.value - 1) {
				var navType:String = NavigationEvent.GOTO_X;
				dispatchNavigationEvent(navType, view.controlbar.paneUnderControl, e.currentTarget.value - 1);
			}
			view.stage.focus = view.stage;
		}
		private function handlePairWiseLinkerToggle(e:MouseEvent):void {
			if (view.controlbar.isPlaying) view.controlbar.stopSlideshow();
			if (view.controlbar.isInPairwiseMode) {
				view.controlbar.isInPairwiseMode = false;
				view.controlbar.paneControl.enabled = true;
				view.controlbar.pairwiseLinker.styleName = "PairwiseLinked";
			} else {
				view.controlbar.isInPairwiseMode = true;
				view.controlbar.paneControl.enabled = false;
				view.controlbar.pairwiseLinker.styleName = "PairwiseUnlinked";
				if (view.controlbar.paneUnderControl == SlideshowCursor.SECOND_PANE) {
					view.controlbar.paneUnderControl = SlideshowCursor.FIRST_PANE;
					colorizeControlBarControls(LIGHT_BLUE);
				} 
				var navType:String = NavigationEvent.GOTO_X;
				var firstPaneCursor:int = slideShow.getCurrentPosition(windowName, SlideshowCursor.FIRST_PANE);
				dispatchNavigationEvent(navType, SlideshowCursor.FIRST_PANE, firstPaneCursor);
				updatePaneEdgeControls(SlideshowCursor.FIRST_PANE);
			}
		}
		private function colorizeControlBarControls(theColor:String):void {
			if (theColor == SALMON) {
				view.controlbar.paneControl.styleName = "YinYangFlipped";
				view.controlbar.delay.styleName = "salmonColor";
				view.controlbar.first.styleName = "FirstP2";
				view.controlbar.previous.styleName = "PreviousP2";
				view.controlbar.play.styleName = "PlayP2";
				view.controlbar.pause.styleName = "PauseP2";
				view.controlbar.next.styleName = "NextP2";
				view.controlbar.last.styleName = "LastP2";
				view.controlbar.scrubBar.styleName = "ScrubBarSliderRed";
				view.controlbar.firstRect.fill = view.controlbar.capacitySurface.graphicsData[1].geometry[0].fills[1]; 
				view.controlbar.secondRect.fill = view.controlbar.capacitySurface.graphicsData[1].geometry[0].fills[1]; 
			} else if (theColor == LIGHT_BLUE) {
				view.controlbar.paneControl.styleName = "YinYang";
				view.controlbar.delay.styleName = "lightBlue";
				view.controlbar.first.styleName = "First";
				view.controlbar.previous.styleName = "Previous";
				view.controlbar.play.styleName = "Play";
				view.controlbar.pause.styleName = "Pause";
				view.controlbar.next.styleName = "Next";
				view.controlbar.last.styleName = "Last";
				view.controlbar.scrubBar.styleName = "ScrubBarSliderBlue";
				view.controlbar.firstRect.fill = view.controlbar.capacitySurface.graphicsData[1].geometry[0].fills[0]; 
				view.controlbar.secondRect.fill = view.controlbar.capacitySurface.graphicsData[1].geometry[0].fills[0]; 
			}
		}
		private function handlePaneControlToggle(e:MouseEvent = null):void {
			if (view.controlbar.isPlaying) view.controlbar.stopSlideshow();
			if (view.controlbar.paneUnderControl == SlideshowCursor.FIRST_PANE) {
				view.controlbar.paneUnderControl = SlideshowCursor.SECOND_PANE;
				colorizeControlBarControls(SALMON);
			} else {
				view.controlbar.paneUnderControl = SlideshowCursor.FIRST_PANE;
				colorizeControlBarControls(LIGHT_BLUE);
			}
			updatePaneEdgeControls(view.controlbar.paneUnderControl);
			view.controlbar.theReflection.invalidateDisplayList();
		}
		private function stateChangeToDoublePane(e:Event):void {
			initializeSecondPaneImage();
			updatePaneEdgeControls(SlideshowCursor.FIRST_PANE);
			view.doublepane.imageHolder.menuData.menuitem.(@id=='split_1').@label = view.doublepane.imageHolder.menuData.menuitem.(@id=='split_1').@unsplitText;
			view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@label = view.doublepane.direction == BoxDirection.HORIZONTAL ? view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitHText :  view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitVText;
			view.doublepane.imageHolder2.menuData.menuitem.(@id=='split_1').@label = view.doublepane.imageHolder.menuData.menuitem.(@id=='split_1').@unsplitText;
			view.doublepane.imageHolder2.menuData.menuitem.(@id=='split_2').@label = view.doublepane.direction == BoxDirection.HORIZONTAL ? view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitHText :  view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitVText;
		}
		private function handleDisplaySplitEvent(e:Event):void {
			if (e.type == MouseEvent.CLICK) {
				handleDisplaySplit(e.currentTarget as LinkButton);
			}
			var rcEvent:RightClickMenuEvent = e as RightClickMenuEvent;
			if (e.type == RightClickMenuEvent.UNSPLIT_DISPLAY && this.windowName == rcEvent.targetWindow) {
				handleDisplaySplit(view.controlbar.singlescreen);
			} else if (e.type == RightClickMenuEvent.SPLIT_DISPLAY_HORIZONTALLY && this.windowName == rcEvent.targetWindow) {
				handleDisplaySplit(view.controlbar.singleVsplit);
			} else if (e.type == RightClickMenuEvent.SPLIT_DISPLAY_VERTICALLY && this.windowName == rcEvent.targetWindow) {
				handleDisplaySplit(view.controlbar.singleHsplit);
			}
		}
		private function handleDisplaySplit(targetButton:LinkButton):void {
			var splitType:String = targetButton == view.controlbar.singlescreen ? ControlBarEvent.UNSPLIT_DISPLAY : targetButton == view.controlbar.singleHsplit ? ControlBarEvent.SPLIT_DISPLAY_H : ControlBarEvent.SPLIT_DISPLAY_V;
			var haveDispatchedControlBarEvent:Boolean = false;
			if (view.controlbar.isPlaying) view.controlbar.stopSlideshow();
			if (view.currentState == "singlePane") {
				view.singlepane.imageHolder.dispatchEvent(new RightClickMenuEvent(RightClickMenuEvent.IMAGE_IS_VISIBLE, this.windowName));				
			} else {
				view.doublepane.imageHolder.dispatchEvent(new RightClickMenuEvent(RightClickMenuEvent.IMAGE_IS_VISIBLE, this.windowName));
				view.doublepane.imageHolder2.dispatchEvent(new RightClickMenuEvent(RightClickMenuEvent.IMAGE_IS_VISIBLE, this.windowName));
			}
			if (view.currentState == "singlePane" && targetButton != view.controlbar.singlescreen) {
				moduleDispatcher.dispatchEvent(new ControlBarEvent(ControlBarEvent.HIDE_CATALOGDATA_WINDOW, windowName, view.controlbar.paneUnderControl));
				haveDispatchedControlBarEvent = view.controlbar.dispatchEvent(new ControlBarEvent(splitType, windowName, view.controlbar.paneUnderControl));
				eventMap.mapListener(view.doublepane, DividerEvent.DIVIDER_DRAG, handleCenterViewsInDoublePane);
				//eventMap.mapListener(view.doublepane.imageHolder2, FlexEvent.CREATION_COMPLETE, stateChangeToDoublePane);
				updateTopBarStatus("doublePane");
			}
			if (targetButton == view.controlbar.singlescreen) {
				eventMap.unmapListener(view.doublepane, DividerEvent.DIVIDER_DRAG, handleCenterViewsInDoublePane);
				moduleDispatcher.dispatchEvent(new ControlBarEvent(ControlBarEvent.HIDE_CATALOGDATA_WINDOW, windowName, SlideshowCursor.FIRST_PANE));
				moduleDispatcher.dispatchEvent(new ControlBarEvent(ControlBarEvent.HIDE_CATALOGDATA_WINDOW, windowName, SlideshowCursor.SECOND_PANE));
				updateTopBarStatus("singlePane");
			}
			if (!haveDispatchedControlBarEvent) view.controlbar.dispatchEvent(new ControlBarEvent(splitType, windowName, view.controlbar.paneUnderControl));
			if (view.currentState == "doublePane" && targetButton != view.controlbar.singlescreen) {
				eventMap.mapListener(view.doublepane, DividerEvent.DIVIDER_DRAG, handleCenterViewsInDoublePane);
				view.doublepane.imageHolder.menuData.menuitem.(@id=='split_1').@label = view.doublepane.imageHolder.menuData.menuitem.(@id=='split_1').@unsplitText;
				view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@label = view.doublepane.direction == BoxDirection.HORIZONTAL ? view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitHText :  view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitVText;
				view.doublepane.imageHolder2.menuData.menuitem.(@id=='split_1').@label = view.doublepane.imageHolder.menuData.menuitem.(@id=='split_1').@unsplitText;
				view.doublepane.imageHolder2.menuData.menuitem.(@id=='split_2').@label = view.doublepane.direction == BoxDirection.HORIZONTAL ? view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitHText :  view.doublepane.imageHolder.menuData.menuitem.(@id=='split_2').@splitVText;
				displayRefreshDelay.reset();
				displayRefreshDelay.start();
			}
			if (targetButton == view.controlbar.singlescreen && view.controlbar.paneUnderControl != SlideshowCursor.FIRST_PANE) {
				this.handlePaneControlToggle();
			}
			view.controlbar.pairwiseLinker.enabled = (splitType != ControlBarEvent.UNSPLIT_DISPLAY && slideShow.numSlides > 2);
			view.controlbar.isInPairwiseMode = false;
			view.controlbar.paneControl.enabled = view.controlbar.pairwiseLinker.enabled;
			view.controlbar.pairwiseLinker.styleName = "PairwiseLinked";
		}
		private function updatePaneEdgeControls(whichPane:String):void {
			var e:SlideshowCursorChangeEvent = new SlideshowCursorChangeEvent(SlideshowCursorChangeEvent.POSITION_CHANGED);
			e.targetWindow = windowName;
			e.targetPane = whichPane;
			e.newPosition = slideShow.getCurrentPosition(windowName, whichPane);
			e.numPositions = slideShow.numSlides;
			moduleDispatcher.dispatchEvent(e);
		}
		private function initializeSecondPaneImage():void {
			trace("initialize");
			var navEvent:NavigationEvent = new NavigationEvent(NavigationEvent.GOTO_X);
			var firstPaneCursor:int = slideShow.getCurrentPosition(windowName, SlideshowCursor.FIRST_PANE);
			navEvent.targetPosition = firstPaneCursor < slideShow.numSlides - 1 ? firstPaneCursor + 1 : firstPaneCursor;
			navEvent.targetWindow = this.windowName;
			navEvent.targetPane = SlideshowCursor.SECOND_PANE;
			moduleDispatcher.dispatchEvent(navEvent);
			updatePaneEdgeControls(SlideshowCursor.SECOND_PANE);
		}
		private function handleCenterViewsInDoublePane(e:DividerEvent):void {
			view.doublepane.imageHolder.imageViewer.centerView();
			view.doublepane.imageHolder2.imageViewer.centerView();	
		}
		private function moveWindowToTopLeft(e:TimerEvent):void {
			displayRefreshDelay.stop();
			moduleDispatcher.dispatchEvent(new ControlBarEvent(ControlBarEvent.MOVE_WINDOW_TO_TOPLEFT, windowName, view.controlbar.paneUnderControl));
		}
		private function handleShowControlBarEvent(e:ControlBarEvent):void {
			if (view.controlbar.pinbutton.styleName == "PinnedButton") return; //Currently pinned, so abort
			if (view.currentState == "doublePane") {
				if (view.doublepane.direction == BoxDirection.VERTICAL && e.targetPane == SlideshowCursor.FIRST_PANE) return;
				if (view.doublepane.direction == BoxDirection.HORIZONTAL) {
					if (e.targetPane == SlideshowCursor.FIRST_PANE && e.edgeBlock == ControlBarEvent.RIGHT_EDGE_BLOCK) return;
					if (e.targetPane == SlideshowCursor.SECOND_PANE && e.edgeBlock == ControlBarEvent.LEFT_EDGE_BLOCK) return;
				}
			} 
			view.controlbar.dispatchEvent(e);
		}
		private function handleShowTopBarEvent(e:TopBarEvent):void {
			if (view.topbar.smallpinbutton.styleName == "SmallPinnedButton") return; //Currently pinned, so abort
			if (view.currentState == "doublePane") {
				if (view.doublepane.direction == BoxDirection.HORIZONTAL && e.targetPane == SlideshowCursor.FIRST_PANE) return;
				if (view.doublepane.direction == BoxDirection.VERTICAL && e.targetPane == SlideshowCursor.SECOND_PANE) return;
			} 
			view.topbar.dispatchEvent(e);
		}
		private function handlePlayNextSlide(e:TimerEvent):void {
			if (view.controlbar.delayInSeconds - view.controlbar.playTimer.currentCount < 1) {
				view.controlbar.playTimer.reset();
				if (slideShow.getCurrentPosition(windowName, view.controlbar.paneUnderControl) < slideShow.numSlides - 1) {
					view.controlbar.setTimeUntilNext(view.controlbar.delayInSeconds);
					var navType:String = NavigationEvent.NEXT;
					var targetPos:int = -1;
					if (view.controlbar.isInPairwiseMode) {
						targetPos = slideShow.getCurrentPosition(this.windowName, view.controlbar.paneUnderControl) + 2;
						if (targetPos < slideShow.numSlides) {
							navType = NavigationEvent.GOTO_X;
						} else {
							targetPos = -1;
						}
					}
					dispatchNavigationEvent(navType, view.controlbar.paneUnderControl, targetPos)
					view.controlbar.playTimer.start();
				} else {
					view.controlbar.stopSlideshow();
				}
			} else {
				view.controlbar.setTimeUntilNext(view.controlbar.delayInSeconds - view.controlbar.playTimer.currentCount);
			}
		}
		private function handleToggleBlankScreenEvent(e:Event=null):void {
			if (view.currentState == "singlePane") {
				view.singlepane.imageHolder.imageViewer.visible = !view.singlepane.imageHolder.imageViewer.visible;
				view.singlepane.imageHolder.dispatchEvent(new RightClickMenuEvent(view.singlepane.imageHolder.imageViewer.visible ? RightClickMenuEvent.IMAGE_IS_VISIBLE : RightClickMenuEvent.IMAGE_IS_HIDDEN, this.windowName));
				view.controlbar.blankscreen.styleName = (view.singlepane.imageHolder.imageViewer.visible) ? "ScreenBlank" : "ScreenReveal";
			} else if (e == null || e.type == MouseEvent.CLICK) {
				if (view.doublepane.imageHolder.imageViewer.visible || view.doublepane.imageHolder2.imageViewer.visible) {
					view.doublepane.imageHolder.imageViewer.visible = false;
					view.doublepane.imageHolder2.imageViewer.visible = false;
				} else {
					view.doublepane.imageHolder.imageViewer.visible = true;
					view.doublepane.imageHolder2.imageViewer.visible = true;
				}
				view.doublepane.imageHolder.dispatchEvent(new RightClickMenuEvent(view.doublepane.imageHolder.imageViewer.visible ? RightClickMenuEvent.IMAGE_IS_VISIBLE : RightClickMenuEvent.IMAGE_IS_HIDDEN, this.windowName));
				view.doublepane.imageHolder2.dispatchEvent(new RightClickMenuEvent(view.doublepane.imageHolder2.imageViewer.visible ? RightClickMenuEvent.IMAGE_IS_VISIBLE : RightClickMenuEvent.IMAGE_IS_HIDDEN, this.windowName));
				view.controlbar.blankscreen.styleName = (view.doublepane.imageHolder.imageViewer.visible) ? "ScreenBlank" : "ScreenReveal";
			} else {
				var rcEvent:RightClickMenuEvent = e as RightClickMenuEvent;
				if (rcEvent.targetWindow != this.windowName) return;
				if (rcEvent.type == RightClickMenuEvent.HIDE_IMAGE) {
					if (rcEvent.targetPane == SlideshowCursor.FIRST_PANE) {
						view.doublepane.imageHolder.imageViewer.visible = false;
						view.controlbar.blankscreen.styleName = view.doublepane.imageHolder2.imageViewer.visible ? (view.doublepane.direction == BoxDirection.HORIZONTAL ? "ScreenBlankLeftOnly" : "ScreenBlankTopOnly") : "ScreenReveal";
					} else {
						view.doublepane.imageHolder2.imageViewer.visible = false;
						view.controlbar.blankscreen.styleName = view.doublepane.imageHolder.imageViewer.visible ? (view.doublepane.direction == BoxDirection.HORIZONTAL ? "ScreenBlankRightOnly" : "ScreenBlankBottomOnly") : "ScreenReveal";
					}
				} else if (e.type == RightClickMenuEvent.SHOW_IMAGE) {
					if (rcEvent.targetPane == SlideshowCursor.FIRST_PANE) {
						view.doublepane.imageHolder.imageViewer.visible = true;
						view.controlbar.blankscreen.styleName = view.doublepane.imageHolder2.imageViewer.visible ? "ScreenBlank" : (view.doublepane.direction == BoxDirection.HORIZONTAL ? "ScreenBlankRightOnly" : "ScreenBlankBottomOnly");
					} else {
						view.doublepane.imageHolder2.imageViewer.visible = true;
						view.controlbar.blankscreen.styleName = view.doublepane.imageHolder.imageViewer.visible ? "ScreenBlank" : (view.doublepane.direction == BoxDirection.HORIZONTAL ? "ScreenBlankLeftOnly" : "ScreenBlankTopOnly");
					}
				}
				view.doublepane.imageHolder.dispatchEvent(new RightClickMenuEvent(view.doublepane.imageHolder.imageViewer.visible ? RightClickMenuEvent.IMAGE_IS_VISIBLE : RightClickMenuEvent.IMAGE_IS_HIDDEN, this.windowName));
				view.doublepane.imageHolder2.dispatchEvent(new RightClickMenuEvent(view.doublepane.imageHolder2.imageViewer.visible ? RightClickMenuEvent.IMAGE_IS_VISIBLE : RightClickMenuEvent.IMAGE_IS_HIDDEN, this.windowName));
			}
		}
		private function handleProgressBarClickEvent(e:MouseEvent):void {
			if (view.controlbar.capacitySurface.hitTestPoint(e.stageX, e.stageY, false)) {
				var targetSlideIdx:int = Math.floor(e.localX/view.controlbar.divisionWidth);
				if (targetSlideIdx != view.controlbar.scrubBar.value-1) {
					var navType:String = NavigationEvent.GOTO_X;
					dispatchNavigationEvent(navType, view.controlbar.paneUnderControl, targetSlideIdx);
				}
			}			
		}
		private function handleProgressBarUpdate(e:CacheEvent):void {
			if (!isProgressBarInitialized) return;
			switch (e.type) {
				case CacheEvent.ITEM_CACHED :
					var indices:Array = slideShow.getSlideIdDuplicates(e.slideid);
					if (indices.length == 1) {
						view.controlbar.adjustProgressBar(indices[0], 1);
					} else if (indices.length > 1 && view.controlbar.progressArray[indices[1]] < 1) {
						for(var i:int=0; i < indices.length; i++) {
							view.controlbar.adjustProgressBar(indices[i], 1);
						}
					}
					break;
				case CacheEvent.ITEM_DOWNLOAD_FAILED :
					view.controlbar.adjustProgressBar(slideShow.getSlideIdIndex(e.slideid), 0.01);
					break;
				case CacheEvent.ITEM_DOWNLOAD_PROGRESS_UPDATE :
					view.controlbar.adjustProgressBar(slideShow.getSlideIdIndex(e.slideid), e.percentDownloaded);
					break;
			}
			view.controlbar.theReflection.invalidateDisplayList();
		}
		private function handleNavigationEvent(e:MouseEvent):void {
			var navType:String;
			var targetPos:int = -1;
			var cursor:int;
			switch (e.currentTarget["id"]) {
				case "first" :
					navType = NavigationEvent.FIRST;
					break;
				case "previous" :
					navType = NavigationEvent.PREVIOUS;
					if (view.controlbar.isInPairwiseMode) {
						cursor = slideShow.getCurrentPosition(this.windowName, view.controlbar.paneUnderControl) - 2;
						if (cursor > -1) {
							navType = NavigationEvent.GOTO_X;
							targetPos = cursor;
						}
					}
					break;
				case "next" :
					navType = NavigationEvent.NEXT;
					if (view.controlbar.isInPairwiseMode) {
						cursor = slideShow.getCurrentPosition(this.windowName, view.controlbar.paneUnderControl) + 2;
						if (cursor < slideShow.numSlides) {
							navType = NavigationEvent.GOTO_X;
							targetPos = cursor;
						}
					}
					break;
				case "last" :
					navType = NavigationEvent.LAST;
					break;
			}
			dispatchNavigationEvent(navType, view.controlbar.paneUnderControl, targetPos);
		}
		private function dispatchNavigationEvent(navType:String, whichPane:String, targetPosition:int = -1):void {
			trace("navEvent: " + navType);
			var navEvent:NavigationEvent = new NavigationEvent(navType);
			navEvent.targetPosition = targetPosition;
			navEvent.targetWindow = windowName;
			navEvent.targetPane = whichPane;
			moduleDispatcher.dispatchEvent(navEvent);
			if (view.controlbar.isInPairwiseMode) {
				var secondNavEvent:NavigationEvent = new NavigationEvent(NavigationEvent.GOTO_X);
				secondNavEvent.targetWindow = windowName;
				secondNavEvent.targetPane = SlideshowCursor.SECOND_PANE;
				secondNavEvent.targetPosition = slideShow.getPairedCursor(windowName);
				moduleDispatcher.dispatchEvent(secondNavEvent);
			}
		}
		private function handleSlideNavigationChange(e:SlideshowCursorChangeEvent):void {
			if (e.targetWindow != windowName) return;
			if (!isProgressBarInitialized) {
				view.controlbar.initProgressBar(e.numPositions);
				view.controlbar.dualmonitors.enabled = true;
				view.controlbar.singleHsplit.enabled = true;
				view.controlbar.singleVsplit.enabled = true;
				view.controlbar.singlescreen.enabled = false;
				view.controlbar.blankscreen.enabled = true;
				view.topbar.info.enabled = true;
				isProgressBarInitialized = true;
			}
			if (e.targetPane == view.controlbar.paneUnderControl) {
				view.controlbar.previous.enabled = (e.newPosition > 0);
				view.controlbar.first.enabled = view.controlbar.previous.enabled;
				view.controlbar.next.enabled = (e.newPosition < e.numPositions - 1);
				view.controlbar.last.enabled = view.controlbar.next.enabled;
				if (!view.controlbar.last.enabled && view.controlbar.isPlaying) view.controlbar.stopSlideshow();
				view.controlbar.play.enabled = !view.controlbar.isPlaying && view.controlbar.last.enabled;
				view.controlbar.scrubBar.value = e.newPosition + 1;
			}
			var menu:XML;
			if (view.currentState == "singlePane") {
				menu = view.singlepane.imageHolder.menuData;
			} else if (e.targetPane == SlideshowCursor.FIRST_PANE) {
				menu = view.doublepane.imageHolder.menuData;
			} else if (e.targetPane == SlideshowCursor.SECOND_PANE) {
				menu = view.doublepane.imageHolder2.menuData;
			}
			updateRightClickMenu(menu, e.newPosition, e.numPositions);
			updateTopBarStatus(view.currentState);
			view.controlbar.theReflection.invalidateDisplayList();
		}
		private function updateRightClickMenu(menu:XML, position:int, numPositions:int):void {
			if (menu == null) return;
			menu.menuitem.(@id=='first').@enabled = (position > 0);
			menu.menuitem.(@id=='previous').@enabled = (position > 0);
			menu.menuitem.(@id=='next').@enabled = (position < numPositions - 1);
			menu.menuitem.(@id=='last').@enabled = (position < numPositions - 1);
			//menu.menuitem.(@id=='fullscreen').@enabled = true;
			var submenu:XML = FlexGlobals.topLevelApplication.titlesSubmenu;
			if (menu.menuitem.(@id=='goto').@submenuversion != submenu.@version) {
				var children:XMLList = XMLList(menu.menuitem.(@id=='goto')).children();
				var numChildren:int = children.length();
				for(var i:int=0; i < numChildren; i++) {
					delete children[0];
				}
				for(i=0; i < submenu.children().length(); i++) {
					menu.menuitem.(@id=='goto').appendChild(submenu.children()[i]);
				}
				menu.menuitem.(@id=='goto').@submenuversion = submenu.@version;
				menu.menuitem.(@id=='goto').@enabled = true;
			}
			if (menu.menuitem.(@id=='show_hide_image').@enabled == "false") {
				menu.menuitem.(@id=='show_hide_image').@enabled = true;
				menu.menuitem.(@id=='resize_image').@enabled = true;
				menu.menuitem.(@id=='reposition_image').@enabled = true;
				menu.menuitem.(@id=='show_hide_catalog_data').@enabled = true;
				menu.menuitem.(@id=='split_1').@enabled = true;
				menu.menuitem.(@id=='split_2').@enabled = true;
			}
		}
		private function handleSecondWindowTopbarIsReady(e:TopBarEvent):void {
			if (e.targetWindow != SlideshowCursor.SECOND_WINDOW) return;
			var menu:XML;
			var position:int = slideShow.getCurrentPosition(this.windowName, SlideshowCursor.FIRST_PANE);
			var numPositions:int = slideShow.numSlides;
			if (view.currentState == "singlePane") {
				menu = view.singlepane.imageHolder.menuData;
			} else if (e.targetPane == SlideshowCursor.FIRST_PANE) {
				menu = view.doublepane.imageHolder.menuData;
			} else if (e.targetPane == SlideshowCursor.SECOND_PANE) {
				menu = view.doublepane.imageHolder2.menuData;
			}
			updateRightClickMenu(menu, position, numPositions);
			updateTopBarStatus(view.currentState);
		}
		private function updateTopBarStatus(targetState:String):void {
			if (slideShow.currentShow == null) {
				view.topbar.XofY.text = "";
				view.topbar.slideshowTitle.text = "";
				view.topbar.slideTitle.text = "";
				view.topbar.hideShowTitle.visible = false;
				view.topbar.hideShowTitle.includeInLayout = false;
			} else if (slideShow.currentShow.numSlides < 1) {
				view.topbar.XofY.text = "0 of 0";
				view.topbar.slideshowTitle.text = "Selected slideshow (" + slideShow.currentShow.title + ") is empty!";
				view.topbar.slideTitle.text = "";
				view.topbar.hideShowTitle.visible = false;
				view.topbar.hideShowTitle.includeInLayout = false;	
			} else if (targetState == "singlePane") {
				view.topbar.XofY.text = "Slide " + (slideShow.getCurrentPosition(this.windowName, SlideshowCursor.FIRST_PANE) + 1).toString() + " of " + slideShow.numSlides;
				view.topbar.slideshowTitle.text = slideShow.currentShow.title;
				if (view.topbar.hideShowTitle.styleName == "HideTitle") {
					view.topbar.slideshowTitle.text += ":";
				} else {
					view.topbar.slideshowTitle.text += " ";
				}
				view.topbar.hideShowTitle.visible = true;
				view.topbar.hideShowTitle.includeInLayout = true;
				view.topbar.slideTitle.text = " " + slideShow.currentShow.slides[slideShow.getCurrentPosition(this.windowName, SlideshowCursor.FIRST_PANE)].title;
			} else {
				view.topbar.XofY.text = "Slides " + (slideShow.getCurrentPosition(this.windowName, SlideshowCursor.FIRST_PANE) + 1).toString() + ", " + (slideShow.getCurrentPosition(this.windowName, SlideshowCursor.SECOND_PANE) + 1).toString()  + " of " + slideShow.numSlides;
				view.topbar.slideshowTitle.text = slideShow.currentShow.title;
				view.topbar.slideTitle.text = "";
				view.topbar.hideShowTitle.visible = false;
				view.topbar.hideShowTitle.includeInLayout = false;
			}
			this.displayRefreshDelay2.reset();
			this.displayRefreshDelay2.start();
		}
		private function handleInvalidateMainTitleReflector(e:TimerEvent):void {
			this.displayRefreshDelay2.stop();
			view.topbar.mainTitleReflector.invalidateDisplayList();
			view.topbar.XofYReflector.invalidateDisplayList();
		}
		private function handleToggleTopBarPinning(e:MouseEvent, fromKeyboard:Boolean = false):void {
			if (view.topbar.smallpinbutton.styleName == "SmallPinButton") { //Currently unpinned, so pin.
				view.topbar.smallpinbutton.styleName = "SmallPinnedButton";
				view.topbar.includeInLayout = true;
				if (fromKeyboard && !view.moveInFromTop.isPlaying) {
					view.moveInFromTop.play();
				}
				if (e.shiftKey && view.controlbar.pinbutton.styleName == "PinButton") {
					view.controlbar.pinbutton.styleName = "PinnedButton";
					view.controlbar.includeInLayout = true;	
					if (!view.moveInFromBottom.isPlaying) view.moveInFromBottom.play();
				}
			} else { //Currently pinned, so unpin.
				view.topbar.smallpinbutton.styleName = "SmallPinButton";
				view.topbar.includeInLayout = false;
				if (fromKeyboard && !view.moveOutFromTop.isPlaying) {
					view.moveOutFromTop.play();
				}
				if (e.shiftKey && view.controlbar.pinbutton.styleName == "PinnedButton") {
					view.controlbar.pinbutton.styleName = "PinButton";
					view.controlbar.includeInLayout = false;
					if (!view.moveOutFromBottom.isPlaying) view.moveOutFromBottom.play();
				}
			}
		}
		private function handleToggleControlBarPinning(e:MouseEvent, fromKeyboard:Boolean = false):void {
			if (view.controlbar.pinbutton.styleName == "PinButton") { //Currently unpinned, so pin.
				view.controlbar.pinbutton.styleName = "PinnedButton";
				view.controlbar.includeInLayout = true;
				if (fromKeyboard && !view.moveInFromBottom.isPlaying) {
					view.moveInFromBottom.play();
				}
				if (e.shiftKey && view.topbar.smallpinbutton.styleName == "SmallPinButton") {
					view.topbar.smallpinbutton.styleName = "SmallPinnedButton";
					view.topbar.includeInLayout = true;	
					if (!view.moveInFromTop.isPlaying) view.moveInFromTop.play();
				}
			} else { //Currently pinned, so unpin.
				view.controlbar.pinbutton.styleName = "PinButton";
				view.controlbar.includeInLayout = false;
				if (fromKeyboard && !view.moveOutFromBottom.isPlaying) {
					view.moveOutFromBottom.play();
				}
				if (e.shiftKey && view.topbar.smallpinbutton.styleName == "SmallPinnedButton") {
					view.topbar.smallpinbutton.styleName = "SmallPinButton";
					view.topbar.includeInLayout = false;
					if (!view.moveOutFromTop.isPlaying) view.moveOutFromTop.play();
				}
			}
		}
	}
}