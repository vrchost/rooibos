package org.mdid.MediaViewer.models.vo
{
	public class ListItemValueObject {
		
		[Bindable]
		public var label:String;
		
		[Bindable]
		public var isSelected:Boolean;
		
		public function ListItemValueObject(lbl:String = "", selected:Boolean = false) {
			label = lbl;
			isSelected = selected;
			super();
		}
	}
}