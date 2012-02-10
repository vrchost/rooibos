package org.mdid.MediaViewer.views.mediators
{
	import com.adobe.air.preferences.Preference;
	
	import mx.events.CloseEvent;
	import mx.events.StateChangeEvent;
	
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.models.LoginModel;
	import org.mdid.MediaViewer.services.Mdid3MessageService;
	import org.mdid.MediaViewer.views.components.LoginWindow;
	import org.robotlegs.mvcs.Mediator;
	
	public class LoginWindowMediator extends Mediator
	{
		[Inject]
		public var view:LoginWindow;
		
		[Inject]
		public var prefs:Preference;
		
		[Inject]
		public var loginModel:LoginModel;
		
		private var mdidurl:String;

		public function LoginWindowMediator() {
			super();
		}
		override public function onRegister():void {
			eventMap.mapListener(eventDispatcher, LoginEvent.LOGIN_SUCCESSFUL, handleLoginMessageReceived)
			eventMap.mapListener(eventDispatcher, LoginEvent.LOGIN_FAILED, handleLoginMessageReceived)
			eventMap.mapListener(eventDispatcher, SlideshowsEvent.LOAD_SLIDESHOWS_SUCCESSFUL, handleLoadSlideshowEventMessageReceived)
			eventMap.mapListener(eventDispatcher, SlideshowsEvent.LOAD_SLIDESHOWS_FAILED, handleLoadSlideshowEventMessageReceived)
			eventMap.mapListener(view, LoginEvent.LOGIN_USER, dispatch);
			eventMap.mapListener(view, LoginEvent.LOGOUT, dispatch);
			eventMap.mapListener(view, SlideshowsEvent.LOAD_SLIDESHOWS, dispatch);
			eventMap.mapListener(view, SlideshowsEvent.SELECT_SLIDESHOW, dispatch);
			eventMap.mapListener(view, StateChangeEvent.CURRENT_STATE_CHANGE, handleStateChange);
			view.prefs = this.prefs;
			if (!view.prefs.isLatestDataLoaded) view.prefs.load();
			mdidurl = view.prefs.getValue("mdid_url");
			if (loginModel.isLoggedIn) {
				view.currentState = "loggedin";
			} else {
				view.currentState = "feedbackline";
				if (mdidurl == null || mdidurl.length < 1) {
					view.loginButton.enabled = false;
					view.savebutton.enabled = true;
					view.updateMessage.text = "Please enter the URL for your MDID.";
					view.savebutton.setFocus();
				} else {
					view.loginButton.enabled = true;
					view.urlinput.text = mdidurl;
					view.usernameField.setFocus();
				}	
			}
		}
		private function handleStateChange(e:StateChangeEvent):void {
			if (view.currentState == "notloggedin") {
				if (!view.prefs.isLatestDataLoaded) view.prefs.load();
				mdidurl = view.prefs.getValue("mdid_url");
				if (mdidurl == null || mdidurl.length < 1) {
					view.loginButton.enabled = false;
					view.savebutton.enabled = true;
					view.updateMessage.text = "Please enter the URL for your MDID.";
					view.savebutton.setFocus();
				} else {
					view.loginButton.enabled = true;
					view.urlinput.text = mdidurl;
					view.usernameField.setFocus();
				}	
			}
		}
		private function handleLoadSlideshowEventMessageReceived(e:SlideshowsEvent):void {
			if (e.type == SlideshowsEvent.LOAD_SLIDESHOWS_SUCCESSFUL) {
				view.dispatchEvent(new SlideshowsEvent(SlideshowsEvent.SELECT_SLIDESHOW));
				view.dispatchEvent(new CloseEvent(CloseEvent.CLOSE));	
			} else if (e.type == SlideshowsEvent.LOAD_SLIDESHOWS_FAILED) {
				view.setCurrentState("retrievingslideshowsfailed");
				view.errormessage2.text = "[ Log out and try again later or contact your MDID administrator. ]"
			}
			view.closeButton.visible = true;
		}
		private function handleLoginMessageReceived(e:LoginEvent):void {
			if (e.type == LoginEvent.LOGIN_SUCCESSFUL) {
				view.setCurrentState("retrievingslideshows");
				view.dispatchEvent(new SlideshowsEvent(SlideshowsEvent.LOAD_SLIDESHOWS));
			} else if (e.type == LoginEvent.LOGIN_FAILED) {
				view.setCurrentState("loginfailed");
				view.tryagainbutton.setFocus();
				view.errormessage.text = e.errorMessage + (e.errorMessage.charAt(e.errorMessage.length-1) == "." ? "" : ".");
			}
			view.parent.dispatchEvent(e);
		}
	}
}