package org.mdid.MediaViewer.models
{
	import mx.collections.ArrayCollection;
	import mx.collections.ArrayList;
	import mx.effects.easing.Back;
	
	import org.as3commons.collections.SortedList;
	import org.as3commons.collections.utils.StringComparator;
	import org.mdid.MediaViewer.models.vo.ListItemValueObject;
	import org.mdid.MediaViewer.models.vo.Slideshow;
	import org.robotlegs.mvcs.Actor;
	
	public class SlideshowsModel extends Actor
	{
		private var _slideshows:ArrayCollection;
		private var _sorted:SortedList = new SortedList(new StringComparator());
		
		public function get firstSlideshow():Slideshow {
			if (numSlideshows < 1) return null;
			return _slideshows[0] as Slideshow;
		}
		
		[Bindable]
		public var tags:ArrayCollection = new ArrayCollection();
		
		public function SlideshowsModel() { }
		
		public function get numSlideshows():int {
			return (_slideshows == null) ? 0 : _slideshows.length;
		}
		
		public function get isSlideshowLoaded():Boolean {
			return (_slideshows != null);
		}
		public function get slideshows():ArrayCollection {
			return _slideshows;
		}
		
		public function set slideshows(value:ArrayCollection):void {
			_slideshows = value;
			for each(var item:Object in _slideshows) {
				var a:Array = item.tags;
				for each (var thing:String in a) {
					if (!_sorted.has(thing)) {
						_sorted.add(thing);
					}
				}
			}
			for each (var tagname:String in _sorted.toArray()) {
				tags.addItem(new ListItemValueObject(tagname, false));
			}
		}
		
		public function clearSlideshows():void {
			_slideshows.removeAll();
			_sorted = new SortedList(new StringComparator());
			tags.removeAll();
		}
		
		public function resetTags():void {
			for each(var item:ListItemValueObject in tags) {
				item.isSelected = false;
			}
		}
	}
}