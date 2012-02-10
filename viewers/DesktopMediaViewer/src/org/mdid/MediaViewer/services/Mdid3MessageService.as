package org.mdid.MediaViewer.services
{
	import com.adobe.air.preferences.Preference;
	import com.adobe.crypto.MD5;
	import com.adobe.serialization.json.JSONDecoder;
	
	import mx.collections.ArrayCollection;
	import mx.messaging.channels.HTTPChannel;
	import mx.rpc.AsyncToken;
	import mx.rpc.Responder;
	import mx.rpc.events.FaultEvent;
	import mx.rpc.events.ResultEvent;
	import mx.rpc.http.HTTPService;
	
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.mdid.MediaViewer.events.SlideshowsEvent;
	import org.mdid.MediaViewer.models.LoginModel;
	import org.mdid.MediaViewer.models.SlideshowModel;
	import org.mdid.MediaViewer.models.SlideshowsModel;
	import org.mdid.MediaViewer.models.vo.Slideshow;
	import org.mdid.MediaViewer.models.vo.User;
	import org.robotlegs.mvcs.Actor;
	
	public class Mdid3MessageService extends Actor implements IMessageService
	{
		[Inject]
		public var loginModel:LoginModel;
		
		[Inject]
		public var prefs:Preference;
		
		[Inject]
		public var slideshowsModel:SlideshowsModel;
		
		[Inject]
		public var slideshowModel:SlideshowModel;
		
		private var _user:User;
		
		public function getSlideshow(id:int):void {
			var service:HTTPService = new HTTPService();
			var responder:Responder = new Responder(handleGetSlideshowResult, handleGetSlideshowFault);
			var token:AsyncToken;
			service.resultFormat = "text";
			service.method = "GET";
			service.url = baseURL + "api/presentation/" + id.toString() + "/?sessionid=" + this.loginModel.user.sessiontoken;
			token = service.send();
			token.addResponder(responder);			
			if (slideshowModel.currentShow != null) dispatch(new SlideshowsEvent(SlideshowsEvent.UNLOAD_CURRENT_SLIDESHOW));
		}
		
		public function getSlideshowList():void {
			var service:HTTPService = new HTTPService();
			var responder:Responder = new Responder(handleGetSlideshowListResult, handleGetSlideshowListFault);
			var token:AsyncToken;
			service.resultFormat = "text";
			service.method = "GET";
			service.url = baseURL + "api/presentations/currentuser/?sessionid=" + this.loginModel.user.sessiontoken;
			token = service.send();
			token.addResponder(responder);
		}
		public function get loggedIn():Boolean
		{
			return Boolean(loginModel.user);
		}
		public function logOut():void {
			loginModel.user = null;
			var service:HTTPService = new HTTPService();
			var responder:Responder = new Responder(handleLogoutResult, handleLogoutFault);
			var token:AsyncToken;
			service.resultFormat = "text";
			service.method = "GET";
			service.url = baseURL + "api/logout/";
			token = service.send();
			token.addResponder(responder);
			trace('loggedout');
			if (slideshowModel.currentShow != null) dispatch(new SlideshowsEvent(SlideshowsEvent.UNLOAD_CURRENT_SLIDESHOW));
		}
		public function keepSessionAlive():void {
			//trace("keepalive");
			if (!loginModel.isLoggedIn) return;
			var service:HTTPService = new HTTPService();
			var responder:Responder = new Responder(handleKeepAliveResult, handleKeepAliveFault);
			var token:AsyncToken;
			service.resultFormat = "text";
			service.method = "GET";
			service.url = baseURL + "api/keepalive/?sessionid=" + this.loginModel.user.sessiontoken;
			token = service.send();
			token.addResponder(responder);
		}
		public function logIn(user:User):void {
			var service:HTTPService = new HTTPService();
			var responder:Responder = new Responder(handleLoginResult, handleLoginFault);
			var token:AsyncToken;
			var params:Object = new Object();
			params.username = user.username;
			params.password = user.password;
			this._user = user;
			service.resultFormat = "text";
			service.method = "POST";
			service.url = baseURL + "api/login/";
			token = service.send(params);
			token.addResponder(responder);
		}
		protected function get baseURL():String {
			var value:String = prefs.getValue("mdid_url");
			if (value.charAt(value.length - 1) != "/") value += "/";
			return value;
		}
		protected function handleGetSlideshowResult(e:ResultEvent):void {
			var jd:JSONDecoder = new JSONDecoder(e.result.toString());
			var res:String = jd.getValue().result == null ? "" : jd.getValue().result;
			if (res.toLowerCase() != "ok") {
				dispatch(new SlideshowsEvent(SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_FAILED, "Unable to retrieve selected slideshow."));
				return;
			}
			var id:String = jd.getValue().id == null ? "" : jd.getValue().sessionid;
			var title:String = jd.getValue().title == null ? "No Title" : jd.getValue().title;
			var slides:ArrayCollection = jd.getValue().content == null ? null : new ArrayCollection(jd.getValue().content);
			slideshowModel.currentShow = new Slideshow(id, title, slides);
			dispatch(new SlideshowsEvent(SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_SUCCESSFUL));
		}
		protected function handleGetSlideshowFault(e:FaultEvent):void {
			dispatch(new SlideshowsEvent(SlideshowsEvent.LOAD_SELECTED_SLIDESHOW_FAILED, e.fault.faultString));
			trace(e.fault.faultDetail);
		}
		protected function handleGetSlideshowListResult(e:ResultEvent):void {
			var jd:JSONDecoder = new JSONDecoder(e.result.toString());
			var res:String = jd.getValue().result == null ? "" : jd.getValue().result;
			if (res.toLowerCase() != "ok") {
				dispatch(new SlideshowsEvent(SlideshowsEvent.LOAD_SLIDESHOWS_FAILED, "Unable to retrieve presentations."));
				return;
			}
			var presentations:ArrayCollection = new ArrayCollection(jd.getValue().presentations);
			this.slideshowsModel.slideshows = presentations;
			dispatch(new SlideshowsEvent(SlideshowsEvent.LOAD_SLIDESHOWS_SUCCESSFUL));
		}
		protected function handleGetSlideshowListFault(e:FaultEvent):void {
			dispatch(new SlideshowsEvent(SlideshowsEvent.LOAD_SLIDESHOWS_FAILED, e.fault.faultString));
			trace(e.fault.faultDetail);			
		}
		protected function handleKeepAliveResult(e:ResultEvent):void {
			var jd:JSONDecoder = new JSONDecoder(e.result.toString());
			var res:String = jd.getValue().result == null ? "" : jd.getValue().result;
			//trace(res);
		}
		protected function handleLogoutResult(e:ResultEvent):void {
			var jd:JSONDecoder = new JSONDecoder(e.result.toString());
			var res:String = jd.getValue().result == null ? "" : jd.getValue().result;
			//trace(res);
		}
		protected function handleLoginResult(e:ResultEvent):void {
			var jd:JSONDecoder;
			var res:String;
			try {
				jd  = new JSONDecoder(e.result.toString());
				res = jd.getValue().result == null ? "" : jd.getValue().result;
			} catch (e:Error) {
				res = "error";
			}
			if (res.toLowerCase() != "ok") {
				dispatch(new LoginEvent(LoginEvent.LOGIN_FAILED, this.loginModel.user, "Check username and password."));
				return;
			}
			var sessionid:String = jd.getValue().sessionid == null ? "" : jd.getValue().sessionid;
			var userid:String = jd.getValue().userid == null ? MD5.hash(this._user.username) : jd.getValue().userid;

			this.loginModel.user = this._user;
			this.loginModel.user.sessiontoken = sessionid;
			this.loginModel.user.userid = userid;
			dispatch(new LoginEvent(LoginEvent.LOGIN_SUCCESSFUL, this.loginModel.user));
		}
		protected function handleLogoutFault(e:FaultEvent):void {
			trace("logout fault encountered: " + e.fault.faultDetail);
		}
		protected function handleKeepAliveFault(e:FaultEvent):void {
			trace("keepalive fault encountered: " + e.fault.faultDetail);
		}
		protected function handleLoginFault(e:FaultEvent):void {
			dispatch(new LoginEvent(LoginEvent.LOGIN_FAILED, this.loginModel.user, "Check your MDID URL (" + e.fault.faultCode + ")"));
		}		
	}
}