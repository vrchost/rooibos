package org.mdid.MediaViewer.views.mediators
{
	import flash.events.MouseEvent;
	
	import mx.events.EventListenerRequest;
	
	import org.mdid.MediaViewer.events.ControlBarEvent;
	import org.mdid.MediaViewer.events.SlideshowCursorChangeEvent;
	import org.mdid.MediaViewer.events.TopBarEvent;
	import org.mdid.MediaViewer.models.vo.SlideshowCursor;
	import org.mdid.MediaViewer.views.components.EdgeControls;
	import org.robotlegs.utilities.modular.mvcs.ModuleMediator;
	
	public class EdgeControlsMediator extends ModuleMediator
	{
		[Inject]
		public var view:EdgeControls;
		
		[Inject(name="windowname")]
		public var windowName:String;
		
		private var whichPane:String;

		public function EdgeControlsMediator() {
			super();
		}
		override public function onRegister():void {
			whichPane = (view.parent["id"].toLocaleLowerCase() == "imageholder") ? SlideshowCursor.FIRST_PANE : SlideshowCursor.SECOND_PANE;
			addModuleListener(SlideshowCursorChangeEvent.POSITION_CHANGED, handleSlideNavigationChange);
			eventMap.mapListener(view.bottomEdge.leftBlock, MouseEvent.ROLL_OVER, dispatchShowControlBarEvent);
			eventMap.mapListener(view.bottomEdge.rightBlock, MouseEvent.ROLL_OVER, dispatchShowControlBarEvent);
			eventMap.mapListener(view.topEdge.rightBlock, MouseEvent.ROLL_OVER, dispatchShowTopBarEvent);
		}
		private function dispatchShowTopBarEvent(e:MouseEvent):void {
			dispatch(new TopBarEvent(TopBarEvent.SHOW_TOPBAR, windowName, whichPane, TopBarEvent.LEFT_EDGE_BLOCK));
		}
		private function dispatchShowControlBarEvent(e:MouseEvent):void {
			dispatch(new ControlBarEvent(ControlBarEvent.SHOW_CONTROLBAR, windowName, whichPane, e.currentTarget == view.bottomEdge.leftBlock ? ControlBarEvent.LEFT_EDGE_BLOCK : ControlBarEvent.RIGHT_EDGE_BLOCK));
		}
		private function handleSlideNavigationChange(e:SlideshowCursorChangeEvent):void {
			if (e.targetWindow != windowName || e.targetPane != whichPane) return;
			if (e.newPosition > 0) {
				view.leftEdge.previous.source = view.leftEdge.previousUpOver;
			} else {
				view.leftEdge.previous.source = view.leftEdge.previousVestige;
			}
			if (e.newPosition < e.numPositions - 1) {
				view.rightEdge.next.source = view.rightEdge.nextUpOver;
			} else {
				view.rightEdge.next.source = view.rightEdge.nextVestige;
			}
		}
	}
}