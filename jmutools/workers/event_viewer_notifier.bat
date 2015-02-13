@ECHO OFF

wevtutil qe %1 /f:RenderedXML /q:"<QueryList><Query Id='0' Path='System'><Select Path='System'>*[System[(EventRecordID=%2)]]</Select></Query></QueryList>" | python hipchat_event_notifier.py
