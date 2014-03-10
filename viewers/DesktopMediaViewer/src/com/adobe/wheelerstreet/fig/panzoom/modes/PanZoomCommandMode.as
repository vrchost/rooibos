package com.adobe.wheelerstreet.fig.panzoom.modes {
	import com.adobe.wheelerstreet.fig.panzoom.ImageViewer;
	import com.adobe.wheelerstreet.fig.panzoom.commands.PanMouseCommandSansEdge;
	import com.adobe.wheelerstreet.fig.panzoom.commands.PanToPointCommand;
	import com.adobe.wheelerstreet.fig.panzoom.commands.ZoomCommand;
	import com.adobe.wheelerstreet.fig.panzoom.events.PanZoomEvent;
	import com.adobe.wheelerstreet.fig.panzoom.interfaces.ICommandMode;
	import com.adobe.wheelerstreet.fig.panzoom.utils.ContentRectangle;
	
	import flash.events.MouseEvent;
	import flash.geom.Point;
	
	import mx.core.Window;
	import mx.managers.CursorManager;
	
	public class PanZoomCommandMode implements ICommandMode {
		
		private static var CLICK_DEADZONE_RADIUS:int = 4;
		private static var CENTERVIEW_DEADZONE_RADIUS:int = 30;
		
		private var _client:ImageViewer;		
		private var _reciever:ContentRectangle;
		private var _isActivated:Boolean;
		private var _mouseDownPosition:Point;
		private var _maxScaleFactor:Number;
		private var _minScaleFactor:Number;
		private var _isMouseDown:Boolean = false;
		
		// commands
		private var _panMouseCommand:PanMouseCommandSansEdge;
		private var _panToPointCommand:PanToPointCommand;
		private var _zoomCommand:ZoomCommand;
		
		// cursor assets
		private var cursorID:Number = 0;
		[Embed(source="../icons/iconography.swf", symbol="IconHandOpen")] 
		private var _iconHandOpen:Class;		
		[Embed(source="../icons/iconography.swf", symbol="IconHandClosed")] 
		private var _iconHandClosed:Class;	
		
		/////////////////////////////////////////////////////////
		//
		// constructor
		//
		/////////////////////////////////////////////////////////		
		/**
		 * the PanZoomCmmandMode encapsulates all the command functionality into a 
		 * single mode that can be disabled. 
		 */
		public function PanZoomCommandMode(client:ImageViewer, reciever:ContentRectangle, maxScaleFactor:Number, minScaleFactor:Number) {
			_isActivated = false;
			_reciever = reciever;
			_client = client;
			_maxScaleFactor = maxScaleFactor;
			_minScaleFactor = minScaleFactor;
		}
		
		/////////////////////////////////////////////////////////
		//
		// interface
		//
		/////////////////////////////////////////////////////////
		/**
		 *  Returns the state of the mode.
		 */		
		public function isActivated():Boolean {
			return _isActivated;
		}
		
		/**
		 * Activates the mode and creates the command objects, and sets up 
		 * the mouse event listeners.
		 */
		public function activate():void {
			// interface
			_isActivated = true;
			// check to make sure the client can 
			// recieve  double-click mouse events.
			if (!_client.doubleClickEnabled)
				_client.doubleClickEnabled = true;			
			
			// objects
			if (_panMouseCommand == null) {
				_panMouseCommand = new PanMouseCommandSansEdge(_client, _reciever);
			}				
			if (_panToPointCommand == null) {
				_panToPointCommand = new PanToPointCommand(_client, _reciever);
			}	
			if (_zoomCommand == null) {
				_zoomCommand = new ZoomCommand(_client, _reciever);
			}
			
			// events
			_client.addEventListener(MouseEvent.MOUSE_DOWN  , handleMouse);			
			_client.addEventListener(MouseEvent.MOUSE_WHEEL , handleMouse);
			_client.addEventListener(MouseEvent.MOUSE_OUT   , handleMouse);
			_client.addEventListener(MouseEvent.MOUSE_OVER  , handleMouse);			
			
		}
		/**
		 * Deactivates the mode by removing the mouse event listeners.
		 */
		public function deactivate():void {
			_isActivated = false;
			
			// events
			_client.removeEventListener(MouseEvent.MOUSE_DOWN  , handleMouse);			
			_client.removeEventListener(MouseEvent.MOUSE_WHEEL , handleMouse);
			_client.removeEventListener(MouseEvent.MOUSE_OUT   , handleMouse);
			_client.removeEventListener(MouseEvent.MOUSE_OVER  , handleMouse);						
		}
		
		/////////////////////////////////////////////////////////
		//
		// events
		//
		/////////////////////////////////////////////////////////
		/**
		 *  @private
		 */    
		private function handleMouse(e:MouseEvent):void {
			switch(e.type)
			{
				// 1.
				case "mouseDown":
					this._isMouseDown = true;
					//
					// add listeners
					_client.stage.addEventListener(MouseEvent.MOUSE_UP, handleMouse);					
					_client.stage.addEventListener(MouseEvent.MOUSE_MOVE, handleMouse);					
					
					//
					// remove listeners
					_client.removeEventListener(MouseEvent.MOUSE_DOWN, handleMouse);					
					
					//
					// commands / actions
					_mouseDownPosition = new Point(e.localX, e.localY);
					
					_panMouseCommand.execute();
					_client.cursorManager.removeAllCursors();  
					cursorID = _client.cursorManager.setCursor(_iconHandClosed);						
					break;
				
				// 2.
				case "mouseUp":
					this._isMouseDown = false;
					//
					// add listeners
					_client.addEventListener(MouseEvent.MOUSE_DOWN, handleMouse);	
					_client.addEventListener(MouseEvent.CLICK, handleMouse);	
					_client.addEventListener(MouseEvent.DOUBLE_CLICK, handleMouse)
					
					//
					// remove listeners
					_client.stage.removeEventListener(MouseEvent.MOUSE_UP, handleMouse);					
					
					//
					// commands/actions	
					if (_client.cursorManager.currentCursorID > 0) {
						_client.cursorManager.removeAllCursors(); 
						cursorID = _client.cursorManager.setCursor(_iconHandOpen);	
					} else {
						_client.cursorManager.removeAllCursors(); 
					}
					break;			
				// 3.				
				case "click":
					
					//
					// add listeners
					_client.addEventListener(MouseEvent.DOUBLE_CLICK, handleMouse);
					
					//
					// remove listeners
					_client.removeEventListener(MouseEvent.CLICK, handleMouse);						
					
					//
					// commands / actions
					var __dist:Number = Point.distance(_mouseDownPosition, new Point(e.localX, e.localY));
					
					// only fire center view command if the click comes 
					// within the CLICK_DEADZONE_RADIUS && if view is smaller than the content.
					if (__dist < CLICK_DEADZONE_RADIUS)// && !_client.viewRect.containsRect(_reciever))
					{
						_panToPointCommand.fromPoint = new Point(e.localX , e.localY);
						_panToPointCommand.toPoint = new Point(_client.width/2 , _client.height/2);
						_panToPointCommand.execute();
					}
					break;
				// 4.				
				case "doubleClick":
					//
					// remove listeners
					_client.removeEventListener(MouseEvent.DOUBLE_CLICK, handleMouse);						
					//
					// commands / actions
					if(e.shiftKey) {
						_zoomCommand.direction = "out";						
					} else {
						_zoomCommand.direction = "in";							
					}
					_panToPointCommand.addEventListener(PanZoomEvent.COMMAND_COMPLETE, handleCenterView)				
					break;
				
				case "mouseMove":
					//
					// remove listeners
					_client.stage.removeEventListener(MouseEvent.MOUSE_MOVE, handleMouse);							
					//										
					// commands 
					break;
				case "mouseOut":
					// commands 
					_client.cursorManager.removeAllCursors();  
					//
					break;
				case "mouseOver":
					//
					// cursors
					if (this._isMouseDown) {
						_client.cursorManager.removeAllCursors();
						cursorID = _client.cursorManager.setCursor(_iconHandClosed);	
					} else {					
						_client.cursorManager.removeAllCursors();  
						cursorID = _client.cursorManager.setCursor(_iconHandOpen);						
					}
					break;
				case "mouseWheel":
					var __factor:Number = 1.125;					
					_reciever.zoomOrigin = new Point(
						(-_reciever.x + _client.mouseX) *   1/_reciever.scaleX,
						(-_reciever.y + _client.mouseY) * 1/_reciever.scaleY
					);					
					if (e.delta > 0) {
						var scaleUp:Number = _reciever.scaleX * __factor;
						if (scaleUp > _maxScaleFactor) scaleUp = _maxScaleFactor;
						_reciever.scaleByOrigin(scaleUp);										
						_client.bitmapScaleFactor = scaleUp;						
						
					} else {
						var scaleDown:Number = _reciever.scaleX / __factor;
						if (scaleDown < _minScaleFactor) scaleDown = _minScaleFactor;
						_reciever.scaleByOrigin(scaleDown);										
						_client.bitmapScaleFactor = scaleDown;		
					}
					
					_client.invalidateDisplayList();
					break;
			}
		}
		
		/**
		 *  @private
		 */	
		private function handleCenterView(e:PanZoomEvent):void
		{
			switch(e.type) {
				case "commandComplete":
					_panToPointCommand.removeEventListener(PanZoomEvent.COMMAND_COMPLETE, handleCenterView)
					_zoomCommand.execute();
					_client.invalidateDisplayList();					
					break;
			}	
		}
	}
}