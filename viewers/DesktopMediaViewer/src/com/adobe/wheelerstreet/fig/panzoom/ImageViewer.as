package com.adobe.wheelerstreet.fig.panzoom
{
	import com.adobe.wheelerstreet.fig.panzoom.events.LoadCompleteEvent;
	import com.adobe.wheelerstreet.fig.panzoom.events.PanZoomEvent;
	import com.adobe.wheelerstreet.fig.panzoom.modes.PanZoomCommandMode;
	import com.adobe.wheelerstreet.fig.panzoom.utils.ContentRectangle;
	
	import flash.display.Bitmap;
	import flash.display.Loader;
	import flash.display.Stage;
	import flash.events.Event;
	import flash.events.IOErrorEvent;
	import flash.events.NativeDragEvent;
	import flash.events.ProgressEvent;
	import flash.geom.Matrix;
	import flash.geom.Point;
	import flash.geom.Rectangle;
	import flash.net.URLRequest;
	import flash.system.LoaderContext;
	
	import mx.controls.Alert;
	import mx.core.UIComponent;
	import mx.effects.AnimateProperty;
	import mx.events.FlexEvent;
	import mx.events.ResizeEvent;
	import mx.events.TweenEvent;
	import mx.managers.DragManager;
	
	public class ImageViewer extends UIComponent {
		[Bindable]
		public var autoCenterImageOnLoad:Boolean = false;
		[Bindable]
		public var bitmapScaleFactorMin:Number = .125;		
		[Bindable]
		public var bitmapScaleFactorMax:Number = 5;			

		public var viewRect:Rectangle;		
		
		private var _panZoomCommandMode:PanZoomCommandMode;
		private var _contentRectangle:ContentRectangle;
		private var _bitmap:Bitmap;
		private var _bitmapScaleFactor:Number;
		private var _smoothBitmap:Boolean = false;
		private var _imageURL:String;
		private var _loader:Loader;
		private var _isLoading:Boolean = false;

		/**
		* Setting the imageURL triggers the loading of the image and extraction 
		* and assignment of it's bitmapData. 
		*/ 		
		[Bindable]
		public function get imageURL():String {
			return _imageURL;
		}
		private var _imageVisibility:Boolean = true;
		public function set imageURL(value:String):void {
			// setting imageURL triggers loading sequence
			if (_isLoading) return;
			if (value == _imageURL) return;
			_imageURL = value;
			_loader = new Loader();
            _loader.load(new URLRequest(value));
			_isLoading = true; 
			_imageVisibility = this.visible;
			this.visible = false;
             // load events 
 			_loader.contentLoaderInfo.addEventListener(Event.COMPLETE, handleLoadComplete);
			_loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, handleLoadIOError);
			//_loader.contentLoaderInfo.addEventListener(ProgressEvent.PROGRESS, handleLoadProgress);					
		}
		
		/**			
		* Setting the ImageViewer's bitmap triggers the activation of the PanZoomCommandMode.
		* 
		* <p>The PanZoomCommandMode acts as the 'invoker' element in the Command Pattern.
		* It's constructor requires that you assoiciate it with a 'client' and a 'reciever'. 
		* In this implementation the 'client' is the ImageView (this) and the 
		* reciever is the bitmapData transform matrix.</p> 
		*/
		public function get bitmap():Bitmap {
			return _bitmap;
		}
		
		public function set bitmap(value:Bitmap):void {
			if (value == _bitmap)
				return;
			_bitmap = value;
			if (_bitmap != null) {
				_contentRectangle = new ContentRectangle(0,0,_bitmap.width, _bitmap.height, viewRect);		
			}
			//_contentRectangle.viewAll(viewRect);

			_panZoomCommandMode = new  PanZoomCommandMode(this, _contentRectangle, 2, .1)			
			_panZoomCommandMode.activate();
			invalidateDisplayList();
		}
		
		/**
		* Tracks the scale of the bitmap being displayed.
		* Setting the bitmapScale factor invalidates the displayList since any
		* change will requite an update.
		*/ 	
		[Bindable]
		public function get bitmapScaleFactor():Number {
			return _bitmapScaleFactor;
		}
		public function set bitmapScaleFactor(value:Number):void {
			if (value == bitmapScaleFactor ) {
				return;
			}	
			if (value < bitmapScaleFactorMin) {
				return
			}
			if (value > bitmapScaleFactorMax) {
				return;
			}
			_bitmapScaleFactor = value;
			invalidateDisplayList();				
		}
		
		/**
		 * setting smoothBitmap to true hurts performance slightly
		 */
		[Bindable]
		public function get smoothBitmap():Boolean {
			return _smoothBitmap;
		}
		public function set smoothBitmap(value:Boolean):void {
			if (value == _smoothBitmap) return;
			_smoothBitmap = value;
			invalidateDisplayList();	
		}		
		
		/////////////////////////////////////////////////////////
		//
		// public functions
		//
		/////////////////////////////////////////////////////////
		
		/**
		 * The zoom function requires a direction to be assigned when the function 
		 * is triggerd.  "in" zooms in and conversly "out" zooms out.
		 */
		private var _animateZoom:AnimateProperty = new AnimateProperty(this);		
		public function zoom(direction:String, allTheWay:Boolean):void {
			if (_animateZoom.isPlaying) return;
			
			_animateZoom.property = "bitmapScaleFactor";
			_animateZoom.addEventListener(TweenEvent.TWEEN_UPDATE, handleTween);
			_animateZoom.addEventListener(TweenEvent.TWEEN_END, handleTween);			
			switch (direction) {
				case "in":
					if (_bitmapScaleFactor * 2 > bitmapScaleFactorMax || allTheWay) {
						_animateZoom.toValue = bitmapScaleFactorMax;
						
					} else {
						_animateZoom.toValue = _bitmapScaleFactor * 2;				
					}				
					break;
				case "out":
					if (_bitmapScaleFactor / 2 < bitmapScaleFactorMin || allTheWay) {
						_animateZoom.toValue = bitmapScaleFactorMin;
					} else {
						_animateZoom.toValue = _bitmapScaleFactor / 2;				
					}				
					break;					
			}
			_animateZoom.play();
			function handleTween(e:TweenEvent):void {
				switch (e.type) {
					case "tweenUpdate":
						_contentRectangle.zoom = bitmapScaleFactor;						
						break;
					case "tweenEnd":
						_contentRectangle.zoom = bitmapScaleFactor;
						dispatchEvent(new PanZoomEvent(PanZoomEvent.IMAGE_RESIZED));
						_animateZoom.removeEventListener(TweenEvent.TWEEN_END, handleTween);	
						_animateZoom.removeEventListener(TweenEvent.TWEEN_UPDATE, handleTween);
						break;
				}
			}	 
		}

		/**
		 * The zoomByOrigin function zooms in on the users current mouse position.  
		 * This function requires a direction to be assigned when the function 
		 * is triggerd.  "in" zooms in and conversly "out" zooms out.
		 */
		private var _animateZoomByOrigin:AnimateProperty = new AnimateProperty();		
		public function zoomByOrigin(direction:String):void {
			if (_animateZoomByOrigin.isPlaying) return;
			_animateZoomByOrigin = new AnimateProperty(_contentRectangle);		
			_animateZoomByOrigin.property = "zoomByOrigin";			
			_animateZoomByOrigin.addEventListener(TweenEvent.TWEEN_UPDATE, handleTween);
			_animateZoomByOrigin.addEventListener(TweenEvent.TWEEN_END, handleTween);
			_contentRectangle.zoomOrigin = new Point( (-_contentRectangle.x + mouseX) *  1/_contentRectangle.scaleX,
													  (-_contentRectangle.y + mouseY) *  1/_contentRectangle.scaleY  );		
			switch (direction) {
				case "in":
					if (_bitmapScaleFactor * 2 > bitmapScaleFactorMax) {
						_animateZoomByOrigin.toValue = bitmapScaleFactorMax;
					} else {
						_animateZoomByOrigin.toValue = _bitmapScaleFactor * 2;				
					}				
					break;
				case "out":
					if (_bitmapScaleFactor / 2 > bitmapScaleFactorMax) {
						_animateZoomByOrigin.toValue = bitmapScaleFactorMax;
					} else {
						_animateZoomByOrigin.toValue = _bitmapScaleFactor / 2;				
					}				
					break;					
			}
			_animateZoomByOrigin.play();
			function handleTween(e:TweenEvent):void
			{
				switch (e.type) {
					case "tweenUpdate":
						bitmapScaleFactor = e.value	as Number;		
						break;
					case "tweenEnd":
						_animateZoomByOrigin.removeEventListener(TweenEvent.TWEEN_END, handleTween);	
						_animateZoomByOrigin.removeEventListener(TweenEvent.TWEEN_UPDATE, handleTween);
						break;
				}
			}				
		}
		
		public function setZoom(scale:Number):void {
			if (scale > bitmapScaleFactorMax) {
				scale = bitmapScaleFactorMax;
			} else if (scale < bitmapScaleFactorMin) {
				scale = bitmapScaleFactorMin;
			}
			_contentRectangle.zoom = scale;
			bitmapScaleFactor = scale;
			//_contentRectangle.centerToPoint(new Point(this.viewRect.width/2, this.viewRect.height/2));
			invalidateDisplayList();
			dispatchEvent(new PanZoomEvent(PanZoomEvent.IMAGE_RESIZED));
		}
		
		public function centerView():void {
			_contentRectangle.viewAll(viewRect);
			var newScale:Number = _contentRectangle.scaleX;
			if (newScale < this.bitmapScaleFactorMin) {
				newScale = this.bitmapScaleFactorMin;
			} else if (bitmapScaleFactor > this.bitmapScaleFactorMax) {
				newScale = this.bitmapScaleFactorMax;
			}
			this.setZoom(newScale);
			invalidateDisplayList();
		}
		/** 
		 * Added by Kevin Hegg on 10/11/2010. Use in place of setZoom() when you want smooth
		 * transition from current scale to target scale.
		 **/
		private var _animateZoomTo:AnimateProperty = new AnimateProperty(this);		
		public function zoomTo(scale:Number, moveToCenterOnTweenEnd:Boolean = false):void {
			if (_animateZoomTo.isPlaying) return;
			if (scale > bitmapScaleFactorMax) {
				scale = bitmapScaleFactorMax;
			} else if (scale < bitmapScaleFactorMin) {
				scale = bitmapScaleFactorMin;
			}
			_animateZoomTo.property = "bitmapScaleFactor";
			_animateZoomTo.toValue = scale;
			_animateZoomTo.addEventListener(TweenEvent.TWEEN_UPDATE, handleTween);
			_animateZoomTo.addEventListener(TweenEvent.TWEEN_END, handleTween);			
			if (moveToCenterOnTweenEnd) _animateZoomTo.addEventListener(TweenEvent.TWEEN_END, moveToCenter);		
			_animateZoomTo.play();
			function handleTween(e:TweenEvent):void {
				switch (e.type) {
					case "tweenUpdate":
						_contentRectangle.zoom = bitmapScaleFactor;		
						break;
					case "tweenEnd":
						_contentRectangle.zoom = bitmapScaleFactor;
						dispatchEvent(new PanZoomEvent(PanZoomEvent.IMAGE_RESIZED));
						_animateZoomTo.removeEventListener(TweenEvent.TWEEN_END, handleTween);		
						_animateZoomTo.removeEventListener(TweenEvent.TWEEN_UPDATE, handleTween);
						break;
				}
			}	 
		}

		public function zoomToCenterView():void {
			var newScale:Number = _contentRectangle.getFitToRectangleXandY(viewRect).x;
			if (newScale < this.bitmapScaleFactorMin) {
				newScale = this.bitmapScaleFactorMin;
			} else if (newScale > this.bitmapScaleFactorMax) {
				newScale = this.bitmapScaleFactorMax;
			}
			zoomTo(newScale, true);
		}
		
		private var _animateX:AnimateProperty = new AnimateProperty();
		private var _animateY:AnimateProperty = new AnimateProperty();
		public function moveToCenter(e:TweenEvent = null):void {
			if (_animateX.isPlaying || _animateY.isPlaying) return;
			if (e != null) e.currentTarget.removeEventListener(TweenEvent.TWEEN_END, moveToCenter);
			_animateX = new AnimateProperty(_contentRectangle);
			_animateY = new AnimateProperty(_contentRectangle);
			var xVal:Number = (viewRect.width - (_contentRectangle.width))/2;
			var yVal:Number = (viewRect.height - (_contentRectangle.height))/2;
			_animateX.property = "x";
			_animateX.toValue = xVal;
			_animateX.addEventListener(TweenEvent.TWEEN_UPDATE, handleTweenX);
			_animateX.addEventListener(TweenEvent.TWEEN_END, handleTweenX);
			_animateY.property = "y";
			_animateY.toValue = yVal;
			_animateY.addEventListener(TweenEvent.TWEEN_UPDATE, handleTweenY);
			_animateY.addEventListener(TweenEvent.TWEEN_END, handleTweenY);
			_animateX.play();
			_animateY.play();
			function handleTweenX(e:TweenEvent):void {
				switch (e.type) {
					case "tweenUpdate":
						_contentRectangle.x = e.value as Number;
						invalidateDisplayList();
						break;
					case "tweenEnd":
						_contentRectangle.x = e.value as Number;
						invalidateDisplayList();
						_animateX.removeEventListener(TweenEvent.TWEEN_END, handleTweenX);	
						_animateX.removeEventListener(TweenEvent.TWEEN_UPDATE, handleTweenX);
						break;
				}
			}				
			function handleTweenY(e:TweenEvent):void {
				switch (e.type) {
					case "tweenUpdate":
						_contentRectangle.y = e.value as Number;		
						break;
					case "tweenEnd":
						_contentRectangle.y = e.value as Number;
						invalidateDisplayList();
						_animateY.removeEventListener(TweenEvent.TWEEN_END, handleTweenY);	
						_animateY.removeEventListener(TweenEvent.TWEEN_UPDATE, handleTweenY);
						break;
				}
			}				
		}

		/////////////////////////////////////////////////////////
		//
		// constructor
		//
		/////////////////////////////////////////////////////////
	    /**
	     *  Constructor.
	     */	
	    import mx.effects.Dissolve;
	    private var fadeIn:Dissolve;
		public function ImageViewer():void {
			viewRect = new Rectangle();
			_contentRectangle = new ContentRectangle(0,0,0,0,viewRect);
			addEventListener(ResizeEvent.RESIZE, handleResize);
			//addEventListener(FlexEvent.CREATION_COMPLETE, handleCreationComplete);
			function handleCreationComplete(e:FlexEvent):void {
				_contentRectangle.zoom = .5;	
				bitmapScaleFactor = _contentRectangle.zoom;
				invalidateDisplayList();
			}
			fadeIn = new Dissolve();
			fadeIn.color = 0x000000;
			fadeIn.duration = 300;
			this.setStyle("showEffect", fadeIn);
		}
		
	    /**
	     *  @private
	     */
		private function handleResize(e:ResizeEvent):void {
			if (_contentRectangle == null) return;
			_contentRectangle.centerToPoint(new Point(this.width/2, this.height/2));
		}
		
		/////////////////////////////////////////////////////////
		//
		// protected overrides
		//		
		/////////////////////////////////////////////////////////

		/**
		 * When the display list is updated the bitmap is drawn via a bitmapFill
		 * applied to the UIComponents graphics layer. The size and position of the bitmap 
		 * are determined by the bitmapData's transform matrix, which is derived by parsing
		 * the _contentRectangle's properties.   
		 * 
		 */
		override protected function updateDisplayList(unscaledWidth:Number, unscaledHeight:Number):void
		{
			super.updateDisplayList(unscaledWidth, unscaledHeight);
			viewRect.width = width;
			viewRect.height = height;
			if (_bitmap == null) {
				// if there's no bitmapData fill the component with black
				//graphics.beginFill(0x000000,1)
				//graphics.drawRect(0,0,unscaledWidth,unscaledHeight);								
				//graphics.drawRect(_contentRectangle.x,_contentRectangle.y,_contentRectangle.width, _contentRectangle.height);
			
			} else if (viewRect != null) {
				var __bitmapTransform:Matrix = new Matrix(_contentRectangle.width / _bitmap.width,
											  0, 0,
											  _contentRectangle.height / _bitmap.height,
											  _contentRectangle.topLeft.x,
											  _contentRectangle.topLeft.y
											  );

				// fill the component with the bitmap.
				graphics.clear();
				graphics.beginBitmapFill(_bitmap.bitmapData,  // bitmapData
										 __bitmapTransform,   // matrix
										 false,                // tile?
										 _smoothBitmap		  // smooth?
										 );					 
				
				//graphics.drawRect(0,0,unscaledWidth, unscaledHeight);
				graphics.drawRect(_contentRectangle.x,_contentRectangle.y,_contentRectangle.width, _contentRectangle.height);
			}
		}

		/**
	    *  @private
	    */
		// load handlers
		private function handleLoadComplete(e:Event):void {
			bitmap = Bitmap(_loader.content);
            _isLoading = false;
            this.endEffectsStarted();
            this.visible = this._imageVisibility;
			if (autoCenterImageOnLoad) this.centerView();
			dispatchEvent(new LoadCompleteEvent(LoadCompleteEvent.LOAD_COMPLETE));			
		}

		/**
	    *  @private
	    */
		private function handleLoadIOError(e:IOErrorEvent):void {
            _isLoading = false;
		}
		
		/**
	    *  @private
	    */
		private function handleLoadProgress(e:ProgressEvent):void {
			if (_bitmap != null && this.visible) {
				this.alpha = 1 - (e.bytesLoaded / e.bytesTotal);
				if (this.alpha < .2) this.visible = false;
			}
		}				
	}
}