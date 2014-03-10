package com.adobe.controls
{
	import flash.display.Bitmap;
	import flash.display.BitmapData;
	import flash.display.DisplayObject;
	import flash.display.Graphics;
	import flash.display.Sprite;
	import flash.events.ErrorEvent;
	import flash.filters.BlurFilter;
	import flash.geom.ColorTransform;
	import flash.geom.Matrix;
	import flash.geom.Rectangle;
	import flash.utils.Dictionary;
	
	import mx.collections.ArrayCollection;
	import mx.controls.listClasses.IListItemRenderer;
	import mx.controls.listClasses.ListItemRenderer;
	import mx.core.EdgeMetrics;
	import mx.core.IDataRenderer;
	import mx.core.IFactory;
	import mx.core.IInvalidating;
	import mx.core.IUIComponent;
	import mx.core.UIComponent;
	import mx.core.UIComponentGlobals;
	import mx.effects.AnimateProperty;
	import mx.effects.Blur;
	import mx.effects.Fade;
	import mx.effects.Move;
	import mx.effects.TweenEffect;
	import mx.effects.easing.Bounce;
	import mx.effects.easing.Quadratic;
	import mx.events.EffectEvent;
	import mx.events.TweenEvent;
	import mx.managers.ILayoutManager;
	import mx.managers.ILayoutManagerClient;
	import mx.managers.LayoutManager;
	
	
	
	/**
	 *  Color of the proxy for items not in the cache.
	 */
	[Style(name="proxyColor", type="Color", inherit="no")]
	/**
	*  The fade out time of the proxy from proxyAlpha to zero once the animation
	 * is complete on a multipage scroll.
	*/	
	[Style(name="proxyDuration", type="uint", inherit="no")]
	/**
	* The amount of alpha applied to the proxy image.
	*/	
	[Style(name="proxyAlpha", type="Number", inherit="no")]	
	/**
	* The minimum amount of spacing between the items.
	*/	
	[Style(name="spacing", type="Number", inherit="no")]
	
	
	public class PagedList extends UIComponent
	{
		private var _dataProvider:ArrayCollection;
		private var _itemRenderer:IFactory;
		private var _renderers:Dictionary;
		private var _rendererPool:Array = [];
		private var visibleItems:Array;
		
		private var _itemsDirty:Boolean;
		private var _renderersDirty:Boolean;
		
		//private var _spacing:uint = 10;
		
		private var _currentPage:uint = 0;
		private var _pendingPage:uint;
		private var _totalPages:uint;
		[Bindable] public var itemsPerPage:uint;
		private var itemsToRender:int;

		private var direction:String;
		public const DIRECTION_FORWARD:String = "forward";
		public const DIRECTION_REVERSE:String = "reverse";
		
		private var templateItem:IListItemRenderer;
		
		private var pageMetrics:EdgeMetrics;
		private var viewMetrics:EdgeMetrics;
		private var oldViewMetrics:EdgeMetrics;
		
		private var multipageScroll:Boolean = false;
		/**
		* Made public to allow querying 
		*/		
		public var animating:Boolean = false;
		private var _animateProperties:Array = [];
			
		public function PagedList()
		{
			_renderers = new Dictionary();
			pageMetrics = new EdgeMetrics();
			super();
		}

		/**
		 * Instead of building all the renderers in the dataProvider Ely suggested creating 
		 * a pool of renderers we need as dictated by the viewable area. Since the 
		 * commitProperties is called  after updateDisplayList, where the number of 
		 * visible items per page is determined, the commit properties will be decoupled
		 * from the assigning of content and addition of children to the display list.
		 * 
		 * This leaves the commitProperties as just a call to updateDisplayList when the 
		 * data is dirty.
		 * 
		 * Note: You cannot get explicitOrMeasuredWidth/Height here, I always forget
		 * 
		 */		
		override protected  function commitProperties():void
		{
			if(!_dataProvider) 
				return;
			
			_itemsDirty = true;
			invalidateDisplayList();
			
			super.commitProperties();
		}
		
		/**
		 * Checks resized and dirty items renderers
		 * 
		 * @param unscaledWidth
		 * @param unscaledHeight
		 * 
		 */		
		override protected function updateDisplayList(unscaledWidth:Number, unscaledHeight:Number):void
		{
			if(!_dataProvider)
				return;
			
			// need the dimentions of the component for 
			// pagination
			viewMetrics = new EdgeMetrics(0,0,unscaledWidth,unscaledHeight);
			// check to see if the page width/height has changed or if
			// it is the first pass through if so re draw the page. 					
			if(!oldViewMetrics ||
				viewMetrics.right != oldViewMetrics.right ||
				viewMetrics.bottom != oldViewMetrics.bottom)
				_renderersDirty = true;
			
			measurePage();			
			
			oldViewMetrics = viewMetrics;
		}
		/**
		 * Measures the number of items that fit in a page. It uses the first item of the
		 * list as a template item. 
		 * 
		 */		
		private function measurePage():void 
		{
			
			var vm:EdgeMetrics = viewMetrics;
			var pm:EdgeMetrics = pageMetrics = new EdgeMetrics(); // page metrics
			var inLayout:Boolean = true;
			
			// get a measuring item which is not visible but used for 
			// measuring the items 
			var item:IListItemRenderer = getMeasuringRenderer();
			setupRendererFromData(item,_dataProvider.getItemAt(0));			

			// check to make sure we are not measuring based on a zero width this occurs 
			// on the first pass or so of the updateDisplayList
			if(item.getExplicitOrMeasuredWidth() < 0 || item.getExplicitOrMeasuredHeight() < 0) 
				return;
			
			itemsPerPage = 0;
			
			// first figure out the page metrics, how many can fit per
			// page and subsiquently how many pages are there 
			
			while(inLayout) {
				var itemsWidth:uint = pm.right +item.getExplicitOrMeasuredWidth() + pSpacing;
												
				if(itemsWidth < vm.right) {
					pm.right = itemsWidth;			
					itemsPerPage++;
				} else {
					inLayout = false;
				}		
			} 
	

			totalPages = Math.ceil(_dataProvider.length/itemsPerPage);
			// bug
			if(_currentPage >= totalPages)  {
				currentPage = totalPages - 1;
				
			}
			//trace("items: "+_dataProvider.length+" perPage: "+itemsPerPage+" totalPages: "+totalPages+" currentPage: "+_currentPage);			
			var visiblePages:uint 				= (_currentPage == 0 || _currentPage == (totalPages-1))? 2 :3;
			var maxItemsToRender:uint 			= visiblePages * itemsPerPage;
			var remainingItems:uint 			= (_currentPage == 0)? (_dataProvider.length-itemsPerPage) : (_dataProvider.length-((_currentPage-1)*itemsPerPage));
			// used in commitRenderers and doAnimation
			itemsToRender						= Math.min(maxItemsToRender,remainingItems);
			
			
			commitRenderers(visiblePages);
			
		}
		/**
		 * Commits or stores renderers based on the number of visible pages which can be
		 * 2 or3 depending on the position in the list.
		 * 
		 * 
		 * @param visiblePages
		 * 
		 */				
		private function commitRenderers(visiblePages:uint):void 
		{	
			var vm:EdgeMetrics = viewMetrics;
			var pm:EdgeMetrics = pageMetrics;
			var item:IListItemRenderer = getMeasuringRenderer();
			setupRendererFromData(item,_dataProvider.getItemAt(0));	
			
			var pageCounter:uint = 0; // tracks the page 0,1 or 2 
			
			var evenSpacing:uint = (vm.right-pm.right)/itemsPerPage; 			
			
			// mark all items to be deleted and 
			// force them to earn being shown
			for (var d:Object in _renderers) {
				 Destination(d).state = "removed";
			}
			
			var pageItemOffset:uint = itemsPerPage * Math.max(Math.min((totalPages-1),(_currentPage - 1)),0);
			visibleItems = [];

			for(var i:uint=0; i < itemsToRender; i++) {
				
				// get the current absolute position of the item in the data provider				
				// get data associated with the current item and then get the cached
				// ItemRenderer if there is one. 
				var currentItem:uint = pageItemOffset+i; 				
				// don't go past the end!
				if(currentItem < _dataProvider.length) {
				
					var data:Object = _dataProvider.getItemAt(currentItem);
					// this checks to see if we have the item in the display list already
					// if we do then we just reassign it if not a new Renderer is needed
					var cachedItem:IListItemRenderer = getItemAt(currentItem) ;
			
					if(!cachedItem) {					
						var destination:Destination = new Destination();
						item = getRenderer();
						
						setupRendererFromData(item,data);
						destination.state = "added";
						destination.position = currentItem;
						_renderers[destination] = item;
						addChildAt(DisplayObject(item),0);
						
					} else {
						
						if(data != cachedItem.data)
							cachedItem.data = data;
													
						item = cachedItem;

					}
					// only make the items visible if we are not animating otherwise 
					// they will show behind the animated bitmap. They will be made
					// visible when the bitmap is done animating
					if(animating) {
						item.visible = false;
					} else {
						item.visible = true;
					}
					
					// spacing and positiong of the items it's only center positioning for now
					if(pm.right >= vm.right) {
						item.x = i * (item.getExplicitOrMeasuredWidth()+pSpacing) ;
					} else {
						var division:int = Math.round(vm.right / itemsPerPage);
						var divistionMidpoint:int = division * .5;
						var currentItemNumber:int = i + 1;
						
						item.x = (currentItemNumber*division) - divistionMidpoint - (item.getExplicitOrMeasuredWidth()*.5);					
					}
					if((i+1)%itemsPerPage == 0) 
						pageCounter++;
					
					visibleItems.push(item);
				}
			}	
			// set the scrollRect mask in one viewRect.right if
			// we are not on the first page
			if(_currentPage == 0) 
			{
				scrollX = 0;
			}  else {
				scrollX = vm.right;
			}
			
			// remove the references to the renderers we don't need. 
			for (d in _renderers) {				
				if(Destination(d).state == "removed") {
					storeRenderer(UIComponent(_renderers[d]));
					removeChild(UIComponent(_renderers[d]));					
					delete _renderers[d];
				}
			}

			_renderersDirty = false;
		}
		
		
		/**
		 * This retrieves a Renderer at the position we need in the pagedList
		 * and prepares it for viewing by setting the state to animation. Others
		 * in the _renderers list will be cleaned up.
		 * @param position
		 * @return 
		 * 
		 */		
		private function getItemAt(position:uint):IListItemRenderer 
		{
			var li:IListItemRenderer;
			for (var d:Object in _renderers) {
				if(position == Destination(d).position) {
					d.state = "animation";
					li = _renderers[d];	
					return li as IListItemRenderer;
				}
			}			
			return null;
		}
		/**
		 * Measures the container. 
		 * 
		 */		
		override protected function measure():void
		{
			var mHeight:Number = 0;
			var mWidth:Number = 0;
			
			if(itemsPerPage == 0)
				return;
				
			var item:IListItemRenderer = getMeasuringRenderer();
			mHeight = Math.max(mHeight,item.getExplicitOrMeasuredHeight());
			
			for(var i:uint=0; i< itemsPerPage;i++)
			{
				setupRendererFromData(item,_dataProvider.getItemAt(0));
				mWidth += item.getExplicitOrMeasuredWidth() + pSpacing ;
			}
			
			measuredWidth = mWidth;
			measuredHeight = mHeight;
		}
		
		[Bindable]
		public function get totalPages():uint
		{
			return _totalPages;
		}
		
		public function set totalPages(value:uint):void 
		{
			_totalPages = value;
		}
		
		
		[Bindable]
		public function set currentPage(value:int):void
		{
			// exit if the position is invalid or no change is needed
							
			
			if(value < 0) {
				_currentPage = 0;
				return;
			}
			
			if(value >  (_totalPages-1)) {
				_currentPage = _totalPages-1;
				return;
			}
			
			if(_currentPage == value) 
				return;	
				
			if(animating) 
			{ 
				// store off the value so we can move to it when the animation 
				// is complete and we are not there.
				_pendingPage = value;
			} else {			
				// we don't want to animate if we are downsizing and on a page 
				// that is over the number of pages
				if(_currentPage > (_totalPages-1)) {
					_currentPage = value;		
				} else {
					direction = (value > _currentPage)? DIRECTION_FORWARD : DIRECTION_REVERSE;
					multipageScroll = (Math.abs(_currentPage - value) > 1)? true : false;
				
					_currentPage = value;				
					doPageAnimation();
				}
			} 
			
		}
		
		public function get currentPage():int
		{
			return _currentPage;		
		}
		
		
		/**
		 * This method does the heavey lifting of the animation. I have gone back and forth 
		 * on the most efficient means of providing quick and realistic scanning through
		 * cached items and have settled on using a bitmap overlay. The only major drawback 
		 * to this is that it requires a very liberal crossdomain file in order to manipulate
		 * the bitmap data.
		 * 
		 * There are two sections in this method. The first renders the bitmaps from the items
		 * and the second assigns the animate properties for the bitmaps. 
		 * 
		 * 
		 */		
		private function doPageAnimation():void
		{
			// get our measuring item renderer
			var item:IListItemRenderer 	= getMeasuringRenderer();			
			setupRendererFromData(item,_dataProvider.getItemAt(0));						
			
			// pages to animate will be 2 or 3 depending on multipage or
			// if we are at the first page. The first page cannot go backwards
			// and the scrollRect is at x = 0
			var pageNumber:int = (multipageScroll)? 3 : 2;

			// hold the bitmaps
			var pageBitmaps:Array = [];
			
			for(var i:uint =0; i < pageNumber; i++) 
			{
				var bmpData:BitmapData = new BitmapData(viewMetrics.right,item.getExplicitOrMeasuredHeight(),true,0x00FFFFFF);
				var m:Matrix = new Matrix();									

				for(var j:uint=0; j < itemsPerPage; j++) {
					
					var currentItem:uint;
					if(multipageScroll) {
						if(direction == DIRECTION_FORWARD) {
							currentItem = (i > 1)?  ( 1*itemsPerPage) + j: ( i*itemsPerPage) + j;	
						} else {
							currentItem = (i == 0)?  j:( (i-1)*itemsPerPage) + j;
						}
					} else {
						currentItem = ( i*itemsPerPage) + j;
					}										
					
					
					if(direction == DIRECTION_FORWARD && scrollX != 0) {
						currentItem = currentItem + itemsPerPage;
					}
					
					// make sure we are not running off the end of the list					
					if(currentItem < visibleItems.length) {
						
						item = visibleItems[currentItem] as IListItemRenderer ;					
						
						// centered layout same as above but this time the x offset uses the 
						// matrix to position the bitmap information when drawn to the bitmap
						if(pageMetrics.right >= viewMetrics.right) {
							m.tx  = j * (item.getExplicitOrMeasuredWidth()+pSpacing) ;
						} else {
							var division:int = Math.round(viewMetrics.right / itemsPerPage);
							var divistionMidpoint:int = division * .5;
							var currentItemNumber:int = j + 1;
							
							m.tx  = (currentItemNumber*division) - divistionMidpoint - (item.getExplicitOrMeasuredWidth()*.5);					
						}
	
						if(multipageScroll) {
																		
							if((direction == DIRECTION_FORWARD && i > 1) || (direction == DIRECTION_REVERSE && i == 0)) {
								var c:ColorTransform = new ColorTransform(2,2,2,pProxyAlpha);
								c.color = pProxyColor;
								//c.color = 0xcc3300;	
								bmpData.draw(item,m,c); 
							} else {
								bmpData.draw(item,m); 
							}
							
						} else {
							bmpData.draw(item,m); 				
						}			
					
					}						
				}
				
				var bmp:Bitmap = new Bitmap(bmpData);			
				bmp.y = item.y;
				if(direction == DIRECTION_FORWARD) {
					bmp.x = (i+1) *viewMetrics.right;	
				} else {
					if(multipageScroll) {
						if(_currentPage == 0) {
							bmp.x = (i-2) *viewMetrics.right;	
						} else {
							bmp.x = (i-1) *viewMetrics.right;	
						}
					} else {
						bmp.x = i *viewMetrics.right;	
					}
				}		
					
				addChild(bmp as DisplayObject);
				item.visible = false;							
				pageBitmaps.push(bmp);
				
			}
			
			for(i=0; i < pageBitmaps.length; i++) {
				bmp = pageBitmaps[i] as Bitmap;
				var ap:AnimateProperty = new AnimateProperty(bmp);
				ap.addEventListener(TweenEvent.TWEEN_UPDATE,animate_tweenUpdate);
				ap.addEventListener(EffectEvent.EFFECT_END,animate_effectEnd);
				ap.easingFunction = mx.effects.easing.Quadratic.easeInOut;
				ap.duration = (multipageScroll)? 750 : 500;
				ap.property = "x";				

				var fromValue:int = bmp.x;
				var toValue:int = 0;
				
				if(multipageScroll) {
					if(direction == DIRECTION_FORWARD) {
						toValue = bmp.x -( viewMetrics.right *2);
					} else {
						
						toValue = bmp.x +( viewMetrics.right *2);
					}
				} else {
					if(direction == DIRECTION_FORWARD) {
						toValue = bmp.x - viewMetrics.right;
					} else {
						if(_currentPage == 0 ) {						
							bmp.x = bmp.x - viewMetrics.right;
							fromValue = bmp.x;
						} 
						toValue = bmp.x+viewMetrics.right;			
					}
					
				}
			
				ap.fromValue = fromValue;
				ap.toValue = toValue;				
				
				ap.play();
				animating = true;
				_animateProperties.push(ap);
			}
			
			invalidateDisplayList();
		}
		/**
		 * Handles the blurring effect based on the percent traveled. Applies the 
		 * blur at each event.
		 * 
		 * @param e
		 * 
		 */		
		private function animate_tweenUpdate(e:TweenEvent):void
		{
			var animate:AnimateProperty = e.target as AnimateProperty;
			var value:Number 					= e.value as Number;			
			var blurAmount:Number 				= 0;			
			var prct:Number 					= (value - animate.fromValue)/(animate.toValue - animate.fromValue);
			var blurMultiplier:int 				= 200;
			if(prct > .5) {
				blurAmount = (1-prct)*blurMultiplier;
			} else {
				blurAmount = prct*blurMultiplier;
			}
			var bf:BlurFilter = new BlurFilter(blurAmount,0);
			var bmp:Bitmap = animate.target as Bitmap;
			
			bmp.filters = [bf];
		}
		/**
		 * Handles the end of the animation for each of the bitmap animate properties. This method
		 * confirms that all of the animations are complete before removing the bitmaps from the 
		 * display list. If they are complete then the items behind the proxy bitmaps are made visible.
		 * 
		 * We also check to see if this has been a mutlipage scroll in which case we will want to remove
		 * the proxy images with a fade out.
		 * 
		 * 
		 * @param event EffectEvent 
		 * 
		 */		
		private function animate_effectEnd(e:EffectEvent):void
		{

			var animate:AnimateProperty = e.target as AnimateProperty;
			if(!animate) {
				return;
			}
			animate.removeEventListener(TweenEvent.TWEEN_UPDATE, animate_tweenUpdate);
			animate.removeEventListener(TweenEvent.TWEEN_END, animate_effectEnd);			
			
			animate.target.filters = [];
			
			var bmp:Bitmap = animate.target as Bitmap;
			
			for(i=0; i < _animateProperties.length; i++) {
				var ap:AnimateProperty = _animateProperties[i] as AnimateProperty;
				if(!ap.isPlaying) {
					_animateProperties.pop();
				}
			}
			// check to make sure all animations are complete			
			if(_animateProperties.length == 0) {
				animating = false;
				
				var pageItemOffset:uint = itemsPerPage * Math.max(_currentPage - 1,0);
				for(var i:uint =0; i < itemsToRender; i++) 
				{
					var currentItem:uint = pageItemOffset+i; 
					if(currentItem < _dataProvider.length) {						
						var cachedItem:IListItemRenderer = getItemAt(currentItem) ;
						if(cachedItem) 
							cachedItem.visible = true;
					}
				}
			} 	
			// check multipage scroll
			if(multipageScroll) {
				var fade:Fade = new Fade(bmp);
				fade.addEventListener(EffectEvent.EFFECT_END,animate_effectEnd);
				fade.duration = pProxyDuration;
				fade.alphaFrom = pProxyAlpha;
				fade.alphaTo = 0;
				fade.play(); 										
			} else {
				removeChild(animate.target as DisplayObject);
			}				
			// if the currentPage has changed during the animation
			// then move to the new location
			if(_pendingPage) {
				currentPage = _pendingPage;
				_pendingPage = undefined;
			}
			
		}
		/**
		 * Handles the fadeout of a multipage scroll. This only
		 * happens on multiplage forward or backwards and can be e
		 * 
		 * 
		 * @param event EffectEvent 
		 * 
		 */		
		private function animate_fadeOut(e:EffectEvent):void
		{
			var fade:Fade = e.target as Fade;
			fade.removeEventListener(EffectEvent.EFFECT_END,animate_effectEnd);
			removeChild(fade.target as DisplayObject);
		}
		
		
		// STYLE getters/setters
		/**
		 * 
		 * 
		 * 
		 * @private 
		 * 
		 */		
		private function get pSpacing():uint
		{
			var result:uint = getStyle("spacing");
			if(isNaN(result))
				result = 10;
			return result;
		}
		/**
		 * 
		 * @private 
		 * 
		 */		
		private function get pProxyColor():Number
		{
			var result:Number = getStyle("proxyColor");
			if(isNaN(result))
				result = 0x666666;
			return result;
		}
		/**
		 * 
		 * @private 
		 * 
		 */		
		private function get pProxyDuration():Number
		{
			var result:Number = getStyle("proxyDuration");
			if(isNaN(result))
				result = 500;
			return result;
		}
		/**
		 * @private 
		 * 
		 */		
		private function get pProxyAlpha():Number
		{
			var result:Number = getStyle("proxyAlpha");
			if(isNaN(result))
				result = .6;
			return result;
		}
		/**
		 * Sets scrollRect x position. 
		 * 
		 * @param value
		 * 
		 */		
		private function set scrollX(value:uint):void
		{
			scrollRect = new Rectangle(value,0, viewMetrics.right,viewMetrics.bottom);						
		}
		/**
		 * Gets the scrollRect x position 
		 * @return 
		 * 
		 */		
		private function get scrollX():uint
		{
			var rect:Rectangle = scrollRect;
			return rect.x;
		}
		
		/**
		 * The item renderer must implement the IFactory interface. As of this version
		 * there is not listening for changes in the dataProvider
		 * 
		 * @param value
		 * 
		 */		
		public function set itemRenderer(value:IFactory):void 
		{
			if(value is IFactory)
				_itemRenderer = value;
			
			// clear out the visible renderers
			for each(var key:Object in _renderers) 
			{
				removeChild(_renderers[key]);
			}			
			// clear all renderers
			_rendererPool = [];
			_renderers = new Dictionary();
			// items being rendered are dirty			
			_itemsDirty = true;
			// rebuild 
			invalidateDisplayList();
		}
		
		
		
		/**
		 * Set the dataprovider object
		 * 
		 * 
		 * @param value
		 * 
		 */		
		[Bindable]
		public function set dataProvider(value:Object):void
		{
			if(value is Array) {
				_dataProvider = new ArrayCollection(value as Array);
			} 
			if(value is ArrayCollection) {
				_dataProvider = value as ArrayCollection;
			}
			_itemsDirty = true;
			invalidateProperties();
			invalidateSize();
		}
	 	/**
	 	 * Return the dataProvider object
	 	 * 
	 	 * 
	 	 * @return 
	 	 * 
	 	 */		
	 	public function get dataProvider():Object
	 	{ 
	 		return _dataProvider;
	 	}
		
	 	
	 	/**
	 	 * @private
	 	 * 
	 	 * UTILITY METHOD
		 * Instead of using the templateItem the list controls use this
		 * measuring renderer. Which is invisible and tracked using
		 * "hiddenItem"
		 **/
		private function getMeasuringRenderer():IListItemRenderer
	    {
	        var item:IListItemRenderer =
	            IListItemRenderer(getChildByName("hiddenItem"));
	        if (!item)
	        {
	            item = getRenderer();
	            item.owner = this;
	            item.name = "hiddenItem";
	            item.visible = false;
	            item.styleName = this;
	           	addChild(DisplayObject(item));
	        }
	        
	        return item;
	    }
	    
	    /**
	    * 
		* This is a very unique function that is used internally to apply 
		* data to a renderer in a list component. This method invalidates the 
		* size and the item via UIComponentGlobals. In Ely and Sho's renderers they
		* create all the elements at once. The paged list is an open ended
		* renderer with an infinate number of items. To accomodate this 
		* the renderers are recycled.
		**/
		private function setupRendererFromData(item:IListItemRenderer, data:Object):void
	    {
	        item.data = data;
	
	        if (item is IInvalidating)
	            IInvalidating(item).invalidateSize();  
	
			var lm:LayoutManager = new LayoutManager();
			lm.validateClient(ILayoutManagerClient(item), true);
	    }		
		/**
		 * 
		 * 
		 * For getting or creating renderers in a pool
		 * keeps us from creating enless renderers
		 **/		
		protected function getRenderer():IListItemRenderer
		{
			if(_rendererPool.length > 0 ) {
				return _rendererPool.pop() as IListItemRenderer;
			} else {
				return IListItemRenderer(_itemRenderer.newInstance());
			}
		}		
		/**
		 * For storing off renderers into pool
		 **/
		protected function storeRenderer(item:UIComponent):void 
		{
			_rendererPool.push(item);
		}
	}
}
/**
 * Tracks item loctions
 **/ 
class Destination 
{
	public var x:int;
	public var y:int;
	public var state:String;
	public var position:uint;
}