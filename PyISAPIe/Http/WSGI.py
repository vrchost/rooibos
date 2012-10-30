# $URL: https://pyisapie.svn.sourceforge.net/svnroot/pyisapie/Tags/1.1.0-rc4/PyISAPIe/Python/Http/WSGI.py $
# $Rev: 165 $ $Date: 2009-06-15 14:19:18 -0700 (Mon, 15 Jun 2009) $
# (C)2008 Phillip Sitbon <phillip@sitbon.net>
#
"""WSGI Compatibility handler.

From the Request() function in Isapi.py, call RunWSGI()
with the selected application as the parameter. I'm not
confident about this being fully compliant, but it's
pretty close.

I wrote this, almost verbatim, from the PEP 333 example
server code. Some of the functionality is at a lower level;
for example, if the headers have been sent already, the
DLL handles throwing the exception. It does not, however,
actually replace headers that have already been *set*.
"""
from PyISAPIe import Read, Write, Env, Header
import PyISAPIe
import logging

# Set these for compatibility with WSGI - no readline[s] yet.
PyISAPIe.read = Read
PyISAPIe.write = Write
PyISAPIe.flush = lambda: None

IsapiEnvAuto = [
  "REQUEST_METHOD",
  "SCRIPT_NAME",
  "PATH_INFO",
  "QUERY_STRING",
  "CONTENT_TYPE",
  "CONTENT_LENGTH",
  "SERVER_NAME",
  "SERVER_PORT",
  "SERVER_PROTOCOL",
  
  # not required.
  # perhaps include these when iterating?
  
  #"AUTH_PASSWORD",
  #"AUTH_TYPE",
  #"AUTH_USER",
  #"CACHE_URL",
  #"CERT_COOKIE",
  #"CERT_FLAGS",
  #"CERT_ISSUER",
  #"CERT_KEYSIZE",
  #"CERT_SECRETKEYSIZE",
  #"CERT_SERIALNUMBER",
  #"CERT_SERVER_ISSUER",
  #"CERT_SERVER_SUBJECT",
  #"CERT_SUBJECT",
  #"GATEWAY_INTERFACE",
  #"HTTP_ACCEPT_ENCODING",
  #"HTTP_ACCEPT_LANGUAGE",
  #"HTTP_CONNECTION",
  #"HTTP_COOKIE",
  #"HTTP_HOST",
  #"HTTP_REFERER",
  #"HTTP_URL",
  #"HTTP_USER_AGENT",
  #"HTTP_VERSION",
  "HTTPS",
  #"HTTPS_KEYSIZE",
  #"HTTPS_SECRETKEYSIZE",
  #"HTTPS_SERVER_ISSUER",
  #"HTTPS_SERVER_SUBJECT",
  #"INSTANCE_ID",
  #"LOCAL_ADDR",
  #"LOGON_USER",
  #"PATH_TRANSLATED",
  "REMOTE_ADDR",
  #"REMOTE_HOST",
  #"REMOTE_PORT",
  #"REMOTE_USER",
  #"SCRIPT_TRANSLATED",
  #"SERVER_PORT_SECURE",
  #"SERVER_SOFTWARE",
  #"SSI_EXEC_DISABLED",
  #"UNENCODED_URL",
  #"UNMAPPED_REMOTE_USER",
  #"URL",  
]

EnvWSGI = {
  "wsgi.input"        : PyISAPIe,
  "wsgi.errors"       : PyISAPIe,
  "wsgi.version"      : (1,0),
  "wsgi.multithread"  : True,
  "wsgi.multiprocess" : True,
  "wsgi.run_once"     : False,
  "wsgi.url_scheme"   : "http",
}

class IsapiEnv(dict):
  def __init__(This, Base, *Args, **Kwds):
    dict.__init__(This, *Args, **Kwds)
    
    # Autoload the required variables
    for Key in IsapiEnvAuto:
      This[Key] = getattr(Env, Key)


    ScriptName = This["SCRIPT_NAME"]
    PathInfo = This["PATH_INFO"]
    
    # This will make us WSGI compliant, provided
    # AllowPathInfoForScriptMappings is NOT TRUE
    
    if ScriptName.endswith("/"):
      ScriptName = ScriptName[:-1]
      
    if Base.endswith("/"):
      Base = Base[:-1]
    
    if PathInfo.startswith(Base):
      ScriptName = PathInfo[:len(Base)]
      PathInfo = PathInfo[len(Base):]
        
      if not PathInfo.startswith("/"):
        PathInfo = "/" + PathInfo
      
    This["SCRIPT_NAME"] = ScriptName
    This["PATH_INFO"] = PathInfo
    
    # client headers-
    #  need to pre-load these for iteration.
    #  not sure if it would be any different from adding HTTP_* to the
    #  above list?
    
    ClientHeaders = \
      dict((N.upper(), V) for N, V in \
        [Item.split(":",1) for Item in Env.ALL_HTTP.split("\n") if Item])
  
    This.update(ClientHeaders)
  
    # set the proper url scheme
  
    if This.get("HTTPS","off") in ("on","1"):
      This["wsgi.url_scheme"] = "https"
      
      
  def __getitem__(This, Key):
    if Key in This:
      return dict.__getitem__(This,Key)
      
    Value = This[Key] = getattr(Env,Key)
    return Value


def RunWSGI(Application, Base = "/"):
  # WSGI server environment & ISAPI variables
  Environ = IsapiEnv(Base, EnvWSGI)
  
  Result = Application(Environ, StartResponse)
  
  try:
    if Result.has_header('Content-Length'):
      Write(''.join(Data for Data in Result if Data))
    else:
      for Data in Result:
        if Data:
          Write(Data)
  except Exception, ex:
    logging.debug("PyISAPIe: Exception on RunWSGI Write: %s" % repr(ex))
    raise
  finally:
    if hasattr(Result, "close"):
      Result.close()

def StartResponse(Status, Headers, ExcInfo = None):
  if ExcInfo:
    try:
      raise ExcInfo[0], ExcInfo[1], ExcInfo[2]
      
    finally:
      ExcInfo = None
      
  Status = int(Status.split(" ",1)[0])
  Header(Status = Status)
  
  for NameValue in Headers:
    Lname = NameValue[0].lower()
    
    if Lname == "content-length":
      Header(Length = int(NameValue[1]))
      continue
      
    elif Lname == "connection":
      if NameValue[1].lower() == "close":
        Header(Close = True)
      continue
      
    Header("%s: %s" % NameValue)
    
  return Write
