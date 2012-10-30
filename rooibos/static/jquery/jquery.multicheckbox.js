   $.fn.multicheckbox = function(settings) {
     var config = {'mixed': false, 
				   'checkedValue': 'true', 
				   'uncheckedValue': 'false', 
				   'mixedValue': 'mixed'};
 
     if (settings) $.extend(config, settings);
 
     this.each(function() {
		$(this).css("cursor", "pointer");
	   if($(this).is(':checked')){
		  this.greyed = true;
	   }
	   
	   if(config.mixed || $(this).attr('mixed') == 'true'){
			$(this).attr('value', config.mixedValue);
			$(this).attr('checked', 'checked');
			$(this).fadeTo(1, .3);
			this.greyed = false;
	   }
	   
	   $(this).click(function(){
		if($(this).is(':checked')){
			if(!this.greyed){
				$(this).attr('value', config.checkedValue);
				$(this).fadeTo(1, 1);
				this.greyed = true;
			}
		}else{
			if(this.greyed){
				$(this).attr('value', config.mixedValue);
				$(this).attr('checked', 'checked');
				$(this).fadeTo(1, .3);
				this.greyed = false;
			}else {
				$(this).attr('value', config.uncheckedValue);
				$(this).fadeTo(1, 1);
			}
		}
	   });
     });
 
     return this;
	}
 