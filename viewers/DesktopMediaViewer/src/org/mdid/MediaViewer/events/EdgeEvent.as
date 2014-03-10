package org.mdid.MediaViewer.events
{
	import flash.events.Event;
	
	public class EdgeEvent extends Event
	{
		public static const FIRST:String = "gotoFirstSlideEvent";
		public static const NEXT:String = "gotoNextSlideEvent";
		public static const LAST:String = "gotoLastSlideEvent";
		public static const PREVIOUS:String = "gotoPreviousSlideEvent";
		public static const ZOOMIN:String = "zoomInEvent";
		public static const ZOOMINMAX:String = "zoomInMaxEvent";
		public static const ZOOMOUT:String = "zoomOutEvent";
		public static const ZOOMOUTMAX:String = "zoomOutMaxEvent";
		public static const TOGGLE_CATALOG_DATA_DISPLAY:String = "toggleCatalogDataDisplayEvent";

		public function EdgeEvent(type:String)
		{
			super(type, false, false);
		}
		override public function clone():Event
		{
			return new EdgeEvent(type);
		}
	}
}