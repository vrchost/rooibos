package com.adobe.wheelerstreet.fig.panzoom.events
{
	import flash.events.Event;

	public class LoadCompleteEvent extends Event
	{
		public static const LOAD_COMPLETE:String = "commandComplete";
		
		public function LoadCompleteEvent(type:String)
		{
			super(type, true, false);
		}
		
	}
}