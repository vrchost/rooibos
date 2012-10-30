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

package flexlib.mdi.containers
{
	import flash.display.DisplayObject;
	import flash.events.Event;
	import flash.events.MouseEvent;
	import flash.geom.Rectangle;
	import flash.text.Font;
	import flash.ui.ContextMenu;
	import flash.utils.getQualifiedClassName;
	
	import flexlib.mdi.events.MDIWindowEvent;
	import flexlib.mdi.managers.MDIManager;
	
	import mx.containers.Canvas;
	import mx.containers.Panel;
	import mx.controls.Button;
	import mx.controls.CheckBox;
	import mx.core.Container;
	import mx.core.UIComponent;
	import mx.core.UITextField;
	import mx.core.mx_internal;
	import mx.managers.CursorManager;
	import mx.styles.CSSStyleDeclaration;
	import mx.styles.StyleManager;
	
	
	//--------------------------------------
	//  Events
	//--------------------------------------
	
	/**
	 *  Dispatched when the toggle fontcolor button is clicked.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.FONTCOLOR
	 */
	[Event(name="fontcolor", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when the toggle fontsize button is clicked.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.FONTSIZE
	 */
	[Event(name="fontsize", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when the display info or display notes checkbox is clicked.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.DISPLAYINFONOTES
	 */
	[Event(name="displayinfonotes", type="flexlib.mdi.events.MDIWindowEvent")]
		
	/**
	 *  Dispatched when the close button is clicked.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.CLOSE
	 */
	[Event(name="close", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when the window gains focus and is given topmost z-index of MDIManager's children.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.FOCUS_START
	 */
	[Event(name="focusStart", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when the window loses focus and no longer has topmost z-index of MDIManager's children.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.FOCUS_END
	 */
	[Event(name="focusEnd", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when the window starts being dragged.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.DRAG_START
	 */
	[Event(name="dragStart", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched while the window is being dragged.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.DRAG
	 */
	[Event(name="drag", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when the window stops being dragged.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.DRAG_END
	 */
	[Event(name="dragEnd", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when a resize handle is pressed.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.RESIZE_START
	 */
	[Event(name="resizeStart", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched while the mouse is down on a resize handle.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.RESIZE
	 */
	[Event(name="resize", type="flexlib.mdi.events.MDIWindowEvent")]
	
	/**
	 *  Dispatched when the mouse is released from a resize handle.
	 *
	 *  @eventType flexlib.mdi.events.MDIWindowEvent.RESIZE_END
	 */
	[Event(name="resizeEnd", type="flexlib.mdi.events.MDIWindowEvent")]
	
	
	//--------------------------------------
	//  Skins + Styles
	//--------------------------------------
	
	/**
	 *  Style declaration name for the window when it has focus.
	 *
	 *  @default "mdiWindowFocus"
	 */
	[Style(name="styleNameFocus", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the window when it does not have focus.
	 *
	 *  @default "mdiWindowNoFocus"
	 */
	[Style(name="styleNameNoFocus", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the text in the title bar
	 * 	when the window is in focus. If <code>titleStyleName</code> (inherited from Panel)
	 *  is set, titleStyleNameFocus will be overridden by it.
	 *
	 *  @default "mdiWindowTitleStyle"
	 */
	[Style(name="titleStyleNameFocus", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the text in the title bar
	 * 	when the window is not in focus. If <code>titleStyleName</code> (inherited from Panel)
	 *  is set, <code>titleStyleNameNoFocus</code> will be overridden by it.
	 *  If <code>titleStyleNameNoFocus</code> is not set but <code>titleStyleNameFocus</code>
	 *  is, <code>titleStyleNameFocus</code> will be used, regardless of the window's focus state.
	 */
	[Style(name="titleStyleNameNoFocus", type="String", inherit="no")]
	
	/**
	 *  Reference to class that will contain window control buttons like
	 *  minimize, close, etc. Changes to this style will be detected and will
	 *  initiate the instantiation and addition of a new class instance.
	 *
	 *  @default flexlib.mdi.containers.MDIWindowControlsContainer
	 */
	[Style(name="windowControlsClass", type="Class", inherit="no")]
		
	/**
	 *  Style declaration name for the window's fontcolor button.
	 *  If <code>fontColorBtnStyleNameNoFocus</code> is not provided this style
	 *  will be used regardless of the window's focus. If <code>fontColorBtnStyleNameNoFocus</code>
	 *  is provided this style will be applied only when the window has focus.
	 *
	 *  @default "mdiWindowFontColorBtn"
	 */
	[Style(name="fontColorBtnStyleName", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the window's fontcolor button when window does not have focus.
	 *  See <code>fontColorBtnStyleName</code> documentation for details.
	 */
	[Style(name="fontColorBtnStyleNameNoFocus", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the window's fontsize button.
	 *  If <code>fontSizeBtnStyleNameNoFocus</code> is not provided this style
	 *  will be used regardless of the window's focus. If <code>fontSizeBtnStyleNameNoFocus</code>
	 *  is provided this style will be applied only when the window has focus.
	 *
	 *  @default "mdiWindowFontSizeBtn"
	 */
	[Style(name="fontSizeBtnStyleName", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the window's fontsize button when window does not have focus.
	 *  See <code>fontSizeBtnStyleName</code> documentation for details.
	 */
	[Style(name="fontSizeBtnStyleNameNoFocus", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the window's close button.
	 *  If <code>closeBtnStyleNameNoFocus</code> is not provided this style
	 *  will be used regardless of the window's focus. If <code>closeBtnStyleNameNoFocus</code>
	 *  is provided this style will be applied only when the window has focus.
	 *
	 *  @default "mdiWindowCloseBtn"
	 */
	[Style(name="closeBtnStyleName", type="String", inherit="no")]
	
	/**
	 *  Style declaration name for the window's close button when window does not have focus.
	 *  See <code>closeBtnStyleName</code> documentation for details.
	 */
	[Style(name="closeBtnStyleNameNoFocus", type="String", inherit="no")]
	
	
	/**
	 *  Name of the class used as cursor when resizing the window horizontally.
	 */
	[Style(name="resizeCursorHorizontalSkin", type="Class", inherit="no")]
	
	/**
	 *  Distance to horizontally offset resizeCursorHorizontalSkin.
	 */
	[Style(name="resizeCursorHorizontalXOffset", type="Number", inherit="no")]
	
	/**
	 *  Distance to vertically offset resizeCursorHorizontalSkin.
	 */
	[Style(name="resizeCursorHorizontalYOffset", type="Number", inherit="no")]
	
	
	/**
	 *  Name of the class used as cursor when resizing the window vertically.
	 */
	[Style(name="resizeCursorVerticalSkin", type="Class", inherit="no")]
	
	/**
	 *  Distance to horizontally offset resizeCursorVerticalSkin.
	 */
	[Style(name="resizeCursorVerticalXOffset", type="Number", inherit="no")]
	
	/**
	 *  Distance to vertically offset resizeCursorVerticalSkin.
	 */
	[Style(name="resizeCursorVerticalYOffset", type="Number", inherit="no")]
	
	
	/**
	 *  Name of the class used as cursor when resizing from top left or bottom right corner.
	 */
	[Style(name="resizeCursorTopLeftBottomRightSkin", type="Class", inherit="no")]
	
	/**
	 *  Distance to horizontally offset resizeCursorTopLeftBottomRightSkin.
	 */
	[Style(name="resizeCursorTopLeftBottomRightXOffset", type="Number", inherit="no")]
	
	/**
	 *  Distance to vertically offset resizeCursorTopLeftBottomRightSkin.
	 */
	[Style(name="resizeCursorTopLeftBottomRightYOffset", type="Number", inherit="no")]
	
	/**
	 *  Name of the class used as cursor when resizing from top right or bottom left corner.
	 */
	[Style(name="resizeCursorTopRightBottomLeftSkin", type="Class", inherit="no")]
	
	/**
	 *  Distance to horizontally offset resizeCursorTopRightBottomLeftSkin.
	 */
	[Style(name="resizeCursorTopRightBottomLeftXOffset", type="Number", inherit="no")]
	
	/**
	 *  Distance to vertically offset resizeCursorTopRightBottomLeftSkin.
	 */
	[Style(name="resizeCursorTopRightBottomLeftYOffset", type="Number", inherit="no")]
	
	
	/**
	 * Central window class used in flexlib.mdi. Includes min/max/close buttons by default.
	 */
	public class MDIWindow extends Panel
	{		
		/**
	     * Size of edge handles. Can be adjusted to affect "sensitivity" of resize area.
	     */
	    public var edgeHandleSize:Number = 6;
	    
	    /**
	     * Size of corner handles. Can be adjusted to affect "sensitivity" of resize area.
	     */
		public var cornerHandleSize:Number = 12;
	    
	    /**
	     * @private
	     * Internal storage for windowState property.
	     */
		private var _windowState:int;
		
		/**
	     * @private
	     * Internal storage of previous state, used in min/max/restore logic.
	     */
		private var _prevWindowState:int;
		
		/**
		 * @private
		 * Internal storage of style name to be applied when window is in focus.
		 */
		private var _styleNameFocus:String;
		
		/**
		 * @private
		 * Internal storage of style name to be applied when window is out of focus.
		 */
		private var _styleNameNoFocus:String;
		
		/**
	     * Parent of window controls (min, restore/max and close buttons).
	     */
		private var _windowControls:MDIWindowControlsContainer;
		
		/**
		 * @private
		 * Flag to determine whether or not close button is visible.
		 */
		private var _showCloseButton:Boolean = true;
		
		
		/**
		 * Flag determining whether or not this window is resizable.
		 */
		public var resizable:Boolean = true;
		
		/**
		 * Flag determining whether or not this window is draggable.
		 */
		public var draggable:Boolean = true;
		
		/**
	     * @private
	     * Resize handle for top edge of window.
	     */
		private var resizeHandleTop:Button;
		
		/**
	     * @private
	     * Resize handle for right edge of window.
	     */
		private var resizeHandleRight:Button;
		
		/**
	     * @private
	     * Resize handle for bottom edge of window.
	     */
		private var resizeHandleBottom:Button;
		
		/**
	     * @private
	     * Resize handle for left edge of window.
	     */
		private var resizeHandleLeft:Button;
		
		/**
	     * @private
	     * Resize handle for top left corner of window.
	     */
		private var resizeHandleTL:Button;
		
		/**
	     * @private
	     * Resize handle for top right corner of window.
	     */
		private var resizeHandleTR:Button;
		
		/**
	     * @private
	     * Resize handle for bottom right corner of window.
	     */
		private var resizeHandleBR:Button;
		
		/**
	     * @private
	     * Resize handle for bottom left corner of window.
	     */
		private var resizeHandleBL:Button;		
		
		/**
		 * Resize handle currently in use.
		 */
		private var currentResizeHandle:Button;
		
		/**
	     * Rectangle to represent window's size and position when resize begins
	     * or window's size/position is saved.
	     */
		public var savedWindowRect:Rectangle;
		
		/**
		 * @private
		 * Flag used to intelligently dispatch resize related events
		 */
		private var _resizing:Boolean;
		
		/**
		 * Invisible shape laid over titlebar to prevent funkiness from clicking in title textfield.
		 * Making it public gives child components like controls container access to size of titleBar.
		 */
		public var titleBarOverlay:Canvas;
		
		/**
		 * @private
		 * Flag used to intelligently dispatch drag related events
		 */
		private var _dragging:Boolean;
		
		/**
		 * @private
	     * Mouse's x position when resize begins.
	     */
		private var dragStartMouseX:Number;
		
		/**
		 * @private
	     * Mouse's y position when resize begins.
	     */
		private var dragStartMouseY:Number;
		
		/**
		 * @private
	     * Maximum allowable x value for resize. Used to enforce minWidth.
	     */
		private var dragMaxX:Number;
		
		/**
		 * @private
	     * Maximum allowable x value for resize. Used to enforce minHeight.
	     */
		private var dragMaxY:Number;
		
		/**
		 * @private
	     * Amount the mouse's x position has changed during current resizing.
	     */
		private var dragAmountX:Number;
		
		/**
		 * @private
	     * Amount the mouse's y position has changed during current resizing.
	     */
		private var dragAmountY:Number;
		
		/**
	     * Window's context menu.
	     */
		public var winContextMenu:ContextMenu = null;
		
		/**
		 * Reference to MDIManager instance this window is managed by, if any.
	     */
		public var windowManager:MDIManager;
		
		/**
		 * @private
		 * Storage var to hold value originally assigned to styleName since it gets toggled per focus change.
		 */
		private var _windowStyleName:Object;
		
		/**
		 * @private
		 * Storage var for hasFocus property.
		 */
		private var _hasFocus:Boolean;
		
		/**
		 * @private store the backgroundAlpha when minimized.
	     */
		private var backgroundAlphaRestore:Number = 1;
		
		[Embed(source="/flexlib/mdi/assets/img/fontcolor_toggle.png")]
		private static var DEFAULT_FONTCOLOR_BUTTON:Class;
		[Embed(source="/flexlib/mdi/assets/img/fontcolor_toggle_over.png")]
		private static var DEFAULT_FONTCOLOR_BUTTON_OVER:Class;
		
		[Embed(source="/flexlib/mdi/assets/img/fontsize_toggle.png")]
		private static var DEFAULT_FONTSIZE_BUTTON:Class;
		[Embed(source="/flexlib/mdi/assets/img/fontsize_toggle_over.png")]
		private static var DEFAULT_FONTSIZE_BUTTON_OVER:Class;
		
		[Embed(source="/flexlib/mdi/assets/img/close_window.png")]
		private static var DEFAULT_CLOSE_BUTTON:Class;
		[Embed(source="/flexlib/mdi/assets/img/close_window_over.png")]
		private static var DEFAULT_CLOSE_BUTTON_OVER:Class;
		
		[Embed(source="/flexlib/mdi/assets/img/resizeCursorH.gif")]
		private static var DEFAULT_RESIZE_CURSOR_HORIZONTAL:Class;
		private static var DEFAULT_RESIZE_CURSOR_HORIZONTAL_X_OFFSET:Number = -10;
		private static var DEFAULT_RESIZE_CURSOR_HORIZONTAL_Y_OFFSET:Number = -10;
		
		[Embed(source="/flexlib/mdi/assets/img/resizeCursorV.gif")]
		private static var DEFAULT_RESIZE_CURSOR_VERTICAL:Class;
		private static var DEFAULT_RESIZE_CURSOR_VERTICAL_X_OFFSET:Number = -10;
		private static var DEFAULT_RESIZE_CURSOR_VERTICAL_Y_OFFSET:Number = -10;
		
		[Embed(source="/flexlib/mdi/assets/img/resizeCursorTLBR.gif")]
		private static var DEFAULT_RESIZE_CURSOR_TL_BR:Class;
		private static var DEFAULT_RESIZE_CURSOR_TL_BR_X_OFFSET:Number = -10;
		private static var DEFAULT_RESIZE_CURSOR_TL_BR_Y_OFFSET:Number = -10;
		
		[Embed(source="/flexlib/mdi/assets/img/resizeCursorTRBL.gif")]
		private static var DEFAULT_RESIZE_CURSOR_TR_BL:Class;
		private static var DEFAULT_RESIZE_CURSOR_TR_BL_X_OFFSET:Number = -10;
		private static var DEFAULT_RESIZE_CURSOR_TR_BL_Y_OFFSET:Number = -10;
		
		[Embed(source='C:/WINDOWS/FONTS/VERDANAB.TTF', fontName='_verdanab', fontWeight='bold', unicodeRange='U+0020-U+0040,U+0041-U+005A')]
		public static var _verdanab:Class;

		private static var classConstructed:Boolean = classConstruct();
		
		/**
		 * Define and prepare default styles.
		 */
		private static function classConstruct():Boolean
		{
			//------------------------
		    //  type selector
		    //------------------------
			var selector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("MDIWindow");
			if(!selector)
			{
				selector = new CSSStyleDeclaration();
			}
			// these are default names for secondary styles. these can be set in CSS and will affect
			// all windows that don't have an override for these styles.
			selector.defaultFactory = function():void
			{
				this.styleNameFocus = "mdiWindowFocus";
				this.styleNameNoFocus = "mdiWindowNoFocus";
				
				this.titleStyleName = "mdiWindowTitleStyle";
				
				this.closeBtnStyleName = "mdiWindowCloseBtn";
				this.fontColorBtnStyleName = "mdiWindowFontColorBtn";
				this.fontSizeBtnStyleName = "mdiWindowFontSizeBtn";
				
				this.windowControlsClass = MDIWindowControlsContainer;
				
				this.resizeCursorHorizontalSkin = DEFAULT_RESIZE_CURSOR_HORIZONTAL;
				this.resizeCursorHorizontalXOffset = DEFAULT_RESIZE_CURSOR_HORIZONTAL_X_OFFSET;
				this.resizeCursorHorizontalYOffset = DEFAULT_RESIZE_CURSOR_HORIZONTAL_Y_OFFSET;
				
				this.resizeCursorVerticalSkin = DEFAULT_RESIZE_CURSOR_VERTICAL;
				this.resizeCursorVerticalXOffset = DEFAULT_RESIZE_CURSOR_VERTICAL_X_OFFSET;
				this.resizeCursorVerticalYOffset = DEFAULT_RESIZE_CURSOR_VERTICAL_Y_OFFSET;
				
				this.resizeCursorTopLeftBottomRightSkin = DEFAULT_RESIZE_CURSOR_TL_BR;
				this.resizeCursorTopLeftBottomRightXOffset = DEFAULT_RESIZE_CURSOR_TL_BR_X_OFFSET;
				this.resizeCursorTopLeftBottomRightYOffset = DEFAULT_RESIZE_CURSOR_TL_BR_Y_OFFSET;
				
				this.resizeCursorTopRightBottomLeftSkin = DEFAULT_RESIZE_CURSOR_TR_BL;
				this.resizeCursorTopRightBottomLeftXOffset = DEFAULT_RESIZE_CURSOR_TR_BL_X_OFFSET;
				this.resizeCursorTopRightBottomLeftYOffset = DEFAULT_RESIZE_CURSOR_TR_BL_Y_OFFSET;
			}
			
			//------------------------
		    //  focus style
		    //------------------------
			var styleNameFocus:String = selector.getStyle("styleNameFocus");
			var winFocusSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("." + styleNameFocus);
			if(!winFocusSelector)
			{
				winFocusSelector = new CSSStyleDeclaration();
			}
			winFocusSelector.defaultFactory = function():void
			{
				this.headerHeight = 26;
				this.roundedBottomCorners = true;
				this.borderColor = 0xADADAD;
				this.borderThicknessTop = 0;
				this.borderThicknessRight = 3;
				this.borderThicknessBottom = 3;
				this.borderThicknessLeft = 3;
				this.borderAlpha = 1;
				this.backgroundAlpha = 1.0;//.85;
			}
			StyleManager.setStyleDeclaration("." + styleNameFocus, winFocusSelector, false);
			
			//------------------------
		    //  no focus style
		    //------------------------
			var styleNameNoFocus:String = selector.getStyle("styleNameNoFocus");
			var winNoFocusSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("." + styleNameNoFocus);
			if(!winNoFocusSelector)
			{
				winNoFocusSelector = new CSSStyleDeclaration();
			}
			winNoFocusSelector.defaultFactory = function():void
			{
				this.headerHeight = 26;
				this.roundedBottomCorners = true;
				this.borderColor = 0xCCCCCC;
				this.borderThicknessTop = 0;
				this.borderThicknessRight = 3;
				this.borderThicknessBottom = 3;
				this.borderThicknessLeft = 3;
				this.borderAlpha = .5;
				this.backgroundAlpha = 1.0;//.5;
			}					
			StyleManager.setStyleDeclaration("." + styleNameNoFocus, winNoFocusSelector, false);

			
			//------------------------
		    //  title style
		    //------------------------
			flash.text.Font.registerFont(_verdanab);
			var titleStyleName:String = selector.getStyle("titleStyleName");
			var winTitleSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("." + titleStyleName);
			if(!winTitleSelector)
			{
				winTitleSelector = new CSSStyleDeclaration();
			}
			winTitleSelector.defaultFactory = function():void
			{
				this.fontFamily = "_verdanab";
				this.fontSize = 11;
				this.fontWeight = "bold";
				this.color = 0x000000;
			}
			StyleManager.setStyleDeclaration("." + titleStyleName, winTitleSelector, false);
			
			//------------------------
		    //  fontColor button
		    //------------------------
			var fontColorBtnStyleName:String = selector.getStyle("fontColorBtnStyleName");
			var fontColorBtnSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("." + fontColorBtnStyleName);
			if(!fontColorBtnSelector)
			{
				fontColorBtnSelector = new CSSStyleDeclaration();
			}
			fontColorBtnSelector.defaultFactory = function():void
			{
				this.upSkin = DEFAULT_FONTCOLOR_BUTTON;
				this.overSkin = DEFAULT_FONTCOLOR_BUTTON_OVER;
				this.downSkin = DEFAULT_FONTCOLOR_BUTTON;
				this.disabledSkin = DEFAULT_FONTCOLOR_BUTTON;
			}
			StyleManager.setStyleDeclaration("." + fontColorBtnStyleName, fontColorBtnSelector, false);
			
			//------------------------
		    //  fontSize button
		    //------------------------
			var fontSizeBtnStyleName:String = selector.getStyle("fontSizeBtnStyleName");
			var fontSizeBtnSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("." + fontSizeBtnStyleName);
			if(!fontSizeBtnSelector)
			{
				fontSizeBtnSelector = new CSSStyleDeclaration();
			}
			fontSizeBtnSelector.defaultFactory = function():void
			{
				this.upSkin = DEFAULT_FONTSIZE_BUTTON;
				this.overSkin = DEFAULT_FONTSIZE_BUTTON_OVER;
				this.downSkin = DEFAULT_FONTSIZE_BUTTON;
				this.disabledSkin = DEFAULT_FONTSIZE_BUTTON;
			}
			StyleManager.setStyleDeclaration("." + fontSizeBtnStyleName, fontSizeBtnSelector, false);
			
			//------------------------
		    //  close button
		    //------------------------
			var closeBtnStyleName:String = selector.getStyle("closeBtnStyleName");
			var closeBtnSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("." + closeBtnStyleName);
			if(!closeBtnSelector)
			{
				closeBtnSelector = new CSSStyleDeclaration();
			}
			closeBtnSelector.defaultFactory = function():void
			{
				this.upSkin = DEFAULT_CLOSE_BUTTON;
				this.overSkin = DEFAULT_CLOSE_BUTTON_OVER;
				this.downSkin = DEFAULT_CLOSE_BUTTON;
				this.disabledSkin = DEFAULT_CLOSE_BUTTON;
			}
			StyleManager.setStyleDeclaration("." + closeBtnStyleName, closeBtnSelector, false);
			
			// apply it all
			StyleManager.setStyleDeclaration("MDIWindow", selector, false);
			
			return true;
		}
		
		/**
		 * Constructor
	     */
		public function MDIWindow()
		{
			super();
			minWidth = minHeight = width = height = 225;
			windowState = MDIWindowState.NORMAL;
			doubleClickEnabled = false;
			
			windowControls = new MDIWindowControlsContainer();
		}
		
		public function get windowStyleName():Object
		{
			return _windowStyleName;
		}
		
		public function set windowStyleName(value:Object):void
		{
			if(_windowStyleName === value)
				return;
			
			_windowStyleName = value;
			updateStyles();
		}
		
		/**
		 * Create resize handles and window controls.
		 */
		override protected function createChildren():void
		{
			super.createChildren();
			
			if(!titleBarOverlay)
			{
				titleBarOverlay = new Canvas();
				titleBarOverlay.width = this.width;
				titleBarOverlay.height = this.titleBar.height;
				titleBarOverlay.alpha = 0;
				titleBarOverlay.setStyle("backgroundColor", 0x000000);
				rawChildren.addChild(titleBarOverlay);
			}
			
			// edges
			if(!resizeHandleTop)
			{
				resizeHandleTop = new Button();
				resizeHandleTop.x = cornerHandleSize * .5;
				resizeHandleTop.y = -(edgeHandleSize * .5);
				resizeHandleTop.height = edgeHandleSize;
				resizeHandleTop.alpha = 0;
				resizeHandleTop.focusEnabled = false;
				rawChildren.addChild(resizeHandleTop);
			}
			
			if(!resizeHandleRight)
			{
				resizeHandleRight = new Button();
				resizeHandleRight.y = cornerHandleSize * .5;
				resizeHandleRight.width = edgeHandleSize;
				resizeHandleRight.alpha = 0;
				resizeHandleRight.focusEnabled = false;
				rawChildren.addChild(resizeHandleRight);
			}
			
			if(!resizeHandleBottom)
			{
				resizeHandleBottom = new Button();
				resizeHandleBottom.x = cornerHandleSize * .5;
				resizeHandleBottom.height = edgeHandleSize;
				resizeHandleBottom.alpha = 0;
				resizeHandleBottom.focusEnabled = false;
				rawChildren.addChild(resizeHandleBottom);
			}
			
			if(!resizeHandleLeft)
			{
				resizeHandleLeft = new Button();
				resizeHandleLeft.x = -(edgeHandleSize * .5);
				resizeHandleLeft.y = cornerHandleSize * .5;
				resizeHandleLeft.width = edgeHandleSize;
				resizeHandleLeft.alpha = 0;
				resizeHandleLeft.focusEnabled = false;
				rawChildren.addChild(resizeHandleLeft);
			}
			
			// corners
			if(!resizeHandleTL)
			{
				resizeHandleTL = new Button();
				resizeHandleTL.x = resizeHandleTL.y = -(cornerHandleSize * .3);
				resizeHandleTL.width = resizeHandleTL.height = cornerHandleSize;
				resizeHandleTL.alpha = 0;
				resizeHandleTL.focusEnabled = false;
				rawChildren.addChild(resizeHandleTL);
			}
			
			if(!resizeHandleTR)
			{
				resizeHandleTR = new Button();
				resizeHandleTR.width = resizeHandleTR.height = cornerHandleSize;
				resizeHandleTR.alpha = 0;
				resizeHandleTR.focusEnabled = false;
				rawChildren.addChild(resizeHandleTR);
			}
			
			if(!resizeHandleBR)
			{
				resizeHandleBR = new Button();
				resizeHandleBR.width = resizeHandleBR.height = cornerHandleSize;
				resizeHandleBR.alpha = 0;
				resizeHandleBR.focusEnabled = false;
				rawChildren.addChild(resizeHandleBR);
			}
			
			if(!resizeHandleBL)
			{
				resizeHandleBL = new Button();
				resizeHandleBL.width = resizeHandleBL.height = cornerHandleSize;
				resizeHandleBL.alpha = 0;
				resizeHandleBL.focusEnabled = false;
				rawChildren.addChild(resizeHandleBL);
			}
			
			// bring windowControls to top as they are created in constructor
			rawChildren.setChildIndex(DisplayObject(windowControls), rawChildren.numChildren - 1);
			
			addListeners();
		}
		
		/**
		 * Position and size resize handles and window controls.
		 */
		override protected function updateDisplayList(w:Number, h:Number):void
		{
			super.updateDisplayList(w, h);
			
			titleBarOverlay.width = this.width;
			titleBarOverlay.height = this.titleBar.height;
			
			// edges
			resizeHandleTop.x = cornerHandleSize * .5;
			resizeHandleTop.y = -(edgeHandleSize * .5);
			resizeHandleTop.width = this.width - cornerHandleSize;
			resizeHandleTop.height = edgeHandleSize;
			
			resizeHandleRight.x = this.width - edgeHandleSize * .5;
			resizeHandleRight.y = cornerHandleSize * .5;
			resizeHandleRight.width = edgeHandleSize;
			resizeHandleRight.height = this.height - cornerHandleSize;
			
			resizeHandleBottom.x = cornerHandleSize * .5;
			resizeHandleBottom.y = this.height - edgeHandleSize * .5;
			resizeHandleBottom.width = this.width - cornerHandleSize;
			resizeHandleBottom.height = edgeHandleSize;
			
			resizeHandleLeft.x = -(edgeHandleSize * .5);
			resizeHandleLeft.y = cornerHandleSize * .5;
			resizeHandleLeft.width = edgeHandleSize;
			resizeHandleLeft.height = this.height - cornerHandleSize;
			
			// corners
			resizeHandleTL.x = resizeHandleTL.y = -(cornerHandleSize * .5);
			resizeHandleTL.width = resizeHandleTL.height = cornerHandleSize;
			
			resizeHandleTR.x = this.width - cornerHandleSize * .5;
			resizeHandleTR.y = -(cornerHandleSize * .5);
			resizeHandleTR.width = resizeHandleTR.height = cornerHandleSize;
			
			resizeHandleBR.x = this.width - cornerHandleSize * .5;
			resizeHandleBR.y = this.height - cornerHandleSize * .5;
			resizeHandleBR.width = resizeHandleBR.height = cornerHandleSize;
			
			resizeHandleBL.x = -(cornerHandleSize * .5);
			resizeHandleBL.y = this.height - cornerHandleSize * .5;
			resizeHandleBL.width = resizeHandleBL.height = cornerHandleSize;
			
			// cause windowControls container to update
			UIComponent(windowControls).invalidateDisplayList();
		}
		
		
		public function get hasFocus():Boolean
		{
			return _hasFocus;
		}
		
		/**
		 * Property is set by MDIManager when a window's focus changes. Triggers an update to the window's styleName.
		 */
		public function set hasFocus(value:Boolean):void
		{
			// guard against unnecessary processing
			if(_hasFocus == value)
				return;
			
			// set new value
			_hasFocus = value;
			updateStyles();
		}
		
		/**
		 * Mother of all styling functions. All styles fall back to the defaults if necessary.
		 */
		private function updateStyles():void
		{
			var selectorList:Array = getSelectorList();
			
			// if the style specifies a class to use for the controls container that is
			// different from the current one we will update it here
			if(getStyleByPriority(selectorList, "windowControlsClass"))
			{
				var clazz:Class = getStyleByPriority(selectorList, "windowControlsClass") as Class;
				var classNameExisting:String = getQualifiedClassName(windowControls);
				var classNameNew:String = getQualifiedClassName(clazz);
				
				if(classNameExisting != classNameNew)
				{
					windowControls = new clazz();
					// sometimes necessary to adjust windowControls subcomponents
					callLater(windowControls.invalidateDisplayList);
				}
			}
			
			// set window's styleName based on focus status
			if(hasFocus)
			{
				setStyle("styleName", getStyleByPriority(selectorList, "styleNameFocus"));
			}
			else
			{
				setStyle("styleName", getStyleByPriority(selectorList, "styleNameNoFocus"));
			}
			
			// style the window's title
			// this code is probably not as efficient as it could be but i am sick of dealing with styling
			// if titleStyleName (the style inherited from Panel) has been set we use that, regardless of focus
			if(!hasFocus && getStyleByPriority(selectorList, "titleStyleNameNoFocus"))
			{
				setStyle("titleStyleName", getStyleByPriority(selectorList, "titleStyleNameNoFocus"));
			}
			else if(getStyleByPriority(selectorList, "titleStyleNameFocus"))
			{
				setStyle("titleStyleName", getStyleByPriority(selectorList, "titleStyleNameFocus"));
			}
			else
			{
				getStyleByPriority(selectorList, "titleStyleName")
			}
			
			// style fontColor button
			if(fontColorBtn)
			{
				// use noFocus style if appropriate and one exists
				if(!hasFocus && getStyleByPriority(selectorList, "fontColorBtnStyleNameNoFocus"))
				{
					fontColorBtn.styleName = getStyleByPriority(selectorList, "fontColorBtnStyleNameNoFocus");
				}
				else
				{
					fontColorBtn.styleName = getStyleByPriority(selectorList, "fontColorBtnStyleName");
				}
			}
			
			// style fontSize button
			if(fontSizeBtn)
			{
				// use noFocus style if appropriate and one exists
				if(!hasFocus && getStyleByPriority(selectorList, "fontSizeBtnStyleNameNoFocus"))
				{
					fontSizeBtn.styleName = getStyleByPriority(selectorList, "fontSizeBtnStyleNameNoFocus");
				}
				else
				{
					fontSizeBtn.styleName = getStyleByPriority(selectorList, "fontSizeBtnStyleName");
				}
			}
			
			// style close button
			if(closeBtn)
			{
				// use noFocus style if appropriate and one exists
				if(!hasFocus && getStyleByPriority(selectorList, "closeBtnStyleNameNoFocus"))
				{
					closeBtn.styleName = getStyleByPriority(selectorList, "closeBtnStyleNameNoFocus");
				}
				else
				{
					closeBtn.styleName = getStyleByPriority(selectorList, "closeBtnStyleName");
				}
			}
		}
		
		protected function getSelectorList():Array
		{
			// initialize array with ref to ourself since inline styles take highest priority
			var selectorList:Array = new Array(this);
			
			// if windowStyleName was set by developer we associated styles to the list
			if(windowStyleName)
			{
				// make sure a corresponding style actually exists
				var classSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("." + windowStyleName);
				if(classSelector)
				{
					selectorList.push(classSelector);
				}
			}
			// add type selector (created in classConstruct so we know it exists)
			var typeSelector:CSSStyleDeclaration = StyleManager.getStyleDeclaration("MDIWindow");
			selectorList.push(typeSelector);
			
			return selectorList;
		}
		
		/**
		 * Function to return appropriate style based on our funky setup.
		 * Precedence of styles is inline, class selector (as specified by windowStyleName)
		 * and then type selector (MDIWindow).
		 * 
		 * @private
		 */
		protected function getStyleByPriority(selectorList:Array, style:String):Object
		{			
			var n:int = selectorList.length;			
			
			for(var i:int = 0; i < n; i++)
			{
				// we need to make sure this.getStyle() is not pointing to the style defined
				// in the type selector because styles defined in the class selector (windowStyleName)
				// should take precedence over type selector (MDIWindow) styles
				// this.getStyle() will return styles from the type selector if an inline
				// style was not specified
				if(selectorList[i] == this 
				&& selectorList[i].getStyle(style) 
				&& this.getStyle(style) === selectorList[n - 1].getStyle(style))
				{
					continue;
				}
				if(selectorList[i].getStyle(style))
				{
					// if this is a style name make sure the style exists
					if(typeof(selectorList[i].getStyle(style)) == "string"
						&& !(StyleManager.getStyleDeclaration("." + selectorList[i].getStyle(style))))
					{
						continue;
					}
					else
					{
						return selectorList[i].getStyle(style);
					}
				}
			}
			
			return null;
		}
		
		/**
		 * Detects change to styleName that is executed by MDIManager indicating a change in focus.
		 * Iterates over window controls and adjusts their styles if they're focus-aware.
		 */
		override public function styleChanged(styleProp:String):void
		{
			super.styleChanged(styleProp);
			
			if(!styleProp || styleProp == "styleName")
				updateStyles(); 
		}
		
		/**
		 * Reference to class used to create windowControls property.
		 */
		public function get windowControls():MDIWindowControlsContainer
		{
			return _windowControls;
		}
		
		/**
		 * When reference is set windowControls will be reinstantiated, meaning runtime switching is supported.
		 */
		public function set windowControls(controlsContainer:MDIWindowControlsContainer):void
		{
			if(_windowControls)
			{
				var cntnr:Container = Container(windowControls);
				cntnr.removeAllChildren();
				rawChildren.removeChild(cntnr);
				_windowControls = null;
			}
			
			_windowControls = controlsContainer;
			_windowControls.window = this;
			rawChildren.addChild(UIComponent(_windowControls));
		}
				
		/**
		 * fontColor window button.
		 */
		public function get fontColorBtn():Button
		{
			return windowControls.fontColorBtn;
		}
		
		/**
		 * fontSize window button.
		 */
		public function get fontSizeBtn():Button
		{
			return windowControls.fontSizeBtn;
		}
		
		/**
		 * display notes checkbox.
		 */
		public function get displayNotesCbox():CheckBox
		{
			return windowControls.displayNotesCbox;
		}
		
		public function get displayInfoCbox():CheckBox
		{
			return windowControls.displayInfoCbox;
		}
		
		/**
		 * Close window button.
		 */
		public function get closeBtn():Button
		{
			return windowControls.closeBtn;
		}
		
		public function get showCloseButton():Boolean
		{
			return _showCloseButton;
		}
		
		public function set showCloseButton(value:Boolean):void
		{
			_showCloseButton = value;
			if(closeBtn && closeBtn.visible != value)
			{
				closeBtn.visible = value;
				invalidateDisplayList();
			}
		}
		
		/**
		 * Returns reference to titleTextField which is protected by default.
		 * Provided to allow MDIWindowControlsContainer subclasses as much freedom as possible.
		 */
		public function getTitleTextField():UITextField
		{
			return titleTextField as UITextField;
		}
		
		/**
		 * Returns reference to titleIconObject which is mx_internal by default.
		 * Provided to allow MDIWindowControlsContainer subclasses as much freedom as possible.
		 */
		public function getTitleIconObject():DisplayObject
		{
			use namespace mx_internal;
			return titleIconObject as DisplayObject;
		}
		
		/**
		 * Save style settings for minimizing.
	     */
		public function saveStyle():void
		{
			this.backgroundAlphaRestore = this.getStyle("backgroundAlpha");
		}
		
		/**
		 * Restores style settings for restore and maximize
	     */
		public function restoreStyle():void
		{
			this.setStyle("backgroundAlpha", this.backgroundAlphaRestore);
		}
		
		/**
		 * Add listeners for resize handles and window controls.
		 */
		private function addListeners():void
		{
			// edges
			resizeHandleTop.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleTop.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleTop.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			resizeHandleRight.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleRight.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleRight.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			resizeHandleBottom.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleBottom.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleBottom.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			resizeHandleLeft.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleLeft.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleLeft.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			// corners
			resizeHandleTL.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleTL.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleTL.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			resizeHandleTR.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleTR.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleTR.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			resizeHandleBR.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleBR.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleBR.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			resizeHandleBL.addEventListener(MouseEvent.ROLL_OVER, onResizeButtonRollOver, false, 0, true);
			resizeHandleBL.addEventListener(MouseEvent.ROLL_OUT, onResizeButtonRollOut, false, 0, true);
			resizeHandleBL.addEventListener(MouseEvent.MOUSE_DOWN, onResizeButtonPress, false, 0, true);
			
			// titleBar overlay
			titleBarOverlay.addEventListener(MouseEvent.MOUSE_DOWN, onTitleBarPress, false, 0, true);
			titleBarOverlay.addEventListener(MouseEvent.MOUSE_UP, onTitleBarRelease, false, 0, true);
			
			// window controls
			addEventListener(MouseEvent.CLICK, windowControlClickHandler, false, 0, true);
			
			// clicking anywhere brings window to front
//			addEventListener(MouseEvent.MOUSE_DOWN, bringToFrontProxy);
//			contextMenu.addEventListener(ContextMenuEvent.MENU_SELECT, bringToFrontProxy);
		}
		
		/**
		 * Click handler for default window controls (minimize, maximize/restore and close).
		 */
		private function windowControlClickHandler(event:MouseEvent):void
		{
			if(windowControls)
			{
				if (windowControls.fontSizeBtn && event.target == windowControls.fontSizeBtn)
				{
					dispatchToggleFontSize(event);
				}
				else if (windowControls.fontColorBtn && event.target == windowControls.fontColorBtn)
				{
					dispatchToggleFontColor(event);
				}
				else if (windowControls.displayNotesCbox && event.target == windowControls.displayNotesCbox) 
				{
					dispatchToggleDisplayInfoNotes(windowControls.displayNotesCbox.selected, windowControls.displayInfoCbox.selected, event);
				}
				else if (windowControls.displayInfoCbox && event.target == windowControls.displayInfoCbox) 
				{
					dispatchToggleDisplayInfoNotes(windowControls.displayNotesCbox.selected, windowControls.displayInfoCbox.selected, event);
				}
				else if (windowControls.closeBtn && event.target == windowControls.closeBtn)
				{
					close();
				}
			}
		}
		
		/**
		 * Called automatically by clicking on window this now delegates execution to the manager.
		 */
		private function bringToFrontProxy(event:Event):void
		{
			windowManager.bringToFront(this);
		}
		/**
		 * Dispatch toggle fontcolor event.
		 */
		public function dispatchToggleFontColor(e:MouseEvent = null):void
		{
			var myWindowEvent:MDIWindowEvent = new MDIWindowEvent(MDIWindowEvent.FONTCOLOR, this);
			myWindowEvent.panePosition = e.currentTarget.panePosition;
			dispatchEvent(myWindowEvent);
		}
		
		/**
		 * Dispatch toggle fontsize event.
		 */
		public function dispatchToggleFontSize(e:MouseEvent = null):void
		{
			var myWindowEvent:MDIWindowEvent = new MDIWindowEvent(MDIWindowEvent.FONTSIZE, this);
			myWindowEvent.panePosition = e.currentTarget.panePosition;
			dispatchEvent(myWindowEvent);
		}
		
		/**
		 * Dispatch toggle displayinfonotes event.
		 */
		public function dispatchToggleDisplayInfoNotes(isNotesSelected:Boolean, isInfoSelected:Boolean, e:MouseEvent = null):void
		{
			var myWindowEvent:MDIWindowEvent = new MDIWindowEvent(MDIWindowEvent.DISPLAYINFONOTES, this);
			myWindowEvent.panePosition = e.currentTarget.panePosition;
			dispatchEvent(myWindowEvent);
			//dispatchEvent(new MDIWindowEvent(MDIWindowEvent.DISPLAYNOTES, this));
		}
				
		/**
		 * Close the window.
		 */
		public function close(event:MouseEvent = null):void
		{
			dispatchEvent(new MDIWindowEvent(MDIWindowEvent.CLOSE, this));
		}
		
		/**
		 * Save the panel's floating coordinates.
		 * 
		 * @private
		 */
		private function savePanel():void
		{
			savedWindowRect = new Rectangle(this.x, this.y, this.width, this.height);
		}
		
		/**
		 * Title bar dragging.
		 * 
		 * @private
		 */
		private function onTitleBarPress(event:MouseEvent):void
		{
			// only floating windows can be dragged
			if(this.windowState == MDIWindowState.NORMAL && draggable)
			{
				if(windowManager.enforceBoundaries)
				{
					this.startDrag(false, new Rectangle(0, 0, parent.width - this.width, parent.height - this.height));
				}
				else
				{
					this.startDrag();
				}				
				
				systemManager.addEventListener(MouseEvent.MOUSE_MOVE, onWindowMove);
				systemManager.addEventListener(MouseEvent.MOUSE_UP, onTitleBarRelease);
				systemManager.stage.addEventListener(Event.MOUSE_LEAVE, onTitleBarRelease);
			}
		}
		
		private function onWindowMove(event:MouseEvent):void
		{
			if(!_dragging)
			{
				_dragging = true;
				// clear styles (future versions may allow enforcing constraints on drag)
				this.clearStyle("top");
				this.clearStyle("right");
				this.clearStyle("bottom");
				this.clearStyle("left");
				dispatchEvent(new MDIWindowEvent(MDIWindowEvent.DRAG_START, this));
			}
			dispatchEvent(new MDIWindowEvent(MDIWindowEvent.DRAG, this));
		}
		
		private function onTitleBarRelease(event:Event):void
		{
			this.stopDrag();
			if(_dragging)
			{
				_dragging = false;
				dispatchEvent(new MDIWindowEvent(MDIWindowEvent.DRAG_END, this));
			}
			systemManager.removeEventListener(MouseEvent.MOUSE_MOVE, onWindowMove);
			systemManager.removeEventListener(MouseEvent.MOUSE_UP, onTitleBarRelease);
			systemManager.stage.removeEventListener(Event.MOUSE_LEAVE, onTitleBarRelease);
		}
		
		/**
		 * Mouse down on any resize handle.
		 */
		private function onResizeButtonPress(event:MouseEvent):void
		{
			if(windowState == MDIWindowState.NORMAL && resizable)
			{
				currentResizeHandle = event.target as Button;
				setCursor(currentResizeHandle);
				dragStartMouseX = parent.mouseX;
				dragStartMouseY = parent.mouseY;
				savePanel();
				
				dragMaxX = savedWindowRect.x + (savedWindowRect.width - minWidth);
				dragMaxY = savedWindowRect.y + (savedWindowRect.height - minHeight);
				
				systemManager.addEventListener(Event.ENTER_FRAME, updateWindowSize, false, 0, true);
				systemManager.addEventListener(MouseEvent.MOUSE_MOVE, onResizeButtonDrag, false, 0, true);
				systemManager.addEventListener(MouseEvent.MOUSE_UP, onResizeButtonRelease, false, 0, true);
				systemManager.stage.addEventListener(Event.MOUSE_LEAVE, onMouseLeaveStage, false, 0, true);
			}
		}
		
		private function onResizeButtonDrag(event:MouseEvent):void
		{
			if(!_resizing)
			{
				_resizing = true;
				dispatchEvent(new MDIWindowEvent(MDIWindowEvent.RESIZE_START, this));
			}			
			dispatchEvent(new MDIWindowEvent(MDIWindowEvent.RESIZE, this));
		}
		
		/**
		 * Mouse move while mouse is down on a resize handle
		 */
		private function updateWindowSize(event:Event):void
		{
			if(windowState == MDIWindowState.NORMAL && resizable)
			{
				dragAmountX = parent.mouseX - dragStartMouseX;
				dragAmountY = parent.mouseY - dragStartMouseY;
				
				if(currentResizeHandle == resizeHandleTop && parent.mouseY > 0)
				{
					this.y = Math.min(savedWindowRect.y + dragAmountY, dragMaxY);
					this.height = Math.max(savedWindowRect.height - dragAmountY, minHeight);
				}
				else if(currentResizeHandle == resizeHandleRight && parent.mouseX < parent.width)
				{
					this.width = Math.max(savedWindowRect.width + dragAmountX, minWidth);
				}
				else if(currentResizeHandle == resizeHandleBottom && parent.mouseY < parent.height)
				{
					this.height = Math.max(savedWindowRect.height + dragAmountY, minHeight);
				}
				else if(currentResizeHandle == resizeHandleLeft && parent.mouseX > 0)
				{
					this.x = Math.min(savedWindowRect.x + dragAmountX, dragMaxX);
					this.width = Math.max(savedWindowRect.width - dragAmountX, minWidth);
				}
				else if(currentResizeHandle == resizeHandleTL && parent.mouseX > 0 && parent.mouseY > 0)
				{
					this.x = Math.min(savedWindowRect.x + dragAmountX, dragMaxX);
					this.y = Math.min(savedWindowRect.y + dragAmountY, dragMaxY);
					this.width = Math.max(savedWindowRect.width - dragAmountX, minWidth);
					this.height = Math.max(savedWindowRect.height - dragAmountY, minHeight);				
				}
				else if(currentResizeHandle == resizeHandleTR && parent.mouseX < parent.width && parent.mouseY > 0)
				{
					this.y = Math.min(savedWindowRect.y + dragAmountY, dragMaxY);
					this.width = Math.max(savedWindowRect.width + dragAmountX, minWidth);
					this.height = Math.max(savedWindowRect.height - dragAmountY, minHeight);
				}
				else if(currentResizeHandle == resizeHandleBR && parent.mouseX < parent.width && parent.mouseY < parent.height)
				{
					this.width = Math.max(savedWindowRect.width + dragAmountX, minWidth);
					this.height = Math.max(savedWindowRect.height + dragAmountY, minHeight);
				}
				else if(currentResizeHandle == resizeHandleBL && parent.mouseX > 0 && parent.mouseY < parent.height)
				{
					this.x = Math.min(savedWindowRect.x + dragAmountX, dragMaxX);
					this.width = Math.max(savedWindowRect.width - dragAmountX, minWidth);
					this.height = Math.max(savedWindowRect.height + dragAmountY, minHeight);
				}
			}
		}
		
		private function onResizeButtonRelease(event:MouseEvent = null):void
		{
			if(windowState == MDIWindowState.NORMAL && resizable)
			{
				if(_resizing)
				{
					_resizing = false;
					dispatchEvent(new MDIWindowEvent(MDIWindowEvent.RESIZE_END, this));
				}
				currentResizeHandle = null;
				systemManager.removeEventListener(Event.ENTER_FRAME, updateWindowSize);
				systemManager.removeEventListener(MouseEvent.MOUSE_MOVE, onResizeButtonDrag);
				systemManager.removeEventListener(MouseEvent.MOUSE_UP, onResizeButtonRelease);
				systemManager.stage.removeEventListener(Event.MOUSE_LEAVE, onMouseLeaveStage);
				CursorManager.removeCursor(CursorManager.currentCursorID);
			}
		}
		
		private function onMouseLeaveStage(event:Event):void
		{
			onResizeButtonRelease();
			systemManager.stage.removeEventListener(Event.MOUSE_LEAVE, onMouseLeaveStage);
		}
		
		
		private function setCursor(target:Button):void
		{
			var styleStub:String;			
			
			switch(target)
			{
				case resizeHandleRight:
				case resizeHandleLeft:
					styleStub = "resizeCursorHorizontal";
				break;
				
				case resizeHandleTop:
				case resizeHandleBottom:
					styleStub = "resizeCursorVertical";
				break;
				
				case resizeHandleTL:
				case resizeHandleBR:
					styleStub = "resizeCursorTopLeftBottomRight";
				break;
				
				case resizeHandleTR:
				case resizeHandleBL:
					styleStub = "resizeCursorTopRightBottomLeft";
				break;
			}
			
			var selectorList:Array = getSelectorList();
			
			resizeComponent.cursorManager.removeCursor(resizeComponent.cursorManager.currentCursorID);
			resizeComponent.cursorManager.setCursor(Class(getStyleByPriority(selectorList, styleStub + "Skin")), 
									2, 
									Number(getStyleByPriority(selectorList, styleStub + "XOffset")), 
									Number(getStyleByPriority(selectorList, styleStub + "YOffset")));
		}
		
		private function onResizeButtonRollOver(event:MouseEvent):void
		{
			// only floating windows can be resized
			// event.buttonDown is to detect being dragged over
			if(windowState == MDIWindowState.NORMAL && resizable && !event.buttonDown)
			{
				setCursor(event.target as Button);
			}
		}
		
		private function onResizeButtonRollOut(event:MouseEvent):void
		{
			if(!event.buttonDown)
			{
				CursorManager.removeCursor(CursorManager.currentCursorID);
			}
		}
		
		public function set showControls(value:Boolean):void
		{
			Container(windowControls).visible = value;
		}
		
		private function get windowState():int
		{
			return _windowState;
		}
		
		private function set windowState(newState:int):void
		{
			_prevWindowState = _windowState;
			_windowState = newState;
		}
		
	}
}