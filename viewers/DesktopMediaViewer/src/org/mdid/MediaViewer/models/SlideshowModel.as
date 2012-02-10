package org.mdid.MediaViewer.models
{
	import org.mdid.MediaViewer.events.CacheEvent;
	import org.mdid.MediaViewer.events.NavigationEvent;
	import org.mdid.MediaViewer.events.SlideshowCursorChangeEvent;
	import org.mdid.MediaViewer.models.vo.Slideshow;
	import org.mdid.MediaViewer.models.vo.SlideshowCursor;
	import org.mdid.MediaViewer.services.ICachingService;
	import org.mdid.MediaViewer.services.constants.Caching;
	import org.robotlegs.utilities.modular.mvcs.ModuleActor;
	
	public class SlideshowModel extends ModuleActor
	{
		[Inject]
		public var cacheService:ICachingService;
		
		[Inject]
		public var cursor:SlideshowCursor;
		
		[Embed(source='/assets/skins/skin.swf', symbol='SlideshowUnavailable')]
		private var slideshowUnavailable:Class;
		
		private var _currentShow:Slideshow;
		
		public function get numSlides():int {
			return _currentShow == null ? -1 : _currentShow.numSlides;
		}
		public function set currentShow(show:Slideshow):void {
			_currentShow = show;
			cursor.setCursor(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.FIRST_PANE, (numSlides>0) ? 0 : -1);
			cursor.setCursor(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.SECOND_PANE, (numSlides>1) ? 1 : cursor.getCursor(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.FIRST_PANE));
			cursor.setCursor(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.FIRST_PANE, (numSlides>0) ? 0 : -1);
			cursor.setCursor(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.SECOND_PANE, (numSlides>1) ? 1 : cursor.getCursor(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.FIRST_PANE));
			dispatchSlideshowCursorChangeEvent(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.FIRST_PANE, cursor.getCursor(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.FIRST_PANE), numSlides);
			dispatchSlideshowCursorChangeEvent(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.SECOND_PANE, cursor.getCursor(SlideshowCursor.MAIN_WINDOW, SlideshowCursor.FIRST_PANE), numSlides);
			dispatchSlideshowCursorChangeEvent(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.FIRST_PANE, cursor.getCursor(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.FIRST_PANE), numSlides);
			dispatchSlideshowCursorChangeEvent(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.SECOND_PANE, cursor.getCursor(SlideshowCursor.SECOND_WINDOW, SlideshowCursor.FIRST_PANE), numSlides);
		}
		public function unloadCurrentShow():void {
			cursor.initialize();
			_currentShow = null;
			cacheService.unloadCurrentImageList();
		}
		public function get currentShow():Slideshow {
			return _currentShow;
		}
		public function getSlideIdIndex(slideid:String):int {
			return _currentShow.idLookupList.getItemIndex(slideid);
		}
		public function getSlideIdDuplicates(slideid:String):Array {
			var idIndices:Array = new Array();
			for(var i:int = 0; i < _currentShow.idLookupList.length; i++) {
				if (_currentShow.idLookupList.getItemAt(i) == slideid) {
					idIndices.push(i);
				}
			}
			return idIndices;
		}
		public function getCurrentPosition(winname:String, panename:String):int {
			return cursor.getCursor(winname, panename);
		}
		public function setCurrentPosition(pos:int, winname:String, panename:String):void {
			cursor.setCursor(winname, panename, pos);
		}
		public function getCurrentImageCacheStatus(winname:String, panename:String):String {
			if (cursor.getCursor(winname, panename) >= 0 && cursor.getCursor(winname, panename) < numSlides && currentShow != null) {
				return cacheService.getImageStatus(currentShow.slides.getItemAt(cursor.getCursor(winname, panename)).id);
			} else {
				return Caching.FILE_STATUS_UNKNOWN;
			}
		}
		public function getCurrentImageID(winname:String, panename:String):String {
			if (cursor.getCursor(winname, panename) >= 0 && cursor.getCursor(winname, panename) < numSlides && currentShow != null) {
				return currentShow.slides.getItemAt(cursor.getCursor(winname, panename)).id;
			} else {
				return "";
			}
		}
		public function getCurrentImageURL(winname:String, panename:String):String {
			if (cursor.getCursor(winname, panename) >= 0 && cursor.getCursor(winname, panename) < numSlides && currentShow != null) {
				return cacheService.getImagePath(currentShow.slides.getItemAt(cursor.getCursor(winname, panename)).id);
			} else {
				return "";
			}
		}
		public function getCurrentImage(winname:String, panename:String):Object {
			if (currentShow != null && cursor.getCursor(winname, panename) >= 0 && cursor.getCursor(winname, panename) < numSlides) {
				return cacheService.fetchImage(currentShow.slides.getItemAt(cursor.getCursor(winname, panename)).id);
			} else {
				return slideshowUnavailable;
			}
		}
		public function getPairedCursor(winname:String):int {
			var pairedCursor:int = cursor.getCursor(winname, SlideshowCursor.FIRST_PANE) + 1;
			if (pairedCursor > numSlides -1) pairedCursor = numSlides - 1;
			return pairedCursor;
		}
		public function navigateTo(winname:String, panename:String, navType:String, newPos:int = -1):Object {
			var newCursor:int = cursor.getCursor(winname, panename);
			var oldCursor:int = newCursor;
			switch (navType) {
				case NavigationEvent.FIRST :
					if (newCursor > 0 && numSlides > 0) {
						newCursor = 0;
					} else {
						return null;
					}
					break;
				case NavigationEvent.PREVIOUS :
					if (newCursor > 0 && numSlides > 0) {
						newCursor--;
					} else {
						return null;
					}
					break;
				case NavigationEvent.LAST :
					if (newCursor < numSlides - 1) {
						newCursor = numSlides - 1;
					} else {
						return null;
					}
					break;
				case NavigationEvent.NEXT :
					if (newCursor < numSlides - 1) {
						newCursor++;
					} else {
						return null;
					}
					break;
				case NavigationEvent.GOTO_X :
					if (newPos < 0 || newPos > numSlides - 1) return null;
					newCursor = newPos;
					break;
			}
			if (oldCursor == newCursor) return null;
			cursor.setCursor(winname, panename, newCursor);
			dispatchSlideshowCursorChangeEvent(winname, panename, cursor.getCursor(winname, panename), numSlides);
			var status:String = cacheService.getImageStatus(currentShow.slides.getItemAt(cursor.getCursor(winname, panename)).id);
			if (status == CacheEvent.ITEM_CACHED) {
				return getCurrentImageURL(winname, panename);
			} else {
				return getCurrentImage(winname, panename);
			}
		}
		
		private function dispatchSlideshowCursorChangeEvent(winname:String, panename:String, pos:int, numslides:int):void {
			var cursEvent:SlideshowCursorChangeEvent = new SlideshowCursorChangeEvent(SlideshowCursorChangeEvent.POSITION_CHANGED);
			cursEvent.targetWindow = winname;
			cursEvent.targetPane = panename;
			cursEvent.newPosition = pos;
			cursEvent.numPositions = numslides;
			dispatchToModules(cursEvent);
		}
		
		public function SlideshowModel(){}
	}
}