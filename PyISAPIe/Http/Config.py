# $URL: https://pyisapie.svn.sourceforge.net/svnroot/pyisapie/Tags/1.1.0-rc4/PyISAPIe/Python/Http/Config.py $
# $Rev: 167 $ $Date: 2009-06-16 19:33:31 -0700 (Tue, 16 Jun 2009) $
# (C)2008 Phillip Sitbon <phillip@sitbon.net>
#
"""Configuration parameters for PyISAPIe.

These parameters can be overridden if they are
changed during the import of the ISAPI handler.
"""

# Debug
#
# Used to differentiate between a development and
# production environment. This setting is not used
# internally, meaning that any changes here always
# require a restart or recycle.
#
Debug = False

# InterpreterMap
#
# Determines how separate interpreters are used.
# An interpreter consists of a totally isolated
# environment, although not GIL-independent.
#
# Default: None
# Values:
#   None  - Always use the same interpreter (faster)
#   "XXX" - Given by Env.XXX (i.e. SCRIPT_NAME)
#
InterpreterMap = None
#
# NOTE: There are C extensions that are not compatible
# with this option. If PyISAPIe hangs, that's why.
#

# BufferSize
#
# The amount of data to buffer before sending. The
# buffering policy is strict, meaning that the exact
# size will be sent on each write - this provides
# predictable behavior.
#
# If the buffer is not exceeded when the handler
# exits, a content-length header is sent followed
# by the buffer contents. Otherwise, there are a
# few possibilities:
#
#   Client sends close header or not KeepAlive:
#     - No content length header
#     - Buffers and sends normally
#     - Connection closed
#
#   Keepalive:
#     - No content length header
#     - HTTP/1.1:
#         - Use chunked transfer encoding
#         - Chunk size == BufferSize,
#           or write size if None
#     - HTTP/1.0:
#         - Implies KeepAlive == False
#
# Note: The buffer is allocated on the stack
# for speed - keep an eye on your stack usage
# if you go over 64K, the recommended minimum.
#
# Default: None (output on each write)
# Range:   64-131072
#
BufferSize = 131072
#
# WARNING:
#
#   I noticed some weird behavior lately. When output
#   resorts to chunked transfer encoding, everything
#   runs fine, but after 16k-ish requests in ApacheBench
#   v2.3, it hangs. It sits there for about 100 seconds
#   and finishes its requests- and ALWAYS with 5 connect
#   failures. I can browse the pages while ab is stuck
#   at that 16k point.
#
#   Debugging didn't provide any more information- the IIS
#   worker process threads just stop handling requests from
#   ab for a while, otherwise no errors or Python GIL
#   deadlocks.
#
#   I've reproduced this exact same behavior in IIS 6 and
#   IIS 7, and for now it's chalked up as something funky
#   with ab.
#
#   For now the solution is to buffer in Python or don't go
#   over the 128k buffer limit. Or assume it won't be seen
#   from browsers, which is my case. Please do try to
#   reproduce.
#


# KeepAlive
#
# Use to disable chunked transfer
# encoding for HTTP/1.1 and always
# close the connection.
#
# Default: True
#
KeepAlive = True

# DefaultHeaders
#
# Headers to send (when none have been set) on
# the first write.
#
# Note that output is not considered sent when
# it goes into the buffer.
# Also, don't try to include any \r's, \n's or
# multi-line strings in general - it will only
# confuse the client. To specify a close header,
# use Header(Close=True) for correct behavior.
#
# The most efficient way to specify content
# length is to use Header(Length=NNNN).
#
# Default: Empty
#
DefaultHeaders = ( \
  "Content-Type: text/html",
)

# StaticHeaders
#
# Headers that are always sent. Good to add your
# application-specific headers you'll always need.
# I recommend leaving the X-Powered-By header, it
# is used in some places.
#
# Default: Empty
#
#from PyISAPIe import VersionFull
#StaticHeaders = ( \
#  "X-Powered-By: PyISAPIe-" + VersionFull,
#)
