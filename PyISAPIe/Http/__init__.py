# $URL: https://pyisapie.svn.sourceforge.net/svnroot/pyisapie/Tags/1.1.0-rc4/PyISAPIe/Python/Http/__init__.py $
# $Rev: 167 $ $Date: 2009-06-16 19:33:31 -0700 (Tue, 16 Jun 2009) $
# (C)2008 Phillip Sitbon <phillip@sitbon.net>
#
"""Http interaction module.

Provides interaction with ISAPI built-in module
and access to other tools.

Note: When this package is being loaded for the
first time, the current request context is not
valid because the config and buffering (if used)
are not initialized, so any attempts to access
or manipulate the current request context will
fail.
"""
__all__ = (

  'Config',
  
  # From DLL
  'Read',
  'Write',
  'Env',
  'Header',
  'DisableBuffer'

)

# Imports
#
try:
  from PyISAPIe import Env, Header, Read, Write, DisableBuffer
  Loaded = True

except ImportError:
  # Won't work when extension hasn't been loaded from IIS.
  # Ignoring this error allows access to components and config
  # that don't need the server or a request to be accessed.
  # TODO: Add exception-raising replacements for request-related
  # functions?
  Loaded = False
  pass

# Get the version info. Note that this is NOT imported on star.
# Looks a little excessive but save a lot of low-level work.
#
if Loaded:
  from PyISAPIe import Version as Ver, VersionFull, VersionMajor, VersionMinor, VersionRelease, VersionRevision

  class Version(object):
    Version = Ver
    Full = VersionFull
    Major = VersionMajor
    Minor = VersionMinor
    Release = VersionRelease
    Revision = VersionRevision
    def __str__(This): return This.Version

  Version = Version()
    
  del Ver, VersionFull, VersionMajor, VersionMinor, VersionRelease, VersionRevision
