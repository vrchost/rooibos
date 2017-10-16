# Streaming MP4 files using Red5 Streaming Server on Ubuntu 14.04 LTS
Unless noted otherwise, all commands should be run as `root`.

## Install Red5
Find the URL of the latest release from
`https://github.com/Red5/red5-server/releases` and use it in the steps below.
```
cd /opt
wget https://github.com/Red5/red5-server/releases/download/v1.0.8-M13/red5-server-1.0.8-M13.tar.gz
tar xzf red5-server-1.0.8-M13.tar.gz
chown -R mdid:mdid red5-server
```
### Configure Red5
Edit the file `/opt/red5-server/conf/context.xml` and add the following
line in the `<Context>` section:
```
    <Resources allowLinking="true" />
```
### Improve Red5 startup time (if necessary)
On some systems, startup of the Red5 server is very slow.
According to `https://github.com/Red5/red5-server/wiki/Faster-Start-Up`,
startup time can be improved by editing `/opt/red5-server/red5.sh`
and changing the line
```
SECURITY_OPTS="-Djava.security.debug=failure"
```
to
```
SECURITY_OPTS="-Djava.security.debug=failure -Djava.security.egd=file:/dev/./urandom"
```
## Run Red5 using supervisor
Create a new file `/etc/supervisor/conf.d/red5.conf` with the following
content:
```
[program:red5]
directory=/opt/red5-server
command=
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/red5.log
```
Load the configuration:
```
supervisorctl reload
```
## Configure MDID storage
Create a new storage that will hold the video files to be streamed and set
the _Base_ property to the directory holding the video files.
Set _URL Base_  to `rtmp://your-server-name:1935/vod/mp4:%(filename)s`.
Set _Server Base_ to `/opt/red5-server/webapps/vod/streams`.
Note: MDID will create symlinks from _Server Base_ to files in _Base_ on
demand. In order to clean up temporary video links, you need to run the
hourly jobs using cron, as outlined in the installation instructions.
## Viewing videos
MP4 videos should be uploaded and attached to records as usual.  On the
record page, the _Viewers_ panel in the right column contains a
_Media Player_ link that opens a video player with the streaming video.
