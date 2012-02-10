package com.adobe.controls
{
	import flash.display.Shape;
	
	import mx.controls.Label;
	import mx.core.UIComponent;
	
	
	[Style(name="color", type="uint", format="Color", inherit="yes")]
	
	[Style(name="horizontalAlign", type="String", enumeration="left,center,right", inherit="no")]

	public class Thumb extends UIComponent
	{
		
		private var thumbShape:Shape;
		private var thumbLabel:Label;
		
		private var _label:String;
		
		public function Thumb():void
		{
			super();
		}	
		
		/**
		 * Creates the objects for the background shape and labels
		 * 
		 */		
		override protected function createChildren():void
		{
			super.createChildren();
			
			//
			if (thumbShape == null)
			{
				thumbShape = new Shape;
				thumbShape.alpha = .5;
			}
			addChild(thumbShape);
			

			
			//
			if (thumbLabel == null)
			{
				thumbLabel = new Label;
				thumbLabel.setStyle("textAlign", "right");

			}
			addChild(thumbLabel);
			
		}
		
		
		//
		//
		override protected function commitProperties():void
		{
			super.commitProperties();
			
			//
			thumbLabel.text = _label;
		}
		
		
		override protected function measure():void
		{
			super.measure();
			
			percentHeight = 100;
			percentWidth  = 100;
		}
		/**
		 * 
		 * Draws the thumb background shape to fit 
		 * 
		 * @param unscaledWidth
		 * @param unscaledHeight
		 * 
		 */		
		override protected function updateDisplayList(unscaledWidth:Number, unscaledHeight:Number):void
		{
			super.updateDisplayList(unscaledWidth, unscaledHeight);
			
			thumbLabel.setActualSize(unscaledWidth, unscaledHeight);
			

			//
			thumbShape.graphics.clear();
			thumbShape.graphics.beginFill(0x000000);
			thumbShape.graphics.drawRoundRect(  .25					// x
									      ,0					// y
									      ,unscaledWidth - .25	// width
									      ,unscaledHeight		// height
									      ,5					// ellipse width
									      ,5					// ellipse height
									      );
			
			
						      
							
			
		}
		
		/** getters and setters **/
		public function set label(value:String):void
		{
			if (_label == value) return;
			//	
			_label = value;
			
			invalidateProperties();
			invalidateSize();
	
		}
		public function get label():String
		{
			return _label;
		}	
		
	}
}