package org.mdid.MediaViewer.views.mediators
{
	import com.adobe.protocols.dict.util.CompleteResponseEvent;
	import com.adobe.wheelerstreet.fig.panzoom.events.PanZoomEvent;
	
	import flash.desktop.NativeApplication;
	import flash.display.NativeMenu;
	import flash.display.Stage;
	import flash.events.Event;
	import flash.events.MouseEvent;
	import flash.events.NativeWindowDisplayStateEvent;
	import flash.geom.Point;
	import flash.net.URLRequest;
	import flash.net.navigateToURL;
	import flash.ui.Mouse;
	
	import flashx.textLayout.conversion.TextConverter;
	
	import flex.utils.spark.resize.ResizeManager;
	
	import mx.binding.utils.BindingUtils;
	import mx.controls.LinkButton;
	import mx.events.CloseEvent;
	import mx.events.FlexEvent;
	import mx.events.FlexNativeMenuEvent;
	import mx.events.ResizeEvent;
	import mx.managers.PopUpManager;
	
	import org.mdid.MediaViewer.ParentContext;
	import org.mdid.MediaViewer.events.CacheEvent;
	import org.mdid.MediaViewer.events.ControlBarEvent;
	import org.mdid.MediaViewer.events.EdgeEvent;
	import org.mdid.MediaViewer.events.NavigationEvent;
	import org.mdid.MediaViewer.events.RightClickMenuEvent;
	import org.mdid.MediaViewer.events.SlideshowCursorChangeEvent;
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.models.vo.SlideshowCursor;
	import org.mdid.MediaViewer.services.constants.Caching;
	import org.mdid.MediaViewer.views.components.CatalogWindow;
	import org.mdid.MediaViewer.views.components.ImageHolder;
	import org.robotlegs.mvcs.Mediator;
	import org.robotlegs.utilities.modular.mvcs.ModuleMediator;
	
	import spark.components.Application;
	import spark.components.CheckBox;
	
	public class ImageHolderMediator extends ModuleMediator {
		
		[Inject]
		public var view:ImageHolder;		
		
		[Inject]
		public var slideShow:SlideshowModel;
		
		[Inject(name="windowname")]
		public var windowName:String;
		
		private var catalogWindowPopup:CatalogWindow;
		private var _catWindowIsPopped:Boolean;
		private var catWindowIsFirstPop:Boolean = true;
		private var whichPane:String;
		
		private function get catWindowIsPopped():Boolean {
			return _catWindowIsPopped;
		}
		private function set catWindowIsPopped(val:Boolean):void {
			_catWindowIsPopped = val;
			view.isCatalogWindowVisible = val;
		}
		
		public function ImageHolderMediator() {
			super();
		}
		override public function onRegister():void {
			whichPane = (view.id.toLocaleLowerCase() == "imageholder") ? SlideshowCursor.FIRST_PANE : SlideshowCursor.SECOND_PANE;
			trace("register: " + whichPane);
			//view.theWindowName = (this.windowName == "theMainWindow") ? "mainview" : "secondWindow";
			catalogWindowPopup = new CatalogWindow();
			catWindowIsPopped = false;
			addModuleListener(CacheEvent.ITEM_CACHED, handleItemCached);
			addModuleListener(CacheEvent.ITEM_DOWNLOAD_FAILED, handleItemDownloadFailed);
			eventMap.mapListener(view.edges, EdgeEvent.FIRST, handleEdgeEvent);
			eventMap.mapListener(view.edges, EdgeEvent.PREVIOUS, handleEdgeEvent);
			eventMap.mapListener(view.edges, EdgeEvent.LAST, handleEdgeEvent);
			eventMap.mapListener(view.edges, EdgeEvent.NEXT, handleEdgeEvent);
			eventMap.mapListener(view.edges, EdgeEvent.ZOOMIN, handleZoomFromEdgeEvent);
			eventMap.mapListener(view.edges, EdgeEvent.ZOOMINMAX, handleZoomFromEdgeEvent);
			eventMap.mapListener(view.edges, EdgeEvent.ZOOMOUT, handleZoomFromEdgeEvent);
			eventMap.mapListener(view.edges, EdgeEvent.ZOOMOUTMAX, handleZoomFromEdgeEvent);
			eventMap.mapListener(view.imageViewer, EdgeEvent.TOGGLE_CATALOG_DATA_DISPLAY, handleToggleCatalogDataDisplay);
			eventMap.mapListener(view.imageViewer, PanZoomEvent.IMAGE_RESIZED, handleImageResizeEvent);
			eventMap.mapListener(catalogWindowPopup, CloseEvent.CLOSE, handleToggleCatalogDataDisplay);
			addModuleListener(NavigationEvent.UNLOAD_ALL_SLIDES, handleUnloadImageEvent);
			addModuleListener(NavigationEvent.NEXT, handleNavigationEvent);
			addModuleListener(NavigationEvent.PREVIOUS, handleNavigationEvent);
			addModuleListener(NavigationEvent.LAST, handleNavigationEvent);
			addModuleListener(NavigationEvent.FIRST, handleNavigationEvent);
			addModuleListener(NavigationEvent.GOTO_X, handleNavigationEvent);
			addModuleListener(SlideshowCursorChangeEvent.POSITION_CHANGED, handlePositionChangeEvent);
			addModuleListener(ControlBarEvent.MOVE_WINDOW_TO_TOPLEFT, handleMoveCatalogWindowTopLeft);
			addModuleListener(ControlBarEvent.HIDE_CATALOGDATA_WINDOW, handleShowHideCatalogWindow);
			addModuleListener(ControlBarEvent.SHOW_CATALOGDATA_WINDOW, handleShowHideCatalogWindow);
			eventMap.mapListener(view.rightClickMenu, FlexNativeMenuEvent.ITEM_CLICK, handleRightMenuClick);
			eventMap.mapListener(view, RightClickMenuEvent.IMAGE_IS_HIDDEN, handleRightClickMenuEvent);
			eventMap.mapListener(view, RightClickMenuEvent.IMAGE_IS_VISIBLE, handleRightClickMenuEvent);
			if (whichPane == SlideshowCursor.SECOND_PANE) {
				moduleDispatcher.dispatchEvent(new ControlBarEvent(ControlBarEvent.SECOND_PANE_IS_REGISTERED, windowName, whichPane));
			}
			if (slideShow.getCurrentImageCacheStatus(windowName, whichPane) == Caching.IN_CACHE) {
				view.setCurrentState("imageincache");
				view.imageViewer.imageURL = slideShow.getCurrentImageURL(windowName, whichPane);
			} else {
				view.setCurrentState("imagenotcached");
				view.bitmap.source = slideShow.getCurrentImage(windowName, whichPane);
			}
		}
		private function handleSmoothBitmapChangeEvent(e:Event):void {
			//trace(e.currentTarget);
		}
		private function handleRightClickMenuEvent(e:RightClickMenuEvent):void {
			if (e.type == RightClickMenuEvent.IMAGE_IS_VISIBLE || e.type == RightClickMenuEvent.IMAGE_IS_HIDDEN) {
				view.menuData.menuitem.(@id == 'show_hide_image').@label = (e.type == RightClickMenuEvent.IMAGE_IS_VISIBLE) ? view.menuData.menuitem.(@id == 'show_hide_image').@hideText : view.menuData.menuitem.(@id == 'show_hide_image').@showText;
			}
		}
		private function handleRightMenuClick(e:FlexNativeMenuEvent):void {
			var item:XML = XML(e.item)
			switch (item.@id.toString()) {
				case "first":
					handleEdgeEvent(new EdgeEvent(EdgeEvent.FIRST));
					break;
				case "previous":
					handleEdgeEvent(new EdgeEvent(EdgeEvent.PREVIOUS));
					break;
				case "next":
					handleEdgeEvent(new EdgeEvent(EdgeEvent.NEXT));
					break;
				case "last":
					handleEdgeEvent(new EdgeEvent(EdgeEvent.LAST));
					break;
				case "resize_image":
					view.imageViewer.zoomTo(1);
					break;
				case "reposition_image" :
					view.imageViewer.zoomToCenterView();
					break;
				case "show_hide_image" :
					var shiEventType:String = (item.@label == item.@hideText) ? RightClickMenuEvent.HIDE_IMAGE : RightClickMenuEvent.SHOW_IMAGE;
					dispatchToModules(new RightClickMenuEvent(shiEventType, this.windowName, this.whichPane));
					break;
				case "show_hide_catalog_data" :
					var cbEventType:String = (item.@label == item.@hideText) ? ControlBarEvent.HIDE_CATALOGDATA_WINDOW : ControlBarEvent.SHOW_CATALOGDATA_WINDOW;
					dispatchToModules(new ControlBarEvent(cbEventType, this.windowName, this.whichPane));
					break;
				case "split_1" :
					var s1EventType:String = (item.@label == item.@splitHText) ? RightClickMenuEvent.SPLIT_DISPLAY_HORIZONTALLY : RightClickMenuEvent.UNSPLIT_DISPLAY;
					dispatchToModules(new RightClickMenuEvent(s1EventType, this.windowName, this.whichPane));
					break;
				case "split_2" :
					var s2EventType:String = (item.@label == item.@splitVText) ? RightClickMenuEvent.SPLIT_DISPLAY_VERTICALLY : RightClickMenuEvent.SPLIT_DISPLAY_HORIZONTALLY;
					dispatchToModules(new RightClickMenuEvent(s2EventType, this.windowName, this.whichPane));	
					break;
				case "fullscreen" :
					dispatchToModules(new RightClickMenuEvent(RightClickMenuEvent.TOGGLE_FULLSCREEN, this.windowName, this.whichPane));
				case "goto_mdid_support_url" :
					if (view.parentApplication.mdidSupportURL == null) return;
					navigateToURL(new URLRequest(view.parentApplication.mdidSupportURL));
					break;
				default :
					if (item.@menutype == "submenu") {
						var ne:NavigationEvent = new NavigationEvent(NavigationEvent.GOTO_X);
						ne.targetWindow = this.windowName;
						ne.targetPane = this.whichPane;
						ne.targetPosition = parseInt(item.@id);
						moduleDispatcher.dispatchEvent(ne);
					}
					break;
			}			
		}
		private function handleUnloadImageEvent(e:NavigationEvent):void {
			if (this._catWindowIsPopped) handleToggleCatalogDataDisplay();
			view.currentState = "imagenotcached";
			view.bitmap.source = slideShow.getCurrentImage(windowName, whichPane);
			view.edges.topEdge.zoomin.source = view.edges.topEdge.zoominVestige;
			view.edges.bottomEdge.zoomout.source = view.edges.bottomEdge.zoomoutVestige;
			view.edges.leftEdge.previous.source = view.edges.leftEdge.previousVestige;
			view.edges.rightEdge.next.source = view.edges.rightEdge.nextVestige;
		}
		private function handleMoveCatalogWindowTopLeft(e:ControlBarEvent):void {
			if (!catWindowIsPopped) return;
			catalogWindowPopup.positionAtTopLeft();
			catalogWindowPopup.fitToContainer();
		}
		private function handleShowHideCatalogWindow(e:ControlBarEvent):void {
			if (e.targetWindow != windowName || e.targetPane != whichPane) return;
			if (catWindowIsPopped && e.type == ControlBarEvent.HIDE_CATALOGDATA_WINDOW || !catWindowIsPopped && e.type == ControlBarEvent.SHOW_CATALOGDATA_WINDOW) {
				handleToggleCatalogDataDisplay();
			}
		}
		private function handlePositionChangeEvent(e:SlideshowCursorChangeEvent):void {
			if (catWindowIsPopped && e.targetWindow == windowName && e.targetPane == whichPane) {
				catalogWindowPopup.title = "Slide " + (e.newPosition + 1).toString() + " of " + e.numPositions;
			}
		}
		private function handleToggleCatalogDataDisplay(e:Event = null):void {
			if (catWindowIsPopped) { //Close it
				view.removeEventListener(ResizeEvent.RESIZE, handleViewResize);
				PopUpManager.removePopUp(catalogWindowPopup);
			} else { //Open it
				PopUpManager.addPopUp(catalogWindowPopup, view, false);
				view.addEventListener(ResizeEvent.RESIZE, handleViewResize);
				catalogWindowPopup.catalogWindowContainer = view;
				catalogWindowPopup.title = "Slide " + (slideShow.cursor.getCursor(windowName, whichPane) + 1).toString() + " of " + slideShow.numSlides;
				catalogWindowPopup.dataHolder.textFlow = TextConverter.importToFlow(slideShow.currentShow.formattedCatalogData[slideShow.cursor.getCursor(windowName, whichPane)], TextConverter.TEXT_FIELD_HTML_FORMAT);
				if (catWindowIsFirstPop) {
					catWindowIsFirstPop = false;
					catalogWindowPopup.positionAtTopLeft();
				}
				catalogWindowPopup.fitToContainer();
			}
			catWindowIsPopped = !catWindowIsPopped;
			view.menuData.menuitem.(@id=='show_hide_catalog_data').@label = catWindowIsPopped ? view.menuData.menuitem.(@id=='show_hide_catalog_data').@hideText : view.menuData.menuitem.(@id=='show_hide_catalog_data').@showText;

		}
		private function handleViewResize(e:ResizeEvent):void {
			catalogWindowPopup.fitToContainer();
		}
		private function handleZoomFromEdgeEvent(e:EdgeEvent):void {
			switch (e.type) {
				case EdgeEvent.ZOOMIN :
					view.imageViewer.zoom("in", false);
					break;
				case EdgeEvent.ZOOMINMAX :
					view.imageViewer.zoom("in", true);
					break;
				case EdgeEvent.ZOOMOUT :
					view.imageViewer.zoom("out", false);
					break;
				case EdgeEvent.ZOOMOUTMAX :
					view.imageViewer.zoom("out", true);
					break;
			}
		}
		private function handleImageResizeEvent(e:PanZoomEvent):void {
			if (view.imageViewer.bitmapScaleFactor + .01 >= view.imageViewer.bitmapScaleFactorMax) {
				view.edges.topEdge.zoomin.source = view.edges.topEdge.zoominVestige;
			} else {
				view.edges.topEdge.zoomin.source = view.edges.topEdge.zoominUpOver;
			}
			if (view.imageViewer.bitmapScaleFactor - .01 <= view.imageViewer.bitmapScaleFactorMin) {
				view.edges.bottomEdge.zoomout.source = view.edges.bottomEdge.zoomoutVestige;
			} else {
				view.edges.bottomEdge.zoomout.source = view.edges.bottomEdge.zoomoutUpOver;
			}
		}
		private function gotoSlide(navType:String, newPos:int = -1):void {
			trace("gotoSlide: " + navType);
			var slide:Object = slideShow.navigateTo(windowName, whichPane, navType, newPos);
			if (slide == null) return;
			if (slide is String) {
				view.setCurrentState("imageincache");
				view.imageViewer.imageURL = slideShow.getCurrentImageURL(windowName, whichPane);
				//trace(view.imageViewer.imageURL);
				if (catWindowIsPopped) {
					catalogWindowPopup.dataHolder.textFlow = TextConverter.importToFlow(slideShow.currentShow.formattedCatalogData[slideShow.cursor.getCursor(windowName, whichPane)], TextConverter.TEXT_FIELD_HTML_FORMAT);
				}
			} else if (slide is Class) {
				view.setCurrentState("imagenotcached");
				view.bitmap.source = slideShow.getCurrentImage(windowName, whichPane);
			}
		}
		private function dispatchNavigationEvent(navType:String, whichPane:String, targetPosition:int = -1):void {
			var navEvent:NavigationEvent = new NavigationEvent(navType);
			navEvent.targetPosition = targetPosition;
			navEvent.targetWindow = windowName;
			navEvent.targetPane = whichPane;
			moduleDispatcher.dispatchEvent(navEvent);
		}
		private function handleEdgeEvent(e:EdgeEvent):void {
			var navEvent:NavigationEvent = new NavigationEvent(e.type);
			navEvent.targetWindow = windowName;
			navEvent.targetPane = whichPane;
			dispatchToModules(navEvent);
		}
		private function handleNavigationEvent(e:NavigationEvent):void {
			if (e.targetWindow == windowName && e.targetPane == whichPane) gotoSlide(e.type, e.targetPosition);
		}
		private function handleItemCached(e:CacheEvent):void {
			if (e.slideid == slideShow.getCurrentImageID(windowName, whichPane)) {
				if (view.currentState != "imageincache") {
					view.setCurrentState("imageincache");
				}
				view.imageViewer.imageURL = slideShow.getCurrentImageURL(windowName, whichPane);
			}
		}
		private function handleItemDownloadFailed(e:CacheEvent):void {
			if (e.slideid == slideShow.getCurrentImageID(windowName, whichPane)) {
				if (view.currentState != "imagenotcached") {
					view.setCurrentState("imagenotcached");
				}
				view.bitmap.source = slideShow.getCurrentImage(windowName, whichPane);
			}
		}
	}
}