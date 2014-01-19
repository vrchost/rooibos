package com.adobe.controls
{

	import flash.events.MouseEvent;
	import flash.geom.Rectangle;
	
	import mx.containers.HBox;
	import mx.core.Application;
	import mx.core.UIComponent;
	import mx.effects.Move;
		

	public class PagedListAffordance extends UIComponent
	{
		
		
		private var _numberOfPages:int = 0;
		private var _currentPage:int;
		
		private var thumb:Thumb
		private var hBox:HBox;
		private var pages:Array = new Array;
		
		private var thumbMove:Move = new Move([thumb]);
		
		
		//
		// 
		public function PagedListAffordance():void
		{
			super;
		}
	
	
		override protected function createChildren():void
		{
			super.createChildren();
			
			//
			if (hBox == null)
			{
				hBox = new HBox;
				hBox.setStyle("horizontalGap", "2");
				
			}
			addChild(hBox);
			
			//
			if (thumb == null)
			{
				thumb = new Thumb();			
				thumb.addEventListener(MouseEvent.MOUSE_DOWN, thumbMouseDownHandler);
			}
			addChild(thumb);
		}
		
		
		//
		//
		override protected function commitProperties():void
		{
			super.commitProperties();
			thumb.label = String(_currentPage + 1 + " / " + _numberOfPages);			
		}
		
		
		//
		//
		override protected function measure():void
		{
			super.measure();
		}
		
		
		//
		//
		override protected function updateDisplayList(unscaledWidth:Number, unscaledHeight:Number):void
		{

			hBox.width = unscaledWidth;
			hBox.height = unscaledHeight;
			
			if(_numberOfPages == pages.length)
			{
			

						
			} else 
			{
				for (var i:int = 0 ; i < _numberOfPages ; i ++)
				{
				
					if ( _numberOfPages > pages.length)
					{
						//trace("add page: ");
						
						var pg:Page = new Page();
						pages.push(pg);
						
						pg.pageNumber = pages.length;
						
						pg.addEventListener(MouseEvent.CLICK, handlePageClick);
						pg.addEventListener(MouseEvent.MOUSE_OVER, handelPageMouseOver);
						pg.addEventListener(MouseEvent.MOUSE_DOWN, handlePageMouseDown);
						pg.addEventListener(MouseEvent.MOUSE_OUT, handlePageMouseOut);
						
						hBox.addChild(pg);
						//trace("numberOfPages:"+_numberOfPages+" pages.length: "+pages.length);
					} else if(_numberOfPages < pages.length)
					{

						//trace("remove page: ");
						var deletePage:* = pages.pop();
						hBox.removeChild(deletePage);
						//trace("numberOfPages:"+_numberOfPages+" pages.length: "+pages.length);				
					}	
	
				}				
			}
			if (_numberOfPages == 0)
				return;
			if(pages[_currentPage])
			thumb.x = Page(pages[_currentPage]).x;			
			thumb.width = unscaledWidth/_numberOfPages - 2;
			thumb.height = unscaledHeight;	
				
		}
		
		//
		// mouse events
		
		private var mouseDown:Boolean = false;
		private function thumbMouseDownHandler(e:MouseEvent):void
		{
			thumb.removeEventListener(MouseEvent.MOUSE_DOWN, thumbMouseDownHandler);
			Application.application.addEventListener(MouseEvent.MOUSE_MOVE, appMouseMoveHandler);
			Application.application.addEventListener(MouseEvent.MOUSE_UP, appMouseUpHandler);
			
			thumb.startDrag(false, new Rectangle(0,0, width - thumb.width, 0));
			
			Page(pages[calcPageUnder(thumb.x)]).highlight = true;
			mouseDown = true;
			

		}
		private function appMouseMoveHandler(e:MouseEvent):void
		{
			
  			for (var i:int = 0 ; i < pages.length ; i ++)
			{	
				if (i == calcPageUnder(thumb.x))
				{
					Page(pages[calcPageUnder(thumb.x)]).highlight = true;
					currentPage = i;
										
				} else 
				{
					Page(pages[i]).highlight = false;					
				}
			}		
		}
		
		
		private function appMouseUpHandler(e:MouseEvent):void
		{
			Application.application.removeEventListener(MouseEvent.MOUSE_UP, appMouseUpHandler);
			Application.application.removeEventListener(MouseEvent.MOUSE_MOVE, appMouseMoveHandler);			
			thumb.addEventListener(MouseEvent.MOUSE_DOWN, thumbMouseDownHandler);
			
			thumb.stopDrag();
			for each(var page:Page in pages)
			{
				page.highlight = false;
			}
			
			if (calcPageUnder(thumb.x) == _currentPage)
			{
				doThumbMove();
			}
			
			currentPage = calcPageUnder(thumb.x);
			mouseDown = false;
		}
		
		
		//
		// page mouse events
		private function handlePageClick(e:MouseEvent):void
		{
			currentPage = Page(e.target).pageNumber - 1
		}
		
		private function handelPageMouseOver(e:MouseEvent):void
		{
			Page(e.target).highlight = true;
		}
		
		private function handlePageMouseOut(e:MouseEvent):void
		{
			Page(e.target).highlight = false;
		}
		
		private function handlePageMouseDown(e:MouseEvent):void
		{
			Page(e.target).highlight = false;			
		}
		
		//
		// effects
		private function doThumbMove():void
		{
			thumbMove.xTo = Page(pages[_currentPage]).x;
			thumbMove.play([thumb]);
		}
		
		
		//
		// setters/getters
		[Bindable]
		public function set numberOfPages(value:int):void
		{
			
			_numberOfPages = value;

			if (value < _currentPage)
			{
				_currentPage = value;
			}
			
			invalidateProperties();
			invalidateDisplayList();
	
		}
		public function get numberOfPages():int
		{
			return _numberOfPages;
		}
		
		//
		[Bindable]
		public function set currentPage(value:int):void
		{
			if (value > _numberOfPages) 
				return;
			
			_currentPage = value;		
			
			invalidateProperties();
			
			if (!mouseDown)
				doThumbMove();
			
		}
		
		public function get currentPage():int
		{
			return _currentPage;
		}
					
		private function calcPageUnder(_x:Number):int
		{
			return Math.floor(( (_x + thumb.width /2 ) /unscaledWidth ) * _numberOfPages);
		}
		
		

	}

}

