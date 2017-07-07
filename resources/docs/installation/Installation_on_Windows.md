# Installation on Windows

The following instructions are for Windows 2012 R2.

Unless noted otherwise, everything should be done using an administrator
account.

## Server Preparation

Make sure IIS is installed and includes the CGI feature.

### Packages

The following software packages are required.  They can be downloaded freely
and include a graphical installer.

* MySQL (https://dev.mysql.com/downloads/windows/installer/)
* Erlang/OTP (http://www.erlang.org/download.html)
* RabbitMQ (https://www.rabbitmq.com/install-windows.html)
* Python 2.7 32-bit (https://www.python.org/download/releases/2.7.8/)
* Microsoft Visual C++ Compiler for Python 2.7 
  (https://www.microsoft.com/en-us/download/details.aspx?id=44266)
* MySQL-Python (https://pypi.python.org/pypi/MySQL-python/1.2.5)

Download the following script and make sure to save it with a `.py` file
extension: https://bootstrap.pypa.io/get-pip.py 

Open a command prompt and run

    c:\python27\python get-pip.py


## Download and install MDID

Download the desired .zip package from https://www.mdid.org/downloads.html,
extract it, and move the contained `rooibos-*` folder to the desired location
and name, e.g. `C:\mdid`.

Open a command prompt and run

    c:\python27\scripts\pip install python-ldap==2.4.39
    c:\python27\scripts\pip install -r c:\mdid\requirements.txt
    c:\python27\scripts\pip install wfastcgi 


## Configure MDID

Open a command prompt and run

    cd /d c:\mdid
    mkdir log
    
    cd rooibos_settings
    copy template.py local_settings.py

Open local_settings.py in a text editor and add the following setting:

    STATIC_ROOT = 'c:/mdid/static'

Make sure to change `SECRET_KEY` to a unique value and do not share it!
Also, if possible, change the asterisk in `ALLOWED_HOSTS` to your server
host name, if you know it, for example `['mdid.yourschool.edu']`.

MDID requires two system environment variables set when running commands
from the command prompt or via scheduled tasks.

    setx -m DJANGO_SETTINGS_MODULE "rooibos_settings.local_settings"
    setx -m PYTHONPATH "c:\mdid"


## Create database

Open a command prompt and run

    "\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe" -u root -p
    
    CREATE DATABASE mdid DEFAULT CHARACTER SET UTF8;
    GRANT ALL PRIVILEGES ON mdid.* TO mdid@localhost IDENTIFIED BY 'rooibos';
    \q
    
    cd /d c:\mdid
    c:\python27\scripts\django-admin.py migrate
    
If you receive a "foreign key constraint" error, run the command a second time.

    mkdir static
    c:\python27\scripts\django-admin.py collectstatic
    

## Configure IIS

* Open IIS Manager
* Select the server
* Under Sites, stop or remove the Default Web Site

* Select the server
* Open FastCGI settings
* Under Actions, click Add Application...
* Full Path: c:\python27\python.exe
* Arguments: c:\python27\lib\site-packages\wfastcgi.py
* Under FastCGI Properties > General, select and open Environment Variables
* Add the following entries:
    * Name: `DJANGO_SETTINGS_MODULE`
        * Value: `rooibos_settings.local_settings`
    * Name: `PYTHONPATH`
        * Value: `c:\mdid`
    * Name: `WSGI_HANDLER`
        * Value: `django.core.wsgi.get_wsgi_application()`
* Close the dialogs

* Select the server
* Select Sites 
* Under Actions, click Add Website...
* Name: mdid
* Physical path: c:\mdid\rooibos
* Close the dialog

* Select Sites > mdid
* Open Handler Mappings
* Under Actions, click Add Module Mapping...
* Request path: *
* Module: FastCgiModule
* Executable: c:\python27\python.exe|c:\python27\lib\site-packages\wfastcgi.py
* Name: Django handler
* Click Request Restrictions
* Uncheck the Invoke handler checkbox
* Click OK
* Click OK
* In the appearing dialog, select No

* Select Sites > mdid
* Under Actions, click on View Virtual Directories
* Click Add Virtual Directory...
* Alias: static
* Physical path: c:\mdid\static
* Click OK

* Select Sites > mdid > static
* Open Handler Mappings
* Under Actions, click View Ordered List...
* Select StaticFile 
* Click Move Up several times until StaticFile is above Django Handler
* Close dialog


## Install Solr

Solr can be installed on the same server as MDID or on a separate server.

### Packages

* Solr 4 (https://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.zip)
* NSSM (https://nssm.cc/release/nssm-2.24.zip)
* Java (http://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html)

Extract the Solr package and rename the contained directory to e.g. `c:\solr`.

Copy and rename the `c:\mdid\solr4` directory to `c:\solr-data`.
Within `c:\solr-data`, rename the `template` directory to `mdid`.

To test the installation before installing the Windows service, open a
command window and run the following commands:

    cd /d c:\solr\bin
    solr.cmd start -f -s c:\solr-data

With this command running, open a browser and navigate to 
http://localhost:8983/solr/#/mdid.  If there are no errors, you can close
the browser and the command window and proceed to the next step.

### Install service

Extract the NSSM package, making sure to use the bit version matching the
installed version of Java.

From a command window run `nssm install solr`.

In the Application tab, enter

* Path: c:\solr\bin\solr.cmd
* Startup directory: c:\solr\bin
* Arguments: -f -s c:\solr-data

Click Install Service.

Run `net start solr`.  After a few moments, the URL 
http://localhost:8983/solr/#/mdid should work again in the browser. 

### Configure MDID

In your `local_settings.py`, set 

    SOLR_URL = 'http://127.0.0.1:8983/solr/mdid'

Adjust the URL accordingly if you are running Solr on a different server etc.


## Worker process

MDID uses a continuously running task to process data imports, etc.

### Packages

* PyWin32 (https://sourceforge.net/projects/pywin32/files/pywin32/)

Make sure to download the correct package for Python 2.7 32-bit.

### Install service

Run `c:\python27\scripts\django-admin workers_service install`.


## Configure recurring tasks

In Task Manager, create the tasks listed below to run periodically.
Make sure to mark the tasks to run whether a user is logged in or not.
The following two settings are always the same, 
only the frequency and arguments vary:

* Action: Start a program
* Program/script: c:\python27\scripts\django-admin.exe

List of tasks:

* Every five minutes
    * Arguments: solr index
* Hourly
    * Arguments: runjobs hourly
* Daily:
    * Arguments: runjobs daily
* Daily:
    * Arguments: solr reindex
* Weekly:
    * Arguments: runjobs weekly
* Monthly:
    * Arguments: runjobs monthly
* Yearly:
    * Arguments: runjobs yearly


## Further steps

In a production environment, the following topics should be investigated:

* Firewall

  MDID only requires port 80 to be open (port 443 if SSL is configured)
* SSL certificate for IIS
* Log rotation for log files in `c:\mdid\log`
* Server and process monitoring
* Backup
