package org.mdid.MediaViewer.services
{
	public interface IResourceManagerService
	{
		function getString(bundle:*, resourceName:String, parameters:Object = null):String;
		function fillString(resource:String, parameters:Object):String;
	}
}