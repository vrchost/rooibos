/*
Copyright (c) 2007 FlexLib Contributors.  See:
    http://code.google.com/p/flexlib/wiki/ProjectContributors

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

package flexlib.mdi.managers
{
	import flash.display.DisplayObject;
	import flash.events.Event;
	import flash.events.EventDispatcher;
	import flash.geom.Point;
	import flash.utils.Dictionary;
	
	import flexlib.mdi.containers.MDIWindow;
	import flexlib.mdi.effects.IMDIEffectsDescriptor;
	import flexlib.mdi.effects.MDIEffectsDescriptorBase;
	import flexlib.mdi.effects.effectClasses.MDIGroupEffectItem;
	import flexlib.mdi.events.MDIManagerEvent;
	import flexlib.mdi.events.MDIWindowEvent;
	
	import mx.collections.ArrayCollection;
	import mx.core.Application;
	import mx.core.EventPriority;
	import mx.core.IFlexDisplayObject;
	import mx.core.UIComponent;
	import mx.effects.CompositeEffect;
	import mx.effects.Effect;
	import mx.effects.effectClasses.CompositeEffectInstance;
	import mx.events.EffectEvent;
	import mx.events.ResizeEvent;
	import mx.managers.PopUpManager;
	import mx.utils.ArrayUtil;
	
	//--------------------------------------
	//  Events
	//--------------------------------------
	
	/**
	 *  Dispatched when a window is added to the manager.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_ADD
	 */
	[Event(name="windowAdd", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched when the close button is clicked.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_CLOSE
	 */
	[Event(name="windowClose", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched when the window gains focus and is given topmost z-index of MDIManager's children.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_FOCUS_START
	 */
	[Event(name="windowFocusStart", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched when the window loses focus and no longer has topmost z-index of MDIManager's children.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_FOCUS_END
	 */
	[Event(name="windowFocusEnd", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched when the window begins being dragged.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_DRAG_START
	 */
	[Event(name="windowDragStart", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched while the window is being dragged.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_DRAG
	 */
	[Event(name="windowDrag", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched when the window stops being dragged.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_DRAG_END
	 */
	[Event(name="windowDragEnd", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched when a resize handle is pressed.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_RESIZE_START
	 */
	[Event(name="windowResizeStart", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched while the mouse is down on a resize handle.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_RESIZE
	 */
	[Event(name="windowResize", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 *  Dispatched when the mouse is released from a resize handle.
	 *
	 *  @eventType flexlib.mdi.events.MDIManagerEvent.WINDOW_RESIZE_END
	 */
	[Event(name="windowResizeEnd", type="flexlib.mdi.events.MDIManagerEvent")]
	
	/**
	 * Class responsible for applying effects and default behaviors to MDIWindow instances such as
	 * tiling, cascading, minimizing, maximizing, etc.
	 */
	public class MDIManager extends EventDispatcher
	{
		
		private static var globalMDIManager:MDIManager;
		public static function get global():MDIManager
		{
			if(MDIManager.globalMDIManager == null)
			{
				globalMDIManager = new MDIManager(Application.application as UIComponent);
				globalMDIManager.isGlobal = true;
			}
			return MDIManager.globalMDIManager;
		}
		
		private var isGlobal:Boolean = false;
		private var windowToManagerEventMap:Dictionary;

		public var enforceBoundaries:Boolean = true;
		
		public var effects:IMDIEffectsDescriptor = new MDIEffectsDescriptorBase();

		/**
     	*   Contstructor()
     	*/
		public function MDIManager(container:UIComponent, effects:IMDIEffectsDescriptor = null):void
		{
			this.container = container;
			if(effects != null)
			{
				this.effects = effects;
			}
			this.container.addEventListener(ResizeEvent.RESIZE, containerResizeHandler);
			
			// map of window events to corresponding manager events
			windowToManagerEventMap = new Dictionary();
			windowToManagerEventMap[MDIWindowEvent.CLOSE] = MDIManagerEvent.WINDOW_CLOSE;
			windowToManagerEventMap[MDIWindowEvent.FOCUS_START] = MDIManagerEvent.WINDOW_FOCUS_START;
			windowToManagerEventMap[MDIWindowEvent.FOCUS_END] = MDIManagerEvent.WINDOW_FOCUS_END;
			windowToManagerEventMap[MDIWindowEvent.DRAG_START] = MDIManagerEvent.WINDOW_DRAG_START;
			windowToManagerEventMap[MDIWindowEvent.DRAG] = MDIManagerEvent.WINDOW_DRAG;
			windowToManagerEventMap[MDIWindowEvent.DRAG_END] = MDIManagerEvent.WINDOW_DRAG_END;
			windowToManagerEventMap[MDIWindowEvent.RESIZE_START] = MDIManagerEvent.WINDOW_RESIZE_START;
			windowToManagerEventMap[MDIWindowEvent.RESIZE] = MDIManagerEvent.WINDOW_RESIZE;
			windowToManagerEventMap[MDIWindowEvent.RESIZE_END] = MDIManagerEvent.WINDOW_RESIZE_END;
			
			// these handlers execute default behaviors, these events are dispatched by this class
			addEventListener(MDIManagerEvent.WINDOW_ADD, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_CLOSE, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
						
			addEventListener(MDIManagerEvent.WINDOW_FOCUS_START, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_FOCUS_END, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_DRAG_START, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_DRAG, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_DRAG_END, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_RESIZE_START, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_RESIZE, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			addEventListener(MDIManagerEvent.WINDOW_RESIZE_END, executeDefaultBehavior, false, EventPriority.DEFAULT_HANDLER);
			
		}
		
		private var _container:UIComponent;
		public function get container():UIComponent
		{
			return _container;
		}
		public function set container(value:UIComponent):void
		{
			this._container = value;
		}

		/**
     	*  @private
     	*  the managed window stack
     	*/
     	[Bindable]
		public var windowList:Array = new Array();

		public function add(window:MDIWindow):void
		{
			if(windowList.indexOf(window) < 0)
			{
				window.windowManager = this;
				
				this.addListeners(window);
				
				this.windowList.push(window);
				
				if(this.isGlobal)
				{
					PopUpManager.addPopUp(window,Application.application as DisplayObject);
					this.position(window);
				}
				else
				{
					// to accomodate mxml impl
					if(window.parent == null)
					{
						this.container.addChild(window);
						this.position(window);
					}
				} 		
				
				dispatchEvent(new MDIManagerEvent(MDIManagerEvent.WINDOW_ADD, window, this));
				bringToFront(window);
			}
		}
		
		/**
		 *  Positions a window on the screen 
		 *  
		 * 	<p>This is primarly used as the default space on the screen to position the window.</p>
		 * 
		 *  @param window:MDIWindow Window to position
		 */
		public function position(window:MDIWindow):void
		{	
			window.x = this.windowList.length * 50;
			window.y = this.windowList.length * 20;
			if((window.x + window.width) > container.width) window.x = 5;
			if((window.y + window.height) > container.height) window.y = 5; 	
			if((window.x + window.width) > container.width) window.width = container.width - 10;
			if((window.y + window.height) > container.height) window.height = container.height - 10; 	
		}
		
		private function windowEventProxy(event:Event):void
		{
			if(event is MDIWindowEvent && !event.isDefaultPrevented())
			{
				var winEvent:MDIWindowEvent = event as MDIWindowEvent;
				var mgrEvent:MDIManagerEvent = new MDIManagerEvent(windowToManagerEventMap[winEvent.type], winEvent.window, this);
				
				switch(winEvent.type)
				{					
					case MDIWindowEvent.CLOSE:
						mgrEvent.effect = this.effects.getWindowCloseEffect(mgrEvent.window, this);
					break;
					
					case MDIWindowEvent.FOCUS_START:
						mgrEvent.effect = this.effects.getWindowFocusStartEffect(winEvent.window, this);
					break;
					
					case MDIWindowEvent.FOCUS_END:
						mgrEvent.effect = this.effects.getWindowFocusEndEffect(winEvent.window, this);
					break;
		
					case MDIWindowEvent.DRAG_START:
						mgrEvent.effect = this.effects.getWindowDragStartEffect(winEvent.window, this);
					break;
		
					case MDIWindowEvent.DRAG:
						mgrEvent.effect = this.effects.getWindowDragEffect(winEvent.window, this);
					break;
		
					case MDIWindowEvent.DRAG_END:
						mgrEvent.effect = this.effects.getWindowDragEndEffect(winEvent.window, this);
					break;
					
					case MDIWindowEvent.RESIZE_START:
						mgrEvent.effect = this.effects.getWindowResizeStartEffect(winEvent.window, this);
					break;
					
					case MDIWindowEvent.RESIZE:
						mgrEvent.effect = this.effects.getWindowResizeEffect(winEvent.window, this);
					break;
					
					case MDIWindowEvent.RESIZE_END:
						mgrEvent.effect = this.effects.getWindowResizeEndEffect(winEvent.window, this);
					break;
				}
				
				dispatchEvent(mgrEvent);
			}			
		}
		
		public function executeDefaultBehavior(event:Event):void
		{
			if(event is MDIManagerEvent && !event.isDefaultPrevented())
			{
				var mgrEvent:MDIManagerEvent = event as MDIManagerEvent;
				
				switch(mgrEvent.type)
				{					
					case MDIManagerEvent.WINDOW_ADD:
						// get the effect here because this doesn't pass thru windowEventProxy()
						mgrEvent.effect = this.effects.getWindowAddEffect(mgrEvent.window, this);
						mgrEvent.effect.play();
					break;
										
					case MDIManagerEvent.WINDOW_CLOSE:
						mgrEvent.effect.addEventListener(EffectEvent.EFFECT_END, onCloseEffectEnd);
						mgrEvent.effect.play();
					break;
					
					case MDIManagerEvent.WINDOW_FOCUS_START:
						mgrEvent.window.hasFocus = true;
						mgrEvent.window.validateNow();
						container.setChildIndex(mgrEvent.window, container.numChildren - 1);
						mgrEvent.effect.play();
					break;
					
					case MDIManagerEvent.WINDOW_FOCUS_END:
						mgrEvent.window.hasFocus = false;
						mgrEvent.window.validateNow();
						mgrEvent.effect.play();
					break;
		
					case MDIManagerEvent.WINDOW_DRAG_START:
						mgrEvent.effect.play();
					break;
		
					case MDIManagerEvent.WINDOW_DRAG:
						mgrEvent.effect.play();
					break;
		
					case MDIManagerEvent.WINDOW_DRAG_END:
						mgrEvent.effect.play();
					break;
					
					case MDIManagerEvent.WINDOW_RESIZE_START:
						mgrEvent.effect.play();
					break;
					
					case MDIManagerEvent.WINDOW_RESIZE:
						mgrEvent.effect.play();
					break;
					
					case MDIManagerEvent.WINDOW_RESIZE_END:
						mgrEvent.effect.play();
					break;
					
				}
			}			
		}
		
		private function onCloseEffectEnd(event:EffectEvent):void
		{
			//remove(event.effectInstance.target as MDIWindow);
			var win:MDIWindow = event.effectInstance.target as MDIWindow;
			win.visible = false;
		}
		
		/**
		 * Handles resizing of container to reposition elements
		 * 
		 *  @param event The ResizeEvent object from event dispatch
		 * 
		 * */
		private function containerResizeHandler(event:ResizeEvent):void
		{	
			//repositions any minimized tiled windows to bottom left in their rows
			//reTileWindows();
		}
		
		public function addCenter(window:MDIWindow):void
		{
			this.add(window);
			this.center(window);
		}
		
		
		/**
		 * Brings a window to the front of the screen. 
		 * 
		 *  @param win Window to bring to front
		 * */
		public function bringToFront(window:MDIWindow):void
		{
			if(this.isGlobal)
			{
				PopUpManager.bringToFront(window as IFlexDisplayObject);
			}
			else
			{				
				for each(var win:MDIWindow in windowList)
				{
					if(win != window && win.hasFocus)
					{
						win.dispatchEvent(new MDIWindowEvent(MDIWindowEvent.FOCUS_END, win));
					}
					if(win == window && !window.hasFocus)
					{
						win.dispatchEvent(new MDIWindowEvent(MDIWindowEvent.FOCUS_START, win));
					}
				}
			}
			
		}
		
		
		/**
		 * Positions a window in the center of the available screen. 
		 * 
		 *  @param window:MDIWindow to center
		 * */
		public function center(window:MDIWindow):void
		{
			window.x = this.container.width / 2 - window.width;
			window.y = this.container.height / 2 - window.height;
		}
		
		/**
		 * Removes all windows from managed window stack; 
		 * */
		public function removeAll():void
		{	
		
			for each(var window:MDIWindow in windowList)
			{
				if(this.isGlobal)
				{
					PopUpManager.removePopUp(window as IFlexDisplayObject);
				}
				else
				{
					container.removeChild(window);
				}
				
				this.removeListeners(window);
			}
			
			this.windowList = new Array();
		}
		
		/**
		 *  @private
		 * 
		 *  Adds listeners 
		 *  @param window:MDIWindow  
		 */
		
		private function addListeners(window:MDIWindow):void
		{
			window.addEventListener(MDIWindowEvent.CLOSE, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			
			window.addEventListener(MDIWindowEvent.FOCUS_START, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			window.addEventListener(MDIWindowEvent.FOCUS_END, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			window.addEventListener(MDIWindowEvent.DRAG_START, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			window.addEventListener(MDIWindowEvent.DRAG, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			window.addEventListener(MDIWindowEvent.DRAG_END, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			window.addEventListener(MDIWindowEvent.RESIZE_START, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			window.addEventListener(MDIWindowEvent.RESIZE, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
			window.addEventListener(MDIWindowEvent.RESIZE_END, windowEventProxy, false, EventPriority.DEFAULT_HANDLER);
		}


		/**
		 *  @private
		 * 
		 *  Removes listeners 
		 *  @param window:MDIWindow 
		 */
		private function removeListeners(window:MDIWindow):void
		{
			window.removeEventListener(MDIWindowEvent.CLOSE, windowEventProxy);
			
			window.removeEventListener(MDIWindowEvent.FOCUS_START, windowEventProxy);
			window.removeEventListener(MDIWindowEvent.FOCUS_END, windowEventProxy);
			window.removeEventListener(MDIWindowEvent.DRAG_START, windowEventProxy);
			window.removeEventListener(MDIWindowEvent.DRAG, windowEventProxy);
			window.removeEventListener(MDIWindowEvent.DRAG_END, windowEventProxy);
			window.removeEventListener(MDIWindowEvent.RESIZE_START, windowEventProxy);
			window.removeEventListener(MDIWindowEvent.RESIZE, windowEventProxy);	
			window.removeEventListener(MDIWindowEvent.RESIZE_END, windowEventProxy);
		}
		
		
		
		
		/**
		 *  Removes a window instance from the managed window stack 
		 *  @param window:MDIWindow Window to remove 
		 */
		public function remove(window:MDIWindow):void
		{	
			
			var index:int = ArrayUtil.getItemIndex(window, this.windowList);
			
			windowList.splice(index, 1);
			
			if(this.isGlobal)
			{
				PopUpManager.removePopUp(window as IFlexDisplayObject);
			}
			else
			{
				container.removeChild(window);
			}
			
			removeListeners(window);
			
			// set focus to newly-highest depth window
			for(var i:int = container.numChildren - 1; i > -1; i--)
			{
				var dObj:DisplayObject = container.getChildAt(i);
				if(dObj is MDIWindow)
				{
					bringToFront(MDIWindow(dObj));
					return;
				}
			}
		}				
		
		/**
		 * Pushes a window onto the managed window stack 
		 * 
		 *  @param win Window:MDIWindow to push onto managed windows stack 
		 * */
		public function manage(window:MDIWindow):void
		{	
			if(window != null)
				windowList.push(window);
		}
		
		/**
		 *  Positions a window in an absolute position 
		 * 
		 *  @param win:MDIWindow Window to position
		 * 
		 *  @param x:int The x position of the window
		 * 
		 *  @param y:int The y position of the window 
		 */
		public function absPos(window:MDIWindow,x:int,y:int):void
		{
			window.x = x;
			window.y = y;		
		}
		
		/**
		 * Gets a list of open windows for scenarios when only open windows need to be managed
		 * 
		 * @return Array
		 */
		public function getOpenWindowList():Array
		{	
			var array:Array = [];
			for(var i:int = 0; i < windowList.length; i++)
			{
				array.push(windowList[i]);
			}
			return array;
		}
		
		// set a min. width/height
		public function resize(window:MDIWindow):void
		{		
			var w:int = this.container.width * .6;
			var h:int = this.container.height * .6
			if(w > window.width)
				window.width = w;
			if(h > window.height)
				window.height=h;
		}
				
	}
}