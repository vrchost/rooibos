package com.adobe.controls
{
	import flash.display.Shape;
	import mx.core.UIComponent;
	import flash.events.MouseEvent;
	import mx.controls.Label;
	import mx.effects.Fade;
	import mx.managers.ToolTipManager;

	public class Page extends UIComponent
	{
				
		private var shape:Shape;
		private var label:Label;
		private var fade:Fade = new Fade();
		
		private var _highlight:Boolean = false;
		private var _pageNumber:int;
		
		
		public function Page():void
		{
			super();
			buttonMode = true;
			tabEnabled = true;
			mouseChildren = false;
			
			fade.duration = 120;
			fade.alphaFrom = .33;
			fade.alphaTo   = .66;
		
			ToolTipManager.enabled = true;
			ToolTipManager.showEffect = new Fade();
		}
		
		override protected function createChildren():void
		{
			super.createChildren();

			if (shape == null)
			{
				shape = new Shape();
				shape.alpha = .33;
			}
			addChild(shape);
			
		}
		
		override protected function commitProperties():void
		{
			super.commitProperties();
			toolTip = "page: " + _pageNumber;
		}
		
		override protected function measure():void
		{
			super.measure();
			
			percentHeight = 100;
			percentWidth  = 100;
		}
		
		
		override protected function updateDisplayList(unscaledWidth:Number, unscaledHeight:Number):void
		{
			super.updateDisplayList(unscaledWidth, unscaledHeight);

			shape.graphics.clear();
			shape.graphics.beginFill(0xFFFFFF);
			shape.graphics.drawRoundRect(  .25					// x
									      ,0					// y
									      ,unscaledWidth - .25	// width
									      ,unscaledHeight		// height
									      ,5					// ellipse width
									      ,5					// ellipse height
									      );	
		}


	    //
	    // setters / getters
	    public function set highlight(value:Boolean):void
	    {
	    	if (value == _highlight)
	    		return;
	    	
	    	
	    	_highlight = value;
	    	
	    	// play the effect forward or backwards based on 'highlight'
	    	if (fade.isPlaying)
	    	{
	    		fade.reverse();
	    	
	    	} else 
	    	{
	    		fade.play([shape], !value);	    		
	    	}	    	    	
	    }
	    
	    public function get highlight():Boolean
	    {
	    	return _highlight;
	    }	    
	    
	    public function set pageNumber(value:int):void
	    {
	    	_pageNumber = value;
	    }
	    
	    public function get pageNumber():int
	    {
	    	return _pageNumber;
	    }
				
	}

}