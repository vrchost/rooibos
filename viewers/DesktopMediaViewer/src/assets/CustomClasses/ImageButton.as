package assets.CustomClasses
{
	import spark.components.Button;
	
	public class ImageButton extends Button
	{
		[Bindable]
		public var imageReference:Class;
		public function ImageButton()
		{
			super();
		}
	}
}