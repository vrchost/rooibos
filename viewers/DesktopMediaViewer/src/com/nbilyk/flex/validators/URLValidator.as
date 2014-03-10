package com.nbilyk.flex.validators {
	import mx.validators.ValidationResult;
	import mx.validators.Validator;
	
	public class URLValidator extends Validator {
		public function URLValidator() {
			super();
		}
		
		private var _invalidUrlError:String = "This is an invalid URL.";
		
		[Inspectable(category="Errors", defaultValue="null")]
		
		/**
		 *  Error message when a string is not a valid url. 
		 *  @default "This is an invalid url."
		 */
		public function get invalidUrlError():String {
			return _invalidUrlError;
		}
		public function set invalidUrlError(value:String):void {
			_invalidUrlError = value;
		}
		
		override protected function doValidation(value:Object):Array {
			var results:Array = super.doValidation(value);
			if (!isUrl(value.toString())) {
				results.push(new ValidationResult(true, "", "invalidUrl", invalidUrlError));   
			}
			return results;
		}
		public static function isUrl(s:String):Boolean {
			var regexp:RegExp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
			return regexp.test(s);
		}
	}
}