[README.txt] Last updated for v1.1.0-rc2  [05-23-09]
--------------------------------------------------------------
Feedback & Bugs:

contact Phillip Sitbon, phillip@sitbon.net

http://pyisapie.sourceforge.net/
--------------------------------------------------------------


How to install PyISAPIe:

  Extract the .zip file anywhere (such as C:\PyISAPIe). The
  DLL directory is the first priority in searching for the
  Http package, so if you want multiple versions or copies
  using the same package, make sure to move Http to
  site-packages or put a Http.pth entry there. The PYTHONPATH
  environment variable is also an option, but a reboot will
  be required after it's set.

  Remeber to give the correct permissions to the PyISAPIe.dll
  (NETWORK SERVICE by default on IIS 6 and 7). IIS6 also requires
  you to create an allowed web service extension for the DLL.
  IIS 7 will ask you to do this by default. Note that if you are
  setting up a wildcard application map, you need to make sure
  Isapi.Request returns True in order for the next handler to get
  the request.
  
  IIS7 Note: Make sure to change the bitness of your worker process
  to 32 bits so it can load the DLL. (Look in advanced options for
  the app pool)

Running your scripts:

By default, Isapi.py loads the file given to it by the HTTP
server (via the value of Http.Env.SCRIPT_TRANSLATED).
This is the fast way to run, because the memory-cached bytecode
is used instead of reloading every time -- if desired
(and it often is for debugging), just alter the Isapi.py
to reload the module every time. I have yet to observe any
negative effects of reloading the module during concurrent
requests, whether it is done with the imp module, reload,
or execfile. I would appreciate hearing any experiences you
have with this setup.

Please bear with me as I update Django/WSGI/Trac support for
version 1.1.0 - I have no idea if it's working right now.

Interface:

The entire interface resides in the Http package. It imports
most of the functionality from the PyISAPIe module, including
the following:

  - Header(Header, Status, Length, Close):
    - As of version 1.0.0, you don't have to call this function.
      If you don't, the DefaultHeaders config param is used.

      Header: A string, or list/tuple of strings containing
              headers to be sent. Separators (\r\n) not
              needed. (Clients expect "Header-Name: Value")

      Status: An integer specifying the HTTP status code,
              defaults to 200. The status string is set
              according to HTTP/1.1 specifications.

      Length: Content length of the (only) data being sent.
              This disables chunked transfer encoding, but
              uses keep-alive when available. This can only
              be set once and there must be exactly one write
              with this size.

      Close:  If true, the `Connection: close` header is
              inserted. Disables chunked transfer encoding.

  - Env.<Var>:

      Passes Var as a string to the ISAPI GetServerVariable
      and returns its result (a string). For IIS, see
      http://msdn.microsoft.com/en-us/library/ms524602.aspx
      Note that any leading `\\?\` is NOT removed as it was
      in version 1.0.0. The global variable __target__ corresponding
      to SCRIPT_TRANSLATED has been removed as of v1.0.0.
      
      There is also a special value, KeepAlive, that specifies
      whether or not the current connection will be closed.
      
      As of 1.0.4 the following applies:
      
      Any variable that is not found or not set returns an
      empty string. I found this to be beneficial when setting
      up WSGI.
      
      There are also two bool variables, DataSent and HeadersSent
      for determining if the respective items have been transmitted
      to the client yet.

  - Read([Bytes]):
  
      Read data from the client (i.e. POST data). Excluding
      the parameter returns all available data.
      See help(Http.Read) for more info.

  - Write(Str):
  
      Write a string to the client. Much faster than using the
      print statement.
      See help(Http.Write) for more info.
      
      NOTE: It doesn't do any str() conversion- the caller must
      do it!


Take a look at the Http.Config module for an explanation of the
adjustable parameters.


Extending with your own (C/C++) modules:

I tried to make writing separate modules that use ISAPI as
easy as possible. If you are familiar with programming python
extensions, then you know how wonderfully easy most of it can
be. Interfacing with PyISAPIe is as simple as getting the pointer
to the current thread's request information, contained in the
Context structure (see PyISAPIe.h). The macro PyContext_LoadAndCheck()
does all the work. There is room for extra flags (for now), and
a pointer to the current EXTENSION_CONTROL_BLOCK. Take note that
the Interpreter structure pointed to is defined for ALL requests,
so make sure not to fiddle with it too much (carelessly), since
changes are not local to the current thread. From there, you can
call the ISAPI functions as you normally would.

Currently, using PyISAPIe from a different library is broken
because the current context is loaded from a TLS slot, and I'm not
sure if exporting TlsIndex_Ctx is enough. If you want to try it,
add "__declspec(dllimport) DWORD TlsIndex_Ctx" to PyISAPIe.h when
compiling your code.

Otherwise, it should be pretty easy just to compile your code into
the included project source.

Latest changes:

 - Not here anymore.
   Please refer to the shiny Trac site for recent changes.

--------------------------------------------------------------
Feedback & Bugs:

contact Phillip Sitbon, phillip@sitbon.net

http://sourceforge.net/projects/pyisapie/
--------------------------------------------------------------
