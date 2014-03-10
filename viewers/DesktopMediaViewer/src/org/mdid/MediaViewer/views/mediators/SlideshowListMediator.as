package org.mdid.MediaViewer.views.mediators
{
	import com.adobe.utils.StringUtil;
	
	import flash.events.MouseEvent;
	
	import mx.collections.ArrayCollection;
	import mx.controls.dataGridClasses.DataGridColumn;
	import mx.events.CloseEvent;
	import mx.formatters.DateFormatter;
	
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.models.LoginModel;
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.models.SlideshowsModel;
	import org.mdid.MediaViewer.models.vo.ListItemValueObject;
	import org.mdid.MediaViewer.views.components.SlideshowList;
	import org.robotlegs.mvcs.Mediator;
	
	public class SlideshowListMediator extends Mediator
	{
		[Inject]
		public var view:SlideshowList;
		
		[Inject]
		public var model:SlideshowsModel;
		
		[Inject]
		public var loginModel:LoginModel;
				
		private var keywords:Array;
		
		public function SlideshowListMediator() {
			super();
		}
		override public function onRegister():void {
			eventMap.mapListener(view, SlideshowsEvent.FILTER_LIST, handleFilterList);
			eventMap.mapListener(view, SlideshowsEvent.LOAD_SELECTED_SLIDESHOW, handleLoadSelectedSlideshow);
			eventMap.mapListener(eventDispatcher, SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_SUCCESSFUL, handleLoadSelectedSlideshowSuccess);
			eventMap.mapListener(eventDispatcher, SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_FAILED, handleLoadSelectedSlideshowFailed);
			if (!loginModel.isLoggedIn) {
				view.setCurrentState("notloggedin");
				eventMap.mapListener(view["logIntoMDID"], MouseEvent.CLICK, handleLoginEvent);
			} else if (!model.isSlideshowLoaded) {
				view.setCurrentState("noslideshows");
			} else {
				view.setCurrentState("default");
				view.title = "Select from " + model.numSlideshows + " Slideshows";
				view.dg.variableRowHeight = true;
				view.dg.dataProvider = model.slideshows;
				var columns:Array = [];
				var column1:DataGridColumn = new DataGridColumn("Title");
				column1.dataField = "title";
				column1.width = 205;
				column1.wordWrap = true;
				columns.push(column1);
				var column2:DataGridColumn = new DataGridColumn("Created On");
				column2.dataField = "created";
				column2.width = 87;
				column2.labelFunction = view.getDataLabel;
				columns.push(column2);
				var column3:DataGridColumn = new DataGridColumn("Modified On");
				column3.dataField = "modified";
				column3.width = 85;
				column3.labelFunction = view.getDataLabel;
				columns.push(column3);
				view.dg.columns = columns;
				view.tagsData = model.tags;
				view.tags.labelField = "label";
				model.slideshows.filterFunction = _filterRows;
				handleFilterList();
			}
		}
		private function handleLoginEvent(e:MouseEvent):void {
			//trace('loginevent');
			view.dispatchEvent(new CloseEvent(CloseEvent.CLOSE));
			dispatch(new LoginEvent(LoginEvent.PROMPT_FOR_LOGIN));
		}
		private function handleLoadSelectedSlideshowSuccess(e:SlideshowsEvent):void {
			//view.setCurrentState("slideshowloaded");
			//view.title = "Your slideshow is loaded.";
			view.closeButton.visible = true;
			view.dispatchEvent(new CloseEvent(CloseEvent.CLOSE));
		}
		private function handleLoadSelectedSlideshowFailed(e:SlideshowsEvent):void {
			view.setCurrentState("slideshowfailedtoload");
			view.title = "Failed to retrieve slideshow...";
			view.errormessage.text = e.errorMessage;
			view.closeButton.visible = true;
		}
		private function handleLoadSelectedSlideshow(e:SlideshowsEvent):void {
			view.setCurrentState("loadingslideshow");
			view.title = "Retrieving slideshow...";
			view.loadingSelectedLabel.text = "Retrieving selected slideshow: " + e.selectedSlideshow.title + ".";
			view.closeButton.visible = false;
			dispatch(e);
		}
		private function handleFilterList(e:SlideshowsEvent=null):void {
			var searchtext:String = (StringUtil.trim(view.searchBox.text)).toLowerCase();
			keywords = searchtext.split(" ");
			view.dg.selectedIndex = -1;
			model.slideshows.refresh();
		}
		private function _filterRows(item:Object):Boolean {
			if (!view.showHiddenCheckbox.selected && item.hidden) return false;
			for each(var tag:ListItemValueObject in model.tags) {
				if (tag.isSelected) {
					var isMatched:Boolean = false;
					for each(var thing:String in item.tags) {
						if (thing ==tag.label) {
							isMatched = true;
							break;
						}
					}
					if (!isMatched) return false;
				}
			}
			var title:String = item.title.toLowerCase();
			for each(var keyword:String in keywords) {
				if (title.indexOf(keyword, 0) < 0) return false;
			} 
			return true;
		}
	}
}