package com.adobe.controls
{
	import mx.controls.sliderClasses.SliderThumb;
	import mx.core.mx_internal;
	
	use namespace mx_internal;

	public class FlexibleSliderThumb extends SliderThumb
	{
        override protected function measure():void {
            super.measure();
            measuredWidth = currentSkin.measuredWidth;
            measuredHeight = currentSkin.measuredHeight;
        }
	}
}