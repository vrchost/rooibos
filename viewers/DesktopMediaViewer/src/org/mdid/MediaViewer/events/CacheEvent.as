package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class CacheEvent extends Event {
		public static const ITEM_CACHED:String = "itemCachedEvent";
		public static const ITEM_QUEUED_FOR_DOWNLOAD:String = "itemQueuedForDownloadEvent";
		public static const ITEM_DOWNLOAD_STARTED:String = "itemDownloadStartedEvent";
		public static const ITEM_DOWNLOAD_PROGRESS_UPDATE:String = "itemDownloadProgressUpdateEvent";
		public static const ITEM_DOWNLOAD_FAILED:String = "itemDownloadFailedEvent";
		
		private var _slideid:String;
		private var _percentDownloaded:Number;
		
		public function get slideid():String {
			return _slideid;
		}
		public function get percentDownloaded():Number {
			return _percentDownloaded;
		}

		public function CacheEvent(type:String, slideId:String, percentDownloaded:Number = 0, bubbles:Boolean=false, cancelable:Boolean=false) {
			_slideid = slideId;
			_percentDownloaded = percentDownloaded;
			super(type, false, false);
		}
		override public function clone():Event {
			return new CacheEvent(type, _slideid, _percentDownloaded);
		}
	}
}