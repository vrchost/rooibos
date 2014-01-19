package com.adobe.wheelerstreet.fig.panzoom.commands
{
	import com.adobe.wheelerstreet.fig.panzoom.ImageViewer;
	import com.adobe.wheelerstreet.fig.panzoom.events.PanZoomEvent;
	import com.adobe.wheelerstreet.fig.panzoom.interfaces.ICommand;
	import com.adobe.wheelerstreet.fig.panzoom.utils.ContentRectangle;
	import com.adobe.wheelerstreet.fig.panzoom.utils.MouseTracker;
	
	import flash.events.EventDispatcher;
	import flash.events.MouseEvent;
	import flash.events.TimerEvent;
	import flash.geom.Point;
	import flash.utils.Timer;
	
	import mx.core.UIComponent;
	import mx.effects.AnimateProperty;
	import mx.events.TweenEvent;

	public class PanMouseCommandSansEdge extends EventDispatcher implements ICommand {

		private static var TRANSLATE_TOLERANCE:Number = .25;
		
		private var _client:UIComponent;
		private var _reciever:ContentRectangle;
		private var _isExecuting:Boolean;

		private var _initOrginPoint:Point;
		
		private var _mouseDownPosition:Point;
		private var _mousePosition:Point;

		private var _panTimer:Timer
		private var _animatePropertyX:AnimateProperty
		private var _animatePropertyY:AnimateProperty
		
		private var _mouseTracker:MouseTracker;
		
		private var _minEdgeWidth:int = 100;
		
		private var _panAnimationSpeed:Number = .25;
		private var _springAnimationSpeed:Number = .125;		
		
		
		/////////////////////////////////////////////////////////
		//
		// constructor
		//
		/////////////////////////////////////////////////////////
		/**
		 * the PanMouseCommand triggers movement of the the ContentRectangle (_reciever) against
		 * the bitmap ImageView (_client).
		 */
		public function PanMouseCommandSansEdge(client:ImageViewer, reciever:ContentRectangle):void {
			_client = client;
			_reciever = reciever;
		}
		
		
		/////////////////////////////////////////////////////////
		//
		// interface
		//
		/////////////////////////////////////////////////////////
		/**
	    * begins pan mouse action by listening for mouse movements and animating the 
	    * transition between fired mouseMove positions.
	    */		
		public function execute():void {
			//trace("execute");
			// remove previous listeners
			if(_panTimer != null) {
				_client.stage.removeEventListener(MouseEvent.MOUSE_UP, handleMouse);	
				_client.stage.removeEventListener(MouseEvent.MOUSE_MOVE, handleMouse);	
				_panTimer.removeEventListener(TimerEvent.TIMER, handlePanTimer);
			}

			if (_animatePropertyX != null && _animatePropertyX.isPlaying) {
				_animatePropertyX.pause();
			}
			if (_animatePropertyY != null && _animatePropertyY.isPlaying) {
				_animatePropertyY.pause();
			}	
						
			_animatePropertyX = new AnimateProperty(_reciever);	
			_animatePropertyX.property = "x";
			_animatePropertyY = new AnimateProperty(_reciever);	
			_animatePropertyY.property = "y";
								
			_isExecuting = true;
			
			// objects
			_panTimer = new Timer(10,0);					
			_mouseTracker = new MouseTracker();
			_mouseDownPosition = new Point(_client.mouseX, _client.mouseY);
			_mousePosition = new Point(_mouseDownPosition.x, _mouseDownPosition.y);
			_initOrginPoint = new Point( _reciever.x, _reciever.y);
	
			// listeners
			_client.stage.addEventListener(MouseEvent.MOUSE_UP, handleMouse);	
			_client.stage.addEventListener(MouseEvent.MOUSE_MOVE, handleMouse);	
			_panTimer.addEventListener(TimerEvent.TIMER, handlePanTimer);
		}
		public function cancel():void {
			_isExecuting = false;
		}
		public function isExecuting():Boolean {
			return _isExecuting;
		}
		
		/////////////////////////////////////////////////////////
		//
		// interface
		//
		/////////////////////////////////////////////////////////
		/**
		*  @private
		*/
		private function handleMouse(e:MouseEvent):void {			
			switch (e.type) {
				case "mouseUp":
					_panTimer.stop();
					_mouseTracker.end();	
					
					//					
					// events
					_client.stage.removeEventListener(MouseEvent.MOUSE_UP, handleMouse);		
					_panTimer.removeEventListener(TimerEvent.TIMER, handlePanTimer);
					
					//
					// objects	
					addEventListener(PanZoomEvent.COMMAND_COMPLETE, handleSpringComplete);
					break;
				case "mouseMove":
					//
					// events
					// removing the move listener here forces the move event to fire once.  
					_client.stage.removeEventListener(MouseEvent.MOUSE_MOVE, handleMouse);	
					addEventListener(PanZoomEvent.COMMAND_COMPLETE, handleSpringComplete);
										
					_panTimer.start();
					_mouseTracker.start();
					break;
			}
		}
		/**
		*  @private
		*/		
		private function handlePanTimer(e:TimerEvent):void {			
			// begin tracking stage's mouse (note: this captures mouse
			// events outside the player and/or browser)
			_mouseTracker.track(_client.systemManager.stage.mouseX, _client.systemManager.stage.mouseY);

			var dx:int = _mouseTracker.getMouseDelta().x;
			var dy:int = _mouseTracker.getMouseDelta().y;
		
			_mousePosition.x += dx;	
			_mousePosition.y += dy;

			// animate twards _mousePosition
			var newX:int = _panAnimationSpeed * ((_mousePosition.x - _mouseDownPosition.x) - (_reciever.x - _initOrginPoint.x));
			var newY:int = _panAnimationSpeed * ((_mousePosition.y - _mouseDownPosition.y) - (_reciever.y - _initOrginPoint.y));
			if ( (newX < 0 && _reciever.right + newX > ImageViewer(_client).viewRect.left + _minEdgeWidth) || (newX > 0 && _reciever.left + newX < ImageViewer(_client).viewRect.right - _minEdgeWidth)) {
				_reciever.x += newX;
			}
			if ( (newY < 0 && _reciever.bottom + newY > ImageViewer(_client).viewRect.top + _minEdgeWidth) || (newY > 0 && _reciever.top + newY < ImageViewer(_client).viewRect.bottom - _minEdgeWidth)) {
				_reciever.y += newY;
			}
			_client.invalidateDisplayList();
		}

		/**
		*  @private
		*/		
		private function handleSpringTween(e:TweenEvent):void {
			_client.invalidateDisplayList();
			//trace(_reciever.x);
		}
		/**
		*  @private
		*/		
 		private function handleSpringComplete(e:PanZoomEvent):void {
			cancel();
			removeEventListener(PanZoomEvent.COMMAND_COMPLETE, handleSpringComplete);
		} 
	}
}