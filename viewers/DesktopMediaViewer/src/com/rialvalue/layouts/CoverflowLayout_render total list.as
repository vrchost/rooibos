package com.rialvalue.layouts {
	import flash.events.TimerEvent;
	import flash.geom.Matrix3D;
	import flash.geom.PerspectiveProjection;
	import flash.geom.Point;
	import flash.geom.Vector3D;
	import flash.utils.Timer;
	
	import mx.core.ILayoutElement;
	import mx.core.IVisualElement;
	import mx.core.UIComponent;
	
	import spark.layouts.supportClasses.LayoutBase;
	
	public class CoverflowLayout extends LayoutBase {
		private static const ANIMATION_DURATION:int = 10;
		private static const ANIMATION_STEPS:int = 24; // fps
		private static const RIGHT_SIDE:int = -1;
		private static const LEFT_SIDE:int = 1;
		
		private var finalMatrixs:Vector.<Matrix3D>;
		private var centerX:Number;
		private var centerY:Number;
		private var transitionTimer:Timer;
		
		
		private var _elementRotation:Number;
		private var _selectedItemProximity:Number;
		private var _selectedIndex:int;
		private var _depthDistance:Number;
		private var _perspectiveProjectionX:Number;
		private var _perspectiveProjectionY:Number;
		private var _focalLength:Number = 300;
		private var _horizontalDistance:Number = 100;
		
		
		public function set perspectiveProjectionX(value:Number):void {
			_perspectiveProjectionX = value;
			invalidateTarget();
		}
		
		
		public function set perspectiveProjectionY(value:Number):void {
			_perspectiveProjectionY = value;
			invalidateTarget();
		}
		
		
		public function set focalLength(value:Number):void {
			_focalLength = value;
			invalidateTarget();
		}
		
		
		public function set elementRotation(value:Number):void {
			_elementRotation = value;
			invalidateTarget();
		}
		
		
		public function set horizontalDistance(value:Number):void {
			_horizontalDistance = value;
			invalidateTarget();
		}
		
		
		public function set depthDistance(value:Number):void {
			_depthDistance = value;
			invalidateTarget();
		}
		
		
		public function set selectedItemProximity(value:Number):void {
			_selectedItemProximity = value;
			invalidateTarget();
		}
		
		
		public function set selectedIndex(value:Number):void {
			_selectedIndex = value;
			
			if (target) {
				target.invalidateDisplayList();
				target.invalidateSize();
			}
		}
		
		
		private function invalidateTarget():void {
			if (target) {
				target.invalidateDisplayList();
				target.invalidateSize();
			}
		}
		
		
		private function centerPerspectiveProjection(width:Number, height:Number):void {
			_perspectiveProjectionX = _perspectiveProjectionX != -1 ? _perspectiveProjectionX : width / 2;
			_perspectiveProjectionY = _perspectiveProjectionY != -1 ? _perspectiveProjectionY : height / 2;
			
			var perspectiveProjection:PerspectiveProjection = new PerspectiveProjection();
			perspectiveProjection.projectionCenter = new Point(_perspectiveProjectionX, _perspectiveProjectionY);
			perspectiveProjection.focalLength = _focalLength;
			
			target.transform.perspectiveProjection = perspectiveProjection;
		}
		
		
		private function positionCentralElement(element:ILayoutElement, width:Number, height:Number):Matrix3D {
			element.setLayoutBoundsSize(NaN, NaN, false);
			var matrix:Matrix3D = new Matrix3D();
			var elementWidth:Number = element.getLayoutBoundsWidth(false);
			var elementHeight:Number = element.getLayoutBoundsHeight(false);
			
			centerX = (width - elementWidth) / 2;
			centerY = (height - elementHeight) / 2;
			
			matrix.appendTranslation(centerX, centerY-12, -_selectedItemProximity);
			
			element.setLayoutBoundsSize(NaN, NaN, false);
			
			if (element is IVisualElement) {
				IVisualElement(element).depth = 10;
			}
			
			return matrix;
		}
		
		
		private function positionLateralElement(element:ILayoutElement, index:int, side:int):Matrix3D {
			element.setLayoutBoundsSize(NaN, NaN, false);
			var matrix:Matrix3D = new Matrix3D();
			var elementWidth:Number = element.getLayoutBoundsWidth(false);
			var elementHeight:Number = element.getLayoutBoundsHeight(false);
			
			var zPosition:Number = index * _depthDistance;
			
			if (side == RIGHT_SIDE) {
				matrix.appendTranslation(-elementWidth+11, 0, 0);
				matrix.appendTranslation(2 * elementWidth - _horizontalDistance, 0, 0);
			}
			matrix.appendTranslation(centerX - side * (index) * _horizontalDistance, centerY, zPosition);
			if (element is IVisualElement) {
				IVisualElement(element).depth = -zPosition;
			}
			
			return matrix;
		}
		
		private var leftOffset:int = 0;
		private var rightOffset:int = 0;
		private var numElements:int = 0;
		override public function updateDisplayList(width:Number, height:Number):void {
			var i:int = 0;
			var j:int = 0;
			var matrix:Matrix3D;
			
			numElements = target.numElements;
			if (numElements > 0) {
				finalMatrixs = new Vector.<Matrix3D>(numElements);
				
				var midElement:int = _selectedIndex;
				
				matrix = positionCentralElement(target.getVirtualElementAt(_selectedIndex), width, height);
				finalMatrixs[midElement] = matrix;
				
				for (i = midElement - 1; i >= 0; i--) {
					matrix = positionLateralElement(target.getVirtualElementAt(i), midElement - i, LEFT_SIDE);
					finalMatrixs[i] = matrix;
				}
				
				for (j = 1, i = midElement + 1; i < numElements; i++, j++) {
					matrix = positionLateralElement(target.getVirtualElementAt(i), j, RIGHT_SIDE);
					finalMatrixs[i] = matrix;
				}
				
				playTransition();
			}
		}
		
		
		private function playTransition():void {
			if (transitionTimer) {
				transitionTimer.stop();
				transitionTimer.reset();
			} else {
				transitionTimer = new Timer(ANIMATION_DURATION / ANIMATION_STEPS, ANIMATION_STEPS);
				transitionTimer.addEventListener(TimerEvent.TIMER, animationTickHandler);
				transitionTimer.addEventListener(TimerEvent.TIMER_COMPLETE, animationTimerCompleteHandler);
			}
			transitionTimer.start();
			
		}
		
		
		private function animationTickHandler(event:TimerEvent):void {
			var initialMatrix:Matrix3D;
			var finalMatrix:Matrix3D;
			var element:ILayoutElement;
			
			for (var i:int = 0; i < numElements; i++) {
				finalMatrix = finalMatrixs[i];
				element = target.getVirtualElementAt(i);
				initialMatrix = UIComponent(element).transform.matrix3D;
				initialMatrix.interpolateTo(finalMatrix, 1.0);
				element.setLayoutMatrix3D(initialMatrix, false);
			}
		}
		
		
		private function animationTimerCompleteHandler(event:TimerEvent):void {
			finalMatrixs = null;
		}
	}
}