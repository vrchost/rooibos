package org.mdid.MediaViewer.services
{
	import avmplus.INCLUDE_ACCESSORS;
	
	import com.adobe.air.preferences.Preference;
	import com.adobe.net.DynamicURLLoader;
	
	import flash.errors.IOError;
	import flash.events.DataEvent;
	import flash.events.Event;
	import flash.events.FileListEvent;
	import flash.events.IOErrorEvent;
	import flash.events.ProgressEvent;
	import flash.filesystem.File;
	import flash.filesystem.FileMode;
	import flash.filesystem.FileStream;
	import flash.net.URLLoaderDataFormat;
	import flash.net.URLRequest;
	import flash.system.Capabilities;
	import flash.utils.ByteArray;
	import flash.utils.Dictionary;
	
	import mx.collections.ArrayCollection;
	import mx.collections.ArrayList;
	
	import org.as3commons.collections.SortedMap;
	import org.as3commons.collections.framework.IIterator;
	import org.as3commons.collections.utils.NumericComparator;
	import org.mdid.MediaViewer.events.CacheEvent;
	import org.mdid.MediaViewer.models.LoginModel;
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.services.constants.Caching;
	import org.robotlegs.mvcs.Actor;
	import org.robotlegs.utilities.modular.mvcs.ModuleActor;
	
	public class CachingService extends ModuleActor implements ICachingService {
		
		[Inject]
		public var prefs:Preference;
		
		[Inject]
		public var loginModel:LoginModel;
		
		[Embed(source='/assets/skins/skin.swf', symbol='ImageInDownloadQueue')]
		[Bindable]
		private var imageInDownloadQueue:Class;
		
		[Embed(source='/assets/skins/skin.swf', symbol='ImageIsBeingDownloaded')]
		[Bindable]
		private var imageIsBeingDownloaded:Class;
		
		[Embed(source='/assets/skins/skin.swf', symbol='MissingImage')]
		[Bindable]
		private var missingImage:Class;
		
		[Embed(source='/assets/skins/skin.swf', symbol='EmptySlideshow')]
		[Bindable]
		private var emptySlideshow:Class;
		
		public static const NUM_BYTES_IN_GIG:Number = 1073741824;
		public static const MAX_CACHE_SIZE_IN_GIGS:Number = 15;
		public static const MIN_AVAIL_FREE_SPACE_IN_GIGS:Number = 3;
		//Approximately five months; remove from cache any file that has not be accessed in last five months
		public static const MAX_STALE_IN_DAYS:Number = 30 * 5;
		public static const NUM_MS_IN_ONE_DAY:Number = 1000 * 60 * 60 * 24;
		public static const MAX_STALE_IN_MS:Number = MAX_STALE_IN_DAYS * NUM_MS_IN_ONE_DAY;
		
		private var thumbDict:Dictionary;
		private var imageDict:Dictionary;
		private var thumbQueue:ArrayList;
		private var imageQueue:ArrayList;
		private var _thumbFilePaths:ArrayList;
		private var numberFullImageUrlLoaders:int = 2;
		private var isCleanCachePending:Boolean;
		private var cachedFilesList:SortedMap;
		private var cachedUserDirectoriesList:Array;
		
		public function get thumbFilePaths():ArrayList {
			return _thumbFilePaths;
		}
		
		public function get isThumbCachingComplete():Boolean {
			return thumbQueue.length < 1;
		}
		
		public function getImagePath(id:String):String {
			var val:String = (loginModel.isLoggedIn && imageDict != null && imageDict[id].status != null && imageDict[id].status == Caching.IN_CACHE) ? getUserStorageDir().nativePath + File.separator + id : "";
			if (val.length > 0 && flash.system.Capabilities.os.indexOf("Mac OS") > -1) val = "file://" + val;
			return val;
		}
		public function fetchEmptySlideshowImage():Object {
			return emptySlideshow;
		}
		public function getImageStatus(id:String):String {
			if (imageDict[id] == null) return Caching.FILE_STATUS_UNKNOWN;
			return imageDict[id].status;
		}
		public function fetchImagePath(id:String):String {
			return (imageDict[id].status == Caching.IN_CACHE) ? getImagePath(id) : "";
		}
		public function fetchImage(id:String):Object {
			switch (imageDict[id].status) {
				case Caching.IN_CACHE :
					return getImagePath(id);
					break;
				case Caching.IN_DOWNLOAD_QUEUE :
					return imageInDownloadQueue;
					break;
				case Caching.IS_DOWNLOADING :
					return imageIsBeingDownloaded;
					break;
				case Caching.DOWNLOAD_FAILED :
				default :
					return missingImage;
			}
		}
		public function fetchThumbnail(id:String):String {
			if (thumbDict[id].status == Caching.IN_CACHE) {
				var val:String = getUserStorageDir().nativePath + File.separator + loginModel.user.userid + File.separator + "thumb_" + id;
				if (val.length > 0 && flash.system.Capabilities.os.indexOf("Mac OS") > -1) val = "file://" + val;
				return val;
			} else {
				return thumbDict[id].thumburl;
			}
		}
		public function unloadCurrentImageList():void {
			thumbDict = null;
			imageDict = null;
			if (thumbQueue != null) thumbQueue.removeAll();
			if (_thumbFilePaths != null) _thumbFilePaths.removeAll();
			if (imageQueue != null) imageQueue.removeAll();
		}
		public function getStorageDir():File {
			//TODO: Check prefs file first; if storageDirectory not null and points to valid directory, use that instead of appstordir
			var dir:File = File.applicationStorageDirectory;
			if (!dir.exists) {
				dir.createDirectory();
			}
			return dir;
		}
		public function getUserStorageDir():File {
			if (!loginModel.isLoggedIn) return null;
			var dir:File = getStorageDir().resolvePath(loginModel.user.userid);
			if (!dir.exists) {
				dir.createDirectory();
			}
			return dir;
		}
		public function preCacheImages(theSlides:ArrayCollection):void {
			var userDir:File = getUserStorageDir();
			imageDict = new Dictionary();
			imageQueue = new ArrayList();
			for each(var slide:Object in theSlides) {
				var obj:Object = new Object();
				if (userDir.resolvePath(slide.id.toString()).exists) {
					obj.status = Caching.IN_CACHE;
					imageDict[slide.id] = obj;
					dispatchToModules(new CacheEvent(CacheEvent.ITEM_CACHED, slide.id.toString(), 1));
				} else {
					obj.status = Caching.IN_DOWNLOAD_QUEUE;
					obj.imageurl = slide.image;
					imageDict[slide.id] = obj;
					if (imageQueue.getItemIndex(slide.id) < 0) {
						imageQueue.addItem(slide.id);
					}
				}
			}
			//TODO: Check prefs for numLoaders value; use that instead of numberFullImageUrlLoaders
			for(var i:int = 0; i < numberFullImageUrlLoaders; i++) {
				cacheNextImage();
			}
			isCleanCachePending = true;
		}
		public function preCacheImageThumbnails(theSlides:ArrayCollection):void {
			var userDir:File = getUserStorageDir();
			thumbDict = new Dictionary();
			thumbQueue = new ArrayList();
			_thumbFilePaths = new ArrayList();
			for each(var slide:Object in theSlides) {
				var obj:Object = new Object();
				var val:String = getUserStorageDir().nativePath + File.separator + "thumb_" + slide.id.toString()
				if (val.length > 0 && flash.system.Capabilities.os.indexOf("Mac OS") > -1) val = "file://" + val;
				_thumbFilePaths.addItem({source: val,title: slide.title});
				if (userDir.resolvePath("thumb_" + slide.id.toString()).exists) {
					obj.status = Caching.IN_CACHE;
					thumbDict[slide.id] = obj;
				} else {
					obj.status = Caching.IN_DOWNLOAD_QUEUE;
					obj.thumburl = slide.thumbnail;
					thumbDict[slide.id] = obj;
					thumbQueue.addItem(slide.id);
				}
			}
			cacheNextThumb();
		}
		protected function get baseURL():String {
			if (!prefs.isLatestDataLoaded) prefs.load();
			var value:String = prefs.getValue("mdid_url");
			if (value == null || value.length < 1) return "";
			if (value.charAt(value.length - 1) != "/") value += "/";
			return value;
		}
		private var cacheSizeInBytes:Number;
		protected function cleanCache():void {
			var f:File = getStorageDir();
			cachedFilesList = new SortedMap(new NumericComparator());
			cacheSizeInBytes = 0;
			var tempArr:Array = f.getDirectoryListing();
			cachedUserDirectoriesList = new Array();
			for (var i:int = 0; i < tempArr.length; i++) {
				if (tempArr[i].isDirectory) cachedUserDirectoriesList.push(tempArr[i]);
			}
			if (cachedUserDirectoriesList.length > 0) {
				var d:File = cachedUserDirectoriesList.pop();
				d.addEventListener(FileListEvent.DIRECTORY_LISTING, dirListingHandler);
				d.getDirectoryListingAsync();
			}
		}
		private function dirListingHandler(e:FileListEvent):void {
			for each(var f:File in e.files) {
				if (!f.isDirectory) {
					var now:Date = new Date();
					//remove stale files
					if (now.getTime() - f.modificationDate.getTime() > MAX_STALE_IN_MS) {
						f.deleteFile();
						break;
					}
					cacheSizeInBytes += f.size;
					//keep fresh files (that is, don't add them to cachedFileList) -- accessed less than 12 hours ago
					if (now.getTime() - f.modificationDate.getTime() > NUM_MS_IN_ONE_DAY / 2) {
						cachedFilesList.add(f, f.modificationDate.getTime());						
					}
				}
			}
			e.target.removeEventListener(FileListEvent.DIRECTORY_LISTING, dirListingHandler);
			if (cachedUserDirectoriesList.length > 0) {
				var d:File = cachedUserDirectoriesList.pop();
				d.addEventListener(FileListEvent.DIRECTORY_LISTING, dirListingHandler);
				d.getDirectoryListingAsync();
				d.modificationDate
			} else {
				var spaceAvailInGigs:Number = getStorageDir().spaceAvailable / 1024 / 1024 / 1024;
				var cacheSizeInGigs:Number = cacheSizeInBytes / 1024 / 1024 / 1024;
				if (cacheSizeInGigs < MAX_CACHE_SIZE_IN_GIGS && spaceAvailInGigs > MIN_AVAIL_FREE_SPACE_IN_GIGS) {
					cachedFilesList = null;
					return;	
				}
				var fArray:Array = cachedFilesList.keysToArray();
				var curFSz:Number = 0;
				for each(var f2:File in fArray) {
					//don't trash images accessed within past 12 hours;
					curFSz = f2.size;
					try {
						f2.deleteFile();
					} catch(e:Error) {
						break;
					}
					cacheSizeInBytes -= curFSz;
					spaceAvailInGigs = getStorageDir().spaceAvailable / 1024 / 1024 / 1024;
					cacheSizeInGigs = cacheSizeInBytes / 1024 / 1024 / 1024;
					//remove an extra .5 gigabytes from cache so we don't go through this loop everytime we load a new slidehsow
					if (cacheSizeInGigs + .5 < MAX_CACHE_SIZE_IN_GIGS && spaceAvailInGigs > MIN_AVAIL_FREE_SPACE_IN_GIGS) {
						cachedFilesList = null;
						return;	
					}					
				}
				cachedFilesList = null;
			}
		}
		private function cacheNextImage():void {
			if (imageQueue.length > 0) {
				var val:String = imageQueue.getItemAt(0).toString();
				imageQueue.removeItemAt(0);
				cacheImage(val);
			} else if (isCleanCachePending) {
				cleanCache();
				isCleanCachePending = false;
			}
		}
		private function cacheNextThumb():void {
			if (thumbQueue.length > 0) {
				var val:String = thumbQueue.getItemAt(0).toString();
				thumbQueue.removeItemAt(0);
				cacheThumb(val);
			}			
		}
		private function cacheImage(id:String):void {
			if (imageDict[id] == null) return;
			var loader:DynamicURLLoader = new DynamicURLLoader();
			loader.slideid = id;
			loader.addEventListener(Event.COMPLETE, onImageDataLoaded);
			//Following two lines bring UI to a crawl during caching
			//this.lastTenthLoaded = -1;
			//loader.addEventListener(ProgressEvent.PROGRESS, onImageProgress);
			//Following XX lines replace prior two lines
			dispatchToModules(new CacheEvent(CacheEvent.ITEM_DOWNLOAD_PROGRESS_UPDATE, loader.slideid, .5));			
			loader.addEventListener(IOErrorEvent.IO_ERROR, onImageLoadError);
			loader.dataFormat = URLLoaderDataFormat.BINARY;
			imageDict[id].status = Caching.IS_DOWNLOADING;
			loader.load(new URLRequest(baseURL + imageDict[id].imageurl + "?" + loginModel.user.sessiontoken));
			//trace(baseURL + imageDict[id].imageurl + "?" + loginModel.user.sessiontoken)
			dispatch(new CacheEvent(CacheEvent.ITEM_DOWNLOAD_STARTED, id, 0));
		}
		private function cacheThumb(id:String):void {
			if (thumbDict[id] == null) return;
			var loader:DynamicURLLoader = new DynamicURLLoader();
			loader.slideid = id;
			loader.addEventListener(Event.COMPLETE, onThumbDataLoaded);
			loader.addEventListener(IOErrorEvent.IO_ERROR, onThumbLoadError);
			loader.dataFormat = URLLoaderDataFormat.BINARY;
			thumbDict[id].status = Caching.IS_DOWNLOADING;
			loader.load(new URLRequest(baseURL + thumbDict[id].thumburl + "?" + loginModel.user.sessiontoken));
		}
		private function onImageLoadError(e:IOErrorEvent):void {
			var loader:DynamicURLLoader = DynamicURLLoader(e.target);		
			var slideid:String = String(loader.slideid);
			if (imageDict[slideid] == null) return;
			trace("onImageLoadError: " + e.errorID + " (slide url=" + baseURL + imageDict[slideid].imageurl + "?" + loginModel.user.sessiontoken + ")");
			imageDict[slideid].status = Caching.DOWNLOAD_FAILED;
			dispatch(new CacheEvent(CacheEvent.ITEM_DOWNLOAD_FAILED, slideid, 0));
			cacheNextImage();
		}
		private function onThumbLoadError(e:IOErrorEvent):void {
			var loader:DynamicURLLoader = DynamicURLLoader(e.target);		
			var slideid:String = String(loader.slideid);
			if (thumbDict[slideid] == null) return;
			trace("onThumbLoadError: " + e.errorID);
			thumbDict[slideid].status = Caching.DOWNLOAD_FAILED;
			//TODO: Dispatch event here (cacheing attempt failed for slideid)
			cacheNextThumb();
		}
		private function onImageDataLoaded(e:Event):void {
			var loader:DynamicURLLoader = DynamicURLLoader(e.target);		
			//loader.removeEventListener(ProgressEvent.PROGRESS, onImageProgress);
			var slideid:String = String(loader.slideid);
			var f:File = new File(getUserStorageDir().nativePath + File.separator + slideid);
			var fileStream:FileStream = new FileStream();
			fileStream.open(f, FileMode.WRITE);
			fileStream.writeBytes(loader.data as ByteArray);
			fileStream.close();
			//if (imageDict[slideid] == null) return;
			imageDict[slideid].status = Caching.IN_CACHE;
			dispatchToModules(new CacheEvent(CacheEvent.ITEM_CACHED, slideid, 1));
			cacheNextImage();
			//trace("image: " + loader.bytesTotal);
		}
		private function onThumbDataLoaded(e:Event):void {
			var loader:DynamicURLLoader = DynamicURLLoader(e.target);		
			var slideid:String = String(loader.slideid);
			var f:File = new File(getUserStorageDir().nativePath + File.separator + "thumb_" + slideid);
			var fileStream:FileStream = new FileStream();
			fileStream.open(f, FileMode.WRITE);
			fileStream.writeBytes(loader.data as ByteArray);
			fileStream.close();
			if (thumbDict[slideid] == null) return;
			thumbDict[slideid].status = Caching.IN_CACHE;
			cacheNextThumb();
		}
		private var lastTenthLoaded:int = -1;
		private function onImageProgress(e:ProgressEvent):void {
			var loader:DynamicURLLoader = DynamicURLLoader(e.target);
			if (loader.bytesTotal <= 0) return;
			var whichTenth:int = Math.round(10*loader.bytesLoaded/loader.bytesTotal);
			if (whichTenth == lastTenthLoaded) return;
			lastTenthLoaded = whichTenth;
			var slideid:String = String(loader.slideid);
			if (imageDict[slideid] == null) return;
			if (loader.bytesTotal > 0) {
				dispatchToModules(new CacheEvent(CacheEvent.ITEM_DOWNLOAD_PROGRESS_UPDATE, slideid, loader.bytesLoaded/loader.bytesTotal));
			}
		}
	}
}