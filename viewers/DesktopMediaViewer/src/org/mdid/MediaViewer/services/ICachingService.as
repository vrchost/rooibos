package org.mdid.MediaViewer.services
{
	import flash.filesystem.File;
	
	import mx.collections.ArrayCollection;
	import mx.collections.ArrayList;
	
	import org.mdid.MediaViewer.models.vo.Slideshow;
	
	public interface ICachingService
	{
		//function shrinkCache():void;
		//function getUserStorageDir():File;
		function fetchEmptySlideshowImage():Object;
		function getImageStatus(id:String):String;
		function unloadCurrentImageList():void;
		function getImagePath(id:String):String;
		function fetchImage(id:String):Object;
		function fetchThumbnail(id:String):String;
		function preCacheImages(slides:ArrayCollection):void;
		function preCacheImageThumbnails(slides:ArrayCollection):void;
		function get thumbFilePaths():ArrayList;
		function get isThumbCachingComplete():Boolean;
	}
}