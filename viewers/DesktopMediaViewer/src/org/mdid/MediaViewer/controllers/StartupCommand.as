package org.mdid.MediaViewer.controllers
{
	import org.mdid.MediaViewer.events.LoginEvent;
	import org.robotlegs.base.ContextEvent;
	import org.robotlegs.mvcs.Command;
	
	public class StartupCommand extends Command
	{
		override public function execute():void
		{
			// Do some custom startup stuff here!
			//trace("Startupcommand");
			dispatch(new LoginEvent(LoginEvent.PROMPT_FOR_LOGIN));
			//heggkj: following line causes StartupCommand to run a second time, which is NOT good
			//dispatch( new ContextEvent( ContextEvent.STARTUP_COMPLETE ) );
		}
	}
}