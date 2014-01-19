package org.mdid.MediaViewer.models.vo
{
	import mx.collections.ArrayCollection;
	import mx.collections.ArrayList;

	public class Slideshow
	{
		public var title:String;
		public var id:String;
		public var slides:ArrayCollection = new ArrayCollection();
		public var formattedCatalogData:ArrayCollection = new ArrayCollection();
		public var idLookupList:ArrayList = new ArrayList();
		
		public function get numSlides():int {
			return slides.length;
		}
		public function Slideshow(theId:String, theTitle:String = "", theSlides:ArrayCollection = null)
		{
			id = theId;
			title = theTitle;
			if (title == null || title.length < 1) title = "Untitled";
			slides = theSlides;
			for each(var slide:Object in slides) {
				var temp:String = "";
				for each(var line:Object in slide["metadata"]) {
					//trace(line["label"] + ": " + line["value"]);
					temp += "<p><b>" + line["label"] + ":</b>  " + line["value"] + "</p>";
				}
				formattedCatalogData.addItem(temp);
				idLookupList.addItem(slide.id.toString());
			}
		}
		public function clone():Slideshow {
			return (new Slideshow(id, title, new ArrayCollection(slides.toArray())));
		}
	}
}