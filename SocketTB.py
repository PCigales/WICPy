# SocketTB v1.4.3 (https://github.com/PCigales/WinSocketTB)
# Copyright © 2023 PCigales
# This program is licensed under the GNU GPLv3 copyleft license (see https://www.gnu.org/licenses)

import socket
import ssl
import ctypes, ctypes.wintypes
import threading
import weakref
from collections import deque
import time
import datetime
import types
from functools import reduce, cmp_to_key
import urllib.parse
import email.utils
import html
import mimetypes
import unicodedata
from io import IOBase, BytesIO
import math
import base64
import hmac
try:
  from compression import zlib
except:
  import zlib
try:
  from compression import gzip
except:
  import gzip
try:
  from compression import zstd
except:
  zstd = None
try:
  import brotli
except:
  brotli = None
import os
import hashlib
import struct
import textwrap
import subprocess
from msvcrt import get_osfhandle

__all__ = ['socket', 'ISocketGenerator', 'IDSocketGenerator', 'IDAltSocketGenerator', 'NestedSSLContext', 'HTTPMessage', 'HTTPStreamMessage', 'HTTPRequestConstructor', 'RSASelfSigned', 'UDPIServer', 'UDPIDServer', 'UDPIDAltServer', 'TCPIServer', 'TCPIDServer', 'TCPIDAltServer', 'RequestHandler', 'HTTPRequestHandler', 'HTTPIServer', 'HTTPBasicAuthenticator', 'MultiUDPIServer', 'MultiUDPIDServer', 'MultiUDPIDAltServer', 'WebSocketDataStore', 'WebSocketRequestHandler', 'WebSocketIDServer', 'WebSocketIDAltServer', 'WebSocketIDClient', 'WebRTCSignalingServer', 'WebRTCBasicAuthenticator', 'HTTPIDownload', 'HTTPIListDownload', 'HTTPIUpload', 'NTPClient', 'TOTPassword']

ws2 = ctypes.WinDLL('ws2_32', use_last_error=True)
iphlpapi = ctypes.WinDLL('iphlpapi', use_last_error=True)
wcrypt = ctypes.WinDLL('crypt32', use_last_error=True)
ncrypt = ctypes.WinDLL('ncrypt', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32',  use_last_error=True)
shlwapi = ctypes.WinDLL('shlwapi', use_last_error=True)
byref = ctypes.byref
BYTE = ctypes.wintypes.BYTE
INT = ctypes.wintypes.INT
UINT = ctypes.wintypes.UINT
LONG = ctypes.wintypes.LONG
ULONG = ctypes.wintypes.ULONG
WORD = ctypes.wintypes.WORD
SHORT = ctypes.wintypes.SHORT
USHORT = ctypes.wintypes.USHORT
DWORD = ctypes.wintypes.DWORD
LARGE_INTEGER = ctypes.wintypes.LARGE_INTEGER
ULARGE_INTEGER = ctypes.wintypes.ULARGE_INTEGER
BOOL = ctypes.wintypes.BOOL
PVOID = ctypes.wintypes.LPVOID
HANDLE = ctypes.wintypes.HANDLE
SOCKET  = HANDLE
WSAEVENT = HANDLE
LPCSTR = ctypes.wintypes.LPCSTR
WCHAR = ctypes.wintypes.WCHAR
LPCWSTR = ctypes.wintypes.LPCWSTR
LPWSTR = ctypes.wintypes.LPWSTR
LPVOID = ctypes.wintypes.LPVOID
LPCVOID = ctypes.wintypes.LPCVOID
PSHORT = ctypes.wintypes.PSHORT
PULONG = ctypes.wintypes.PULONG
POINTER = ctypes.POINTER
STRUCTURE = ctypes.Structure
BIGENDIANUNION = ctypes.BigEndianUnion
UNION = ctypes.Union
GUID = BYTE * 16
ULONG_PTR = ctypes.wintypes.WPARAM
WinError = ctypes.WinError
ClosedError = lambda: WinError(10038)
AlreadyError = lambda: WinError(10037)
ConResetError = lambda: WinError(10054)

class WSANETWORKEVENTS(STRUCTURE):
  _fields_ = [('lNetworkEvents', LONG), ('iErrorCode', INT*10)]

class MIB_IPADDRROW(STRUCTURE):
  _fields_ = [('dwAddr', DWORD), ('dwIndex', DWORD), ('dwMask', DWORD), ('dwBCastAddr', DWORD), ('dwReasmSize', DWORD), ('unused', USHORT), ('wType', USHORT)]
class MIB_IPADDRTABLE(STRUCTURE):
  _fields_ = [('dwNumEntries', DWORD), ('table', MIB_IPADDRROW*0)]
P_MIB_IPADDRTABLE = POINTER(MIB_IPADDRTABLE)

class IN_PORT(BIGENDIANUNION):
  _fields_ = [('port', USHORT)]
class IN_ADDR(BIGENDIANUNION):
  _fields_ = [('addr_l', ULONG), ('addr_4b', BYTE * 4)]
class SOCKADDR_IN(STRUCTURE):
  _anonymous_ = ('port',)
  _fields_ = [('family', SHORT), ('port', IN_PORT), ('addr', IN_ADDR), ('zero', BYTE * 8)]
PSOCKADDR_IN = POINTER(SOCKADDR_IN)
class IN6_ADDR(BIGENDIANUNION):
  _fields_ = [('addr_8w', USHORT * 8), ('addr_16b', BYTE * 16)]
class SCOPE_ID_ZONELEVEL(STRUCTURE):
  _fields_ = [('Zone', ULONG, 24), ('Level', ULONG, 4)]
class SCOPE_ID(UNION):
  _anonymous_ = ('ZoneLevel',)
  _fields_ = [('Value', ULONG), ('ZoneLevel', SCOPE_ID_ZONELEVEL)]
class IN_FLOWINFO(BIGENDIANUNION):
  _fields_ = [('flowinfo', ULONG)]
class SOCKADDR_IN6(STRUCTURE):
  _anonymous_ = ('port', 'flowinfo')
  _fields_ = [('family', SHORT), ('port', IN_PORT), ('flowinfo', IN_FLOWINFO), ('addr', IN6_ADDR), ('scope_id', SCOPE_ID)]
PSOCKADDR_IN6 = POINTER(SOCKADDR_IN6)
class SOCKET_ADDRESS(STRUCTURE):
  _fields_ = [('lpSockaddr', PSHORT), ('iSockaddrLength', INT)]
class IP_ADAPTER_UNICAST_ADDRESS(STRUCTURE):
  pass
PIP_ADAPTER_UNICAST_ADDRESS = POINTER(IP_ADAPTER_UNICAST_ADDRESS)
IP_ADAPTER_UNICAST_ADDRESS._fields_ = [('Length', ULONG), ('Flags', DWORD), ('Next', PIP_ADAPTER_UNICAST_ADDRESS), ('Address', SOCKET_ADDRESS), ('PrefixOrigin', INT), ('SuffixOrigin', INT), ('DadState', INT), ('ValidLifetime', ULONG), ('PreferredLifetime', ULONG), ('LeaseLifetime', ULONG), ('OnLinkPrefixLength', BYTE)]
class IP_ADAPTER_ANICAST_ADDRESS(STRUCTURE):
  pass
PIP_ADAPTER_ANICAST_ADDRESS = POINTER(IP_ADAPTER_ANICAST_ADDRESS)
IP_ADAPTER_ANICAST_ADDRESS._fields_ = [('Length', ULONG), ('Flags', DWORD), ('Next', PIP_ADAPTER_ANICAST_ADDRESS), ('Address', SOCKET_ADDRESS)]
class IP_ADAPTER_MULTICAST_ADDRESS(STRUCTURE):
  pass
PIP_ADAPTER_MULTICAST_ADDRESS = POINTER(IP_ADAPTER_MULTICAST_ADDRESS)
IP_ADAPTER_MULTICAST_ADDRESS._fields_ = [('Length', ULONG), ('Flags', DWORD), ('Next', PIP_ADAPTER_MULTICAST_ADDRESS), ('Address', SOCKET_ADDRESS)]
class IP_ADAPTER_DNS_SERVER_ADDRESS(STRUCTURE):
  pass
PIP_ADAPTER_DNS_SERVER_ADDRESS = POINTER(IP_ADAPTER_DNS_SERVER_ADDRESS)
IP_ADAPTER_DNS_SERVER_ADDRESS._fields_ = [('Length', ULONG), ('Reserved', DWORD), ('Next', PIP_ADAPTER_DNS_SERVER_ADDRESS), ('Address', SOCKET_ADDRESS)]
class FlagsSet(STRUCTURE):
  _fields_ = [('DdnsEnabled', ULONG, 1), ('RegisterAdapterSuffix', ULONG, 1), ('Dhcpv4Enabled', ULONG, 1), ('ReceiveOnly', ULONG, 1), ('NoMulticast', ULONG, 1), ('Ipv6OtherStatefulConfig', ULONG, 1), ('NetbiosOverTcpipEnabled', ULONG, 1), ('Ipv4Enabled', ULONG, 1), ('Ipv6Enabled', ULONG, 1), ('Ipv6ManagedAddressConfigurationSupported', ULONG, 1)]
class Flags(UNION):
  _anonymous_ = ('FlagsSet',)
  _fields_ = [('Flags', ULONG), ('FlagsSet', FlagsSet)]
class IP_ADAPTER_PREFIX(STRUCTURE):
  pass
PIP_ADAPTER_PREFIX = POINTER(IP_ADAPTER_PREFIX)
IP_ADAPTER_PREFIX._fields_ = [('Length', ULONG), ('Flage', DWORD), ('Next', PIP_ADAPTER_PREFIX), ('Address', SOCKET_ADDRESS), ('PrefixLength', ULONG)]
class IP_ADAPTER_WINS_SERVER_ADDRESS(STRUCTURE):
  pass
PIP_ADAPTER_WINS_SERVER_ADDRESS = POINTER(IP_ADAPTER_WINS_SERVER_ADDRESS)
IP_ADAPTER_WINS_SERVER_ADDRESS._fields_ = [('Length', ULONG), ('Reserved', DWORD), ('Next', PIP_ADAPTER_WINS_SERVER_ADDRESS), ('Address', SOCKET_ADDRESS)]
class IP_ADAPTER_GATEWAY_ADDRESS(STRUCTURE):
  pass
PIP_ADAPTER_GATEWAY_ADDRESS = POINTER(IP_ADAPTER_GATEWAY_ADDRESS)
IP_ADAPTER_GATEWAY_ADDRESS._fields_ = [('Length', ULONG), ('Reserved', DWORD), ('Next', PIP_ADAPTER_GATEWAY_ADDRESS), ('Address', SOCKET_ADDRESS)]
class IF_LUID_INFO(STRUCTURE):
  _fields_ = [('Reserved', ULARGE_INTEGER, 24), ('NetLuidIndex', ULARGE_INTEGER, 24), ('IfType', ULARGE_INTEGER, 16)]
class IF_LUID(UNION):
  _anonymous_ = ('Info',)
  _fields_ = [('Value', ULARGE_INTEGER), ('Info', IF_LUID_INFO)]
class IP_ADAPTER_DNS_SUFFIX(STRUCTURE):
  pass
PIP_ADAPTER_DNS_SUFFIX = POINTER(IP_ADAPTER_DNS_SUFFIX)
IP_ADAPTER_DNS_SUFFIX._fields_ = [('Next', PIP_ADAPTER_DNS_SUFFIX), ('String', WCHAR * 256)]
class IP_ADAPTER_ADDRESSES(STRUCTURE):
  _anonymous_ = ('Flags',)
PIP_ADAPTER_ADDRESSES = POINTER(IP_ADAPTER_ADDRESSES)
IP_ADAPTER_ADDRESSES._fields_ = [('Length', ULONG), ('IfIndex', DWORD), ('Next', PIP_ADAPTER_ADDRESSES), ('AdapterName', LPCSTR), ('FirstUnicastAddress', PIP_ADAPTER_UNICAST_ADDRESS), ('FirstAnycastAddress', PIP_ADAPTER_ANICAST_ADDRESS), ('FirstMulticastAddress', PIP_ADAPTER_MULTICAST_ADDRESS), ('FirstDnsServerAddress', PIP_ADAPTER_DNS_SERVER_ADDRESS), ('DnsSuffix', LPCWSTR), ('Description', LPCWSTR), ('FriendlyName', LPCWSTR), ('PhysicalAddress', BYTE * 8), ('PhysicalAddressLength', ULONG), ('Flags', Flags), ('Mtu', ULONG), ('IfType', DWORD), ('OperStatus', INT), ('Ipv6IfIndex', DWORD), ('ZoneIndices', ULONG * 16), ('FirstPrefix', PIP_ADAPTER_PREFIX), ('TransmitLinkSpeed', ULARGE_INTEGER), ('ReceiveLinkSpeed', ULARGE_INTEGER), ('FirstWinsServerAddress', PIP_ADAPTER_WINS_SERVER_ADDRESS), ('FirstGatewayAddress', PIP_ADAPTER_GATEWAY_ADDRESS), ('Ipv4Metric', ULONG), ('Ipv6Metric', ULONG), ('Luid', IF_LUID), ('Dhcpv4Server', SOCKET_ADDRESS), ('CompartmentId', UINT), ('NetworkGuid', GUID), ('ConnectionType', INT), ('TunnelType', INT), ('Dhcpv6Server', SOCKET_ADDRESS), ('Dhcpv6ClientDuid', BYTE * 130), ('Dhcpv6ClientDuidLength', ULONG), ('Dhcpv6Iaid', ULONG), ('FirstDnsSuffix', PIP_ADAPTER_DNS_SUFFIX)]

class CRYPT_KEY_PROV_INFO(STRUCTURE):
  _fields_ = [('pwszContainerName', LPWSTR), ('pwszProvName', LPWSTR), ('dwProvType', DWORD), ('dwFlags', DWORD), ('cProvParam', DWORD), ('rgProvParam', PVOID), ('dwKeySpec', DWORD)]
class CERT_EXTENSIONS(STRUCTURE):
  _fields_ = [('cExtension', DWORD), ('rgExtension', HANDLE)]
class SYSTEMTIME(STRUCTURE):
  _fields_ = [('wYear', WORD), ('wMonth', WORD), ('wDayOfWeek', WORD), ('wDay', WORD), ('wHour', WORD), ('WMinute', WORD), ('WSecond', WORD), ('WMilliseconds', WORD)]
P_SYSTEMTIME = POINTER(SYSTEMTIME)
class CRYPT_INTEGER_BLOB(STRUCTURE):
  _fields_ = [('cbData', DWORD), ('pbData', PVOID)]
class CERT_CONTEXT(STRUCTURE):
  _fields_ = [('dwCertEncodingType', DWORD), ('pbCertEncoded', PVOID), ('cbCertEncoded', DWORD), ('pCertInfo', PVOID), ('hCertStore', HANDLE)]
P_CERT_CONTEXT = POINTER(CERT_CONTEXT)

class OVERLAPPED_O(STRUCTURE):
  _fields_= [('Offset', DWORD), ('OffsetHigh', DWORD)]
class OVERLAPPED(STRUCTURE):
  _anonymous_ = ('o',)
  _fields_ = [('Internal', ULONG_PTR), ('InternalHigh', ULONG_PTR), ('o', OVERLAPPED_O), ('hEvent', HANDLE)]

class FILE_ZERO_DATA_INFORMATION(STRUCTURE):
  _fields_ = [('FileOffset', LARGE_INTEGER), ('BeyondFinalZero', LARGE_INTEGER)]

ws2.WSACreateEvent.restype = WSAEVENT
wcrypt.CertCreateSelfSignCertificate.restype = P_CERT_CONTEXT
kernel32.CreateNamedPipeW.restype = HANDLE


class _ISocketMeta(type):

  def func_wrap(cls, mode, func, f):
    def w(self, *args, timeout='', **kwargs):
      return cls._func_wrap(self, mode, func, f, *args, timeout=timeout, **kwargs)
    w.__name__ = func.__name__
    w.__qualname__ = cls._func_wrap.__qualname__[:-10] + func.__name__
    return w

  def __init__(cls, *args, **kwargs):
    type.__init__(cls, *args, **kwargs)
    for name in ('recv', 'recvfrom', 'recv_into', 'recvfrom_into'):
      setattr(cls, name, cls.func_wrap('r', getattr(socket.socket, name), 2 if name[-4:] == 'into' else 1))
    for name in ('send', 'sendto'):
      setattr(cls, name, cls.func_wrap('w', getattr(socket.socket, name), float('inf')))
    def attribute_error(self, *args, **kwargs):
      raise NotImplementedError()
    for name in ('dup', 'makefile', 'ioctl', 'share'):
      setattr(cls, name, attribute_error)


class ISocket(socket.socket, metaclass=_ISocketMeta):

  MODES = {'r': LONG(33), 'a': LONG(8), 'w': LONG(34), 'c': LONG(16)}
  HAS_TIMEOUT = True

  def __init__(self, gen, family=-1, type=-1, proto=-1, fileno=None, timeout=''):
    self.closed = True
    socket.socket.__init__(self, family, type, proto, fileno)
    self.gen = gen
    self.sock_fileno = socket.socket.fileno(self)
    self.sock_timeout = gen.defaulttimeout if timeout == '' else timeout
    socket.socket.settimeout(self, 0)
    self.event = WSAEVENT(ws2.WSACreateEvent())
    self._mode = ''
    self._lock = threading.RLock()
    self.closed = False
    gen.isockets[self] = True

  def lock(self, timeout=''):
    if timeout == '':
      timeout = self.sock_timeout
    if timeout is None:
      if self._lock.acquire():
        return timeout, None, None
      else:
        raise ClosedError() if self.closed else TimeoutError()
    else:
      t = time.monotonic()
      if self._lock.acquire(timeout=timeout):
        return timeout, max(0, timeout + t - time.monotonic()), None
      else:
        raise ClosedError() if self.closed else TimeoutError()

  def unlock(self, ul):
    self._lock.release()

  @property
  def mode(self):
    return self._mode if not self.closed else None

  def _set_mode(self, value):
    if self.closed and value is not None:
      return
    self._mode = value
    ws2.WSAEventSelect(SOCKET(self.sock_fileno), WSAEVENT(None), LONG(0))
    if value is not None:
      ws2.WSAResetEvent(self.event)
      ws2.WSAEventSelect(SOCKET(self.sock_fileno), self.event, self.MODES.get(value, LONG(0)))
    else:
      ws2.WSACloseEvent(self.event)
      self.gen.isockets[self] = False

  @mode.setter
  def mode(self, value):
    if self._mode != value:
      self._set_mode(value)

  def unwrap(self, *, timeout=''):
    ul = self.lock(timeout)[2]
    try:
      self.mode = None
      self.closed = True
      sock = socket.socket(family=self.family, type=self.type, proto=self.proto, fileno=self.sock_fileno) if self.sock_fileno >= 0 else None
      self.detach()
    finally:
      self.unlock(ul)
    try:
      sock.settimeout(self.sock_timeout)
    except:
      pass
    return sock

  def shutdown(self, *args, timeout='', **kwargs):
    ul = self.lock(timeout)[2]
    try:
      if not self.closed:
        socket.socket.shutdown(self, *args, **kwargs)
      else:
        raise ClosedError()
    finally:
      self.unlock(ul)

  def _close(self, deletion=False):
    if deletion:
      self.closed = True
    else:
      with self.gen.lock:
        if self.closed:
          return
        self.closed = True
    ws2.WSASetEvent(self.event)
    ul = self.lock(None)[2]
    self.mode = None
    self.unlock(ul)
    self.sock_fileno = -1

  def close(self, *args, **kwargs):
    self._close()
    socket.socket.close(self, *args, **kwargs)

  def shutclose(self):
    self._close()
    try:
      socket.socket.shutdown(self, socket.SHUT_RDWR)
    except:
      pass
    try:
      socket.socket.close(self)
    except:
      pass

  def detach(self, *args, **kwargs):
    self._close()
    return socket.socket.detach(self, *args, **kwargs)

  def __enter__(self):
    return self

  def __exit__(self, et, ev, tb):
    self.shutclose()

  def __del__(self):
    if self.closed:
      return
    self._close(deletion=True)
    try:
      socket.socket.shutdown(self, socket.SHUT_RDWR)
    except:
      pass
    try:
      socket.socket.close(self)
    except:
      pass
    super().__del__()

  def gettimeout(self):
    return self.sock_timeout

  def settimeout(self, value):
    self.sock_timeout = value

  def getblocking(self):
    return self.sock_timeout != 0.0

  def setblocking(self, flag):
    self.sock_timeout = None if flag else 0.0

  @property
  def timeout(self):
    return self.sock_timeout

  def wait(self, timeout):
    if not self.mode or (timeout is not None and timeout < 0):
      return False
    if ws2.WSAWaitForMultipleEvents(ULONG(1), byref(self.event), BOOL(False), ULONG(int(timeout * 1000) if timeout is not None else -1), BOOL(False)) == 258 or not self.mode:
      return False
    else:
      ws2.WSAResetEvent(self.event)
      return True

  def _func_wrap(self, mode, func, f, *args, timeout='', **kwargs):
    timeout, rt, ul = self.lock(timeout)
    try:
      if self.closed:
        raise ClosedError()
      self.mode = mode
      ws2.WSAResetEvent(self.event)
      try:
        r = func(self, *args, **kwargs)
        if len(args) > f and (args[f] & socket.MSG_PEEK):
          ws2.WSASetEvent(self.event)
        return r
      except BlockingIOError:
        if timeout != 0 and self.wait(rt):
          if len(args) > f and (args[f] & socket.MSG_PEEK):
            ws2.WSASetEvent(self.event)
          return func(self, *args, **kwargs)
      raise ClosedError() if self.closed else TimeoutError()
    finally:
      self.unlock(ul)

  def _sendall(self, bytes, *args, timeout=None, **kwargs):
    with memoryview(bytes).cast('B') as m:
      l = len(m)
      s = 0
      if timeout is None:
        while s < l:
          s += self.send(m[s:], *args, timeout=None, **kwargs)
      else:
        t = time.monotonic()
        rt = timeout
        while s < l:
          if rt < 0:
            raise TimeoutError()
          s += self.send(m[s:], *args, timeout=rt, **kwargs)
          rt = timeout + t - time.monotonic()

  def sendall(self, bytes, *args, timeout='', **kwargs):
    timeout, rt, ul = self.lock(timeout)
    try:
      self._sendall(bytes, *args, timeout=rt, **kwargs)
    finally:
      self.unlock(ul)

  class _PISocket:

    def __init__(self, s):
      self.s = s

    def gettimeout(self):
      return None

    timeout = None

    def __getattr__(self, name):
      return getattr(self.s, name)

    def accept_wrap(self, s, *args, **kwargs):
      return socket.socket.accept(self, *args, **kwargs)

  def accept(self, *args, timeout='', **kwargs):
    a = self._func_wrap('a', self.__class__._PISocket(self).accept_wrap, float('inf'), *args, timeout=timeout, **kwargs)
    isock = self.gen.wrap(a[0])
    isock.settimeout(self.timeout)
    isock.mode = 'r'
    return (isock, a[1])

  def _connect_pending_check(self, rt):
    self._set_mode('c')
    if rt is not None:
      end_time = rt + time.monotonic()
    if self.wait(rt):
      del self._connect_pending
      return None if rt is None else max(end_time - time.monotonic(), 0)
    else:
      return True

  def _connect_pending(self, rt):
    self.mode = 'c'
    return rt

  def connect(self, *args, timeout='', **kwargs):
    timeout, rt, ul = self.lock(timeout)
    try:
      if self.closed:
        raise ClosedError()
      rt = self._connect_pending(rt)
      if rt is True:
        raise AlreadyError()
      ws2.WSAResetEvent(self.event)
      try:
        socket.socket.connect(self, *args, **kwargs)
        return
      except BlockingIOError:
        if timeout != 0 and self.wait(rt):
          self.mode = 'w'
          if self.wait(0):
            return
          else:
            raise WinError(self.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR))
      if self.closed:
        raise ClosedError()
      else:
        self._connect_pending = self._connect_pending_check
        raise TimeoutError()
    finally:
      self.unlock(ul)

  def connect_ex(self, *args, timeout='', **kwargs):
    timeout, rt, ul = self.lock(timeout)
    try:
      if self.closed:
        return 10038
      rt = self._connect_pending(rt)
      if rt is True:
        return 10037
      ws2.WSAResetEvent(self.event)
      try:
        r = socket.socket.connect_ex(self, *args, **kwargs)
        if r == 10035:
          raise BlockingIOError()
        return r
      except BlockingIOError:
        if timeout != 0 and self.wait(rt):
          self.mode = 'w'
          return 0 if self.wait(0) else self.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
      if self.closed:
        return 10038
      else:
        self._connect_pending = self._connect_pending_check
        return 10035
    finally:
      self.unlock(ul)

  @classmethod
  def _wait_for_events(cls, timeout, events, event_c=None):
    c = len(events) if event_c is None else (len(events) + 1)
    if c <= 64:
      if event_c is None:
        w = ws2.WSAWaitForMultipleEvents(ULONG(c), byref((WSAEVENT*c)(*events)), BOOL(False), timeout, BOOL(False))
      else:
        w = ws2.WSAWaitForMultipleEvents(ULONG(c), byref((WSAEVENT*c)(*events, event_c)), BOOL(False), timeout, BOOL(False))
    else:
      ev_c = WSAEVENT(ws2.WSACreateEvent()) if event_c is None else event_c
      t = threading.Thread(target=cls._wait_for_events, args=(timeout, events[63:], ev_c), daemon=True)
      t.start()
      w = ws2.WSAWaitForMultipleEvents(ULONG(64), byref((WSAEVENT*64)(*events[:63], ev_c)), BOOL(False), timeout, BOOL(False))
    if event_c is None:
      if c > 64:
        ws2.WSASetEvent(ev_c)
      return w
    elif w != 258:
      ws2.WSASetEvent(event_c)

  @classmethod
  def waitmult(cls, timeout, *isocks, event=None, reset_event=False):
    if event not in ('None', 'r', 'a', 'w', 'c'):
      return ()
    t = time.monotonic()
    rt = timeout
    locks = 0
    for isock in isocks:
      if (not isock._lock.acquire(timeout=-1)) if timeout is None else (rt < 0 or not isock._lock.acquire(timeout=rt)):
        for i in range(locks):
          isocks[i]._lock.release()
        return ()
      locks += 1
      if event is not None:
        isock._set_mode(event)
      if timeout is not None:
        rt = timeout + t - time.monotonic()
    isocks_ = tuple(isock for isock in isocks if isock.mode)
    c = len(isocks_)
    if cls._wait_for_events(ULONG(int(rt * 1000) if timeout is not None else -1), tuple(isock.event for isock in isocks_)) == 258:
      r = ()
    else:
      r = tuple(isock for isock in isocks_ if (ws2.WSAWaitForMultipleEvents(ULONG(1), byref(isock.event), BOOL(False), ULONG(0), BOOL(False)) != 258 and isock.mode) and ((reset_event and ws2.WSAResetEvent(isock.event)) or True))
    for isock in isocks:
      isock._lock.release()
    return r


class ISocketGenerator:

  CLASS = ISocket

  def __init__(self):
    self.isockets = weakref.WeakKeyDictionary()
    self.lock = threading.Lock()
    self.closed = False
    self.defaulttimeout = socket.getdefaulttimeout()

  def wrap(self, sock):
    with self.lock:
      return self.CLASS(self, sock.family, sock.type, sock.proto, sock.detach(), sock.gettimeout()) if not self.closed else None

  def new(self, family=-1, type=-1, proto=-1):
    with self.lock:
      return self.CLASS(self, family, type, proto) if not self.closed else None

  def __call__(self, *args, **kwargs):
    return self.new(*args, **kwargs) if not args or not isinstance(args[0], socket.socket) else self.wrap(args[0])

  def close(self):
    with self.lock:
      self.closed = True
    for isock, activ in self.isockets.items():
      if activ:
        isock.shutclose()

  def __enter__(self):
    return self

  def __exit__(self, et, ev, tb):
    self.close()

  def getdefaulttimeout(self):
    return self.defaulttimeout

  def setdefaulttimeout(self, timeout):
    self.defaulttimeout = timeout

  def create_connection(self, address, timeout='', source_address=None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM):
    if timeout == '':
      timeout = socket.getdefaulttimeout()
    err = None
    t = time.monotonic()
    rt = timeout
    for res in socket.getaddrinfo(*address, family=family, type=type):
      if self.closed:
        return None
      if timeout is not None and rt < 0:
        raise TimeoutError()
      isock = None
      try:
        isock = self.new(*res[:3])
        if self.closed:
          return None
        if source_address:
          isock.bind(source_address)
        isock.connect(res[4], timeout=rt)
        return isock
      except Exception as _err:
        err = _err
        if isock is not None:
          isock.close()
      if timeout is not None:
        rt = timeout + t - time.monotonic()
    raise err if err is not None else socket.gaierror()

  def create_server(self, address, family=socket.AF_UNSPEC, backlog=None, reuse_port=False, dualstack_ipv6=False, type=socket.SOCK_STREAM):
    res = socket.getaddrinfo(address[0], address[1], family=family, type=type, flags=socket.AI_PASSIVE)[0]
    isock = self.new(*res[:3])
    try:
      if reuse_port:
        isock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      if dualstack_ipv6 and res[0] == socket.AF_INET6:
        isock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
      isock.bind(res[4])
      if type == socket.SOCK_STREAM:
        if backlog is None:
          isock.listen()
        elif backlog is not False:
          isock.listen(backlog)
      return isock
    except Exception as err:
      isock.close()
      raise err

  def waitany(self, timeout, event):
    if event not in ('r', 'a', 'w', 'c') or self.closed:
      return ()
    return ISocket.waitmult(timeout, *(isock for isock, activ in self.isockets.items() if activ), event=event, reset_event=False)

  def socket(self, family=-1, type=-1, proto=-1):
    return self.new(family, type, proto)


class _BIDSocket(ISocket):

  MODES = {'u': LONG(59)}
  MODES_M = {'r': 33, 'a': 8, 'w': 34, 'c': 16}
  IS_DUPLEX = True

  def __init__(self, gen, family=-1, type=-1, proto=-1, fileno=None, timeout=''):
    super().__init__(gen, family, type, proto, fileno, timeout)
    self._condition = threading.Condition(self._lock)
    self._queue_r = deque()
    self._queue_w = deque()

  def lock(self, timeout='', mode='u'):
    th = threading.current_thread()
    if mode == 'r':
      pred = lambda : self._queue_r[0][0] == th
    elif mode == 'w':
      pred = lambda : self._queue_w[0][0] == th
    else:
      pred = lambda : self._queue_r[0][0] == th and self._queue_w[0][0] == th
    if timeout == '':
      timeout = self.sock_timeout
    a_r = a_w = None
    with self._condition:
      if mode != 'w':
        a_r = [th]
        self._queue_r.append(a_r)
      if mode != 'r':
        a_w = [th]
        self._queue_w.append(a_w)
      a = pred()
      if timeout is None:
        if not a:
          a = self._condition.wait_for(pred)
        if a:
          return timeout, None, (a_r, a_w)
        else:
          raise ClosedError() if self.closed else TimeoutError()
      else:
        t = time.monotonic()
        if not a:
          a = self._condition.wait_for(pred, timeout)
        if a:
          return timeout, timeout + t - time.monotonic(), (a_r, a_w)
        else:
          raise ClosedError() if self.closed else TimeoutError()

  def unlock(self, ul):
    a_r, a_w = ul
    with self._condition:
      if a_r is not None:
        a_r[0] = None
        while self._queue_r and self._queue_r[0][0] is None:
          self._queue_r.popleft()
      if a_w is not None:
        a_w[0] = None
        while self._queue_w and self._queue_w[0][0] is None:
          self._queue_w.popleft()
      self._condition.notify_all()

  def accept(self, *args, timeout='', **kwargs):
    a = self._func_wrap('a', self.__class__._PISocket(self).accept_wrap, float('inf'), *args, timeout=timeout, **kwargs)
    isock = self.gen.wrap(a[0])
    isock.settimeout(self.timeout)
    return (isock, a[1])

  def sendall(self, bytes, *args, timeout='', **kwargs):
    timeout, rt, ul = self.lock(timeout, 'w')
    try:
      self._sendall(bytes, *args, timeout=rt, **kwargs)
    finally:
      self.unlock(ul)

  def _connect_pending(self, rt):
    return rt


class IDSocket(_BIDSocket):

  class _RevertibleEvent:

    __slots__ = ('_cond', '_flag', '_ex_flag')

    def __init__(self, lock=None):
      self._cond = threading.Condition(lock or threading.Lock())
      self._ex_flag = self._flag = False

    def __repr__(self):
      return '%s: %s>' % (object.__repr__(self)[:-1], ('set' if self._flag else 'unset'))

    def is_set(self):
      return self._flag

    def was_set(self):
      return self._ex_flag

    def set(self):
      with self._cond:
        self._ex_flag = self._flag
        self._flag = True
        self._cond.notify_all()
      return self._ex_flag

    def setf(self):
      self._ex_flag = self._flag
      self._flag = True
      self._cond.notify_all()
      return self._ex_flag

    def unset(self):
      with self._cond:
        ex_flag = self._flag
        self._flag &= self._ex_flag
        self._ex_flag = ex_flag
      return self._ex_flag

    def clear(self):
      with self._cond:
        self._ex_flag = self._flag
        self._flag = False
      return self._ex_flag

    def clearf(self):
      self._ex_flag = self._flag
      self._flag = False
      return self._ex_flag

    def unclear(self):
      with self._cond:
        ex_flag = self._flag
        self._flag |= self._ex_flag
        self._ex_flag = ex_flag
      return self._ex_flag

    def wait(self, timeout=None):
      with self._cond:
        return True if self._flag else self._cond.wait(timeout)

  class _CountedWSAEvent:

    __slots__ = ('_event', '_lock', '_counter', '_closed')

    def __init__(self):
      self._counter = 0
      self._lock = threading.Lock()
      self._event = WSAEVENT(ws2.WSACreateEvent())
      self._closed = False

    def inc(self):
      with self._lock:
        if not self._counter:
          ws2.WSASetEvent(self._event)
        self._counter += 1

    def dec(self):
      with self._lock:
        self._counter -= 1
        if not self._counter:
          ws2.WSAResetEvent(self._event)

    def close(self):
      with self._lock:
        if not self._closed:
          self._closed = True
        else:
          return
      ws2.WSACloseEvent(self._event)

    def __del__(self):
      self.close()

  def __init__(self, gen, family=-1, type=-1, proto=-1, fileno=None, timeout=''):
    super().__init__(gen, family, type, proto, fileno, timeout)
    self._erlock = threading.RLock()
    self._ewlock = threading.RLock()
    self._elock = {'r': self._erlock, 'a': self._erlock, 'w': self._ewlock, 'c': self._ewlock}
    self.events = {m: self.__class__._RevertibleEvent(self._elock[m]) for m in ('r', 'a', 'w', 'c')}
    self.wait_start()

  def _close(self, deletion=False):
    if deletion:
      self.closed = True
    else:
      with self.gen.lock:
        if self.closed:
          return
        self.closed = True
    self._wevent.inc()
    ws2.WSASetEvent(self.event)
    self.wthread.join()
    ul = self.lock(None)[2]
    self.mode = None
    self.unlock(ul)
    self.sock_fileno = -1

  @staticmethod
  def _wait(ref):
    self = ref()
    if not self:
      return
    e = self.event
    f = SOCKET(self.sock_fileno)
    NetworkEvents = WSANETWORKEVENTS()
    cEvents = ULONG(2)
    hEvents = (WSAEVENT*2)(e, self._wevent._event)
    fWaitAll = BOOL(True)
    dwTimeout = ULONG(-1)
    fAlertable = BOOL(False)
    while not self.closed:
      del self
      ws2.WSAWaitForMultipleEvents(cEvents, byref(hEvents), fWaitAll, dwTimeout, fAlertable)
      self = ref()
      if self:
        if not self.closed:
          with self._erlock, self._ewlock:
            if ws2.WSAEnumNetworkEvents(f, e, byref(NetworkEvents)):
              ws2.WSAResetEvent(e)
            else:
              for m in ('r', 'a', 'w', 'c'):
                if NetworkEvents.lNetworkEvents & self.MODES_M[m]:
                  self.events[m].setf()
                  ev = self.gen.events[m]
                  if ev is not None:
                    ev.set()
      else:
        return
    for m in ('r', 'a', 'w', 'c'):
      self.events[m].set()
      ev = self.gen.events[m]
      if ev is not None:
        ev.set()
    self._wevent.close()
    del self

  def wait_start(self):
    self.mode = 'u'
    self._wevent = self.__class__._CountedWSAEvent()
    self.wthread = threading.Thread(target=self.__class__._wait, args=(weakref.getweakrefs(self)[0],), daemon=True)
    self.wthread.start()

  def wait(self, timeout, mode):
    if not self.mode:
      return False
    self._wevent.inc()
    w = self.events[mode].wait(None if timeout is None else max(timeout, 0.000001))
    self._wevent.dec()
    return w and bool(self.mode)

  def _func_wrap(self, m, func, f, *args, timeout='', **kwargs):
    timeout, rt, ul = self.lock(timeout, m)
    try:
      if self.closed:
        raise ClosedError()
      end_time = None
      while True:
        try:
          with self._elock[m]:
            self.events[m].clearf()
            r = func(self, *args, **kwargs)
            if len(args) > f and (args[f] & socket.MSG_PEEK):
              self.events[m].setf()
          return r
        except BlockingIOError:
          if timeout == 0:
            break
          if rt is not None:
            if end_time is None:
              end_time = rt + time.monotonic()
            else:
              rt = end_time - time.monotonic()
          if not self.wait(rt, m):
            break
        except OSError as err:
          if err.winerror is None:
            self.events[m].unclear()
          raise
        except:
          self.events[m].unclear()
          raise
      raise ClosedError() if self.closed else TimeoutError()
    finally:
      self.unlock(ul)

  def _connect_pending_check(self, rt):
    if rt is not None:
      end_time = rt + time.monotonic()
    if self.wait(rt, 'c'):
      del self._connect_pending
      return None if rt is None else max(end_time - time.monotonic(), 0)
    else:
      return True

  def connect(self, *args, timeout='', **kwargs):
    timeout, rt, ul =  self.lock(timeout, 'c')
    try:
      if self.closed:
        raise ClosedError()
      rt = self._connect_pending(rt)
      if rt is True:
        raise AlreadyError()
      try:
        with self._elock['c']:
          self.events['c'].clearf()
          self.events['w'].clearf()
          socket.socket.connect(self, *args, **kwargs)
        return
      except BlockingIOError:
        if timeout != 0 and self.wait(rt, 'c'):
          if not self.events['w'].is_set():
            raise WinError(self.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR))
          else:
            return
      except OSError as err:
        if err.winerror is None or err.winerror == 10056:
          self.events['c'].unclear()
          self.events['w'].unclear()
        else:
          self._connect_pending = self._connect_pending_check
        raise
      except:
        self.events['c'].unclear()
        self.events['w'].unclear()
        raise
      if self.closed:
        raise ClosedError()
      else:
        self._connect_pending = self._connect_pending_check
        raise TimeoutError()
    finally:
      self.unlock(ul)

  def connect_ex(self, *args, timeout='', **kwargs):
    timeout, rt, ul =  self.lock(timeout, 'c')
    try:
      if self.closed:
        return 10038
      rt = self._connect_pending(rt)
      if rt is True:
        return 10037
      try:
        with self._elock['c']:
          self.events['c'].clearf()
          self.events['w'].clearf()
          r = socket.socket.connect_ex(self, *args, **kwargs)
        if r == 10035:
          raise BlockingIOError()
        if r == 10056:
          self.events['c'].unclear()
          self.events['w'].unclear()
        return r
      except BlockingIOError:
        if timeout != 0 and self.wait(rt, 'c'):
          return self.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) if not self.events['w'].is_set() else 0
      except:
        self.events['c'].unclear()
        self.events['w'].unclear()
        raise
      if self.closed:
        return 10038
      else:
        self._connect_pending = self._connect_pending_check
        return 10035
    finally:
      self.unlock(ul)

  @classmethod
  def waitmult(cls, *args, **kwargs):
    raise NotImplementedError()


class IDAltSocket(_BIDSocket):

  def __init__(self, gen, family=-1, type=-1, proto=-1, fileno=None, timeout=''):
    super().__init__(gen, family, type, proto, fileno, timeout)
    self._erlock = threading.Lock()
    self._ewlock = threading.Lock()
    self._elock = {'r': self._erlock, 'a': self._erlock, 'w': self._ewlock, 'c': self._ewlock}
    self.events = {m: False for m in ('r', 'a', 'w', 'c')}
    self._network_events = WSANETWORKEVENTS()
    self.mode = 'u'

  def wait(self, end_time, mode, rt=None):
    rem_time = -1 if end_time is None else (int(((end_time - time.monotonic()) if rt is None else rt) * 1000))
    while True:
      if not self.mode or (end_time is not None and rem_time < 0):
        return False
      if ws2.WSAWaitForMultipleEvents(ULONG(1), byref(self.event), BOOL(False), ULONG(rem_time), BOOL(False)) == 258 or not self.mode:
        return False
      if self._elock[mode] == self._ewlock:
        self._ewlock.release()
        self._erlock.acquire()
      self._ewlock.acquire()
      if not ws2.WSAWaitForMultipleEvents(ULONG(1), byref(self.event), BOOL(False), ULONG(0), BOOL(False)):
        if ws2.WSAEnumNetworkEvents(SOCKET(self.sock_fileno), self.event, byref(self._network_events)):
          ws2.WSAResetEvent(self.event)
        else:
          for m in ('r', 'a', 'w', 'c'):
            if self._network_events.lNetworkEvents & self.MODES_M[m]:
              self.events[m] = True
      self._erlock.release()
      self._ewlock.release()
      self._elock[mode].acquire()
      if not self.mode:
        ws2.WSASetEvent(self.event)
        return False
      if self.events[mode]:
        return True
      if end_time is not None:
        rem_time = int((end_time - time.monotonic()) * 1000)

  def _func_wrap(self, m, func, f, *args, timeout='', **kwargs):
    if self.closed:
      raise ClosedError()
    timeout, rt, ul = self.lock(timeout, m)
    try:
      end_time = None
      self._elock[m].acquire()
      while True:
        try:
          r = func(self, *args, **kwargs)
          if len(args) <= f or not (args[f] & socket.MSG_PEEK):
            self.events[m] = False
          return r
        except BlockingIOError:
          self.events[m] = False
          if timeout == 0:
            raise ClosedError() if self.closed else TimeoutError()
          if rt is not None and end_time is None:
            end_time = rt + time.monotonic()
            w = self.wait(end_time, m, rt)
          else:
            w = self.wait(end_time, m)
          if w is False:
            raise ClosedError() if self.closed else TimeoutError()
        except OSError as err:
          if err.winerror is not None:
            self.events[m] = False
          raise
    finally:
      self._elock[m].release()
      self.unlock(ul)

  def _connect_pending_check(self, rt):
    end_time = None if rt is None else rt + time.monotonic()
    if not self.wait(end_time, rt, 'c'):
      return True
    del self._connect_pending
    return None if rt is None else max(end_time - time.monotonic(), 0)

  def connect(self, *args, timeout='', **kwargs):
    if self.closed:
      raise ClosedError()
    timeout, rt, ul =  self.lock(timeout, 'c')
    try:
      rt = self._connect_pending(rt)
      if rt is True:
        raise AlreadyError()
      self._elock['c'].acquire()
      try:
        socket.socket.connect(self, *args, **kwargs)
        self.events['c'] = False
        self.events['w'] = False
        self._connect_pending = self._connect_pending_check
        return
      except BlockingIOError:
        self.events['c'] = False
        self.events['w'] = False
        if timeout == 0 or self.wait((None if rt is None else rt + time.monotonic()), 'c', rt) is False:
          self._connect_pending = self._connect_pending_check
          raise ClosedError() if self.closed else TimeoutError()
        if not self.events['w']:
          raise WinError(self.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR))
      except OSError as err:
        if err.winerror is not None and err.winerror != 10056:
          self.events['c'] = False
          self.events['w'] = False
          self._connect_pending = self._connect_pending_check
        raise
    finally:
      self._elock['c'].release()
      self.unlock(ul)

  def connect_ex(self, *args, timeout='', **kwargs):
    if self.closed:
      return 10038
    timeout, rt, ul =  self.lock(timeout, 'c')
    try:
      rt = self._connect_pending(rt)
      if rt is True:
        return 10037
    finally:
      self.unlock(ul)
    try:
      self._elock['c'].acquire()
      try:
        r = socket.socket.connect_ex(self, *args, **kwargs)
        if r == 10035:
          raise BlockingIOError()
        if r != 10056:
          self.events['c'] = False
          self.events['w'] = False
          self._connect_pending = self._connect_pending_check
        return r
      except BlockingIOError:
        self.events['c'] = False
        self.events['w'] = False
        if timeout == 0 or self.wait((None if rt is None else rt + time.monotonic()), 'c', rt) is False:
          self._connect_pending = self._connect_pending_check
          return 10038 if self.closed else 10035
        return self.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) if not self.events['w'] else 0
    finally:
      self._elock['c'].release()
      self.unlock(ul)

  @classmethod
  def waitmult(cls, timeout, *idsocks, event=None, reset_event=False):
    if event not in ('r', 'a', 'w', 'c'):
      return ()
    rt = timeout
    uls = []
    for idsock in idsocks:
      try:
        if rt is not None and rt < 0:
          raise TimeoutError()
        rt, ul = idsock.lock(rt, event)[1:2]
        uls.append(ul)
      except ClosedError:
        uls.append(None)
      except TimeoutError:
        for idsock, ul in zip(idsocks, uls):
          if ul is not None:
            idsock.unlock(ul)
        return ()
    if rt is not None:
      end_time = rt + time.monotonic()
    while True:
      if rt is not None and rt < 0:
        r = ()
        break
      idsocks_ = tuple(idsock for idsock in idsocks if idsock.mode)
      c = len(idsocks_)
      if cls._wait_for_events(ULONG(int(rt * 1000) if timeout is not None else -1), tuple(e for idsock in idsocks_ for e in (idsock.event, idsock.events[event]))) == 258:
        r = ()
        break
      r = []
      for idsock in idsocks_:
        if not idsock.mode:
          continue
        if not ws2.WSAWaitForMultipleEvents(ULONG(1), byref(idsock.event), BOOL(False), ULONG(0), BOOL(False)):
          with idsock._erlock, idsock._ewlock:
            if ws2.WSAEnumNetworkEvents(SOCKET(idsock.sock_fileno), idsock.event, byref(idsock._network_events)):
              ws2.WSAResetEvent(idsock.event)
            else:
              for m in ('r', 'a', 'w', 'c'):
                if idsock._network_events.lNetworkEvents & cls.MODES_M[m]:
                  ws2.WSASetEvent(idsock.events[m])
        if not ws2.WSAWaitForMultipleEvents(ULONG(1), byref(idsock.events[event]), BOOL(False), ULONG(0), BOOL(False)):
          r.append(idsock)
          if reset_event:
            ws2.WSAResetEvent(idsock.events[event])
      if r:
        break
      if rt is not None:
        rt = end_time - time.monotonic()
    for idsock, ul in zip(idsocks, uls):
      if ul is not None:
        idsock.unlock(ul)
    return r


class IDSocketGenerator(ISocketGenerator):

  CLASS = IDSocket

  def __init__(self):
    super().__init__()
    self.idsockets = self.isockets
    self.events = {m: None for m in ('r', 'a', 'w', 'c')}

  def waitany(self, timeout, event):
    if event not in ('r', 'a', 'w', 'c') or self.closed:
      return ()
    with self.lock:
      if self.events[event] is not None:
        return ()
      self.events[event] = threading.Event()
    idsocks = tuple(idsock for idsock, activ in self.idsockets.items() if (activ and (idsock._wevent.inc() or True)))
    r = tuple(idsock for idsock in idsocks if (idsock.mode and idsock.events[event].is_set()))
    try:
      if r:
        return r
      if self.events[event].wait(timeout if timeout is None else max(timeout, 0.000001)) and not self.closed:
        return tuple(idsock for idsock in idsocks if idsock.mode and idsock.events[event].is_set())
    finally:
      for idsock in idsocks:
        idsock._wevent.dec()
      self.events[event] = None
    return ()


class IDAltSocketGenerator(IDSocketGenerator):

  CLASS = IDAltSocket

  def waitany(self, timeout, event):
    if event not in ('r', 'a', 'w', 'c') or self.closed:
      return ()
    return IDSocket.waitmult(timeout, *(idsock for idsock, activ in self.idsockets.items() if activ), event=event, reset_event=False)


class RSASelfSigned:

  def __init__(self, name, years):
    self.name = name
    self.years = years
    self.ready = threading.Event()

  def generate(self):
    pcbEncoded = DWORD(0)
    wcrypt.CertStrToNameW(DWORD(1), LPCWSTR('CN=' + self.name), DWORD(2), None, None, byref(pcbEncoded), None)
    pSubjectIssuerBlob = CRYPT_INTEGER_BLOB()
    pSubjectIssuerBlob.cbData = DWORD(pcbEncoded.value)
    pSubjectIssuerBlob.pbData = ctypes.cast(ctypes.create_string_buffer(pcbEncoded.value), PVOID)
    wcrypt.CertStrToNameW(DWORD(1), LPCWSTR('CN=' + self.name), DWORD(2), None, PVOID(pSubjectIssuerBlob.pbData), byref(pcbEncoded), None)
    phProvider = HANDLE(0)
    ncrypt.NCryptOpenStorageProvider(byref(phProvider), LPCWSTR('Microsoft Software Key Storage Provider'), DWORD(0))
    phKey = HANDLE(0)
    ncrypt.NCryptCreatePersistedKey(phProvider, byref(phKey), LPCWSTR('RSA'), None, DWORD(1), DWORD(0))
    ncrypt.NCryptSetProperty(phKey, LPCWSTR('Export Policy'), byref(ULONG(3)), 4, ULONG(0x80000000))
    ncrypt.NCryptSetProperty(phKey, LPCWSTR('Length'), byref(DWORD(2048)), 4, ULONG(0x80000000))
    ncrypt.NCryptFinalizeKey(phKey, DWORD(0x40))
    pKeyProvInfo = CRYPT_KEY_PROV_INFO()
    pKeyProvInfo.pwszContainerName = LPWSTR('CN=' + self.name)
    pKeyProvInfo.pwszProvName = LPWSTR('Microsoft Software Key Storage Provider')
    pKeyProvInfo.dwProvType = DWORD(0x01)
    pKeyProvInfo.dwFlags = DWORD(0x40)
    pKeyProvInfo.cProvParam = DWORD(0)
    pKeyProvInfo.rgProvParam = PVOID(0)
    pKeyProvInfo.dwKeySpec = DWORD(1)
    pSignatureAlgorithm = None
    pStartTime = P_SYSTEMTIME(SYSTEMTIME())
    kernel32.GetSystemTime(pStartTime)
    pEndTime = P_SYSTEMTIME(SYSTEMTIME())
    ctypes.memmove(pEndTime, pStartTime, ctypes.sizeof(SYSTEMTIME))
    pEndTime.contents.wYear += self.years
    if pEndTime.contents.wMonth == 2 and pEndTime.contents.wDay == 29:
      pEndTime.contents.wDay = 28
    pExtensions = CERT_EXTENSIONS()
    pExtensions.cExtension = 0
    pExtensions.rgExtension = PVOID(0)
    pCertContext = wcrypt.CertCreateSelfSignCertificate(phKey, pSubjectIssuerBlob, DWORD(0), pKeyProvInfo, pSignatureAlgorithm, pStartTime, pEndTime, pExtensions)
    self.cert = ctypes.string_at(pCertContext.contents.pbCertEncoded, pCertContext.contents.cbCertEncoded)
    pcbResult = DWORD(0)
    ncrypt.NCryptExportKey(phKey, None, LPCWSTR('PKCS8_PRIVATEKEY'), None, None, 0, byref(pcbResult), DWORD(0x40))
    pbOutput = ctypes.create_string_buffer(pcbResult.value)
    ncrypt.NCryptExportKey(phKey, None, LPCWSTR('PKCS8_PRIVATEKEY'), None, pbOutput, pcbResult, byref(pcbResult), DWORD(0x40))
    self.key = bytes(pbOutput)
    ncrypt.NCryptFreeObject(phProvider)
    ncrypt.NCryptDeleteKey(phKey, DWORD(0x40))
    wcrypt.CertFreeCertificateContext(pCertContext)

  def get_PEM(self):
    return ('-----BEGIN CERTIFICATE-----\r\n' + '\r\n'.join(textwrap.wrap(base64.b64encode(self.cert).decode('utf-8'), 64)) + '\r\n-----END CERTIFICATE-----\r\n', '-----BEGIN PRIVATE KEY-----\r\n' + '\r\n'.join(textwrap.wrap(base64.b64encode(self.key).decode('utf-8'), 64)) + '\r\n-----END PRIVATE KEY-----\r\n')

  def _pipe_PEM(self, certname, keyname, number=1):
    pipe_c = HANDLE(kernel32.CreateNamedPipeW(LPCWSTR('\\\\.\\pipe\\' + certname + ('.pem' if certname[:4].lower() != '.pem' else '')), DWORD(0x00000002), DWORD(0), DWORD(1), DWORD(0x100000), DWORD(0x100000), DWORD(0), HANDLE(0)))
    pipe_k = HANDLE(kernel32.CreateNamedPipeW(LPCWSTR('\\\\.\\pipe\\' + keyname + ('.pem' if keyname[:4].lower() != '.pem' else '')), DWORD(0x00000002), DWORD(0), DWORD(1), DWORD(0x100000), DWORD(0x100000), DWORD(0), HANDLE(0)))
    self.ready.set()
    pem = tuple(t.encode('utf-8') for t in self.get_PEM())
    n = DWORD(0)
    for i in range(number):
      for (p, v) in zip((pipe_c, pipe_k), pem):
        kernel32.ConnectNamedPipe(p, LPVOID(0))
        kernel32.WriteFile(p, ctypes.cast(v, LPCVOID), DWORD(len(v)), byref(n), LPVOID(0))
        kernel32.FlushFileBuffers(p)
        kernel32.DisconnectNamedPipe(p)
    kernel32.CloseHandle(pipe_c)
    kernel32.CloseHandle(pipe_k)

  def pipe_PEM(self, certname, keyname, number=1):
    pipe_thread = threading.Thread(target=self._pipe_PEM, args=(certname, keyname), kwargs={'number': number}, daemon=True)
    pipe_thread.start()
    self.ready.wait()

  def __enter__(self):
    self.generate()
    return self

  def __exit__(self, type, value, traceback):
    pass


class NestedSSLContext(ssl.SSLContext):

  class SSLSocket(ssl.SSLSocket):

    _esocket = socket.socket()
    _esocket.detach()
    HAS_TIMEOUT = True

    def __new__(cls, *args, **kwargs):
      if not hasattr(cls, 'sock'):
        raise TypeError('%s does not have a public constructor. Instances are returned by NestedSSLContext.wrap_socket().' % cls.__name__)
      cls_ = cls.__bases__[0]
      self = super(cls_, cls_).__new__(cls_, *args, **kwargs)
      self.socket = cls.sock
      cls.sock = None
      self.sock_hto = getattr(self.socket.__class__, 'HAS_TIMEOUT', False)
      return self

    class _PSocket:

      def __init__(self, s):
        self.s = s

      def detach(self):
        pass

      def __getattr__(self, name):
        return getattr(self.s, name)

    @classmethod
    def _create(cls, sock, *args, **kwargs):
      self = ssl.SSLSocket._create.__func__(type('BoundSSLSocket', (cls,), {'sock': sock}), cls._PSocket(sock), *args, **kwargs)
      return self

    def detach(self):
      try:
        self.socket.detach()
      except:
        pass
      self._sslobj = None
      self.socket = self._esocket
      return super().detach()

    def unwrap(self, *, timeout=''):
      try:
        if self._sslobj:
          sock = self._sslobj.shutdown(timeout=timeout)
          self._sslobj = None
          return sock
        else:
          raise ValueError('No SSL wrapper around ' + str(self))
      finally:
        self.detach()

    def close(self):
      try:
        self.socket.close()
      except:
        pass
      self.detach()

    def shutdown(self, how):
      super().shutdown(how)
      try:
        self.socket.shutdown(how)
      except:
        pass

    def shutclose(self):
      try:
        if self._sslobj:
          self._sslobj._close()
      except:
        pass
      try:
        if hasattr(self.socket, 'shutclose'):
          self.socket.shutclose()
        else:
          self.shutdown(socket.SHUT_RDWR)
          self.socket.close()
      except:
        pass
      self.detach()

    def settimeout(self, value):
      try:
        super().settimeout(value)
      except:
        pass
      try:
        self.socket.settimeout(value)
      except:
        pass

    def setblocking(self, flag):
      try:
        super().setblocking(flag)
      except:
        pass
      try:
        self.socket.setblocking(flag)
      except:
        pass

    def do_handshake(self, block=False, *, timeout=''):
      if timeout == '':
        timeout = self.gettimeout()
      to = None if (timeout == 0.0 and block) else timeout
      self._sslobj.do_handshake(timeout=to)

    def verify_client_post_handshake(self, *, timeout=''):
      if self._sslobj:
        return self._sslobj.verify_client_post_handshake(timeout=timeout)
      else:
        raise ValueError('No SSL wrapper around ' + str(self))

    def _wrap_no_sslobj(self, func, *args, timeout='', **kwargs):
      if self.sock_hto:
        return func(*args, **kwargs, timeout=timeout)
      else:
        try:
          if timeout != '':
            to = self.socket.gettimeout()
            self.socket.settimeout(timeout)
          return func(*args, **kwargs)
        finally:
          if timeout != '':
            self.socket.settimeout(to)

    def recv(self, buflen=16384, flags=0, *, timeout=''):
      if self._sslobj is not None:
        if flags != 0:
          raise ValueError('non-zero flags not allowed in calls to recv() on %s' % self.__class__)
        try:
          return self._sslobj.read(buflen, timeout=timeout)
        except ssl.SSLEOFError:
          if self.suppress_ragged_eofs:
            return b''
          else:
            raise
      else:
        return self._wrap_no_sslobj(self.socket.recv, buflen, flags, timeout=timeout)

    def recv_into(self, buffer, nbytes=None, flags=0, *, timeout=''):
      if nbytes is None:
        nbytes = len(buffer) if buffer else 16384
      if self._sslobj is not None:
        if flags != 0:
          raise ValueError('non-zero flags not allowed in calls to recv_into() on %s' % self.__class__)
        try:
          return self._sslobj.read(nbytes, buffer, timeout=timeout)
        except ssl.SSLEOFError:
          if self.suppress_ragged_eofs:
            return 0
          else:
            raise
      else:
        return self._wrap_no_sslobj(self.socket.recv_into, buffer, nbytes, flags, timeout=timeout)

    def recvfrom(self, buflen=1024, flags=0, *, timeout=''):
      if self._sslobj is not None:
        raise ValueError('recvfrom not allowed on instances of %s' % self.__class__)
      else:
        return self._wrap_no_sslobj(self.socket.recvfrom, buflen, flags, timeout=timeout)

    def recvfrom_into(self, buffer, nbytes=None, flags=0, *, timeout=''):
      if self._sslobj is not None:
        raise ValueError('recvfrom_into not allowed on instances of %s' % self.__class__)
      else:
        return self._wrap_no_sslobj(self.socket.recvfrom_into, buffer, nbytes, flags, timeout=timeout)

    def send(self, data, flags=0, *, timeout=''):
      if self._sslobj is not None:
        if flags != 0:
          raise ValueError('non-zero flags not allowed in calls to send() on %s' % self.__class__)
        return self._sslobj.write(data, timeout=timeout)
      else:
        return self._wrap_no_sslobj(self.socket.send, data, flags, timeout=timeout)

    def sendto(self, data, flags_or_addr, addr=None, *, timeout=''):
      if self._sslobj is not None:
        raise ValueError('sendto not allowed on instances of %s' % self.__class__)
      else:
        return self._wrap_no_sslobj(self.socket.sendto, data, flags_or_addr, timeout=timeout) if addr is None else self._wrap_no_sslobj(self.socket.sendto, data, flags_or_addr, addr, timeout=timeout)

    def sendall(self, data, flags=0, *, timeout=''):
      if self._sslobj is not None:
        if flags != 0:
          raise ValueError('non-zero flags not allowed in calls to sendall() on %s' % self.__class__)
        if timeout == '':
          timeout = self.gettimeout()
        with memoryview(data).cast('B') as m:
          l = len(m)
          s = 0
          if timeout is None:
            while s < l:
              s += self.send(m[s:], timeout=None)
          else:
            t = time.monotonic()
            rt = timeout
            while s < l:
              if rt < 0:
                raise TimeoutError()
              s += self.send(m[s:], timeout=rt)
              rt = timeout + t - time.monotonic()
      else:
        return self._wrap_no_sslobj(self.socket.sendall, data, flags, timeout=timeout)

    def accept(self, *, timeout=''):
      t = time.monotonic()
      rt = self.gettimeout() if timeout == '' else timeout
      if self.sock_hto:
        sock, addr = self.socket.accept(timeout=rt)
      else:
        try:
          if timeout != '':
            to = self.socket.gettimeout()
            self.socket.settimeout(rt)
          sock, addr = self.socket.accept()
        finally:
          if timeout != '':
            self.socket.settimeout(to)
      timeout = rt
      if rt is not None:
        rt += t - time.monotonic()
        if rt < 0:
          raise TimeoutError()
      sock.settimeout(rt)
      sock = self.context.wrap_socket(sock, do_handshake_on_connect=self.do_handshake_on_connect, suppress_ragged_eofs=self.suppress_ragged_eofs, server_side=True)
      sock.settimeout(timeout)
      return sock, addr

    def _connect(self, addr, *, timeout='', ex=False):
      if self.server_side:
        raise ValueError('can\'t connect in server-side mode')
      if self._connected or self._sslobj is not None:
        raise ValueError('attempt to connect already-connected SSLSocket!')
      self._sslobj = self.context._wrap_socket(self, False, self.server_hostname, owner=self, session=self._session)
      t = time.monotonic()
      rt = self.gettimeout() if timeout == '' else timeout
      try:
        r = 0
        if self.sock_hto:
          if ex:
            r = self.socket.connect_ex(addr, timeout=rt)
          else:
            self.socket.connect(addr, timeout=rt)
        else:
          try:
            if timeout != '':
              to = self.socket.gettimeout()
              self.socket.settimeout(rt)
            if ex:
              r = self.socket.connect_ex(addr)
            else:
              self.socket.connect(addr)
          finally:
            if timeout != '':
              self.socket.settimeout(to)
        if r:
          self._sslobj = None
        else:
          self._connected = True
          if self.do_handshake_on_connect:
            if rt is not None:
              rt += t - time.monotonic()
              if rt < 0:
                raise TimeoutError()
            self.do_handshake(timeout=rt)
        return r
      except:
        self._sslobj = None
        raise

    def connect(self, addr, *, timeout=''):
      self._connect(addr, timeout=timeout, ex=False)

    def connect_ex(self, addr, *, timeout=''):
      return self._connect(addr, timeout=timeout, ex=True)

    def __del__(self):
      self.shutclose()
      super().__del__()

  sslsocket_class = SSLSocket
  ssl_read_ahead = 16384 + 2048
  tls_1_3_tickets_workaround = True

  class _SSLSocket():

    def __init__(self, context, ssl_sock, server_side, server_hostname):
      self.read_ahead = context.ssl_read_ahead
      self.tickets_workaround = context.tls_1_3_tickets_workaround
      self.read_tickets = False
      self._sslsocket = weakref.ref(ssl_sock)
      self.hto = ssl_sock.sock_hto
      self.inc = ssl.MemoryBIO()
      self.out = ssl.MemoryBIO()
      self._sslobj = context.wrap_bio(self.inc, self.out, server_side, server_hostname)._sslobj

    @property
    def sslsocket(self):
      return self._sslsocket()

    def __getattr__(self, name):
      return self._sslobj.__getattribute__(name)

    def __setattr__(self, name, value):
      if name in {'_sslsocket', 'inc', 'out', '_sslobj', 'read_ahead', 'tickets_workaround', 'read_tickets', 'hto'}:
        object.__setattr__(self, name, value)
      else:
        self._sslobj.__setattr__(name, value)

    def _read_record(self, end_time, z, sto):
      sock = self._sslsocket().socket
      bl = b''
      rt = None
      while len(bl) < 5:
        if end_time is not None:
          rt = max(end_time - time.monotonic(), z)
          if rt < 0:
            raise TimeoutError(10060, 'timed out')
          z = -1
        if self.hto:
          b_ = sock.recv(5 - len(bl), timeout=rt)
        else:
          if rt is not None and sto - rt > 0.005:
            sto = rt
            sock.settimeout(rt)
          b_ = sock.recv(5 - len(bl))
        if not b_:
          raise ConResetError()
        bl += b_
      l = int.from_bytes(bl[3:5], 'big')
      self.inc.write(bl)
      z = 0
      while l > 0:
        if end_time is not None:
          rt = max(end_time - time.monotonic(), z)
          if rt < 0:
            raise TimeoutError(10060, 'timed out')
          z = -1
        if self.hto:
          b_ = sock.recv(l, timeout=rt)
        else:
          if rt is not None and sto - rt > 0.005:
            sto = rt
            sock.settimeout(rt)
          b_ = sock.recv(l)
        if not b_:
          raise ConResetError()
        l -= len(b_)
        self.inc.write(b_)
      return sto

    def interface(self, action, *args, timeout='', **kwargs):
      sock = self._sslsocket()
      if timeout == '':
        isto = timeout = sock.gettimeout()
      elif not self.hto:
        isto = sock.gettimeout()
        sock.settimeout(timeout)
      sock = sock.socket
      rt = sto = timeout
      end_time = None if timeout is None else timeout + time.monotonic()
      z = 0
      try:
        while True:
          try:
            res = action(*args, **kwargs)
          except (ssl.SSLWantReadError, ssl.SSLWantWriteError) as err:
            if self.out.pending:
              if end_time is not None:
                rt = max(end_time - time.monotonic(), z)
                if rt < 0:
                  raise TimeoutError(10060, 'timed out')
                z = 0
              if self.hto:
                sock.sendall(self.out.read(), timeout=rt)
              else:
                if rt is not None and sto - rt > 0.005:
                  sto = rt
                  sock.settimeout(rt)
                sock.sendall(self.out.read())
            if err.errno == ssl.SSL_ERROR_WANT_READ and not self.inc.pending:
              try:
                if self.read_ahead:
                  if end_time is not None:
                    rt = max(end_time - time.monotonic(), z)
                    if rt < 0:
                      raise TimeoutError(10060, 'timed out')
                  if self.hto:
                    if not self.inc.write(sock.recv(self.read_ahead, timeout=rt)):
                      raise ConResetError()
                  else:
                    if rt is not None and sto - rt > 0.005:
                      sto = rt
                      sock.settimeout(rt)
                    if not self.inc.write(sock.recv(self.read_ahead)):
                      raise ConResetError()
                else:
                  sto = self._read_record(end_time, z, sto)
              except ConnectionResetError:
                if action == self._sslobj.do_handshake:
                  raise ConResetError()
                else:
                  raise ssl.SSLEOFError(ssl.SSL_ERROR_EOF, 'EOF occurred in violation of protocol')
            z = -1
          else:
            if self.out.pending:
              if end_time is not None:
                rt = max(end_time - time.monotonic(), z)
                if rt < 0:
                  raise TimeoutError(10060, 'timed out')
              if self.hto:
                sock.sendall(self.out.read(), timeout=rt)
              else:
                if rt is not None and sto - rt > 0.005:
                  sto = rt
                  sock.settimeout(rt)
                sock.sendall(self.out.read())
            return res
      finally:
        if not self.hto:
          sock.settimeout(isto)

    def do_handshake(self, timeout=''):
      r = self.interface(self._sslobj.do_handshake, timeout=timeout)
      try:
        v = self.version()
        if self.tickets_workaround and not self.server_side and v.startswith('TLS') and float(v.rpartition('v')[2]) >= 1.3:
          self.read_tickets = True
          object.__setattr__(self, 'read', self._read_first)
      except:
        pass
      return r

    def _close(self):
      if self.read_tickets:
        self.read(1, timeout=0)

    def _read_first(self, length=16384, buffer=None, timeout=''):
      if length > 0:
        del self.read
        self.read_tickets = False
      return self.__class__.read(self, length, buffer, timeout)

    def read(self, length=16384, buffer=None, timeout=''):
      return self.interface(self._sslobj.read, length, timeout=timeout) if buffer is None else self.interface(self._sslobj.read, length, buffer, timeout=timeout)

    def write(self, bytes, timeout=''):
      return self.interface(self._sslobj.write, bytes, timeout=timeout)

    def shutdown(self, timeout=''):
      self.interface(self._sslobj.shutdown, timeout=timeout)
      return self.sslsocket.socket

    def verify_client_post_handshake(self, timeout=''):
      return self.interface(self._sslobj.verify_client_post_handshake, timeout=timeout)

  class _SSLDSocket(_SSLSocket):

    def __init__(self, context, ssl_sock, server_side, server_hostname):
      super().__init__(context, ssl_sock, server_side, server_hostname)
      self.rcondition = threading.Condition()
      self.rcounter = 0
      self.wlock = threading.Lock()

    def __setattr__(self, name, value):
      if name in {'_sslsocket', 'inc', 'out', '_sslobj', 'read_ahead', 'tickets_workaround', 'read_tickets', 'hto', 'wlock', 'rcondition', 'rcounter'}:
        object.__setattr__(self, name, value)
      else:
        self._sslobj.__setattr__(name, value)

    def interface(self, action, *args, timeout='', **kwargs):
      if timeout == '':
        sock = self._sslsocket()
        timeout = sock.gettimeout()
        sock = sock.socket
      else:
        sock = self._sslsocket().socket
      rt = sto = timeout
      end_time = None if timeout is None else timeout + time.monotonic()
      z = 0
      while True:
        rc = self.rcounter & -2
        try:
          res = action(*args, **kwargs)
        except (ssl.SSLWantReadError, ssl.SSLWantWriteError) as err:
          if self.out.pending:
            if end_time is not None:
              rt = max(end_time - time.monotonic(), z)
              if rt < 0 or not self.wlock.acquire(timeout=rt):
                raise TimeoutError(10060, 'timed out')
            else:
              self.wlock.acquire()
            try:
              if end_time is not None:
                rt = max(end_time - time.monotonic(), z)
                if rt < 0:
                  raise TimeoutError(10060, 'timed out')
                z = 0
              b = self.out.read()
              if b:
                sock.sendall(b, timeout=rt)
            finally:
              self.wlock.release()
          if err.errno == ssl.SSL_ERROR_WANT_READ and not self.inc.pending:
            with self.rcondition:
              if self.rcounter == rc:
                self.rcounter += 1
              elif self.rcounter > rc + 1:
                continue
              else:
                if end_time is not None:
                  rt = max(end_time - time.monotonic(), z)
                  if rt < 0:
                    raise TimeoutError(10060, 'timed out')
                self.rcondition.wait(rt)
                continue
            try:
              if self.read_ahead:
                if end_time is not None:
                  rt = max(end_time - time.monotonic(), z)
                  if rt < 0:
                    raise TimeoutError(10060, 'timed out')
                if not self.inc.write(sock.recv(self.read_ahead, timeout=rt)):
                  raise ConResetError()
              else:
                sto = self._read_record(end_time, z, sto)
            except ConnectionResetError:
              if action == self._sslobj.do_handshake:
                raise ConResetError()
              else:
                raise ssl.SSLEOFError(ssl.SSL_ERROR_EOF, 'EOF occurred in violation of protocol')
            finally:
              with self.rcondition:
                self.rcounter += 1
                self.rcondition.notify_all()
          z = -1
        else:
          if self.out.pending:
            if end_time is not None:
              rt = max(end_time - time.monotonic(), z)
              if rt < 0 or not self.wlock.acquire(timeout=rt):
                raise TimeoutError(10060, 'timed out')
            else:
              self.wlock.acquire()
            try:
              if end_time is not None:
                rt = end_time - time.monotonic()
                if rt < 0:
                  raise TimeoutError(10060, 'timed out')
              b = self.out.read()
              if b:
                sock.sendall(b, timeout=rt)
            finally:
              self.wlock.release()
          return res

  def __init__(self, *args, **kwargs):
    self.DefaultSSLContext = ssl.SSLContext(*args, **kwargs)
    ssl.SSLContext.__init__(*args, **kwargs)

  def wrap_callable(self, name):
    def new_callable(*args, **kwargs):
      object.__getattribute__(self.DefaultSSLContext, name)(*args, **kwargs)
      return object.__getattribute__(self, name)(*args, **kwargs)
    return new_callable

  def __getattribute__(self, name):
    if name not in object.__getattribute__(type(self), '_nestedSSLContext_set') and type(object.__getattribute__(self, name)) in (types.BuiltinMethodType, types.MethodType):
      return self.wrap_callable(name)
    else:
      return object.__getattribute__(self, name)

  def __setattr__(self, name, value):
    object.__setattr__(self, name, value)
    if name not in {'DefaultSSLContext', 'ssl_read_ahead'}:
      self.DefaultSSLContext.__setattr__(name, value)

  def wrap_socket(self, sock, *args, **kwargs):
    return ssl.SSLContext.wrap_socket(self.DefaultSSLContext if sock.__class__ == socket.socket else self, sock, *args, **kwargs)

  @classmethod
  def _is_duplex(cls, ssl_sock):
    return getattr(ssl_sock.socket.__class__, 'IS_DUPLEX', False) or (isinstance(ssl_sock.socket, cls.SSLSocket) and cls._is_duplex(ssl_sock.socket))

  def _wrap_socket(self, ssl_sock, server_side, server_hostname, *args, **kwargs):
    return (type(self)._SSLDSocket if self._is_duplex(ssl_sock) else type(self)._SSLSocket)(self, ssl_sock, server_side, server_hostname)

  def wrap_bio(self, *args, **kwargs):
    return self.DefaultSSLContext.wrap_bio(*args, **kwargs)

  def load_pem_cert_chain(self, certpem, keypem=None, password=None):
    cert = RSASelfSigned(None, None)
    if not isinstance(certpem, str):
      certpem = certpem.decode('utf-8')
    if keypem is None:
      keypem = certpem[:certpem.index('-----BEGIN CERTIFICATE-----')]
      certpem = certpem[len(keypem):]
    elif not isinstance(keypem, str):
      keypem = keypem.decode('utf-8')
    cert.get_PEM = lambda: (certpem, keypem)
    cid = base64.b32encode(os.urandom(10)).decode('utf-8')
    cert.pipe_PEM('cert' + cid, 'key' + cid, 2)
    self.load_cert_chain(r'\\.\pipe\cert%s.pem' % cid, r'\\.\pipe\key%s.pem' % cid, password)

  def load_autogenerated_cert_chain(self):
    cid = base64.b32encode(os.urandom(10)).decode('utf-8')
    with RSASelfSigned('TCPIServer' + cid, 1) as cert:
      cert.pipe_PEM('cert' + cid, 'key' + cid, 2)
      self.load_cert_chain(r'\\.\pipe\cert%s.pem' % cid, r'\\.\pipe\key%s.pem' % cid)

  PROTOCOL_TLS_CLIENT = ssl.PROTOCOL_TLS_CLIENT
  PROTOCOL_TLS_SERVER = ssl.PROTOCOL_TLS_SERVER

  _nestedSSLContext_set = {*locals(), '_encode_hostname', 'cert_store_stats', 'get_ca_certs', 'get_ciphers', 'session_stats'}


class HTTPExplodedMessage:

  __slots__ = ('method', 'path', 'version', 'code', 'message', 'headers', 'body', 'expect_close')

  def __init__(self):
    self.method = self.path = self.version = self.code = self.message = self.body = self.expect_close = None
    self.headers = {}

  def __bool__(self):
    return self.method is not None or self.code is not None

  def clear(self):
    self.__init__()
    return self

  def header(self, name, default=None):
    return self.headers.get(name.title(), default)

  def in_header(self, name, value):
    h = self.header(name)
    return False if h is None else (value.lower() in map(str.strip, h.lower().split(',')))

  def cookies(self, domain, path):
    hck = self.header('Set-Cookie')
    domain = domain.lower()
    dom_ip = all(c in '.:[]0123456789' for c in domain)
    ck = {}
    if hck is not None:
      for co in map(str.strip, hck.split('\n')):
        c = map(str.strip, co.split(';'))
        try:
          cn, cv = next(c).split('=', 1)
          if not cn:
            continue
          cd = cp = None
          for ca in c:
            try:
              can, cav = ca.split('=', 1)
            except:
              continue
            if can.lower() == 'domain' and cav:
              cd = (cav.lstrip('.').lower(), True)
            if can.lower() == 'path' and cav[:1] == '/':
              cp = cav
          if cd is None:
            cd = (domain, False)
          else:
            cav = cd[0]
            if (domain != cav) if dom_ip else (domain[-len(cav) - 1 :] not in (cav, '.' + cav)):
              raise
          if cp is None:
            cp = path.rstrip('/') if (path != '/' and path[:1] == '/') else '/'
          ck[(cd, cp, cn)] = cv
        except:
          pass
    return ck

  def __repr__(self):
    if self:
      try:
        return '\r\n'.join(('<HTTPExplodedMessage at %#x>\r\n----------' % id(self), (' '.join(filter(None, (self.method, self.path, self.version, self.code, self.message)))), *('%s: %s' % (k, l) for k, v in self.headers.items() for l in v.split('\n')), ('----------\r\nStreaming body: ' + ('open' if next(c for c in self.body.__closure__ if type(c.cell_contents).__name__ == 'generator').cell_contents.gi_frame else 'closed')) if type(self.body).__name__ == 'function' else '----------\r\nLength of body: %s byte(s)' % len(self.body or ''), '----------\r\nClose expected: %s' % self.expect_close))
      except:
        return '<HTTPExplodedMessage at %#x>\r\n<corrupted object>' % id(self)
    else:
      return '<HTTPExplodedMessage at %#x>\r\n<no message>' % id(self)


class _brotli:

  class decompressobj:
    def __new__(cls):
      return object.__new__(cls) if brotli else None
    def __init__(self):
      self.decompressor = brotli.Decompressor()
    def decompress(self, data):
      return self.decompressor.process(data)
    @property
    def eof(self):
      return self.decompressor.is_finished()

  class compressobj:
    def __new__(cls):
      return object.__new__(cls) if brotli else None
    def __init__(self):
      self.compressor = brotli.Compressor(quality=8, lgwin=19)
    def compress(self, data):
      return self.compressor.process(data)
    def flush(self):
      return self.compressor.finish()


class HTTPMessage:

  @staticmethod
  def _read_headers(msg, http_message):
    if not msg:
      return False
    a = None
    for msg_line in msg.replace('\r\n', '\n').split('\n')[:-2]:
      if a is None:
        try:
          a, b, c = msg_line.strip().split(None, 2)
        except:
          try:
            a, b, c = *msg_line.strip().split(None, 2), ''
          except:
            return False
      else:
        try:
          header_name, header_value = msg_line.split(':', 1)
        except:
          return False
        header_name = header_name.strip().title()
        if header_name:
          header_value = header_value.strip()
          if header_name not in {'Content-Length', 'Location', 'Host'} and http_message.headers.get(header_name):
            if header_value:
              http_message.headers[header_name] += ('\n' if header_name in {'Set-Cookie', 'Www-Authenticate', 'Proxy-Authenticate'} else ', ') + header_value
          else:
            http_message.headers[header_name] = header_value
        else:
          return False
    if a is None:
      return False
    if a[:4].upper() == 'HTTP':
      http_message.version = a.upper()
      http_message.code = b
      http_message.message = c
    else:
      http_message.method = a.upper()
      http_message.path = b
      http_message.version = c.upper()
    if 'Transfer-Encoding' in http_message.headers:
      http_message.headers.pop('Content-Length', None)
    http_message.expect_close = http_message.in_header('Connection', 'close') or (http_message.version.upper() != 'HTTP/1.1' and not http_message.in_header('Connection', 'keep-alive'))
    return True

  @staticmethod
  def _read_trailers(msg, http_message):
    if not msg:
      return False
    for msg_line in msg.replace('\r\n', '\n').split('\n')[:-2]:
      try:
        header_name, header_value = msg_line.split(':', 1)
      except:
        return False
      header_name = header_name.strip().title()
      if header_name:
        if header_name in {'Transfer-Encoding', 'Content-Length', 'Host', 'Content-Encoding', 'Location'}:
          continue
        header_value = header_value.strip()
        if http_message.headers.get(header_name):
          if header_value:
            http_message.headers[header_name] += ('\n' if header_name in {'Set-Cookie', 'Www-Authenticate', 'Proxy-Authenticate'} else ', ') + header_value
        else:
          http_message.headers[header_name] = header_value
      else:
        return False
    return True

  @staticmethod
  def _read(message, max_data, end_time):
    try:
      if end_time is not None:
        rem_time = end_time - time.monotonic()
        if rem_time <= 0:
          return None
        if abs(message.gettimeout() - rem_time) > 0.005:
          message.settimeout(rem_time)
      return message.recv(min(max_data, 1048576))
    except:
      return None

  @staticmethod
  def _read_hto(message, max_data, end_time):
    try:
      if end_time is None:
        return message.recv(min(max_data, 1048576), timeout=None)
      else:
        rem_time = end_time - time.monotonic()
        if rem_time <= 0:
          return None
        return message.recv(min(max_data, 1048576), timeout=rem_time)
    except:
      return None

  @staticmethod
  def _write(message, msg, end_time):
    try:
      if end_time is not None:
        rem_time = end_time - time.monotonic()
        if rem_time <= 0:
          return None
        message.settimeout(rem_time)
      message.sendall(msg)
      return len(msg)
    except:
      return None

  @staticmethod
  def _write_hto(message, msg, end_time):
    try:
      if end_time is None:
        message.sendall(msg, timeout=None)
      else:
        rem_time = end_time - time.monotonic()
        if rem_time <= 0:
          return None
        message.sendall(msg, timeout=rem_time)
      return len(msg)
    except:
      return None

  def __new__(cls, message=None, body=True, decompress=True, decode='utf-8', max_length=1048576, max_hlength=1048576, max_time=None, exceeded=None):
    http_message = HTTPExplodedMessage()
    if isinstance(exceeded, list):
      exceeded[:] = [False]
    else:
      exceeded = None
    if message is None:
      return http_message
    if max_time is False:
      max_time = None
    end_time = None if max_time is None else time.monotonic() + max_time
    max_hlength = min(max_length, max_hlength)
    rem_length = max_hlength
    try:
      if isinstance(message, (tuple, list)):
        iss = isinstance(message[0], socket.socket)
        msg = message[1 if iss else 0]
        message = message[0]
      else:
        iss = isinstance(message, socket.socket)
        msg = b'' if iss else message
    except:
      return http_message
    try:
      if iss:
        try:
          mto = message.gettimeout()
          message.settimeout(max_time)
        except:
          return http_message
        if getattr(message.__class__, 'HAS_TIMEOUT', False):
          read = cls._read_hto
          write = cls._write_hto
        else:
          read = cls._read
          write = cls._write
      while True:
        msg = msg.lstrip(b'\r\n')
        if msg and msg[0] < 0x20:
          return http_message
        body_pos = msg.find(b'\r\n\r\n')
        if body_pos >= 0:
          body_pos += 4
          break
        body_pos = msg.find(b'\n\n')
        if body_pos >= 0:
          body_pos += 2
          break
        if not iss or rem_length <= 0:
          return http_message
        try:
          bloc = read(message, rem_length, end_time)
          if not bloc:
            return http_message
        except:
          return http_message
        rem_length -= len(bloc)
        msg = msg + bloc
      if not cls._read_headers(msg[:body_pos].decode('ISO-8859-1'), http_message):
        return http_message.clear()
      if not iss:
        http_message.expect_close = True
      if http_message.code in ('101', '204', '304'):
        http_message.body = '' if decode else b''
        return http_message
      if not body or http_message.code == '100':
        http_message.body = msg[body_pos:]
        return http_message
      rem_length += max_length - max_hlength
      chunked = http_message.in_header('Transfer-Encoding', 'chunked')
      if chunked:
        body_len = -1
      else:
        body_len = http_message.header('Content-Length')
        if body_len is None:
          if not iss or (http_message.code in ('200', '206') and http_message.expect_close):
            body_len = -1
          else:
            body_len = 0
        else:
          try:
            body_len = max(0, int(body_len))
          except:
            return http_message.clear()
      if decompress and body_len != 0:
        hce = [e for h in (http_message.header('Content-Encoding', ''), http_message.header('Transfer-Encoding', '')) for e in map(str.strip, h.lower().split(',')) if e not in ('chunked', '', 'identity')]
        for ce in hce:
          if ce not in (({'deflate', 'gzip', 'zstd', 'br'} if zstd else {'deflate', 'gzip', 'br'}) if brotli else ({'deflate', 'gzip', 'zstd'} if zstd else {'deflate', 'gzip'})):
            if http_message.method is not None and iss:
              try:
                write(message, ('HTTP/1.1 415 Unsupported media type\r\nContent-Length: 0\r\nDate: %s\r\nCache-Control: no-cache, no-store, must-revalidate\r\n\r\n' % email.utils.formatdate(time.time(), usegmt=True)).encode('ISO-8859-1'), (time.monotonic() + 3) if end_time is None else min(time.monotonic() + 3, end_time))
              except:
                pass
            return http_message.clear()
      else:
        hce = []
      if http_message.in_header('Expect', '100-continue') and iss:
        if body_pos + body_len - len(msg) <= rem_length:
          try:
            if write(message, 'HTTP/1.1 100 Continue\r\n\r\n'.encode('ISO-8859-1'), end_time) is None:
              return http_message.clear()
          except:
            return http_message.clear()
        else:
          try:
            write(message, ('HTTP/1.1 413 Payload too large\r\nContent-Length: 0\r\nDate: %s\r\nCache-Control: no-cache, no-store, must-revalidate\r\n\r\n' % email.utils.formatdate(time.time(), usegmt=True)).encode('ISO-8859-1'), (time.monotonic() + 3) if end_time is None else min(time.monotonic() + 3, end_time))
          except:
            pass
          if exceeded is not None:
            exceeded[0] = True
          return http_message.clear()
      if not chunked:
        if body_len < 0:
          if not iss:
            http_message.body = msg[body_pos:]
          else:
            bbuf = BytesIO()
            rem_length -= bbuf.write(msg[body_pos:])
            while rem_length > 0:
              try:
                bw = bbuf.write(read(message, rem_length, end_time))
                if not bw:
                  break
                rem_length -= bw
              except:
                return http_message.clear()
            if rem_length <= 0:
              if exceeded is not None:
                exceeded[0] = True
              return http_message.clear()
            http_message.body = bbuf.getvalue()
        elif len(msg) < body_pos + body_len:
          if not iss:
            return http_message.clear()
          if body_pos + body_len - len(msg) > rem_length:
            if exceeded is not None:
              exceeded[0] = True
            return http_message.clear()
          bbuf = BytesIO()
          body_len -= bbuf.write(msg[body_pos:])
          while body_len:
            try:
              bw = bbuf.write(read(message, body_len, end_time))
              if not bw:
                return http_message.clear()
              body_len -= bw
            except:
              return http_message.clear()
          http_message.body = bbuf.getvalue()
        else:
          http_message.body = msg[body_pos:body_pos+body_len]
      else:
        bbuf = BytesIO()
        buff = msg[body_pos:]
        while True:
          chunk_pos = -1
          rem_slength = max_hlength - len(buff)
          while chunk_pos < 0:
            buff = buff.lstrip(b'\r\n')
            chunk_pos = buff.find(b'\r\n')
            if chunk_pos >= 0:
              chunk_pos += 2
              break
            chunk_pos = buff.find(b'\n')
            if chunk_pos >= 0:
              chunk_pos += 1
              break
            if not iss or rem_slength <= 0:
              return http_message.clear()
            if rem_length <= 0:
              if exceeded is not None:
                exceeded[0] = True
              return http_message.clear()
            try:
              bloc = read(message, min(rem_length, rem_slength), end_time)
              if not bloc:
                return http_message.clear()
            except:
              return http_message.clear()
            rem_length -= len(bloc)
            rem_slength -= len(bloc)
            buff = buff + bloc
          try:
            chunk_len = int(buff[:chunk_pos].split(b';', 1)[0].rstrip(b'\r\n'), 16)
            if not chunk_len:
              break
          except:
            return http_message.clear()
          if chunk_pos + chunk_len - len(buff) > rem_length:
            if exceeded is not None:
              exceeded[0] = True
            return http_message.clear()
          if len(buff) < chunk_pos + chunk_len:
            if not iss:
              return http_message.clear()
            chunk_len -= bbuf.write(buff[chunk_pos:])
            while chunk_len:
              try:
                bw = bbuf.write(read(message, chunk_len, end_time))
                if not bw:
                  return http_message.clear()
                chunk_len -= bw
              except:
                return http_message.clear()
              rem_length -= bw
            buff = b''
          else:
            bbuf.write(buff[chunk_pos:chunk_pos+chunk_len])
            buff = buff[chunk_pos+chunk_len:]
        http_message.body = bbuf.getvalue()
        rem_length = min(rem_length, max_hlength - body_pos - len(buff) + chunk_pos)
        while not (b'\r\n\r\n' in buff or b'\n\n' in buff):
          if not iss:
            return http_message.clear()
          if rem_length <= 0:
            if exceeded is not None:
              exceeded[0] = True
            return http_message.clear()
          try:
            bloc = read(message, rem_length, end_time)
            if not bloc:
              return http_message.clear()
          except:
            return http_message.clear()
          rem_length -= len(bloc)
          buff = buff + bloc
        if len(buff) - chunk_pos > 2:
          cls._read_trailers(buff[chunk_pos:].decode('ISO-8859-1'), http_message)
      try:
        if http_message.body and hce:
          for ce in hce[::-1]:
            if ce == 'deflate':
              try:
                http_message.body = zlib.decompress(http_message.body)
              except:
                http_message.body = zlib.decompress(http_message.body, wbits=-15)
            elif ce == 'gzip':
              http_message.body = gzip.decompress(http_message.body)
            elif ce == 'zstd':
              http_message.body = zstd.decompress(http_message.body)
            elif ce == 'br':
              http_message.body = brotli.decompress(http_message.body)
            else:
              raise
        if decode:
          http_message.body = http_message.body.decode(decode)
      except:
        if http_message.method is not None and iss:
          try:
            write(message, ('HTTP/1.1 415 Unsupported media type\r\nContent-Length: 0\r\nDate: %s\r\nCache-Control: no-cache, no-store, must-revalidate\r\n\r\n' % email.utils.formatdate(time.time(), usegmt=True)).encode('ISO-8859-1'), (time.monotonic() + 3) if end_time is None else min(time.monotonic() + 3, end_time))
          except:
            pass
        return http_message.clear()
      return http_message
    finally:
      if iss:
        try:
          message.settimeout(mto)
        except:
          pass


class HTTPStreamMessage(HTTPMessage):

  def __new__(cls, message=None, decompress=True, max_hlength=1048576, max_time=None, expect100_handler=None, error415_handler=None):
    http_message = HTTPExplodedMessage()
    if message is None:
      return http_message
    if max_time is False:
      max_time = None
    end_time = None if max_time is None else time.monotonic() + max_time
    rem_length = max_hlength
    try:
      if isinstance(message, (tuple, list)):
        iss = isinstance(message[0], socket.socket)
        msg = message[1 if iss else 0]
        message = message[0]
      else:
        iss = isinstance(message, socket.socket)
        msg = b'' if iss else message
    except:
      return http_message
    bbuf = None
    try:
      if iss:
        try:
          mto = message.gettimeout()
          message.settimeout(max_time)
        except:
          return http_message
        if getattr(message.__class__, 'HAS_TIMEOUT', False):
          read = cls._read_hto
          write = cls._write_hto
        else:
          read = cls._read
          write = cls._write
      while True:
        msg = msg.lstrip(b'\r\n')
        body_pos = msg.find(b'\r\n\r\n')
        if body_pos >= 0:
          body_pos += 4
          break
        body_pos = msg.find(b'\n\n')
        if body_pos >= 0:
          body_pos += 2
          break
        if not iss or rem_length <= 0:
          return http_message
        try:
          bloc = read(message, rem_length, end_time)
          if not bloc:
            return http_message
        except:
          return http_message
        rem_length -= len(bloc)
        msg = msg + bloc
      if not cls._read_headers(msg[:body_pos].decode('ISO-8859-1'), http_message):
        return http_message.clear()
      if not iss:
        http_message.expect_close = True
      if http_message.code in ('101', '204', '304'):
        chunked = False
        body_len = 0
      elif http_message.code == '100':
        chunked = False
        decompress = False
        body_len = len(msg) - body_pos
      else:
        chunked = http_message.in_header('Transfer-Encoding', 'chunked')
        if chunked:
          body_len = -1
        else:
          body_len = http_message.header('Content-Length')
          if body_len is None:
            if not iss or (http_message.code in ('200', '206') and http_message.expect_close):
              body_len = -1
            else:
              body_len = 0
          else:
            try:
              body_len = max(0, int(body_len))
            except:
              return http_message.clear()
      hce = []
      if decompress and body_len != 0:
        hce_ = [e for h in (http_message.header('Content-Encoding', ''), http_message.header('Transfer-Encoding', '')) for e in map(str.strip, h.lower().split(',')) if e not in ('chunked', '', 'identity')]
        hce_.reverse()
        for ce in hce_:
          if ce not in (({'deflate', 'gzip', 'zstd', 'br'} if zstd else {'deflate', 'gzip', 'br'}) if brotli else ({'deflate', 'gzip', 'zstd'} if zstd else {'deflate', 'gzip'})):
            if http_message.method is not None and iss:
              try:
                if error415_handler is None:
                  write(message, ('HTTP/1.1 415 Unsupported media type\r\nContent-Length: 0\r\nDate: %s\r\nCache-Control: no-cache, no-store, must-revalidate\r\n\r\n' % email.utils.formatdate(time.time(), usegmt=True)).encode('ISO-8859-1'), (time.monotonic() + 3) if end_time is None else min(time.monotonic() + 3, end_time))
                elif error415_handler(http_message, ce):
                  continue
              except:
                pass
            return http_message.clear()
          hce.append(ce)
      rce = range(len(hce))
      if http_message.in_header('Expect', '100-continue') and iss:
        try:
          if expect100_handler is None:
            if write(message, 'HTTP/1.1 100 Continue\r\n\r\n'.encode('ISO-8859-1'), end_time) is None:
              return http_message.clear()
          elif not expect100_handler(http_message, body_len):
            return http_message.clear()
        except:
          return http_message.clear()
      bbuf = ssl.MemoryBIO()
    finally:
      if iss and bbuf is None:
        try:
          message.settimeout(mto)
        except:
          pass
    def _body():
      def error(value=None):
        e = GeneratorExit()
        e.value = value or None
        raise e
      def decompress(data, i):
        if data:
          dec = hce[i]
          if isinstance(dec, str):
            if dec == 'deflate':
              if data[0] & 0x0e == 0x08:
                dec = hce[i] = zlib.decompressobj(wbits=15)
              else:
                dec = hce[i] = zlib.decompressobj(wbits=-15)
            elif dec == 'gzip':
              dec = hce[i] = zlib.decompressobj(wbits=31)
            elif dec == 'zstd':
              dec = hce[i] = zstd.ZstdDecompressor()
            elif dec == 'br':
              dec = hce[i] = _brotli.decompressobj()
            else:
              raise
          return dec.decompress(data)
        else:
          return b''
      def bbuf_write(data):
        bbuf.write(reduce(decompress, rce, data))
        return len(data)
      nonlocal body_len
      nonlocal end_time
      try:
        if body_len != 0:
          length, max_time = yield None
          end_time = None if max_time is None else time.monotonic() + max_time
        else:
          return b''
        if not chunked:
          if body_len < 0:
            try:
              bbuf_write(msg[body_pos:])
            except:
              error()
            if iss:
              while True:
                while bbuf.pending > length:
                  length, max_time = yield bbuf.read(length)
                  end_time = None if max_time is None else time.monotonic() + max_time
                try:
                  if max_time is not False:
                    message.settimeout(max_time)
                    max_time = False
                  bw = bbuf_write(read(message, 1048576, end_time))
                  if not bw:
                    break
                except:
                  if bbuf.pending == length:
                    length, max_time = yield bbuf.read(length)
                  error(bbuf.read())
          elif len(msg) < body_pos + body_len:
            try:
              body_len -= bbuf_write(msg[body_pos:])
            except:
              error()
            if not iss:
              while bbuf.pending >= length:
                length, max_time = yield bbuf.read(length)
              error(bbuf.read())
            while body_len:
              while bbuf.pending >= length:
                length, max_time = yield bbuf.read(length)
                end_time = None if max_time is None else time.monotonic() + max_time
              try:
                if max_time is not False:
                  message.settimeout(max_time)
                  max_time = False
                bw = bbuf_write(read(message, min(body_len, 1048576), end_time))
                if not bw:
                  raise
                body_len -= bw
              except:
                error(bbuf.read())
          else:
            try:
              bbuf_write(msg[body_pos:body_pos+body_len])
            except:
              error()
          while bbuf.pending > length:
            length, max_time = yield bbuf.read(length)
            end_time = None if max_time is None else time.monotonic() + max_time
        else:
          buff = msg[body_pos:]
          while True:
            chunk_pos = -1
            rem_slength = max_hlength - len(buff)
            while chunk_pos < 0:
              buff = buff.lstrip(b'\r\n')
              chunk_pos = buff.find(b'\r\n')
              if chunk_pos >= 0:
                chunk_pos += 2
                break
              chunk_pos = buff.find(b'\n')
              if chunk_pos >= 0:
                chunk_pos += 1
                break
              if not iss or rem_slength <= 0:
                if bbuf.pending == length:
                  length, max_time = yield bbuf.read(length)
                error(bbuf.read())
              try:
                if max_time is not False:
                  message.settimeout(max_time)
                  max_time = False
                bloc = read(message, min(rem_slength, 1048576), end_time)
                if not bloc:
                  raise
              except:
                if bbuf.pending == length:
                  length, max_time = yield bbuf.read(length)
                error(bbuf.read())
              rem_slength -= len(bloc)
              buff = buff + bloc
            try:
              chunk_len = int(buff[:chunk_pos].split(b';', 1)[0].rstrip(b'\r\n'), 16)
              if not chunk_len:
                break
            except:
              if bbuf.pending == length:
                length, max_time = yield bbuf.read(length)
              error(bbuf.read())
            if len(buff) < chunk_pos + chunk_len:
              try:
                chunk_len -= bbuf_write(buff[chunk_pos:])
              except:
                error(bbuf.read())
              if not iss:
                while bbuf.pending >= length:
                  length, max_time = yield bbuf.read(length)
                error(bbuf.read())
              while chunk_len:
                while bbuf.pending >= length:
                  length, max_time = yield bbuf.read(length)
                  end_time = None if max_time is None else time.monotonic() + max_time
                try:
                  if max_time is not False:
                    message.settimeout(max_time)
                    max_time = False
                  bw = bbuf_write(read(message, min(chunk_len, 1048576), end_time))
                  if not bw:
                    raise
                  chunk_len -= bw
                except:
                  error(bbuf.read())
              buff = b''
            else:
              try:
                bbuf_write(buff[chunk_pos:chunk_pos+chunk_len])
              except:
                error(bbuf.read())
              buff = buff[chunk_pos+chunk_len:]
            while bbuf.pending > length:
              length, max_time = yield bbuf.read(length)
              end_time = None if max_time is None else time.monotonic() + max_time
          while bbuf.pending > length:
            length, max_time = yield bbuf.read(length)
            end_time = None if max_time is None else time.monotonic() + max_time
          while not (b'\r\n\r\n' in buff or b'\n\n' in buff):
            if not iss:
              if bbuf.pending == length:
                length, max_time = yield bbuf.read(length)
              error(bbuf.read())
            try:
              if max_time is not False:
                message.settimeout(max_time)
                max_time = False
              bloc = read(message, 1048576, end_time)
              if not bloc:
                raise
            except:
              if bbuf.pending == length:
                length, max_time = yield bbuf.read(length)
              error(bbuf.read())
            buff = buff + bloc
          if len(buff) - chunk_pos > 2:
            cls._read_trailers(buff[chunk_pos:].decode('ISO-8859-1'), http_message)
        if bbuf.pending:
          for dec in hce:
            if isinstance(dec, str) or not dec.eof:
              error(bbuf.read())
        return bbuf.read()
      finally:
        if iss:
          try:
            message.settimeout(mto)
          except:
            pass
    bg = _body()
    def body(length=float('inf'), max_time=None, return_pending_on_error=False, *, callback=None):
      if math.isnan(body.__defaults__[0]):
        return None
      if max_time is False:
        max_time = None
      if not length:
        if body.__defaults__[0] == 0 and callback is not None:
          callback()
        return b''
      elif length > 0:
        try:
          return bg.send((length, max_time))
        except StopIteration as e:
          if callback is not None:
            callback()
          return e.value or b''
        except GeneratorExit as e:
          body.__defaults__ = (float('nan'), None, False)
          if callback is not None:
            callback()
          return e.value if return_pending_on_error else None
      elif length == float('-inf'):
        bg.close()
        if callback is not None:
          callback()
        return b''
      else:
        bg.close()
        body.__defaults__ = (float('nan'), None, False)
        if callback is not None:
          callback()
        return None
    http_message.body = body
    try:
      bg.send(None)
    except StopIteration:
      body.__defaults__ = (0, None, False)
    return http_message


class _HTTPBaseRequest:

  RequestPattern = \
    '%s %s HTTP/1.1\r\n' \
    'Host: %s\r\n%s' \
    '\r\n'

  def __init_subclass__(cls, context_class=ssl.SSLContext, socket_source=socket):
    cls.SSLContext = context_class(ssl.PROTOCOL_TLS_CLIENT)
    cls.SSLContext.check_hostname = False
    cls.SSLContext.verify_mode = ssl.CERT_NONE
    cls.ConnectionGenerator = socket_source.create_connection

  @classmethod
  def connect(cls, url, url_p, headers, timeout, max_hlength, end_time, pconnection, ip):
    raise TypeError('the class _HTTPBaseRequest is not intended to be instantiated directly')

  @staticmethod
  def _netloc_split(loc, def_port=''):
    n, s, p = loc.rpartition(':')
    return (n, p or def_port) if (s == ':' and ']' not in p) else (loc, def_port)

  @staticmethod
  def _rem_time(timeout, end_time):
    if end_time is not None:
      rem_time = end_time - time.monotonic()
      if timeout is not None:
        rem_time = min(timeout, rem_time)
    elif timeout is not None:
      rem_time = timeout
    else:
      rem_time = None
    if rem_time is not None and rem_time <= 0:
      raise TimeoutError()
    return rem_time

  def __new__(cls, url, method=None, headers=None, data=None, timeout=30, max_length=16777216, max_hlength=1048576, max_time=None, decompress=True, pconnection=None, retry=None, max_redir=5, unsecuring_redir=False, ip='', basic_auth=None, process_cookies=None):
    if url is None:
      return HTTPMessage()
    if method is None:
      method = 'GET' if data is None else 'POST'
    redir = 0
    exceeded = [False]
    try:
      url_p = urllib.parse.urlsplit(url, allow_fragments=False)
      if headers is None:
        headers = {}
      hitems = tuple((k.strip(), v) for k, v in headers.items())
      if pconnection is None:
        pconnection = [None, {}, []]
        hccl = True
      else:
        l = len(pconnection)
        pconnection[0:3] = (pconnection[0] if l >= 1 else None), (pconnection[1] if l >= 2 else {}), []
        hccl = 'close' in (e.strip() for k, v in hitems if k.lower() == 'connection' for e in v.lower().split(','))
      if data:
        hexp = '100-continue' in (e.strip() for k, v in hitems if k.lower() == 'expect' for e in v.lower().split(','))
      else:
        hexp = False
      headers = {k: v for k, v in hitems if not k.lower() in {'host', 'content-length', 'connection', 'expect'}}
      if hexp:
        headers['Expect'] = '100-continue'
      if 'accept-encoding' not in (k.lower() for k, v in hitems):
        headers['Accept-Encoding'] = (('identity, deflate, gzip, zstd, br' if zstd else 'identity, deflate, gzip, br') if brotli else ('identity, deflate, gzip, zstd' if zstd else 'identity, deflate, gzip')) if decompress else 'identity'
      data_str = None
      if data is not None:
        if hasattr(data, 'read'):
          for k, v in hitems:
            if k.lower() == 'transfer-encoding':
              data_str = k
              if 'chunked' in map(str.strip, v.lower().split(',')):
                data_str = -1
                break
          else:
            for k, v in hitems:
              if k.lower() == 'content-length':
                data_str = int(v)
            if isinstance(data_str, int):
              headers['Content-Length'] = str(data_str)
            else:
              if data_str is None:
                headers['transfer-encoding'] = 'chunked'
              else:
                headers[data_str] += ', chunked'
              data_str = -2
        else:
          data_str = False
          if 'chunked' not in (e.strip() for k, v in hitems if k.lower() == 'transfer-encoding' for e in v.lower().split(',')):
            headers['Content-Length'] = str(len(data))
      headers['Connection'] = 'close' if hccl else 'keep-alive'
      hauth = headers.get('Authorization')
    except:
      return HTTPMessage()
    if retry is None:
      retry = pconnection[0] is not None
    retried = not retry
    end_time = time.monotonic() + max_time if max_time is not None else None
    if process_cookies is None:
      process_cookies = basic_auth is not None
    cook = pconnection[1]
    auth = False
    mess = (lambda c, mt: HTTPStreamMessage(c, decompress=decompress, max_hlength=max_hlength, max_time=mt)) if max_length < 0 else (lambda c, mt: HTTPMessage(c, body=(method.upper() != 'HEAD'), decompress=decompress, decode=None, max_length=max_length, max_hlength=max_hlength, max_time=mt, exceeded=exceeded))
    while True:
      try:
        pconnection[2].append(url)
        ck = {}
        if process_cookies:
          domain = cls._netloc_split(url_p.netloc)[0].lower()
          dom_ip = all(c in '.:[]0123456789' for c in domain)
          path = url_p.path.split('#', 1)[0]
          path = path.rstrip('/') if (path != '/' and path[:1] == '/') else '/'
          for k, v in cook.items():
            if ((domain[-len(k[0][0]) - 1 :] in (k[0][0], '.' + k[0][0])) if (k[0][1] and not dom_ip) else (domain == k[0][0])) and path[: len(k[1]) + (1 if k[1][-1:] != '/' else 0)] in (k[1], k[1] + '/'):
              if (k[2] not in ck) or (len(k[0][0]) > len(ck[k[2]][1]) or (len(k[0][0]) == len(ck[k[2]][1]) and len(k[1]) >= len(ck[k[2]][2]))):
                ck[k[2]] = (v, k[0][0], k[1])
        try:
          path = cls.connect(url, url_p, headers, timeout, max_hlength if max_length < 0 else min(max_length, max_hlength), end_time, pconnection, ip)
          code = '100'
          rem = None
          pconnection[0].settimeout(cls._rem_time(None, end_time))
          msg = cls.RequestPattern % (method, path, url_p.netloc, ''.join('%s: %s\r\n' % kv for kv in (headers if not ck else {**headers, 'Cookie': '; '.join(k + '=' + v[0] for k, v in ck.items())}).items()))
          if not data:
            pconnection[0].sendall(msg.encode('iso-8859-1'))
          elif not hexp and data_str is False:
            pconnection[0].sendall(msg.encode('iso-8859-1') + data)
          else:
            conn = pconnection[0]
            conn.sendall(msg.encode('iso-8859-1'))
            if hexp:
              resp = mess(conn, cls._rem_time(3 if timeout is None else min(3, timeout), end_time))
              conn.settimeout(cls._rem_time(None, end_time))
              code = resp.code
              if code == '100':
                rem = resp.body() if max_length < 0 else resp.body
              if code is None and exceeded != [True]:
                code = '100'
              if data_str is False and code == '100':
                conn.sendall(data)
            if data_str is not False and code == '100':
              hto = getattr(conn.__class__, 'HAS_TIMEOUT', False)
              r = data_str if data_str >= 0 else 1048576
              while r > 0:
                try:
                  b = data.read(min(r, 1048576))
                except:
                  b = b''
                if data_str >= 0:
                  if not b:
                    b = b'\x00' * min(r, 1048576)
                  r -= len(b)
                elif data_str == -1:
                  if not b:
                    break
                elif data_str == -2:
                  if not b:
                    b = b''
                    r = -1
                  b = b'%x\r\n%b\r\n' % (len(b), b)
                while True:
                  try:
                    if not rem:
                      if hto:
                        rem = conn.recv(1, timeout=0)
                      else:
                        conn.settimeout(0)
                        rem = conn.recv(1)
                      if not rem:
                        raise
                  except (BlockingIOError, TimeoutError):
                    break
                  resp = mess((conn, rem), cls._rem_time(None, end_time))
                  code = resp.code
                  if code == '100':
                    rem = resp.body() if max_length < 0 else resp.body
                  else:
                    rem = None
                    break
                if code != '100':
                  break
                if hto:
                  conn.sendall(b, timeout=cls._rem_time(None, end_time))
                else:
                  conn.settimeout(cls._rem_time(None, end_time))
                  conn.sendall(b)
        except TimeoutError:
          raise
        except:
          code = None
        while code == '100':
          resp = mess((pconnection[0] if rem is None else (pconnection[0], rem)), cls._rem_time(None, end_time))
          code = resp.code
          if code == '100':
            rem = resp.body() if max_length < 0 else resp.body
            redir += 1
            if redir > max_redir:
              raise
        if code is None:
          cls._rem_time(None, end_time)
          if retried or exceeded == [True]:
            raise
          retried = True
          try:
            pconnection[0].close()
          except:
            pass
          pconnection[0] = None
          pconnection[2].pop()
          continue
        retried = not retry
        if process_cookies and resp.header('Set-Cookie') is not None:
          cook.update(resp.cookies(cls._netloc_split(url_p.netloc)[0], url_p.path.split('#', 1)[0]))
        if code == '401':
          if not auth and basic_auth is not None and any((l or 'basic')[:5].lower() == 'basic' for l in resp.header('WWW-Authenticate').split('\n')):
            auth = True
            headers['Authorization'] = 'Basic ' + base64.b64encode(basic_auth.encode('utf-8')).decode('utf-8')
            if headers['Connection'] == 'close' or resp.expect_close:
              pconnection[0] = None
          else:
            auth = False
            break
        elif code[:2] == '30' and code != '304':
          auth = False
          if resp.header('location'):
            url = urllib.parse.urljoin(url, resp.header('location'))
            urlo_p = url_p
            url_p = urllib.parse.urlsplit(url, allow_fragments=False)
            if headers['Connection'] == 'close' or resp.expect_close or (urlo_p.scheme.lower() != url_p.scheme.lower() or urlo_p.netloc != url_p.netloc):
              if not unsecuring_redir and urlo_p.scheme.lower() == 'https' and url_p.scheme.lower() != 'https':
                raise
              try:
                pconnection[0].close()
              except:
                pass
              pconnection[0] = None
              headers['Connection'] = 'close'
            redir += 1
            if redir > max_redir:
              break
            if code == '303':
              if method.upper() != 'HEAD':
                method = 'GET'
              data = data_str = None
              for k in list(headers.keys()):
                if k.lower() in {'transfer-encoding', 'content-length', 'content-type', 'expect'}:
                  del headers[k]
          else:
            raise
        else:
          auth = False
          break
      except:
        auth = False
        try:
          pconnection[0].close()
        except:
          pass
        pconnection[0] = None
        return HTTPMessage()
      finally:
        if not auth and 'Authorization' in headers:
          if hauth is not None:
            headers['Authorization'] = hauth
          else:
            del headers['Authorization']
    if max_length < 0:
      def callback():
        resp.body.__kwdefaults__['callback'] = None
        if headers['Connection'] == 'close' or resp.expect_close or math.isnan(resp.body.__defaults__[0]):
          try:
            pconnection[0].close()
          except:
            pass
          pconnection[0] = None
      resp.body.__kwdefaults__['callback'] = callback
      if method.upper() == 'HEAD':
        resp.body(float('-inf'))
      else:
        resp.body(0)
    else:
      if headers['Connection'] == 'close' or resp.expect_close:
        try:
          pconnection[0].close()
        except:
          pass
        pconnection[0] = None
    return resp


def HTTPRequestConstructor(socket_source=socket, proxy=None):
  if not proxy or not proxy.get('ip', None):
    class HTTPRequest(_HTTPBaseRequest, context_class=NestedSSLContext if socket_source != socket else ssl.SSLContext, socket_source=socket_source):
      @classmethod
      def connect(cls, url, url_p, headers, timeout, max_hlength, end_time, pconnection, ip):
        if pconnection[0] is None:
          rem_time = cls._rem_time(timeout, end_time)
          if url_p.scheme.lower() == 'http':
            pconnection[0] = cls.ConnectionGenerator((url_p.hostname, url_p.port if url_p.port is not None else 80), timeout=rem_time, source_address=(ip, 0))
          elif url_p.scheme.lower() == 'https':
            pconnection[0] = cls.ConnectionGenerator((url_p.hostname, url_p.port if url_p.port is not None else 443), timeout=rem_time, source_address=(ip, 0))
            rem_time = cls._rem_time(timeout, end_time)
            pconnection[0].settimeout(rem_time)
            pconnection[0] = cls.SSLContext.wrap_socket(pconnection[0], server_side=False, server_hostname=cls._netloc_split(url_p.netloc)[0])
          else:
            raise
        if pconnection[0] is None:
          raise
        return (url_p.path + ('?' + url_p.query if url_p.query else '')).replace(' ', '%20') or '/'
  else:
    class HTTPRequest(_HTTPBaseRequest, context_class=NestedSSLContext if socket_source != socket or proxy.get('secure', None) else ssl.SSLContext, socket_source=socket_source):
      PROXY = (proxy['ip'], proxy['port'])
      PROXY_AUTH = ('Basic ' + base64.b64encode(proxy['auth'].encode('utf-8')).decode('utf-8')) if proxy.get('auth', None) else ''
      PROXY_SECURE = bool(proxy.get('secure', None))
      PROXY_TUNNEL = bool(proxy.get('tunnel', None))
      @classmethod
      def connect(cls, url, url_p, headers, timeout, max_hlength, end_time, pconnection, ip):
        if pconnection[0] is None:
          rem_time = cls._rem_time(timeout, end_time)
          psock = cls.ConnectionGenerator(cls.PROXY, timeout=rem_time, source_address=(ip, 0))
          if cls.PROXY_SECURE:
            rem_time = cls._rem_time(timeout, end_time)
            psock.settimeout(rem_time)
            psock = cls.SSLContext.wrap_socket(psock, server_side=False, server_hostname=cls.PROXY[0])
          if url_p.scheme.lower() == 'http':
            if cls.PROXY_TUNNEL:
              rem_time = cls._rem_time(timeout, end_time)
              psock.settimeout(rem_time)
              psock.sendall(('CONNECT %s:%s HTTP/1.1\r\nHost: %s:%s\r\n%s\r\n' % (*(cls._netloc_split(url_p.netloc, '80') * 2), ('Proxy-Authorization: %s\r\n' % cls.PROXY_AUTH) if cls.PROXY_AUTH else '')).encode('iso-8859-1'))
              rem_time = cls._rem_time(timeout, end_time)
              if HTTPMessage(psock, body=False, decompress=False, decode=None, max_hlength=max_hlength, max_time=rem_time).code not in ('200', '204'):
                raise
            pconnection[0] = psock
          elif url_p.scheme.lower() == 'https':
            rem_time = cls._rem_time(timeout, end_time)
            psock.settimeout(rem_time)
            psock.sendall(('CONNECT %s:%s HTTP/1.1\r\nHost: %s:%s\r\n%s\r\n' % (*(cls._netloc_split(url_p.netloc, '443') * 2), ('Proxy-Authorization: %s\r\n' % cls.PROXY_AUTH) if cls.PROXY_AUTH else '')).encode('iso-8859-1'))
            rem_time = cls._rem_time(timeout, end_time)
            if HTTPMessage(psock, body=False, decompress=False, decode=None, max_hlength=max_hlength, max_time=rem_time).code not in ('200', '204'):
              raise
            rem_time = cls._rem_time(timeout, end_time)
            psock.settimeout(rem_time)
            pconnection[0] = cls.SSLContext.wrap_socket(psock, server_side=False, server_hostname=cls._netloc_split(url_p.netloc)[0])
          else:
            raise
        if pconnection[0] is None:
          raise
        if url_p.scheme.lower() == 'http' and not cls.PROXY_TUNNEL:
          if cls.PROXY_AUTH:
            headers['Proxy-Authorization'] = cls.PROXY_AUTH
          else:
            headers.pop('Proxy-Authorization', None)
        return ((url_p.path + ('?' + url_p.query if url_p.query else '')) if url_p.scheme.lower() != 'http' or cls.PROXY_TUNNEL else url).replace(' ', '%20') or '/'
  return HTTPRequest


class BaseIServer:

  CLASS = ISocketGenerator

  def __new__(cls, *args, **kwargs):
    if cls is BaseIServer:
      raise TypeError('the class BaseIServer is not intended to be instantiated directly')
    return object.__new__(cls)

  def __init__(self, server_address, request_handler_class, allow_reuse_address=False, dual_stack=True, threaded=False, daemon_thread=False):
    self.server_address = server_address
    self.request_handler_class = request_handler_class
    self.allow_reuse_address = allow_reuse_address
    self.dual_stack = dual_stack
    self.threaded = threaded
    self.daemon_thread = daemon_thread
    self.lock = threading.RLock()
    self.closed = None
    self.isocketgen = self.__class__.CLASS()
    self.thread = None
    self.threads = set()
    self._server_initiate()

  def _server_close(self):
    self.isocketgen.close()

  def _process_request(self, request, client_address):
    try:
      self._handle_request(request, client_address)
    except:
      pass
    try:
      self._close_request(request)
    except:
      pass
    if self.threaded:
      with self.lock:
        self.threads.remove(threading.current_thread())

  def serve(self):
    with self.lock:
      if self.closed is not None:
        return
      self.thread = threading.current_thread()
      self.closed = False
    while not self.closed:
      try:
        request, client_address = self._get_request()
        if self.closed:
          break
        if self.threaded:
          th = threading.Thread(target=self._process_request, args=(request, client_address), daemon=self.daemon_thread)
          self.threads.add(th)
          th.start()
        else:
          self._process_request(request, client_address)
      except:
        pass

  def start(self):
    th = threading.Thread(target=self.serve)
    th.start()

  def _wait_threads(self, threads, timeout=None):
    rt = timeout
    if timeout is not None:
      t = time.monotonic()
    while True:
      if timeout is not None:
        rt = timeout + t - time.monotonic()
        if rt <= 0:
          return False
      with self.lock:
        for th in threads:
          break
        else:
          return True
      th.join(rt)

  def shutdown(self, block_on_close=True):
    with self.lock:
      if self.closed is None or self.closed:
        return
      self.closed = True
    self._server_close()
    self.thread.join()
    self.thread = None
    if block_on_close and self.threaded:
      self._wait_threads(self.threads)

  def stop(self, block_on_close=True):
    self.shutdown()

  def __enter__(self):
    self.start()
    return self

  def __exit__(self, et, ev, tb):
    self.stop()

  @staticmethod
  def retrieve_ipv4s():
    s = ULONG(0)
    while True:
      b = ctypes.create_string_buffer(s.value)
      r = iphlpapi.GetIpAddrTable(b, byref(s), BOOL(False))
      if r == 0:
        break
      elif r != 122:
        return ()
    if s.value == 0:
      return ()
    r = ctypes.cast(b, P_MIB_IPADDRTABLE).contents
    n = r.dwNumEntries
    t = ctypes.cast(byref(r.table), POINTER(MIB_IPADDRROW * n)).contents
    return tuple(socket.inet_ntoa(e.dwAddr.to_bytes(4, 'little')) for e in t if e.wType & 1)

  @staticmethod
  def retrieve_ips(ipv4=True, ipv6=True):
    if ipv4:
      f = 0 if ipv6 else socket.AF_INET
    elif ipv6:
      f = socket.AF_INET6
    else:
      return []
    f = ULONG(f)
    s = ULONG(0)
    while True:
      b = ctypes.create_string_buffer(s.value)
      r = iphlpapi.GetAdaptersAddresses(f, ULONG(14), None, b, byref(s))
      if r == 0:
        break
      elif r != 111:
        return []
    if s.value == 0:
      return []
    ips = []
    paa = ctypes.cast(b, PIP_ADAPTER_ADDRESSES)
    while paa:
      if ctypes.cast(paa, PULONG).contents.value < ctypes.sizeof(IP_ADAPTER_ADDRESSES):
        return []
      aa = paa.contents
      paa = aa.Next
      if aa.OperStatus != 1:
        continue
      pa = aa.FirstUnicastAddress
      while pa:
        if ctypes.cast(pa, PULONG).contents.value < ctypes.sizeof(pa._type_):
          break
        a = pa.contents
        pa = a.Next
        if a.Flags == 2:
          continue
        ad = a.Address
        if ad.iSockaddrLength < ctypes.sizeof(ad.lpSockaddr._type_):
          continue
        f = ad.lpSockaddr.contents.value
        if f == socket.AF_INET:
          ips.append((aa.IfIndex, socket.inet_ntoa(ctypes.cast(ad.lpSockaddr, PSOCKADDR_IN).contents.addr.addr_4b)))
        elif f == socket.AF_INET6:
          ad = ctypes.cast(ad.lpSockaddr, PSOCKADDR_IN6).contents
          ips.append((aa.Ipv6IfIndex, '%s%s' % (socket.inet_ntop(f, ad.addr.addr_8w), ('%%%d' % ad.scope_id.Zone if ad.scope_id.Zone else ''))))
    return ips


class MixinIDServer:

  CLASS = IDSocketGenerator

  def __init_subclass__(cls):
    if 'multi' in cls.__name__.lower():
      cls.idsockets = property(lambda self: self.isockets)
    else:
      cls.idsocket = property(lambda self: self.isocket)


class MixinIDAltServer(MixinIDServer):

  CLASS = IDAltSocketGenerator


class UDPIServer(BaseIServer):

  def __init__(self, server_address, request_handler_class, allow_reuse_address=False, multicast_membership=None, dual_stack=True, max_packet_size=65507, threaded=False, daemon_thread=False):
    self.max_packet_size = max_packet_size
    self.multicast_membership = multicast_membership
    super().__init__(server_address, request_handler_class, allow_reuse_address, dual_stack, threaded, daemon_thread)

  def _server_initiate(self):
    f = socket.AF_UNSPEC
    if self.multicast_membership:
      self.multicast_membership = socket.getaddrinfo(self.multicast_membership, None, type=socket.SOCK_DGRAM)[0]
      f = self.multicast_membership[0]
    if isinstance(self.server_address, int):
      self.server_address = (None, self.server_address)
    self.isocket = self.isocketgen.create_server(self.server_address, family=f, backlog=False, reuse_port=self.allow_reuse_address, dualstack_ipv6=self.dual_stack, type=socket.SOCK_DGRAM)
    self.server_address = self.isocket.getsockname()
    if f == socket.AF_INET:
      self.isocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack('4s4s', socket.inet_aton(self.multicast_membership[4][0]), socket.inet_aton(self.server_address[0])))
    elif f == socket.AF_INET6:
      ai = self.server_address[3]
      if not ai:
        a = self.server_address[0]
        ips = self.retrieve_ips(False, True)
        ai = next((ip[0] for ip in ips if ip[1] == a), next((ip[0] for ip in ips if ip[1].rsplit('%', 1)[0] == a), 0))
      self.isocket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, struct.pack('16sL', socket.inet_pton(socket.AF_INET6, self.multicast_membership[4][0]), ai))

  def _get_request(self):
    return self.isocket.recvfrom(self.max_packet_size)

  def _handle_request(self, request, client_address):
    self.request_handler_class((request, self.isocket), client_address, self)

  def _close_request(self, request):
    pass


class UDPIDServer(MixinIDServer, UDPIServer):

  pass


class UDPIDAltServer(MixinIDAltServer, UDPIServer):

  pass


class TCPIServer(BaseIServer):

  def __init__(self, server_address, request_handler_class, allow_reuse_address=False, dual_stack=True, request_queue_size=128, threaded=False, daemon_thread=False, nssl_context=None):
    self.request_queue_size = request_queue_size
    self.nssl_context = nssl_context
    if self.nssl_context is True:
      self.nssl_context = NestedSSLContext(ssl.PROTOCOL_TLS_SERVER)
      self.nssl_context.load_autogenerated_cert_chain()
    super().__init__(server_address, request_handler_class, allow_reuse_address, dual_stack, threaded, daemon_thread)

  def _server_initiate(self):
    if isinstance(self.server_address, int):
      self.server_address = (None, self.server_address)
    self.isocket = self.isocketgen.create_server(self.server_address, family=socket.AF_UNSPEC, backlog=False, reuse_port=self.allow_reuse_address, dualstack_ipv6=self.dual_stack)
    if self.nssl_context:
      self.isocket = self.nssl_context.wrap_socket(self.isocket, server_side=True)
    self.server_address = self.isocket.getsockname()
    self.isocket.listen(self.request_queue_size)

  def _get_request(self):
    return self.isocket.accept()

  def _handle_request(self, request, client_address):
    self.request_handler_class(request, client_address, self)

  def _close_request(self, request):
    request.shutclose()


class TCPIDServer(MixinIDServer, TCPIServer):

  pass


class TCPIDAltServer(MixinIDAltServer, TCPIServer):

  pass


class RequestHandler:

  def __init__(self, request, client_address, server):
    self.request = request
    self.client_address = client_address
    self.server = server
    self.address = (self.request if isinstance(self.request, socket.socket) else self.request[1]).getsockname()
    self.handle()

  def handle(self):
    closed = False
    while not closed and not self.server.closed:
      print(self.address, self.request, self.client_address)
      req = HTTPMessage(self.request, max_length=1073741824)
      if self.server.closed:
        break
      if req.expect_close:
        closed = True
      if not req.method:
        closed = True
        continue


class MultiUDPIServer(UDPIServer):

  def _server_initiate(self):
    if self.multicast_membership:
      if isinstance(self.multicast_membership, str):
        self.multicast_membership = (self.multicast_membership,)
        self.server_address = (self.server_address,)
      elif isinstance(self.server_address, int):
        self.server_address = (self.server_address,) * len(self.multicast_membership)
      self.multicast_membership = tuple(socket.getaddrinfo(m, None, type=socket.SOCK_DGRAM)[0] for m in self.multicast_membership)
      ips = {}
      self.server_address = tuple(tuple((ip[1], a) for ip in (e[1] for e in enumerate(ips[m[0]] if m[0] in ips else ips.setdefault(m[0], self.retrieve_ips(m[0] == socket.AF_INET, m[0] == socket.AF_INET6))) if e[0] == 0 or e[1][0] != ips[m[0]][e[0] - 1][0])) if isinstance(a, int) else a for a, m in zip(self.server_address, self.multicast_membership))
      self.isockets = tuple(tuple(self.isocketgen.create_server(addr, family=m[0], backlog=False, reuse_port=self.allow_reuse_address, dualstack_ipv6=self.dual_stack, type=socket.SOCK_DGRAM) for addr in a) for a, m in zip(self.server_address, self.multicast_membership))
      self.server_address = tuple(tuple(isock.getsockname() for isock in i) for i in self.isockets)
      for i, a, m in zip(self.isockets, self.server_address, self.multicast_membership):
        if m[0] == socket.AF_INET:
          for isock, addr in zip(i, a):
            isock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, struct.pack('4s4s', socket.inet_aton(m[4][0]), socket.inet_aton(addr[0])))
        elif m[0] == socket.AF_INET6:
          for isock, addr in zip(i, a):
            ai = addr[3]
            if not ai:
              ai = next((ip[0] for ip in (ips[socket.AF_INET6] if socket.AF_INET6 in ips else ips.setdefault(socket.AF_INET6, self.retrieve_ips(False, True))) if ip[1] == addr[0]), next((ip[0] for ip in ips[socket.AF_INET6] if ip[1].rsplit('%', 1)[0] == addr[0]), 0))
            isock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, struct.pack('16sL', socket.inet_pton(socket.AF_INET6, m[4][0]), ai))
    else:
      if isinstance(self.server_address, int):
        self.server_address = tuple((ip[1], self.server_address) for ip in MultiUDPIServer.retrieve_ips())
      self.isockets = tuple(self.isocketgen.create_server(addr, family=socket.AF_UNSPEC, backlog=False, reuse_port=self.allow_reuse_address, dualstack_ipv6=self.dual_stack, type=socket.SOCK_DGRAM) for addr in self.server_address)
      self.server_address = tuple(isock.getsockname() for isock in self.isockets)

  def _get_request(self, isocket):
    return isocket.recvfrom(self.max_packet_size, timeout=0)

  def _handle_request(self, request, client_address, isocket):
    self.request_handler_class((request, isocket), client_address, self)

  def _process_request(self, request, client_address, isocket):
    try:
      self._handle_request(request, client_address, isocket)
    except:
      pass
    if self.threaded:
      with self.lock:
        self.threads.remove(threading.current_thread())

  def serve(self):
    with self.lock:
      if self.closed is not None:
        return
      self.thread = threading.current_thread()
      self.closed = False
    while not self.closed:
      try:
        for isock in self.isocketgen.waitany(None, 'r'):
          try:
            request, client_address = self._get_request(isock)
            if self.closed:
              break
            if self.threaded:
              th = threading.Thread(target=self._process_request, args=(request, client_address, isock), daemon=self.daemon_thread)
              self.threads.add(th)
              th.start()
            else:
              self._process_request(request, client_address, isock)
          except:
            pass
      except:
        pass


class MultiUDPIDServer(MixinIDServer, MultiUDPIServer):

  pass


class MultiUDPIDAltServer(MixinIDAltServer, MultiUDPIServer):

  pass


class _MimeTypes:
  _mimetypes = mimetypes.MimeTypes(strict=False)
  _mimetypes.read_windows_registry(strict=False)
  _mimetypes.encodings_map = {}
  _encode_mimetypes = ({'example', 'text', 'message', 'font'}, {'application/javascript', 'application/ecmascript', 'application/x-ecmascript', 'application/x-javascript', 'application/x-sh', 'application/x-csh', 'application/json', 'application/ld+json', 'application/manifest+json', 'application/vnd.api+json', 'application/rtf', 'application/xml', 'application/xhtml+xml', 'application/atom+xml', 'application/rss+xml', 'application/msword', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint', 'application/font-sfnt', 'application/vnd.ms-fontobject', 'application/xfont-ttf', 'application/xfont-opentype', 'application/xfont-truetype', 'application/wasm', 'application/x-httpd-php', 'application/x-httpd-python', 'application/n-quads', 'application/n-triples', 'application/postscript', 'application/x-python-code', 'image/svg+xml', 'image/x-icon', 'image/vnd.microsoft.icon', 'multipart/form-data'})

  @classmethod
  def _encode_mimetype(cls, mt):
    return mt in cls._encode_mimetypes[1] or mt.split('/', 1)[0] in cls._encode_mimetypes[0]


class HTTPRequestHandler(RequestHandler, _MimeTypes):
  _fn_cmp = cmp_to_key(shlwapi.StrCmpLogicalW)
  _encodings = ({'identity': 50, '*': 75}, (({'deflate': 0, 'gzip': 1, 'zstd': 2, 'br': 3, 'identity': 50, '*': 75} if zstd else {'deflate': 0, 'gzip': 1, 'br': 3, 'identity': 50, '*': 75}) if brotli else ({'deflate': 0, 'gzip': 1, 'zstd': 2, 'identity': 50, '*': 75} if zstd else {'deflate': 0, 'gzip': 1, 'identity': 50, '*': 75})))

  @classmethod
  def _set_enc(cls, aenc, mt='text', fid=False):
    if aenc is None:
      return False
    aenc = aenc.lower().split(',')
    for i in range(len(aenc)):
      ae = aenc[i].split(';')
      if len(ae) == 1:
        aenc[i] = (ae[0].strip(), 1)
      else:
        aeq = ae[1].split('=')
        try:
          if aeq[0].strip() == 'q':
            aenc[i] = (ae[0].strip(), min(max(float(aeq[1].strip()), 0), 1))
          else:
            raise
        except:
          aenc[i] = (ae[0].strip(), 1)
    pid = fid or not cls._encode_mimetype(mt)
    while True:
      senc = cls._encodings[0 if pid else 1]
      aenc.sort(key=lambda ae:senc.get(ae[0], 100))
      aenc.sort(key=lambda ae:ae[1], reverse=True)
      for ae in aenc:
        enc = senc.get(ae[0])
        if ae[1] > 0:
          if enc == 75:
            return False if pid else ('deflate', zlib.compressobj(wbits=15))
          elif enc == 0:
            return 'deflate', zlib.compressobj(wbits=15)
          elif enc == 1:
            return 'gzip', zlib.compressobj(wbits=31)
          elif enc == 2:
            return 'zstd', zstd.ZstdCompressor(level=9)
          elif enc == 3:
            return 'br', _brotli.compressobj()
          elif enc == 50:
            return False
        elif enc in (50, 75):
          break
      else:
        return False
      if fid or not pid:
        return None
      else:
        pid = False

  def _send(self, h, bo=None, bsize=None, brange=None):
    try:
      self.request.sendall(h.encode('ISO-8859-1'))
      if isinstance(bo, IOBase):
        bo.seek((brange[0] if brange else 0), os.SEEK_SET)
        r = brange[1] - brange[0] if brange else bsize
        while r > 0:
          b = bo.read(min(r, 1048576))
          if not b:
            raise
          r -= len(b)
          self.request.sendall(b)
      elif bo:
        self.request.sendall(memoryview(bo)[brange[0]:brange[1]] if brange else bo)
      return True
    except:
      return False

  def _send_close(self, resp, rbody=None):
    end_time = time.monotonic() + 3
    self.request.settimeout(3)
    if self._send(resp, rbody):
      b = b'' if self.req else None
      while True:
        rem_time = end_time - time.monotonic()
        if rem_time <= 0:
          break
        if b is None:
          try:
            self.request.settimeout(rem_time)
            if not self.request.recv(1048576):
              break
          except:
            break
        else:
          b = self.req.body(1048576, max_time=rem_time)
          if b == b'':
            break
    self.request.settimeout(None)
    return False

  def _send_opt(self, c=False):
    resp = \
      'HTTP/1.1 200 OK\r\n' \
      'Content-Length: 0\r\n' \
      'Date: ' + email.utils.formatdate(time.time(), usegmt=True) + '\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, no-store, must-revalidate\r\n' \
      'Allow: OPTIONS, HEAD, GET%s\r\n' \
      '%s' \
      '\r\n' % ((', PUT' if self.server.max_upload else ''), ('Connection: close\r\n' if c else ''))
    return (self._send_close if c else self._send)(resp)

  def _send_cont(self):
    if self._send('HTTP/1.1 100 Continue\r\n\r\n'):
      return True
    else:
      self.error = True
      return False

  def _send_err(self, e, m='', c=False):
    if c is None:
      self.error = (e, m)
      return False
    rbody = \
      '<!DOCTYPE html>\r\n' \
      '<html lang="en">\r\n' \
      '  <head>\r\n' \
      '    <meta charset="utf-8">\r\n' \
      '    <title>%d %s</title>\r\n' \
      '  </head>\r\n' \
      '  <body>\r\n' \
      '    <h1>%s</h1>\r\n' \
      '  </body>\r\n' \
      '</html>' % (e, m, m)
    rbody = rbody.encode('utf-8')
    resp = \
      'HTTP/1.1 %d %s\r\n' \
      'Content-Type: text/html; charset=utf-8\r\n' \
      'Content-Length: %d\r\n' \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, no-store, must-revalidate\r\n' \
      '%s' \
      '\r\n' % (e, m, len(rbody), email.utils.formatdate(time.time(), usegmt=True), ('Connection: close\r\n' if c else ''))
    return (self._send_close if c else self._send)(resp, (rbody if self.req.method != 'HEAD' else None))
  def _send_err_br(self, c=False):
    return self._send_err(400, 'Bad request', c)
  def _send_err_ef(self, c=False):
    return self._send_err(417, 'Expectation failed', c)
  def _send_err_ni(self, c=False):
    return self._send_err(501, 'Not implemented', c)
  def _send_err_nf(self, c=False):
    return self._send_err(404, 'Not found', c)
  def _send_err_rns(self, c=False):
    return self._send_err(416, 'Range not satisfiable', c)
  def _send_err_f(self, c=False):
    return self._send_err(403, 'Forbidden', c)
  def _send_err_mna(self, c=False):
    return self._send_err(405, 'Method not allowed', c)
  def _send_err_umt(self, c=False):
    return self._send_err(415, 'Unsupported media type', c)
  def _send_err_uc(self, c=False):
    return self._send_err(422, 'Unprocessable content', c)
  def _send_err_ptl(self, c=False):
    return self._send_err(413, 'Content too large', c)
  def _send_err_na(self, c=False):
    return self._send_err(406, 'Not acceptable', c)
  def _send_err_c(self, c=False):
    return self._send_err(409, 'Conflict', c)

  def _send_resp(self, rtype, rsize, rbody=None, rmod=None, rrange=None, enc=False):
    resp = \
      'HTTP/1.1 %s\r\n' \
      'Content-Type: %s\r\n' \
      'Content-Length: %d\r\n' \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, must-revalidate\r\n' \
      '%s' \
      'Accept-Ranges: bytes\r\n' \
      '%s' \
      '%s' \
      '\r\n' % (('200 OK' if rrange is None else '206 Partial Content'), rtype, (rrange[1] - rrange[0] if rrange else rsize), email.utils.formatdate(time.time(), usegmt=True), (('Content-Encoding: %s\r\n' % enc[0]) if enc else ''), ('' if rrange is None else ('Content-Range: bytes %d-%d/%d\r\n' % (rrange[0], rrange[1] - 1, rsize))), ('' if rmod is None else ('%sLast-Modified: %s\r\n' % (('Content-Disposition: attachment\r\n' if self.server.recommend_downloading else ''), email.utils.formatdate(rmod, usegmt=True)))))
    return self._send(resp, rbody, rsize, rrange)

  def _send_resp_chnk(self, rtype, rsize, rbody, rmod, rrange=None, enc=False, tenc=False):
    if rrange and enc:
      return False
    resp = \
      'HTTP/1.1 %s\r\n' \
      'Content-Type: %s\r\n' \
      'Transfer-Encoding: chunked%s\r\n' \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, must-revalidate\r\n' \
      '%s' \
      'Accept-Ranges: bytes\r\n' \
      '%s' \
      '%s' \
      '\r\n' % (('200 OK' if rrange is None else '206 Partial Content'), rtype, ((', %s' % tenc[0]) if tenc else ''), email.utils.formatdate(time.time(), usegmt=True), (('Content-Encoding: %s\r\n' % enc[0]) if enc else ''), ('' if rrange is None else ('Content-Range: bytes %d-%d/%d\r\n' % (rrange[0], rrange[1] - 1, rsize))), ('' if rmod is None else ('%sLast-Modified: %s\r\n' % (('Content-Disposition: attachment\r\n' if self.server.recommend_downloading else ''), email.utils.formatdate(rmod, usegmt=True)))))
    try:
      self.request.sendall(resp.encode('ISO-8859-1'))
      if isinstance(rbody, IOBase):
        rbody.seek((rrange[0] if rrange else 0), os.SEEK_SET)
        r = rrange[1] - rrange[0] if rrange else rsize
        while r > 0:
          b = rbody.read(min(r, 1048576))
          if not b:
            raise
          r -= len(b)
          if enc:
            b = enc[1].compress(b)
          if b:
            if tenc:
              b = tenc[1].compress(b)
            if b:
              self.request.sendall(b'%x\r\n%b\r\n' % (len(b), b))
        b = b''
        if enc:
          b = enc[1].flush()
        if tenc:
          b = b''.join((tenc[1].compress(b), tenc[1].flush())) if b else tenc[1].flush()
        if b:
          self.request.sendall(b'%x\r\n%b\r\n' % (len(b), b))
        self.request.sendall(b'0\r\n\r\n')
      elif rbody:
        b = memoryview(rbody)[rrange[0]:rrange[1]] if rrange else rbody
        if b:
          if enc:
            b = b''.join((enc[1].compress(b), enc[1].flush()))
          if tenc:
            b = b''.join((tenc[1].compress(b), tenc[1].flush()))
          self.request.sendall(b'%x\r\n%b\r\n' % (len(b), b))
        self.request.sendall(b'0\r\n\r\n')
      return True
    except:
      return False

  def _send_nm(self):
    resp = \
      'HTTP/1.1 304 Not Modified\r\n' \
      'Content-Length: 0\r\n' \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, no-store, must-revalidate\r\n' \
      '\r\n' % email.utils.formatdate(time.time(), usegmt=True)
    return self._send(resp)

  def _send_mp(self, loc):
    resp = \
      'HTTP/1.1 301 Moved Permanently\r\n' \
      'Content-Length: 0\r\n' \
      'Location: %s\r\n' \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, no-store, must-revalidate\r\n' \
      '\r\n' % (loc, email.utils.formatdate(time.time(), usegmt=True))
    return self._send(resp)

  def _send_c(self, loc, e=False, c=False):
    resp = \
      'HTTP/1.1 %s\r\n' \
      'Content-Length: 0\r\n' \
      'Content-Location: %s\r\n' \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, no-store, must-revalidate\r\n' \
      '%s' \
      '\r\n' % (('204 No Content' if e else '201 Created'), loc, email.utils.formatdate(time.time(), usegmt=True), ('Connection: close\r\n' if c else ''))
    return (self._send_close if c else self._send)(resp)

  def _send_err_u(self, r='', c=False):
    if c is None:
      self.error = (r,)
      return False
    resp = \
      'HTTP/1.1 401 Unauthorized\r\n' \
      'Content-Length: 0\r\n' \
      'WWW-Authenticate: Basic realm="%s", charset="UTF-8"\r\n' \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Cache-Control: no-cache, no-store, must-revalidate\r\n' \
      '%s' \
      '\r\n' % (r or 'HTTPIServer', email.utils.formatdate(time.time(), usegmt=True), ('Connection: close\r\n' if c else ''))
    return (self._send_close if c else self._send)(resp)

  @classmethod
  def _process_path(cls, root, qpath):
    try:
      path, osort = qpath.partition('?')[::2]
      try:
        path = urllib.parse.unquote(path, errors='surrogatepass')
      except:
        path = urllib.parse.unquote(path)
      spath = path.endswith('/')
      path = os.path.normpath(os.path.join('\\', path)).lstrip('\\')
      if ':' in path or path.startswith('\\\\'):
        raise
      apath = os.path.normpath(os.path.join(root, path))
      if os.path.commonpath((root, apath)) != root:
        raise
      rpath = ('\\' + path).replace('\\', '/')
      if spath and not rpath.endswith('/'):
        rpath += '/'
    except:
      return None, None, None
    return apath, rpath, osort

  def _html_from_dir(self, apath, rpath, osort='', upl=False):
    l = [(e.is_dir(), e.name, e.stat()) for e in os.scandir(apath) if (e.is_dir() or e.is_file())]
    nsort = '?NA'
    msort = '?MA'
    ssort = '?SA'
    _fn_cmp = self.__class__._fn_cmp
    if osort == 'ND':
      l.sort(key=lambda t:_fn_cmp(LPCWSTR(t[1])), reverse=True)
    else:
      l.sort(key=lambda t:_fn_cmp(LPCWSTR(t[1])))
      if osort == 'MA':
        msort = '?MD'
        l.sort(key=lambda t:t[2].st_mtime)
      elif osort == 'MD':
        l.sort(key=lambda t:t[2].st_mtime, reverse=True)
      elif osort == 'SA':
        ssort = '?SD'
        l.sort(key=lambda t:t[2].st_size)
      elif osort == 'SD':
        l.sort(key=lambda t:t[2].st_size, reverse=True)
      else:
        nsort = '?ND'
      l.sort(key=lambda t:t[0], reverse=True)
    for i in range(len(l)):
      e = l[i]
      n = e[1] + '\\' if e[0] else e[1]
      rn = e[1] + '/' if e[0] else e[1]
      mt = time.strftime('%Y-%m-%d %H:%M', time.localtime(e[2].st_mtime))
      s = '-' if e[0] else format(e[2].st_size, ',d').replace(',', '·')
      l[i] = '      <tr><td><a href="%s"%s>%s</a><td align="right">&nbsp;&nbsp;%s&nbsp;&nbsp;</td><td align="right">%s</td></tr>\r\n' %(urllib.parse.quote(rn, errors='surrogatepass'), (' download=""' if self.server.recommend_downloading else ''), html.escape(n), mt, s)
    rbody = \
      '<!DOCTYPE html>\r\n' \
      '<html lang="en">\r\n' \
      '  <head>\r\n' \
      '    <meta charset="utf-8">\r\n' \
      '    <title>Index of %s</title>\r\n' \
      '    <script>\r\n' \
      '      function cd() {\r\n' \
      '        let n;\r\n' \
      '        do {\r\n' \
      '          n = window.prompt("Name of the directory:");\r\n' \
      '          if (! n) {return;}\r\n' \
      '        } while (n.match(/[\\\\\\/\\?\\*:<>"\\|]/));\r\n' \
      '        n += "/";\r\n' \
      '        fetch(encodeURI(n), {method: "PUT"}).then(function(r) {if (! r.ok) {throw null;} else {window.location.reload();}}).catch(function(e) {window.alert("Directory creation failed.");});\r\n' \
      '      }\r\n' \
      '      function uf(f) {\r\n' \
      '        if (! f) {return;}\r\n' \
      '        let n;\r\n' \
      '        do {\r\n' \
      '          n = window.prompt("Name of the file:", f.name);\r\n' \
      '          if (! n) {return;}\r\n' \
      '        } while (n.match(/[\\\\\\/\\?\\*:<>"\\|]/));\r\n' \
      '        fetch(encodeURI(n), {method: "PUT", body: f}).then(function(r) {if (! r.ok) {throw null;} else {window.location.reload();}}).catch(function(e) {window.alert("File upload failed.");});\r\n' \
      '      }\r\n' \
      '    </script>\r\n' \
      '  </head>\r\n' \
      '  <body>\r\n' \
      '    <h1>Index of %s</h1>\r\n' \
      '    <table>\r\n' \
      '      <tr><th><a href="%s">Name</a></th><th><a href="%s">Last modified</a></th><th><a href="%s">Size</a></th></tr>\r\n' \
      '      <tr><th colspan="3"><hr></th></tr>\r\n' \
      '%s'\
      '%s'\
      '      <tr><th colspan="3"><hr></th></tr>\r\n' \
      '    </table>\r\n' \
      '%s'\
      '  </body>\r\n' \
      '</html>' % (*((html.escape(rpath),) * 2), nsort, msort, ssort, ('' if rpath == '/' else '     <tr><td><a href="../">Parent Directory</a><td align="right">&nbsp;&nbsp;&nbsp;&nbsp;</td><td align="right">-</td></tr>\r\n'), ''.join(l), ('<button onclick="cd()">Create directory</button>&nbsp;&nbsp;<button onclick="document.getElementsByTagName(\'input\')[0].click()">Upload file</button><input type="file" autocomplete="off" style="display:none;" onchange="uf(this.files[0]); this.value=\'\'">' if upl else ''))
    return rbody.encode('utf-8', errors='surrogateescape')

  @staticmethod
  def split_int(v):
    return DWORD(v & ~(-1 << 32)), DWORD(v >> 32)

  def handle(self, req=None, blen_dec=None):
    closed = False
    if req is not None:
      if isinstance(blen_dec, str):
        return not self._send_err_umt(None)
      if self.error:
        return False
      e100 = True
    else:
      e100 = False
      self.error = None
    root = self.server.root
    while not closed and not self.server.closed:
      if e100:
        if not req.method:
          return self._send_err_br(None)
      else:
        req = self.req = HTTPStreamMessage(self.request, expect100_handler=self.handle, error415_handler=self.handle)
        if self.server.closed:
          continue
        if self.error:
          closed = True
          if self.error is not True:
            (self._send_err_u if len(self.error) == 1 else self._send_err)(*self.error, True)
          continue
        if not req or not req.method:
          closed = not self._send_err_br(True)
          continue
        if req.expect_close:
          closed = True
      if req.method == 'OPTIONS':
        if e100:
          return self._send_cont()
        req.body(1048576)
        b = req.body(1)
        if b is None:
          closed = not self._send_err_uc(True)
          continue
        closed |= not self._send_opt(b != b'')
      elif req.method in {'GET', 'HEAD', 'PUT'}:
        isp = req.method == 'PUT'
        if not isp:
          if e100:
            return self._send_err_ef(None)
          elif req.body(1) != b'':
            closed = not self._send_err_ptl(True)
            continue
        apath, rpath, osort = self._process_path(root, req.path)
        try:
          if apath is None:
            raise
          isd = os.path.isdir(apath)
          if not isp and isd and not rpath.endswith('/'):
            closed |= not self._send_mp(urllib.parse.quote(rpath + '/'))
            continue
        except:
          if e100:
            return self._send_err_f(None)
          closed |= not self._send_err_f(isp)
          continue
        if self.server.basic_auth:
          cred = req.header('Authorization', '').partition(' ')
          cred = cred[2].strip() if cred[0].lower() == 'basic' else ''
          if cred:
            if not self.server.basic_auth(rpath, self, cred.encode('utf-8'), (2 if isp else 1)):
              if e100:
                return self._send_err_f(None)
              closed |= not self._send_err_f(isp)
              continue
          else:
            r = self.server.basic_auth(rpath, self)
            if r is not None:
              if e100:
                return self._send_err_u(r, None)
              closed |= not self._send_err_u(r, isp)
              continue
        rrange = req.header('Range')
        if rrange:
          try:
            unit, rrange = rrange.rpartition('=')[::2]
            if (unit and unit.lower() != 'bytes') or ',' in rrange:
              raise
            rrange = rrange.split('-')
            rrange = (rrange[0].strip(), rrange[1].strip())
          except:
            if e100:
              return self._send_err_rns(None)
            closed |= not self._send_err_rns(isp)
            continue
        if not isp:
          f = None
          try:
            if isd:
              for ind in ('index.htm', 'index.html'):
                try:
                  ipath = os.path.join(apath, ind)
                  if os.path.isfile(ipath):
                    apath = ipath
                    break
                except:
                  pass
              else:
                enc = self._set_enc(req.header('Accept-Encoding'), 'text/html', bool(rrange))
                tenc = self._set_enc(req.header('TE'), 'application/x-compressed' if enc else 'text/html')
                if enc is None or tenc is None:
                  closed |= not self._send_err_na()
                  continue
                rbody = self._html_from_dir(apath, rpath, osort, bool(self.server.max_upload))
                if rrange:
                  try:
                    rrange = (int(rrange[0]), (min(int(rrange[1]) + 1, len(rbody)) if rrange[1] else len(rbody))) if rrange[0] else (len(rbody) - int(rrange[1]), len(rbody))
                    if rrange[0] < 0 or rrange[0] >= rrange[1]:
                      raise
                  except:
                    closed |= not self._send_err_rns()
                    continue
                elif enc and not tenc:
                  rbody = b''.join((enc[1].compress(rbody), enc[1].flush()))
                closed |= not (self._send_resp_chnk('text/html; charset=utf-8', len(rbody), (rbody if req.method == 'GET' else None), None, rrange, enc, tenc) if tenc else self._send_resp('text/html; charset=utf-8', len(rbody), (rbody if req.method == 'GET' else None), None, rrange, enc))
                continue
            if os.path.isfile(apath):
              btype = self.__class__._mimetypes.guess_type(apath, strict=False)[0] or 'application/octet-stream'
              enc = self._set_enc(req.header('Accept-Encoding'), btype, bool(rrange))
              tenc = self._set_enc(req.header('TE'), 'application/x-compressed' if enc else btype)
              if enc is None or tenc is None:
                closed |= not self._send_err_na()
                continue
              with self.server._plock:
                f = open(apath, 'rb')
                h = HANDLE(get_osfhandle(f.fileno()))
                fs = os.stat(f.fileno())
                if rrange:
                  try:
                    rrange = (int(rrange[0]), (min(int(rrange[1]) + 1, fs.st_size) if rrange[1] else fs.st_size)) if rrange[0] else (fs.st_size - int(rrange[1]), fs.st_size)
                    if rrange[0] < 0 or rrange[0] >= rrange[1]:
                      raise
                  except:
                    closed |= not self._send_err_rns()
                    continue
                if not kernel32.LockFileEx(h, DWORD(1), DWORD(0), *self.split_int(rrange[1] - rrange[0] if rrange else fs.st_size), byref(OVERLAPPED(0, 0, OVERLAPPED_O(*self.split_int(rrange[0] if rrange else 0)), None))):
                  closed |= not self._send_err_c()
                  continue
              if req.header('If-None-Match') is None:
                ms = req.header('If-Modified-Since')
                if ms is not None:
                  try:
                    ms = email.utils.parsedate_tz(ms)
                    if ms[9]:
                      raise
                    ms = (*ms[:8], 0, 0)
                    if int(fs.st_mtime) <= email.utils.mktime_tz(ms):
                      closed |= not self._send_nm()
                      continue
                  except:
                    pass
              closed |= not (self._send_resp_chnk(btype, fs.st_size, (f if req.method == 'GET' else None), fs.st_mtime, rrange, enc, tenc) if enc or tenc else self._send_resp(btype, fs.st_size, (f if req.method == 'GET' else None), fs.st_mtime, rrange))
            else:
              closed |= not self._send_err_nf()
          except:
            closed |= not self._send_err_f()
          finally:
            if f:
              try:
                f.close()
              except:
                pass
        else:
          if not self.server.max_upload:
            if e100:
              return self._send_err_mna(None)
            closed = not self._send_err_mna(True)
            continue
          if rpath.endswith('/'):
            if e100:
              return self._send_cont() if blen_dec <= 0 else self._send_err_ptl(None)
            if req.body(1) != b'':
              closed = not self._send_err_ptl(True)
              continue
            try:
              if isd:
                os.utime(apath, (time.time(),) * 2)
                closed |= not self._send_c(rpath, True)
              else:
                os.mkdir(apath)
                closed |= not self._send_c(rpath)
            except FileNotFoundError:
              closed |= not self._send_err_nf()
            except:
              closed |= not self._send_err_f()
          else:
            f = None
            try:
              try:
                if e100:
                  try:
                    size = os.path.getsize(apath)
                  except:
                    size = 0
                else:
                  self.server._plock.acquire()
                  e = os.path.isfile(apath)
                  f = open(apath, ('r+b' if e else 'wb'))
                  h = HANDLE(get_osfhandle(f.fileno()))
                  size = os.stat(f.fileno()).st_size
                if rrange:
                  try:
                    if rrange[0]:
                      if rrange[1]:
                        rrlength = int(rrange[1]) + 1 - int(rrange[0])
                        rrlengthm = False
                      else:
                        rrlength = self.server.max_upload - max(0, int(rrange[0]) - size)
                        rrlengthm = True
                      if rrlength < 0 or rrlength + max(0, int(rrange[0]) - size) > self.server.max_upload:
                        if e100:
                          return self._send_err_ptl(None)
                        closed = not self._send_err_ptl(True)
                        continue
                      if e100:
                        return self._send_cont()
                      f.seek(int(rrange[0]), os.SEEK_SET)
                    else:
                      if e100:
                        return self._send_cont()
                      rrlength = self.server.max_upload
                      rrlengthm = True
                      f.seek(-min(int(rrange[1]), size), os.SEEK_END)
                  except:
                    if e100:
                      return self._send_err_rns(None)
                    closed = not self._send_err_rns(True)
                    continue
                else:
                  if e100:
                    return self._send_cont() if blen_dec <= self.server.max_upload else self._send_err_ptl(None)
                  if int(req.header('Content-Length', 0)) > self.server.max_upload:
                    closed = not self._send_err_ptl(True)
                    continue
                  rrlength = self.server.max_upload
                  rrlengthm = True
                  if not kernel32.LockFileEx(h, DWORD(3), DWORD(0), *self.split_int(size + self.server.max_upload), byref(OVERLAPPED(0, 0, OVERLAPPED_O(*self.split_int(0)), None))):
                    closed = not self._send_err_c(True)
                    continue
                  f.seek(0, os.SEEK_SET)
                  f.truncate(0)
                  if not kernel32.UnlockFileEx(h, DWORD(0), *self.split_int(size + self.server.max_upload), byref(OVERLAPPED(0, 0, OVERLAPPED_O(*self.split_int(0)), None))):
                    closed = not self._send_err_c(True)
                    continue
                if not kernel32.LockFileEx(h, DWORD(3), DWORD(0), *self.split_int(rrlength), byref(OVERLAPPED(0, 0, OVERLAPPED_O(*self.split_int(f.tell())), None))):
                  closed = not self._send_err_c(True)
                  continue
              finally:
                if not e100:
                  self.server._plock.release()
              while rrlength > 0:
                b = req.body(min(rrlength, 1048576))
                if b is None:
                  closed = not self._send_err_uc(True)
                if not b:
                  break
                rrlength -= len(b)
                f.write(b)
              b = req.body(1)
              if b and rrlengthm:
                closed = not self._send_err_ptl(True)
              else:
                closed |= not self._send_c(rpath, e, b != b'')
            except FileNotFoundError:
              if e100:
                return self._send_err_nf(None)
              closed = not self._send_err_nf(True)
            except:
              if e100:
                return self._send_err_f(None)
              closed = not self._send_err_f(True)
            finally:
              if f:
                try:
                  f.close()
                except:
                  pass
      else:
        if e100:
          return self._send_err_ni(None)
        closed |= not self._send_err_ni(bool(req.body(1) != b''))
    if e100:
      self.error = True
      return False


class HTTPIServer(TCPIServer):

  def __init__(self, server_address, root_directory=None, recommend_downloading=False, max_upload_size=0, allow_reuse_address=False, dual_stack=True, request_queue_size=128, threaded=False, daemon_thread=False, nssl_context=None, basic_auth=None):
    self.root = os.path.abspath(root_directory or os.getcwd())
    self.recommend_downloading = recommend_downloading
    self.max_upload = max_upload_size
    self.basic_auth = basic_auth
    self._plock = threading.Lock()
    super().__init__(server_address, HTTPRequestHandler, allow_reuse_address, dual_stack, request_queue_size, threaded, daemon_thread, nssl_context)


class HTTPBasicAuthenticator:

  CRYPT = lambda password, salt: hashlib.scrypt(password, salt=salt, n=32768, r=8, p=1, maxmem=50000000, dklen=64)
  SALT = lambda: os.urandom(64)

  def __init__(self):
    self.realms = {}
    self.credentials = {}
    self._cache = weakref.WeakKeyDictionary()

  def __call__(self, rpath, caller, cred=None, mode=1):
    if caller is not None and (c := self._cache.get(caller)) is None:
      self._cache[caller] = c = {}
    rpath = rpath.lower()
    user = None
    while rpath:
      rpath = rpath.rsplit('/', 1)[0] + '/'
      if (r := self.realms.get(rpath)) is not None:
        if cred is None:
          return r
        else:
          if user is None:
            try:
              user = base64.b64decode(cred).decode('utf-8').split(':', 1)[0]
            except:
              return False
          if (shr := self.credentials.get((user, r))) is not None and mode & shr[2] != 0:
            if (h := c.get((cred, shr[0]))) is None:
              if (h := self.__class__.CRYPT(cred, shr[0])) == shr[1]:
                c[(cred, shr[0])] = h
                return True
            elif h == shr[1]:
              return True
      rpath = rpath.rstrip('/')
    return None if cred is None else (user is None)

  def set_realm(self, path='/', name=''):
    if not path.startswith('/'):
      path = '/' + path
    if name is None:
      self.realms.pop(path.rsplit('/', 1)[0].lower() + '/', None)
    else:
      self.realms[path.rsplit('/', 1)[0].lower() + '/'] = name

  def set_credential(self, user, password, realm='', get=True, put=True):
    if password is None or not (get or put):
      self.credentials.pop((user, realm), None)
    else:
      self.credentials[(user, realm)] = ((salt := self.__class__.SALT()), self.__class__.CRYPT(base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')), salt), ((3 if put else 1) if get else 2))


class WebSocketHandler:

  FRAGMENT_FRAME = 1000000
  TYPES_OPCODES = {'text_data': 0x01, 'binary_data': 0x02, 'close': 0x08, 'ping': 0x09, 'pong': 0x0a}
  OPCODES_TYPES = {0x00: 'data', 0x01: 'data', 0x02: 'data', 0x08: 'close', 0x09: 'ping', 0x0a: 'pong'}

  def __init__(self, connection, side='server'):
    self.connection = connection
    if not hasattr(self, 'path'):
      self.path = None
    self.inactive_maxtime = 180
    self.mask = side in ('client', 'c')
    self.text_message_only = False
    self.error = 0
    self.close_received = False
    self.close_sent = False
    self.close_requested = None
    self.close_send_data = False
    self.closed = False
    self.buffer = bytearray()
    self.frame_type = None
    self.frame_length = None
    self.data_length = None
    self.message_type = None
    self.message_data = None
    self.message_ready = False
    self.ping_data = None
    self.pong_data = None
    self.close_data = None
    self.last_reception_time = None
    self.queue_lock = threading.Lock()
    self.ping_lock = threading.Lock()
    self.pending_pings = 0
    self.send_event = threading.Event()
    self.queue = []
    self.received_id = 0
    self.queued_id = 0
    self.sent_id = 0

  def connected_callback(self):
    pass

  def received_callback(self, id, data):
    pass

  def send_event_callback(self):
    pass

  def send_queued_callback(self, id):
    pass

  def sent_callback(self, id):
    pass

  def close_received_callback(self, code, data):
    pass

  def error_callback(self, error):
    pass

  def closed_callback(self):
    pass

  @staticmethod
  def xor32(mask, data):
    ld = len(data)
    if ld <= 1000000:
      l = (ld + 3) // 4
      m = int.from_bytes(mask * l, 'little')
      l *= 4
      return memoryview((int.from_bytes(data, 'little') ^ m).to_bytes(l, 'little'))[:ld]
    else:
      l = 250000
      m = int.from_bytes(mask * l, 'little')
      l = 1000000
      return memoryview(b''.join(((int.from_bytes(data[i:i+1000000], 'little') ^ m).to_bytes(l, 'little')) for i in range(0, ld, 1000000)))[:ld]

  def build_frame(self, type, data):
    if type == 'data':
      if isinstance(data, str):
        data_m = memoryview(data.encode('utf-8'))
        type = 'text_data'
      else:
        try:
          data_m = memoryview(data)
          type = 'binary_data'
        except:
          return None
    else:
      try:
        data_m = memoryview(data)
      except:
        return None
    opc = WebSocketHandler.TYPES_OPCODES.get(type)
    if opc is None:
      return None
    if self.mask:
      mask = os.urandom(4)
    if opc > 0x02:
      if len(data_m) <= 0x7d:
        return (struct.pack('BB4s', 0x80 + opc, 0x80 + len(data_m), mask) + WebSocketHandler.xor32(mask, data_m)) if self.mask else (struct.pack('BB', 0x80 + opc, len(data_m)) + data_m)
      else:
        return None
    data_f = tuple(data_m[i:i+self.FRAGMENT_FRAME] for i in range(0, len(data_m), self.FRAGMENT_FRAME))
    frames = []
    nf = len(data_f)
    fin = 0x00
    for f in range(nf):
      if f == 1:
        opc = 0x00
      if f == nf - 1:
        fin = 0x80
      df = data_f[f]
      if len(df) <= 0x7d:
        frames.append((struct.pack('BB4s', fin + opc, 0x80 + len(df), mask) + WebSocketHandler.xor32(mask, df)) if self.mask else (struct.pack('BB', fin + opc, len(df)) + df))
      elif len(df) <= 0xffff:
        frames.append((struct.pack('!BBH4s', fin + opc, 0xfe, len(df), mask) + WebSocketHandler.xor32(mask, df)) if self.mask else (struct.pack('!BBH', fin + opc, 0x7e, len(df)) + df))
      elif len(df) <= 0x7fffffffffffffff:
        frames.append((struct.pack('!BBQ4s', fin + opc, 0xff, len(df), mask) + WebSocketHandler.xor32(mask, df)) if self.mask else (struct.pack('!BBQ', fin + opc, 0x7f, len(df)) + df))
      else:
        return None
    return frames

  def send_ping(self):
    try:
      self.connection.sendall(self.build_frame('ping', b'ping'))
    except:
      return False
    return True

  def send_pong(self):
    with self.ping_lock:
      ping_data = self.ping_data
      if ping_data is None:
        return False
      self.ping_data = None
    try:
      self.connection.sendall(self.build_frame('pong', ping_data))
    except:
      return False
    return True

  def send_close(self, data=b''):
    try:
      self.connection.sendall(self.build_frame('close', data))
    except:
      return False
    return True

  def send_data(self, frame):
    try:
      self.connection.sendall(frame)
    except:
      return False
    return True

  def get_type(self):
    if len(self.buffer) == 0:
      return False
    self.frame_type = WebSocketHandler.OPCODES_TYPES.get(self.buffer[0] & 0x0f, 'bad')
    return True

  def get_length(self):
    if len(self.buffer) < 2:
      return False
    if self.buffer[1] & 0x7f <= 0x7d:
      self.data_length = self.buffer[1] & 0x7f
      self.frame_length = (2 if self.mask else 6) + self.data_length
    elif self.buffer[1] & 0x7f == 0x7e:
      if len(self.buffer) < 4:
        return False
      self.data_length = struct.unpack('!H', self.buffer[2:4])[0]
      self.frame_length = (4 if self.mask else 8) + self.data_length
    elif self.buffer[1] & 0x7f == 0x7f:
      if len(self.buffer) < 10:
        return False
      self.data_length = struct.unpack('!Q', self.buffer[2:10])[0]
      self.frame_length = (10 if self.mask else 14) + self.data_length
    return True

  def check_mask(self):
    if len(self.buffer) < 2:
      return False
    if self.buffer[1] >> 7 != 1:
      return False
    return True

  def get_data(self):
    if not self.frame_type or not self.frame_length or self.data_length is None:
      return False
    if len(self.buffer) < self.frame_length:
      return False
    if self.frame_type == 'data':
      if self.message_type is None:
        if self.buffer[0] & 0x0f not in (0x01, 0x02):
          return False
        else:
          self.message_type = {0x01: 'text', 0x02: 'binary'}[self.buffer[0] & 0x0f]
          self.message_data = []
      else:
        if self.buffer[0] & 0x0f in (0x01, 0x02):
          self.message_type = {0x01: 'text', 0x02: 'binary'}[self.buffer[0] & 0x0f]
          self.message_data = []
    if self.frame_type != 'data' and (self.buffer[0] >> 7 != 1 or self.data_length > 0x7d):
      return False
    with memoryview(self.buffer) as buff:
      if self.frame_type == 'data':
        dpos = self.frame_length - self.data_length
        self.message_data.append(buff[dpos:self.frame_length] if self.mask else WebSocketRequestHandler.xor32(buff[dpos-4:dpos].tobytes(), buff[dpos:self.frame_length]))
      elif self.frame_type == 'close':
        self.close_data = bytes(buff[2:self.frame_length] if self.mask else WebSocketRequestHandler.xor32(buff[2:6].tobytes(), buff[6:self.frame_length]))
      elif self.frame_type == 'ping':
        self.ping_lock.acquire()
        self.ping_data = bytes(buff[2:self.frame_length] if self.mask else WebSocketRequestHandler.xor32(buff[2:6].tobytes(), buff[6:self.frame_length]))
        self.ping_lock.release()
      elif self.frame_type == 'pong':
        self.pong_data = bytes(buff[2:self.frame_length] if self.mask else WebSocketRequestHandler.xor32(buff[2:6].tobytes(), buff[6:self.frame_length]))
      else:
        return False
    if self.frame_type == 'data' and self.buffer[0] >> 7 == 1:
      self.message_data = b''.join(self.message_data)
      if self.message_type == 'text':
        try:
          self.message_data = self.message_data.decode('utf-8')
        except:
          return False
      self.message_ready = True
    return True

  def purge_frame(self):
    self.frame_type = None
    del self.buffer[0:self.frame_length]
    self.frame_length = None
    self.data_length = None

  def send(self, data, track=False):
    if self.closed or self.close_received or (self.close_requested is not None and not self.close_send_data):
      return False
    frame = self.build_frame('data', data)
    if frame is None:
      return False
    with self.queue_lock:
      qid = self.queued_id
      self.queued_id += 1
      r = self.send_queued_callback(qid) if track else None
      self.queue.extend(frame)
    self.send_event.set()
    return True if r in (None, False) else r

  def close(self, data=b'', once_data_sent=False):
    if isinstance(data, str):
      data = data.encode('utf-8')
    else:
      data = data or b''
    if len(data) <= 0x7d:
      self.close_send_data = once_data_sent
      self.close_requested = data
      self.send_event.set()
      return True
    return False

  def handle_out(self):
    self.send_event.set()
    while not self.closed:
      se = self.send_event.is_set()
      if se:
        self.send_event.clear()
      if self.close_received:
        if self.close_data is None:
          self.close_data = b''
        code = struct.unpack('!H', self.close_data[:2])[0] if len(self.close_data) >= 2 else 1005
        self.close_received_callback(code, self.close_data[2:])
        self.send_close(self.close_data[:2])
        self.close_data = None
        self.closed = True
        break
      if self.error:
        error = struct.pack('!H', self.error)
        self.error_callback(self.error)
        self.send_close(error)
        self.closed = True
        break
      if self.ping_data is not None:
        self.send_pong()
      if self.close_requested is not None and not self.close_send_data:
        self.send_close((struct.pack('!H', 4000) + self.close_requested) if self.close_requested else b'')
        self.close_sent = True
        break
      if se:
        close = self.close_requested is not None and self.close_send_data
        self.send_event_callback()
        if len(self.queue) > 0:
          frame = self.queue.pop(0)
          if not self.send_data(frame):
            self.error = 1002
            continue
          if frame[0] >> 7 :
            self.sent_callback(self.sent_id)
            self.sent_id += 1
        if len(self.queue) > 0:
          self.send_event.set()
        elif close:
          self.close_send_data = False
          continue
      self.ping_lock.acquire()
      while self.pending_pings <= 1:
        rt = (self.pending_pings / 2 + 1) * self.inactive_maxtime / 2 + self.last_reception_time - time.monotonic()
        if rt <= 0:
          self.pending_pings += 1
          self.ping_lock.release()
          self.send_ping()
          self.ping_lock.acquire()
        else:
          break
      if self.pending_pings > 1:
        rt = self.inactive_maxtime / 2
      self.ping_lock.release()
      self.send_event.wait(rt)

  def handle(self):
    self.connected_callback()
    self.last_reception_time = time.monotonic()
    out_handler_thread = threading.Thread(target=self.handle_out)
    out_handler_thread.start()
    if self.FRAGMENT_FRAME <= 0x7d:
      chunk_size = self.FRAGMENT_FRAME + (2 if self.mask else 6)
    elif self.FRAGMENT_FRAME <= 0xffff:
      chunk_size = self.FRAGMENT_FRAME + (4 if self.mask else 8)
    else:
      chunk_size = self.FRAGMENT_FRAME + (10 if self.mask else 14)
    while not self.closed:
      if self.frame_type or not self.buffer:
        t = time.monotonic()
        rt = self.inactive_maxtime + self.last_reception_time - t
        self.connection.settimeout(max(rt, 0))
        chunk = None
        try:
          chunk = self.connection.recv(chunk_size)
        except:
          pass
        if not chunk:
          self.error = 1002
          self.send_event.set()
          break
        with self.ping_lock:
          self.last_reception_time = time.monotonic()
          self.pending_pings = 0
        self.buffer += chunk
      self.get_type()
      if self.frame_type == 'bad':
        self.error = 1002
        self.send_event.set()
        break
      if not self.get_length():
        continue
      if self.mask == self.check_mask():
        self.error = 1002
        self.send_event.set()
        break
      if len(self.buffer) < self.frame_length:
        continue
      if not self.get_data():
        self.error = 1002
        self.send_event.set()
        break
      if self.frame_type == 'close':
        if self.close_sent:
          self.closed = True
        else:
          self.close_received = True
          self.send_event.set()
        break
      elif self.frame_type == 'ping':
        self.send_event.set()
        self.purge_frame()
      elif self.frame_type == 'pong':
        self.purge_frame()
      elif self.frame_type == 'data':
        if self.message_ready:
          if self.text_message_only and self.message_type != 'text':
            self.error = 1003
            self.send_event.set()
            break
          self.received_callback(self.received_id, self.message_data)
          self.received_id += 1
          self.message_data = None
          self.message_ready = False
          self.message_type = None
        self.purge_frame()
    if out_handler_thread.is_alive():
      try:
        out_handler_thread.join()
      except:
        pass
    self.closed = True
    self.closed_callback()


class WebSocketDataStore:

  def __init__(self, incoming_event=None):
    self.outgoing = []
    self.outgoing_lock = threading.RLock()
    self.incoming = []
    self.incoming_text_only = False
    self.before_shutdown = None
    self.outgoing_condition = threading.Condition()
    if isinstance(incoming_event, threading.Event):
      self.incoming_event = incoming_event
    else:
      self.incoming_event = threading.Event()

  def notify_outgoing(self):
    with self.outgoing_condition:
      self.outgoing_condition.notify_all()

  def set_outgoing(self, ind, value, if_different = False):
    with self.outgoing_lock:
      if ind >= len(self.outgoing):
        self.outgoing.extend([(None, None)]*(ind - len(self.outgoing) + 1))
      if not if_different or value != self.outgoing[ind][1]:
        self.outgoing[ind] = ((0 if self.outgoing[ind][0] is None else (self.outgoing[ind][0] + 1)), value)
    self.notify_outgoing()

  def add_outgoing(self, value):
    with self.outgoing_lock:
      self.outgoing.append((0, value))
    self.notify_outgoing()

  def nest_outgoing(self, value):
    with self.outgoing_lock:
      if len(self.outgoing) == 0:
        self.outgoing.append((0, value))
      else:
        self.outgoing.append((0, self.outgoing[-1][1]))
        self.outgoing[-2] = ((0 if self.outgoing[-2][0] is None else (self.outgoing[-2][0] + 1)), value)
    self.notify_outgoing()

  def set_before_shutdown(self, value):
    self.before_shutdown = value

  def add_incoming(self, value):
    self.incoming.append(value)
    self.incoming_event.set()

  def get_incoming(self):
    if self.incoming:
      try:
        return self.incoming.pop(0)
      except:
        return None
    else:
      return None

  def wait_for_incoming_event(self, timeout=None, clear=False):
    if clear:
      self.incoming_event.clear()
    incoming_event = self.incoming_event.wait(timeout)
    if incoming_event:
      self.incoming_event.clear()
      return True
    else:
      return False


class WebSocketServerChannel:

  def __init__(self, path, datastore):
    self.path = path
    self.datastore = datastore
    self.closed = False
    self.handlers = {}


class WebSocketRequestHandler(RequestHandler, WebSocketHandler):

  def __init__(self, request, client_address, server):
    self.channel = None
    WebSocketHandler.__init__(self, request, 'server')
    self.inactive_maxtime = server.inactive_maxtime
    RequestHandler.__init__(self, request, client_address, server)

  def connected_callback(self):
    WebSocketHandler.connected_callback(self)
    if self.channel.datastore is not None:
      self.text_message_only = self.channel.datastore.incoming_text_only

  def received_callback(self, id, data):
    WebSocketHandler.received_callback(self, id, data)
    if not self.channel.closed and self.channel.datastore is not None:
      self.channel.datastore.add_incoming(data)

  def send_event_callback(self):
    WebSocketHandler.send_event_callback(self)
    if self.channel.datastore is None or not self.outgoing:
      return
    self.outgoing = False
    nb_values = len(self.channel.datastore.outgoing)
    for i in range(nb_values):
      if self.close_received:
        break
      if i == len(self.outgoing_seq):
        self.outgoing_seq.append(None)
      try:
        seq_value, data_value = self.channel.datastore.outgoing[i]
      except:
        break
      if seq_value != self.outgoing_seq[i]:
        if data_value is not None:
          self.send(data_value)
        self.outgoing_seq[i] = seq_value

  def send_queued_callback(self, id):
    WebSocketHandler.send_queued_callback(self, id)
    if self.channel.datastore is None:
      qe = threading.Event()
      self.queued_events[id] = qe
      return qe

  def sent_callback(self, id):
    WebSocketHandler.sent_callback(self, id)
    if self.channel.datastore is None:
      qe = self.queued_events.pop(id, None)
      if qe is not None:
        qe.set()

  def error_callback(self, error):
    WebSocketHandler.error_callback(self, error)

  def close_received_callback(self, code, data):
    WebSocketHandler.close_received_callback(self, code, data)

  def closed_callback(self):
    WebSocketHandler.closed_callback(self)

  def handle_other(self, req):
    resp_err_br = \
      'HTTP/1.1 400 Bad Request\r\n' \
      'Content-Length: 0\r\n' \
      'Connection: close\r\n' \
      '\r\n'
    try:
      self.request.sendall(resp_err_br.encode('ISO-8859-1'))
    except:
      pass

  def handle(self):
    if self.server.closed:
      return
    resp_err_nf = \
      'HTTP/1.1 404 File not found\r\n' \
      'Content-Length: 0\r\n' \
      'Connection: close\r\n' \
      '\r\n'
    req = HTTPMessage(self.request)
    if req.method != 'GET' or not req.in_header('Upgrade', 'websocket') or not req.header('Sec-WebSocket-Key'):
      self.handle_other(req)
      return
    path = req.path.lstrip('/').strip()
    with self.server.lock:
      self.channel = self.server.channels.get(path, None) or self.server.channels.get(path.split('?', 1)[0], None)
      if self.channel is not None:
        self.path = path
        if self.channel.datastore is None:
          self.queued_events = {}
        else:
          self.outgoing_seq = []
          self.outgoing = True
        self.channel.handlers[self] = threading.current_thread()
    if self.channel is None:
      try:
        self.request.sendall(resp_err_nf.encode('ISO-8859-1'))
      except:
        pass
      return
    guid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    sha1 = hashlib.sha1((req.header('Sec-WebSocket-Key') + guid).encode('utf-8')).digest()
    ws_acc = base64.b64encode(sha1).decode('utf-8')
    resp= \
      'HTTP/1.1 101 Switching Protocols\r\n' \
      'Upgrade: websocket\r\n' \
      'Connection: Upgrade\r\n' \
      'Sec-WebSocket-Accept: %s\r\n' \
      '\r\n' % (ws_acc)
    try:
      self.request.sendall(resp.encode('ISO-8859-1'))
    except:
      with self.server.lock:
        del self.channel.handlers[self]
      return
    self.headers = req.headers
    WebSocketHandler.handle(self)
    with self.server.lock:
      del self.channel.handlers[self]


class WebSocketIDServer(TCPIDServer):

  def __init__(self, server_address, request_handler_class=WebSocketRequestHandler, allow_reuse_address=False, dual_stack=True, request_queue_size=128, daemon_thread=False, inactive_maxtime=180, nssl_context=None):
    super().__init__(server_address, request_handler_class, allow_reuse_address, dual_stack, request_queue_size, True, daemon_thread, nssl_context)
    self.address = server_address
    self.channels = {}
    self.inactive_maxtime = inactive_maxtime

  def _sendevents_dispatcher(self, channel):
    with channel.datastore.outgoing_condition:
      while not channel.closed:
        for h in channel.handlers:
          h.outgoing = True
          h.send_event.set()
        channel.datastore.outgoing_condition.wait()

  def open(self, path, datastore=None):
    path = path.lstrip('/').strip()
    with self.lock:
      if self.closed:
        return False
      channel = WebSocketServerChannel(path, datastore)
      if self.channels.setdefault(path, channel) is not channel:
        return False
      if channel.datastore is not None:
        t = threading.Thread(target=self._sendevents_dispatcher, args=(channel,), daemon=self.daemon_thread)
        t.start()
    return True

  def _close(self, channel, timeout, block):
    if channel.datastore is not None:
      try:
        channel.datastore.notify_outgoing()
      except:
        pass
    if not self._wait_threads(channel.handlers.values(), timeout):
      with self.lock:
        for h in channel.handlers:
          h.connection.shutclose()
      if block:
        self._wait_threads(channel.handlers.values())
    if not block:
      with self.lock:
        self.threads.remove(threading.current_thread())

  def close(self, path, data=b'', once_data_sent=False, timeout=None, block_on_close=False):
    path = path.lstrip('/').strip()
    with self.lock:
      channel = self.channels.pop(path, None)
      if channel is None or channel.closed:
        return False
      channel.closed = True
      if channel.datastore is not None:
        data = channel.datastore.before_shutdown
        if once_data_sent:
          for h in channel.handlers:
            h.outgoing = True
            h.send_event.set()
      if isinstance(data, str):
        data = data.encode('utf-8')
      else:
        data = data or b''
      data = data[:0x7d]
      for h in channel.handlers:
        h.close(data, once_data_sent)
    if block_on_close:
      self._close(channel, timeout, True)
    else:
      th = threading.Thread(target=self._close, args=(channel, timeout, False), daemon=self.daemon_thread)
      self.threads.add(th)
      th.start()
    return True

  def sendto(self, path, data, handler, track=False):
    path = path.lstrip('/').strip()
    with self.lock:
      channel = self.channels.get(path, None)
      if channel is None or channel.closed:
        return False
    if handler not in channel.handlers:
      return False
    return handler.send(data, track)

  def broadcast(self, path, data):
    path = path.lstrip('/').strip()
    with self.lock:
      channel = self.channels.get(path, None)
      if channel is None or channel.closed:
        return False
      handlers = list(channel.handlers)
    for handler in handlers:
      handler.send(data)

  def _shutdown(self, timeout, block):
    w = self._wait_threads(self.threads, timeout)
    self._server_close()
    if block and not w:
      self._wait_threads(self.threads)

  def shutdown(self, timeout=None, block_on_close=True):
    if timeout is not None:
      t = time.monotonic()
    with self.lock:
      if self.closed:
        return
      self.closed = True
      self.idsocket.close()
      pathes = list(self.channels.keys())
    for path in pathes:
      self.close(path, once_data_sent=False, timeout=timeout, block_on_close=False)
    self.thread.join()
    self.thread = None
    rt = None if timeout is None else timeout + t - time.monotonic()
    if block_on_close:
      self._shutdown(rt, True)
    else:
      th = threading.Thread(target=self._shutdown, args=(rt, False), daemon=self.daemon_thread)
      th.start()


class WebSocketIDAltServer(MixinIDAltServer, WebSocketIDServer):

  pass


class WebSocketIDClient(WebSocketHandler):

  def __new__(cls, channel_address, datastore=None, headers=None, own_address='', connection_timeout=3, daemon_thread=False, inactive_maxtime=180, proxy=None, idsocket_generator=None):
    self = object.__new__(cls)
    self.channel_address = channel_address
    ca_p = urllib.parse.urlsplit(channel_address, allow_fragments=False)
    channel_address = urllib.parse.urlunsplit(ca_p._replace(scheme=ca_p.scheme.replace('ws', 'http')))
    self.path = (ca_p.path + ('?' + ca_p.query if ca_p.query else '')).replace(' ', '%20').lstrip('/').strip()
    self.idsocketgen = idsocket_generator if isinstance(idsocket_generator, IDSocketGenerator) else IDSocketGenerator()
    self.pconnection = [None]
    key = base64.b64encode(os.urandom(16)).decode('utf-8')
    guid = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    sha1 = hashlib.sha1((key + guid).encode('utf-8')).digest()
    ws_acc = base64.b64encode(sha1).decode('utf-8')
    if proxy is not None:
      proxy['tunnel'] = True
    rep = HTTPRequestConstructor(self.idsocketgen, proxy)(channel_address, headers={**({} if headers is None else {k: v for k, v in headers.items() if k.lower() not in {'upgrade', 'connection', 'sec-websocket-version', 'sec-websocket-key'}}), 'Upgrade': 'websocket', 'Connection': 'Upgrade', 'Sec-WebSocket-Version': '13', 'Sec-WebSocket-Key': key}, max_time=connection_timeout, decompress=False, pconnection=self.pconnection, max_redir=0, ip=own_address)
    if rep.code != '101' or not rep.in_header('Upgrade', 'websocket') or rep.header('Sec-WebSocket-Accept') != ws_acc or rep.expect_close or not self.pconnection[0]:
      return None
    self.pconnection[0].settimeout(None)
    return self

  def __init__(self, channel_address, datastore=None, headers=None, own_address='', connection_timeout=3, daemon_thread=False, inactive_maxtime=180, proxy=None, idsocket_generator=None):
    self.idsocket = self.pconnection[0]
    WebSocketHandler.__init__(self, self.idsocket, 'client')
    self.datastore = datastore
    self.daemon_thread = daemon_thread
    if self.datastore is not None:
      self.outgoing_seq = []
      self.outgoing = True
    else:
      self.queued_events = {}
    self.inactive_maxtime = inactive_maxtime
    self.address = self.idsocket.getsockname()
    self.thread = threading.Thread(target=WebSocketHandler.handle, args=(self,), daemon=self.daemon_thread)
    self.thread.start()

  def connected_callback(self):
    WebSocketHandler.connected_callback(self)
    if self.datastore is not None:
      self.text_message_only = self.datastore.incoming_text_only
      t = threading.Thread(target=self._sendevent_dispatcher, daemon=self.daemon_thread)
      t.start()

  def received_callback(self, id, data):
    WebSocketHandler.received_callback(self, id, data)
    if self.datastore is not None:
      self.datastore.add_incoming(data)

  def send_event_callback(self):
    WebSocketHandler.send_event_callback(self)
    if self.datastore is None or not self.outgoing:
      return
    self.outgoing = False
    nb_values = len(self.datastore.outgoing)
    for i in range(nb_values):
      if self.close_received:
        break
      if i == len(self.outgoing_seq):
        self.outgoing_seq.append(None)
      try:
        seq_value, data_value = self.datastore.outgoing[i]
      except:
        break
      if seq_value != self.outgoing_seq[i]:
        if data_value is not None:
          self.send(data_value)
        self.outgoing_seq[i] = seq_value

  def send_queued_callback(self, id):
    WebSocketHandler.send_queued_callback(self, id)
    if self.datastore is None:
      qe = threading.Event()
      self.queued_events[id] = qe
      return qe

  def sent_callback(self, id):
    WebSocketHandler.sent_callback(self, id)
    if self.datastore is None:
      qe = self.queued_events.pop(id, None)
      if qe is not None:
        qe.set()

  def error_callback(self, error):
    WebSocketHandler.error_callback(self, error)

  def close_received_callback(self, code, data):
    WebSocketHandler.close_received_callback(self, code, data)

  def closed_callback(self):
    WebSocketHandler.closed_callback(self)
    try:
      self.idsocket.shutclose()
    except:
      pass
    if self.datastore is not None:
      try:
        self.datastore.notify_outgoing()
      except:
        pass
    self.pconnection = [None]

  def _sendevent_dispatcher(self):
    with self.datastore.outgoing_condition:
      while not self.closed and self.close_requested is None:
        self.outgoing = True
        self.send_event.set()
        self.datastore.outgoing_condition.wait()

  def _close(self, timeout, block):
    if self.datastore is not None:
      try:
        self.datastore.notify_outgoing()
      except:
        pass
    self.thread.join(timeout)
    if self.thread.is_alive():
      self.idsocket.shutclose()
      if block:
        self.thread.join()
    self.thread = None

  def close(self, data=b'', once_data_sent=False, timeout=None, block_on_close=False):
    if self.datastore is not None:
      data = self.datastore.before_shutdown
      if once_data_sent:
        self.outgoing = True
        self.send_event.set()
    if isinstance(data, str):
      data = data.encode('utf-8')
    else:
      data = data or b''
    data = data[:0x7d]
    WebSocketHandler.close(self, data, once_data_sent)
    if block_on_close:
      self._close(timeout, True)
    else:
      th = threading.Thread(target=self._close, args=(timeout, False), daemon=self.daemon_thread)
      th.start()


class WebRTCSignalingServerChannel(WebSocketServerChannel):

  def __init__(self, path):
    super().__init__(path, None)
    self.peers = {}
    self.lock = threading.Lock()

  def register_peer(self, name, handler):
    with self.lock:
      if not name or name in self.peers:
        return False
      m = ':%s=1' % name
      for n, h in self.peers.items():
        h.send(m)
        handler.send(':%s=1' % n)
      self.peers[name] = handler
      return True

  def unregister_peer(self, name):
    with self.lock:
      if (handler := self.peers.pop(name, None)) is None:
        return False
      m = ':%s=0' % name
      for h in self.peers.values():
        h.send(m)
      return True

  def forward(self, name, data):
    if (handler := self.peers.get(name)) is not None:
      handler.send(data)


class WebRTCSignalingRequestHandler(WebSocketRequestHandler):

  WebRTCScript = \
    '"use strict";\r\n' \
    'const Null = {};\r\n' \
    'const SuperBuiltinConstructor = (thisarg, newtarget, target, constructor, ...args) => newtarget ? Reflect.construct(Object.getPrototypeOf(constructor), args, newtarget) : (thisarg instanceof constructor ? thisarg : Reflect.construct(Object.getPrototypeOf(constructor), args, target ?? constructor));\r\n' \
    'const SuperDerivedConstructor = (thisarg, newtarget, target, constructor, ...args) => newtarget ? (args.push(newtarget), Reflect.apply(Object.getPrototypeOf(constructor), undefined, args)) : (thisarg instanceof constructor ? Reflect.apply(Object.getPrototypeOf(constructor), thisarg, args) : (args.push(target ?? constructor), Reflect.apply(Object.getPrototypeOf(constructor), undefined, args)));\r\n' \
    'const Inherits = (child, parent) => (Object.setPrototypeOf(child.prototype, parent.prototype), Object.setPrototypeOf(child, parent), child);\r\n' \
    'const SuperMethod = (constructor, method, thisarg, ...args) => Object.getPrototypeOf(constructor).prototype[method]?.apply(thisarg, args);\r\n' \
    'const WebRTCPeerConnection = Inherits(function constructor(signaler, dest, target) {\r\n' \
    '  dest = encodeURIComponent(dest);\r\n' \
    '  if (dest == signaler.name || ! signaler.peers.has(dest) || signaler.connections.has(dest)) {return Null;}\r\n' \
    '  const connection = SuperBuiltinConstructor(this, new.target, target, constructor, signaler.config);\r\n' \
    '  connection.signaler = signaler;\r\n' \
    '  signaler.connections.set(dest, connection);\r\n' \
    '  connection.dest = dest;\r\n' \
    '  connection.polite = signaler.name < dest;\r\n' \
    '  connection.processingoffer = false;\r\n' \
    '  connection.processinganswer = false;\r\n' \
    '  connection.onnegotiationneeded = connection.onnegotiationneededhandler;\r\n' \
    '  connection.onicecandidate = connection.onicecandidatehandler;\r\n' \
    '  connection.onconnectionstatechange = connection.onconnectionstatechangehandler;\r\n' \
    '  connection.ondatachannel = connection.ondatachannelhandler;\r\n' \
    '  connection.ontrack = connection.ontrackhandler;\r\n' \
    '  return connection;\r\n' \
    '}, RTCPeerConnection);\r\n' \
    'WebRTCPeerConnection.prototype.onnegotiationneededhandler = function () {\r\n' \
    '  this.processingoffer = true;\r\n' \
    '  this.setLocalDescription().then((function () {\r\n' \
    '    this.signaler.sendto(this.localDescription, this.dest);\r\n' \
    '  }).bind(this)).catch(() => null).finally((function () {this.processingoffer=false;}).bind(this));\r\n' \
    '};\r\n' \
    'WebRTCPeerConnection.prototype.onicecandidatehandler = function ({candidate}) {\r\n' \
    '  if (candidate) {this.signaler.sendto(candidate, this.dest);}\r\n' \
    '};\r\n' \
    'WebRTCPeerConnection.prototype.onconnectionstatechangehandler = function () {\r\n' \
    '  this.signaler.onconnectionstatechangehandler?.call(this, this.connectionState);\r\n' \
    '};\r\n' \
    'WebRTCPeerConnection.prototype.ondatachannelhandler = function ({channel}) {\r\n' \
    '  this.signaler.onconnectiondatachannelhandler?.call(this, channel);\r\n' \
    '};\r\n' \
    'WebRTCPeerConnection.prototype.ontrackhandler = function ({tracks, streams}) {\r\n' \
    '  this.signaler.onconnectiontrackhandler?.call(this, tracks, streams);\r\n' \
    '};\r\n' \
    'WebRTCPeerConnection.prototype.close = function () {\r\n' \
    '  SuperMethod(WebRTCPeerConnection, "close", this);\r\n' \
    '  this.signaler.connections.delete(this.dest);\r\n' \
    '};\r\n' \
    'Object.defineProperty(WebRTCPeerConnection.prototype, "infos", {get() {\r\n' \
    '  const l = this.sctp?.transport?.iceTransport?.getSelectedCandidatePair?.()?.local;\r\n' \
    '  return l == undefined ? null : {type: l.type, protocol: l.protocol, address: `${l.address}:${l.port}`};\r\n' \
    '}});\r\n' \
    'Object.defineProperty(WebRTCPeerConnection.prototype, "infos2", {get() {;\r\n' \
    '  return this.getStats().then(function (stats) {;\r\n' \
    '    const l = stats?.get(stats.values().find(({type, selected}) => type == "candidate-pair" && selected)?.localCandidateId);\r\n' \
    '    return l == undefined ? null : {type: l.candidateType, protocol: l.protocol, address: `${l.address}:${l.port}`};\r\n' \
    '  });\r\n' \
    '}});\r\n' \
    'const WebRTCSignaler = Inherits(function constructor(path, name, config, target) {\r\n' \
    '  if (! name) {return Null;}\r\n' \
    '  const url = new URL(path.indexOf(":") >= 0 ? path : "ws://" + path);\r\n' \
    '  if (url.pathname == "/") {url.pathname = "/signaling";}\r\n' \
    '  name = encodeURIComponent(name);\r\n' \
    '  url.search = "?" + name;\r\n' \
    '  const signaler = SuperBuiltinConstructor(this, new.target, target, constructor, url.href);\r\n' \
    '  signaler.name = name;\r\n' \
    '  signaler.config = config;\r\n' \
    '  signaler.peers = new Set();\r\n' \
    '  signaler.connections = new Map();\r\n' \
    '  signaler.onopen = signaler.onopenhandler;\r\n' \
    '  signaler.onmessage = signaler.onmessagehandler;\r\n' \
    '  signaler.onerror = signaler.onerrorhandler;\r\n' \
    '  signaler.onclose = signaler.onclosehandler;\r\n' \
    '  signaler.onpeeradd = signaler.onpeeraddhandler;\r\n' \
    '  signaler.onpeerremove = signaler.onpeerremovehandler;\r\n' \
    '  return signaler;\r\n' \
    '}, WebSocket);\r\n' \
    'WebRTCSignaler.prototype.conconstr = WebRTCPeerConnection;\r\n' \
    'WebRTCSignaler.prototype.sendto = function(data, dest) {\r\n' \
    '  this.send(`${dest}:${this.name}:${JSON.stringify(data)}`);\r\n' \
    '};\r\n' \
    'WebRTCSignaler.prototype.onopenhandler = null;\r\n' \
    'WebRTCSignaler.prototype.onmessagehandler = function ({data}) {\r\n' \
    '  const p = data.indexOf(":");\r\n' \
    '  if (p == 0) {\r\n' \
    '    const name = data.slice(1, -2);\r\n' \
    '    if (data.slice(-1) == "0") {\r\n' \
    '      this.peers.delete(encodeURIComponent(name));\r\n' \
    '      this.onpeerremove?.(name);\r\n' \
    '    } else {\r\n' \
    '      this.peers.add(encodeURIComponent(name));\r\n' \
    '      this.onpeeradd?.(name);\r\n' \
    '    }\r\n' \
    '  } else if (p > 0) {\r\n' \
    '    const sender = data.substring(0, p);\r\n' \
    '    const msg = JSON.parse(data.substring(p + 1));\r\n' \
    '    if ("type" in msg) {\r\n' \
    '      if (msg.type == "offer") {\r\n' \
    '        const connection = this.connections.get(sender) ?? this.connection(decodeURIComponent(sender));\r\n' \
    '        if (! connection || (! connection.polite && (connection.processingoffer || ! (connection.signalingState == "stable" || connection.processinganswer)))) {return;}\r\n' \
    '        connection.setRemoteDescription(msg).then(connection.setLocalDescription.bind(connection)).then(function () {\r\n' \
    '          connection.signaler.sendto(connection.localDescription, sender);\r\n' \
    '        }).catch(() => null);\r\n' \
    '      } else {\r\n' \
    '        const connection = this.connections.get(sender);\r\n' \
    '        if (! connection) {return;}\r\n' \
    '        connection.processinganswer = msg.type == "answer";\r\n' \
    '        connection.setRemoteDescription(msg).catch(() => null).finally((function () {this.processinganswer=false;}).bind(this));\r\n' \
    '      }\r\n' \
    '    } else if ("candidate" in msg)  {\r\n' \
    '      this.connections.get(sender)?.addIceCandidate(msg).catch(() => null);\r\n' \
    '    }\r\n' \
    '  }\r\n' \
    '};\r\n' \
    'WebRTCSignaler.prototype.onerrorhandler = WebRTCSignaler.prototype.onclosehandler = function () {\r\n' \
    '  this.peers.clear();\r\n' \
    '};\r\n' \
    'WebRTCSignaler.prototype.onpeeraddhandler = WebRTCSignaler.prototype.onpeerremovehandler = null;\r\n' \
    'WebRTCSignaler.prototype.connection = function (dest) {\r\n' \
    '  const connection = this.conconstr(this, dest);\r\n' \
    '  return connection == Null ? null : connection;\r\n' \
    '};\r\n' \
    .encode('utf-8')

  def connected_callback(self):
    super().connected_callback()
    self.text_message_only = True
    name = urllib.parse.unquote(self.path.partition('?')[2])
    if self.channel.register_peer(name, self):
      self.name = name
    else:
      self.name = None
      self.close('unavailable')

  def received_callback(self, id, data):
    dest, data = data.partition(':')[::2]
    self.channel.forward(urllib.parse.unquote(dest), data)

  def closed_callback(self):
    super().closed_callback()
    self.channel.unregister_peer(self.name)

  def handle_other(self, req):
    err = resp = rbody = None
    cresp = \
      'Date: %s\r\n' \
      'Server: SocketTB\r\n' \
      'Access-Control-Allow-Origin: %s\r\n' \
      'Access-Control-Expose-Headers: *\r\n' \
      'Access-Control-Allow-Headers: Authorization\r\n' \
      'Access-Control-Allow-Credentials: true\r\n' \
      'Connection: close\r\n' % (email.utils.formatdate(time.time(), usegmt=True), req.header('Origin', '*'))
    if req.method == 'OPTIONS':
      resp = \
        'HTTP/1.1 200 OK\r\n' \
        'Content-Length: 0\r\n' \
        '%s' \
        'Allow: OPTIONS, HEAD, GET\r\n' \
        '\r\n' % cresp
    elif req.method in {'GET', 'HEAD'}:
      if req.path.lower() == '/script.js':
        rbody = self.__class__.WebRTCScript
        resp = \
          'HTTP/1.1 200 OK\r\n' \
          'Content-Length: %d\r\n' \
          '%s' \
          'Content-Type: text/javascript\r\n' \
          '\r\n' % (len(rbody), cresp)
      elif req.path.lower().startswith('/channel?'):
        if self.server.basic_auth:
          cred = req.header('Authorization', '').partition(' ')
          cred = cred[2].strip() if cred[0].lower() == 'basic' else ''
          name = ('/' + req.path[9:].strip('/')).rstrip('/') + '/'
          if (r := self.server.basic_auth(name, self)) is None:
            err = '404 Not found'
          elif cred:
            if self.server.basic_auth(name, self, cred.encode('utf-8'), 1):
              rbody = r.encode('utf-8')
              resp = \
               'HTTP/1.1 200 OK\r\n' \
               'Content-Length: %d\r\n' \
               '%s' \
               'Content-Type: text/plain\r\n' \
               '\r\n' % (len(rbody), cresp)
            else:
              err = '403 Forbidden'
          else:
            resp = \
              'HTTP/1.1 401 Unauthorized\r\n' \
              'Content-Length: 0\r\n' \
              '%s' \
              'WWW-Authenticate: Basic realm="%s", charset="UTF-8"\r\n' \
              '\r\n' % (cresp, name.strip('/'))
        else:
          err = '404 Not found'
      else:
        err = '404 Not found'
    else:
      err = '501 Not implemented'
    if err:
      resp = \
        'HTTP/1.1 %s\r\n' \
        'Content-Length: 0\r\n' \
        '%s' \
        '\r\n' % (err, cresp)
    try:
      self.request.sendall(resp.encode('ISO-8859-1'))
      if rbody is not None and req.method != 'HEAD':
        self.request.sendall(rbody)
    except:
      pass


class WebRTCSignalingServer(WebSocketIDServer):

  def __init__(self, server_address, allow_reuse_address=False, dual_stack=True, request_queue_size=128, daemon_thread=False, inactive_maxtime=180, nssl_context=None, basic_auth=None):
    super().__init__(server_address, request_handler_class=WebRTCSignalingRequestHandler, allow_reuse_address=allow_reuse_address, dual_stack=dual_stack, request_queue_size=request_queue_size, daemon_thread=daemon_thread, inactive_maxtime=inactive_maxtime, nssl_context=nssl_context)
    self.basic_auth = basic_auth

  def _get_path(self, path_name=''):
    if self.basic_auth:
      return None if (path := self.basic_auth(('/' + path_name.strip('/')).rstrip('/').lower() + '/', None)) is None else ('signaling;' + path)
    else:
      return path_name or 'signaling'

  def open(self, path_name=''):
    with self.lock:
      if self.closed or (path := self._get_path(path_name)) is None:
        return False
      channel = WebRTCSignalingServerChannel(path)
      return self.channels.setdefault(path, channel) is channel

  def close(self, path_name='', timeout=None, block_on_close=False):
    return False if (path := self._get_path(path_name)) is None else super().close(path, data=b'end', once_data_sent=True, timeout=timeout, block_on_close=block_on_close)


class WebRTCBasicAuthenticator(HTTPBasicAuthenticator):

  CODE = lambda: os.urandom(18)

  def set_channel(self, name='', add=True):
    name = ('/' + name.strip('/')).rstrip('/').lower() + '/'
    if add:
      self.realms[name] = (code := base64.urlsafe_b64encode(self.__class__.CODE()).decode('utf-8'))
      return code
    else:
      return bool(self.realms.pop(name, None))

  def set_realm(self, path='/', name=''):
    raise NotImplementedError()

  def set_credential(self, user, password, name=''):
    name = ('/' + name.strip('/')).rstrip('/').lower() + '/'
    if (realm := self.realms.get(name)) is None:
      return False
    if password is None:
      return bool(self.credentials.pop((user, realm), None))
    else:
      self.credentials[(user, realm)] = ((salt := self.__class__.SALT()), self.__class__.CRYPT(base64.b64encode(('%s:%s' % (user, password)).encode('utf-8')), salt), 1)
      return True


class HTTPIDownload(_MimeTypes):

  def __new__(cls, url, file='', headers=None, max_workers=8, section_min=1048576, file_preallocate=None, file_sparse=False, timeout=30, max_hlength=1048576, block_size=1048576, retry=None, max_redir=5, unsecuring_redir=False, ip='', basic_auth=None, process_cookies=None, proxy=None, isocket_generator=None, resume=None):
    self = object.__new__(cls)
    self.isocketgen = isocket_generator if isinstance(isocket_generator, ISocketGenerator) else ISocketGenerator()
    self.url = url
    try:
      if resume:
        if isinstance(resume, cls):
          resume = resume.progress
        if resume['status'] != 'aborted':
          return None
        if 'sections' not in resume:
          resume['sections'] = sorted((sec for work in resume['workers'] for sec in work), key=lambda sec: sec['start'])
        self._workers = [[sec['start'] + sec['downloaded'], sec['size'] - sec['downloaded'], True] for sec in resume.get('sections', ()) if sec['status'] == 'aborted']
        if not self._workers:
          return None
        self._progress = {'status': 'waiting', 'size': resume['size'], 'downloaded': resume['downloaded'], 'percent': resume['percent'], 'error': False, 'workers': [*([sec | {'status': 'waiting'}] for sec in resume['sections'] if sec['status'] == 'aborted'), *filter(None, ([sec.copy() for sec in resume['sections'] if sec['status'] == 'completed'],))], 'eventing': {'condition': threading.Condition(), 'status': False, 'progression': False, 'workers': False}}
      else:
        self._progress = {'status': 'waiting', 'size': 0, 'downloaded': 0, 'percent': 0, 'error': False, 'workers': [], 'eventing': {'condition': threading.Condition(), 'status': False, 'progression': False, 'workers': False}}
      self.headers = {k: v for k, v in (((k_.strip(), v_) for k_, v_ in headers.items()) if isinstance(headers, dict) else ((k_.strip(), v_.strip()) for k_, v_ in (e.split(':', 1) for e in (headers or '').splitlines() if ':' in e))) if k.lower() not in ('host', 'accept-encoding', 'te')}
    except:
      return None
    if any(k.lower() == 'range' for k in self.headers):
      return None
    self.headers['Accept-Encoding'] = 'identity'
    self.headers['TE'] = ('identity, deflate, gzip, zstd, br' if zstd else 'identity, deflate, gzip, br') if brotli else ('identity, deflate, gzip, zstd' if zstd else 'identity, deflate, gzip')
    try:
      file = os.fsdecode(file)
    except:
      pass
    self._file_fz = False
    if isinstance(file, str):
      path = os.path.abspath(os.path.expandvars(file))
      if os.path.isdir(path):
        file = os.path.normpath(os.path.join(path, os.path.basename(urllib.parse.urlsplit(url).path.split(';', 1)[0]).lstrip('\\')))
        if os.path.commonpath((path, file)) != path or os.path.basename(file) in ('', '.', '..'):
          return None
      elif os.path.basename(file) in ('', '.', '..'):
        return None
      else:
        file = path
      try:
        self.file = open(file, ('r+b' if resume else 'wb'))
        self._close = True
      except:
        return None
    elif isinstance(file, int):
      try:
        self.file = open(file, ('r+b' if resume else 'wb'), closefd=False)
        self.file.seek(0, os.SEEK_SET)
        self._close = True
      except:
        return None
    else:
      try:
        if not file.seekable() or not file.writable():
          return None
        file.seek(0, os.SEEK_SET)
        if not resume:
          file.truncate(0)
      except:
        return None
      self.file = file
      self._close = False
    if not resume:
      h = None
      if file_preallocate is None:
        try:
          h = get_osfhandle(self.file.fileno())
          file_preallocate = True
        except:
          pass
      if file_preallocate:
        self._file_fz = 1
      if file_sparse:
        br = DWORD()
        try:
          if kernel32.DeviceIoControl(HANDLE(get_osfhandle(self.file.fileno()) if h is None else h), DWORD(590020), None, DWORD(0), None, DWORD(0), byref(br), None) and file_preallocate:
            self._file_fz = 2
        except:
          pass
    self._file = self.file
    self._bsize = math.ceil(max(block_size, 1024))
    self._maxworks = math.floor(max(max_workers, 1))
    self._secmin = math.ceil(max(section_min, 1024))
    self._req = lambda h, r=HTTPRequestConstructor(self.isocketgen, proxy): r(url, headers=h, timeout=timeout, max_length=-1, max_hlength=max_hlength, decompress=True, retry=retry, max_redir=max_redir, unsecuring_redir=unsecuring_redir, ip=ip, basic_auth=basic_auth, process_cookies=process_cookies)
    self._threads = []
    self._lock = threading.Lock()
    self._flock = threading.Lock()
    return self

  @property
  def progress(self):
    with self._progress['eventing']['condition']:
      return {'status': self._progress['status']} if self._progress['status'] in ('waiting', 'starting') else ({**{k: v for k, v in self._progress.items() if k != 'eventing'}, 'sections': sorted((sec for work in self._progress['workers'] for sec in work), key=lambda sec: sec['start'])} if hasattr(self, '_condition') else {k: v for k, v in self._progress.items() if k not in ('workers', 'eventing')})

  def _nsection(self, w=None, restart=False):
    if restart:
      start = self._workers[w][0]
    else:
      with self._lock:
        if self._req is None:
          return False
        work = None
        sec = None
        size = 0
        for w_, work_ in enumerate(self._workers):
          if work_[2] is True:
            work = work_
            sec = self._progress['workers'][w_][0]
            size = work_[1]
            break
          if w_ == w:
            continue
          size_ = work_[1] - self._bsize
          if size_ >= max(size, 2 * self._secmin):
            work = work_
            sec = self._progress['workers'][w_][0]
            size = size_
        else:
          if work is None:
            return False
          size //= 2
          w_ += 1
        start = work[0] + work[1] - size
    h = {**self.headers, 'Range': 'bytes=%d-' % start}
    try:
      rep = self._req(h)
      if rep.code not in ('200', '206'):
        if work[2] is True and  w_ == 0:
          if self._req is not None:
            with self._progress['eventing']['condition']:
              self._progress['error'] = rep.code or True
        return False
      if rep.header('Content-Encoding') or (rep.header('Accept-Ranges', 'none').lower() != 'bytes' and rep.header('Content-Range', '').split(' ')[0].strip().lower() != 'bytes') or int(rep.header('Content-Range', '').rpartition(' ')[2].split('/', 1)[0].split('-', 1)[0]) != start:
        return False
    except:
      return False
    if restart:
      return rep
    with self._lock:
      if self._req is None:
        return False
      if work[2] is not True:
        if start - work[0] - self._bsize < self._secmin:
          return False
        work[1] -= size
      if w is None:
        th = threading.Thread(target=self._read, args=(w_, rep))
        self._threads.append(th)
        with self._progress['eventing']['condition']:
          if work[2] is True:
            work[2] = threading.Semaphore()
            if w_ == 0:
              self._progress['status'] = 'working (split: yes)'
              self._progress['eventing']['status'] = True
              self._progress['eventing']['progression'] = True
            sec['status'] = 'running'
          else:
            self._workers.append([start, size, threading.Semaphore()])
            sec['size'] -= size
            sec['percent'] = math.floor(sec['downloaded'] / sec['size'] * 100)
            self._progress['workers'].insert(w_, [{'status': 'running', 'start': start, 'size': size, 'downloaded': 0, 'percent': 0}])
          self._progress['eventing']['workers'] = True
          self._progress['eventing']['condition'].notify_all()
        th.start()
        return True
      else:
        self._workers[w][0:2] = start, size
        with self._progress['eventing']['condition']:
          if work[2] is True:
            del self._workers[w_]
            del self._progress['workers'][w_]
            sec['status'] = 'running'
            self._progress['workers'][w].insert(0, sec)
          else:
            sec['size'] -= size
            sec['percent'] = math.floor(sec['downloaded'] / sec['size'] * 100)
            self._progress['workers'][w].insert(0, {'status': 'running', 'start': start, 'size': size, 'downloaded': 0, 'percent': 0})
          self._progress['eventing']['workers'] = True
          self._progress['eventing']['condition'].notify_all()
        return rep

  def _write(self):
    err = False
    while True:
      with self._condition:
        while not self._pending:
          if self._file is None:
            return
          self._condition.wait()
        sem, start, b, sec = self._pending.popleft()
        with self._lock:
          if self._file is None:
            return
          end = sem is None and not any(work[2] for work in self._workers) and not self._pending
      if sem is None:
        if end:
          self.stop(False)
          return
        continue
      with self._flock:
        if self._file is None:
          return
        try:
          self._file.seek(start, os.SEEK_SET)
          self._file.write(b)
        except:
          err = True
          break
        with self._progress['eventing']['condition']:
          notif = False
          self._progress['downloaded'] += len(b)
          p = self._progress['percent']
          self._progress['percent'] = math.floor(self._progress['downloaded'] / self._progress['size'] * 100)
          if p != self._progress['percent']:
            self._progress['eventing']['progression'] = True
            notif = True
          sec['downloaded'] += len(b)
          p = sec['percent']
          sec['percent'] = math.floor(sec['downloaded'] / sec['size'] * 100)
          if p != sec['percent']:
            self._progress['eventing']['workers'] = True
            notif = True
          if sec['size'] == sec['downloaded']:
            sec['status'] = 'completed'
            self._progress['eventing']['workers'] = True
            notif = True
          if notif:
            self._progress['eventing']['condition'].notify_all()
      sem.release()
    if err:
      with self._progress['eventing']['condition']:
        self._progress['error'] = self._progress['error'] or True
      self.stop(False)

  def _read(self, w, rep):
    work = self._workers[w]
    while True:
      with self._progress['eventing']['condition']:
        sec = self._progress['workers'][w][0]
      while True:
        with self._lock:
          if self._req is None:
            return
          r = min(self._bsize, work[1])
        if r <= 0:
          try:
            rep.body(-1)
          except:
            pass
          break
        work[2].acquire()
        with self._lock:
          if self._req is None:
            return
        try:
          b = rep.body(r)
          l = len(b)
          if not l:
            raise
        except:
          with self._lock:
            if self._req is None:
              return
            with self._progress['eventing']['condition']:
              sec['status'] = 'recovering'
              self._progress['eventing']['workers'] = True
              self._progress['eventing']['condition'].notify_all()
          work[2].release()
          rep = None
          while not rep:
            with self._slock:
              with self._lock:
                if self._req is None:
                  return
              rep = self._nsection(w, True)
          with self._lock:
            if self._req is None:
              return
            with self._progress['eventing']['condition']:
              sec['status'] = 'running'
              self._progress['eventing']['workers'] = True
              self._progress['eventing']['condition'].notify_all()
          continue
        with self._condition:
          if self._req is None:
            return
          self._pending.append((work[2], work[0], b, sec))
          self._condition.notify()
          with self._lock:
            work[0] += l
            work[1] -= l
      with self._slock:
        rep = self._nsection(w)
      if not rep:
        break
    with self._condition:
      work[2] = None
      self._pending.append((None, None, None, None))
      self._condition.notify()

  def _sdown(self, rep):
    try:
      while True:
        with self._lock:
          if self._req is None:
            return False
        b = rep.body(self._bsize)
        with self._lock:
          if self._req is None:
            return False
        if b is None:
          raise
        if not b:
          with self._progress['eventing']['condition']:
            if not self._progress['size']:
              self._progress['size'] = self._progress['downloaded']
              self._progress['percent'] = 100
              self._progress['eventing']['progression'] = True
              self._progress['eventing']['condition'].notify_all()
          break
        with self._flock:
          self._file.write(b)
          with self._progress['eventing']['condition']:
            if self._progress['size']:
              self._progress['downloaded'] += len(b)
              p = self._progress['percent']
              self._progress['percent'] = min(math.floor(self._progress['downloaded'] / self._progress['size'] * 100), 100)
              if p != self._progress['percent']:
                self._progress['eventing']['progression'] = True
                self._progress['eventing']['condition'].notify_all()
            else:
              d = self._progress['downloaded']
              self._progress['downloaded'] += len(b)
              if d // self._bsize != self._progress['downloaded'] // self._bsize:
                self._progress['eventing']['progression'] = True
                self._progress['eventing']['condition'].notify_all()
    except:
      if self._req is not None:
        with self._progress['eventing']['condition']:
          self._progress['error'] = self._progress['error'] or True
    finally:
      self.stop(False)

  def _fill_zero(self, size):
    with self._flock:
      if self._file is not None and size:
        try:
          h = HANDLE(get_osfhandle(self._file.fileno()))
        except:
          h = None
        try:
          if h is not None and not kernel32.SetFilePointerEx(h, LARGE_INTEGER(size), None, DWORD(0)) or not kernel32.SetEndOfFile(h) or not kernel32.SetFilePointerEx(h, LARGE_INTEGER(0), None, DWORD(0)):
            return False
          if self._file_fz == 1:
            self._file.seek(0, os.SEEK_SET)
            b = b'0' * 1048576
            for i in range(size // 1048576):
              self._file.write(b)
            size %= 1048576
            if size:
              self._file.write(memoryview(b)[:size])
            self._file.seek(0, os.SEEK_SET)
        except:
          return False
    return True

  def _start(self):
    if hasattr(self, '_workers'):
      section = True
      rep = None
    else:
      h = {**self.headers, 'Range': 'bytes=0-'}
      try:
        rep = self._req(h)
        section = None
        if rep.code in ('200', '206'):
          if rep.header('Content-Encoding'):
            size = 0
            section = False
          else:
            size = int(rep.header('Content-Length', 0))
            if rep.header('Accept-Ranges', 'none').lower() == 'bytes' or rep.header('Content-Range', '').split(' ')[0].strip().lower() == 'bytes':
              if not size:
                try:
                  size = int(rep.header('Content-Range', '').rpartition('/')[2])
                except:
                  pass
              section = bool(size)
            if not section:
              section = rep.header('Transfer-Encoding', 'chunked').lower() == 'chunked' and self.__class__._encode_mimetype(rep.header('Content-Type', 'application/octet-stream').split(';', 1)[0].rstrip()) and (not size or size > 4 * self._secmin) and None
        if section is None:
          try:
            rep.body(-1)
          except:
            pass
          h = self.headers
          h['Accept-Encoding'] = h['TE']
          rep = self._req(h)
          if rep.code != '200':
            if self._req is not None:
              with self._progress['eventing']['condition']:
                self._progress['error'] = rep.code or True
            raise
          size = 0 if rep.header('Content-Encoding') else int(rep.header('Content-Length', 0))
          section = False
      except:
        if self._req is not None:
          with self._progress['eventing']['condition']:
            self._progress['error'] = self._progress['error'] or True
        self.stop(False)
        return
      with self._progress['eventing']['condition']:
        self._progress['size'] = size
    if section:
      with self._lock:
        if self._req is None:
          return
        self._pending = deque()
        self._condition = threading.Condition()
        self._slock = threading.Lock()
        if rep is not None:
          self._workers = []
        th = threading.Thread(target=self._write)
        self._threads.append(th)
        th.start()
      with self._slock:
        with self._lock:
          if self._req is None:
            return
          if rep is not None:
            th = threading.Thread(target=self._read, args=(0, rep))
            self._threads.append(th)
            self._workers.append([0, size, threading.Semaphore()])
            with self._progress['eventing']['condition']:
              self._progress['status'] = 'working (split: yes)'
              self._progress['eventing']['status'] = True
              self._progress['eventing']['progression'] = True
              self._progress['workers'].append([{'status': 'running', 'start': 0, 'size': size, 'downloaded': 0, 'percent': 0}])
              self._progress['eventing']['workers'] = True
              self._progress['eventing']['condition'].notify_all()
            if self._file_fz and not self._fill_zero(size):
              self._file_fz = None
            if self._file_fz is not None:
              th.start()
        if self._file_fz is not None:
          for w in range((0 if rep is None else 1), self._maxworks):
            if not self._nsection():
              if w == 0:
                if self._req is not None:
                  with self._progress['eventing']['condition']:
                    self._progress['error'] = self._progress['error'] or True
                self.stop(False)
              break
    else:
      with self._lock:
        if self._req is None:
          return
        with self._progress['eventing']['condition']:
          self._progress['status'] = 'working (split: no)'
          self._progress['eventing']['status'] = True
          self._progress['eventing']['progression'] = True
          self._progress['eventing']['condition'].notify_all()
        th = threading.Thread(target=self._sdown, args=(rep,))
        self._threads.append(th)
        if self._file_fz and not self._fill_zero(size):
          self._file_fz = None
        if self._file_fz is not None:
          th.start()
    if self._file_fz is None:
      with self._progress['eventing']['condition']:
        self._progress['error'] = self._progress['error'] or True
      self.stop(False)
      return

  def start(self):
    with self._lock:
      if self._req is None or self._file is None or self._threads:
        return
      with self._progress['eventing']['condition']:
        self._progress['status'] = 'starting'
        self._progress['eventing']['status'] = True
        self._progress['eventing']['condition'].notify_all()
      th = threading.Thread(target=self._start)
      self._threads.append(th)
      th.start()

  def stop(self, block_on_close=True):
    with self._lock:
      if self._req is None:
        return
      self._req = None
      self.isocketgen.close()
      with self._flock:
        try:
          if self._close:
            self._file.close()
        except:
          pass
        finally:
          self._file = None
      with self._progress['eventing']['condition']:
        for work in self._progress['workers']:
          for sec in work:
            if sec['status'] != 'completed':
              sec['status'] = 'aborted'
        self._progress['eventing']['workers'] = True
        if (self._progress['size'] or self._progress['percent'] == 100) and self._progress['size'] <= self._progress['downloaded']:
          self._progress['status'] = 'completed'
        else:
          self._progress['status'] = 'aborted'
        self._progress['eventing']['status'] = True
        self._progress['eventing']['condition'].notify_all()
    if hasattr(self, '_condition'):
      with self._condition:
        self._condition.notify()
      for work in self._workers:
        sem = work[2]
        if sem is not None and sem is not True:
          sem.release()
    if block_on_close:
      for th in self._threads:
        th.join()

  def progress_bar(self, length=100):
    with self._progress['eventing']['condition']:
      if self._progress['status'] == 'completed':
        return '█' * length
      elif hasattr(self, '_condition'):
        cs = cb = 0
        return ''.join('█' * (b := math.floor(sec['downloaded'] * (bl := (-cb + (cb := round(length * (cs := cs + sec['size']) / self.progress['size'])))) / sec['size'])) + '░' * (bl - b) for sec in self.progress['sections'])
        pass
      elif self._progress['size']:
        return '█' * (b := min(math.floor(self._progress['downloaded'] * length / self._progress['size']), length)) + '░' * (length - b)
      else:
        return ''

  def wait_finish(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'}), timeout)
      self._progress['eventing']['status'] = False
      return self._progress['status']

  def wait_progression(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'} or self._progress['eventing']['progression']), timeout)
      self._progress['eventing']['progression'] = False
      return '%d%%' % self._progress['percent'] if self._progress['size'] or self._progress['status'] == 'completed' else '%s o' % format(self._progress['downloaded'], 'n')

  def wait_workers(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted', 'working (split: no)'} or self._progress['eventing']['workers']), timeout)
      self._progress['eventing']['workers'] = False
      return self._progress['workers']

  def wait_sections(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted', 'working (split: no)'} or self._progress['eventing']['workers']), timeout)
      self._progress['eventing']['workers'] = False
      return self.progress.get('sections', [])

  def wait_progress_bar(self, length=100, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'} or self._progress['eventing']['progression'] or self._progress['eventing']['workers']), timeout)
      self._progress['eventing']['progression'] = False
      self._progress['eventing']['workers'] = False
      return '%s %3d%%' % (self.progress_bar(length), self._progress['percent']) if self._progress['size'] or self._progress['status'] == 'completed' else '%s o' % format(self._progress['downloaded'], 'n')

  def __enter__(self):
    self.start()
    return self

  def __exit__(self, et, ev, tb):
    self.stop()

  def __repr__(self):
    return '\r\n'.join(('<HTTPIDownload at %#x>\r\n----------' % id(self), 'Url: ' + self.url, *('%s: %s' % (k.title(), v) for k, v in self.progress.items() if k not in ('workers', 'sections'))))


class HTTPIListDownload:

  def __new__(cls, urls, files='', max_downloads=4, headers=None, max_workers=8, section_min=None, timeout=30, max_hlength=1048576, block_size=1048576, retry=None, max_redir=5, unsecuring_redir=False, ip='', basic_auth=None, process_cookies=None, proxy=None):
    if not len(urls):
      return None
    self = object.__new__(cls)
    self.urls = urls
    self._maxdwnlds = math.floor(max(max_downloads, 1))
    try:
      files = os.fsdecode(files)
    except:
      pass
    if isinstance(files, str):
      if not os.path.isdir(os.path.abspath(os.path.expandvars(files))):
        return None
      files = (files,) * len(urls)
    try:
      if len(files) < len(urls):
        return None
      self.idownloads = tuple(HTTPIDownload(url, file, headers, max_workers, section_min, timeout, max_hlength, block_size, retry, max_redir, unsecuring_redir, ip, basic_auth, process_cookies, proxy) for url, file in zip(urls, files))
    except:
      return None
    self._threads = []
    self._lock = threading.Lock()
    self._progress = {'status': 'waiting', 'number': len(urls), 'running': 0, 'completed': 0, 'aborted': 0, 'eventing': {'condition': threading.Condition(), 'status': False, 'processed': False}}
    return self

  @property
  def progress(self):
    with self._progress['eventing']['condition']:
      return {'status': self._progress['status']} if self._progress['status'] == 'waiting' else ({**{k: v for k, v in self._progress.items() if k != 'eventing'}, 'downloads': tuple(idownload.progress if idownload else None for idownload in self.idownloads)})

  def _download(self):
    while True:
      with self._lock:
        if not self._maxdwnlds:
          return
        with self._progress['eventing']['condition']:
          d = sum(self._progress[st] for st in ('running', 'completed', 'aborted'))
          if d >= len(self.urls):
            break
          idownload = self.idownloads[d]
          if idownload:
            idownload.start()
            self._progress['running'] += 1
            self._progress['eventing']['processed'] = True
            self._progress['eventing']['condition'].notify_all()
          else:
            self._progress['aborted'] += 1
            self._progress['eventing']['processed'] = True
            self._progress['eventing']['condition'].notify_all()
            continue
      st = idownload.wait_finish()
      with self._progress['eventing']['condition']:
        self._progress[st] += 1
        self._progress['running'] -= 1
        self._progress['eventing']['processed'] = True
        self._progress['eventing']['condition'].notify_all()
    with self._progress['eventing']['condition']:
      end = self._progress['running'] == 0
    if end:
      self.stop(False)

  def _start(self):
    for d in range(min(len(self.urls), self._maxdwnlds)):
      with self._lock:
        if not self._maxdwnlds:
          return
        th = threading.Thread(target=self._download)
        self._threads.append(th)
        th.start()

  def start(self):
    with self._lock:
      if not self._maxdwnlds or self._threads:
        return
      with self._progress['eventing']['condition']:
        self._progress['status'] = 'running'
        self._progress['eventing']['status'] = True
        self._progress['eventing']['condition'].notify_all()
      th = threading.Thread(target=self._start)
      self._threads.append(th)
      th.start()

  def stop(self, block_on_close=True):
    with self._lock:
      if not self._maxdwnlds:
        return
      self._maxdwnlds = 0
      for idownload in self.idownloads:
        if idownload:
          idownload.stop(block_on_close)
      with self._progress['eventing']['condition']:
        self._progress['running'] = 0
        self._progress['completed'] = 0
        self._progress['aborted'] = 0
        for idownload in self.idownloads:
          if idownload:
            idownload.stop(block_on_close)
            self._progress[idownload.wait_finish()] += 1
          else:
            self._progress['aborted'] += 1
        self._progress['eventing']['processed'] = True
        self._progress['status'] = 'completed' if self._progress['number'] == self._progress['completed'] else 'aborted'
        self._progress['eventing']['status'] = True
        self._progress['eventing']['condition'].notify_all()
    if block_on_close:
      for th in self._threads:
        th.join()

  def wait_finish(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'}), timeout)
      self._progress['eventing']['status'] = False
      return self._progress['status']

  def wait_progression(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'} or self._progress['eventing']['processed']), timeout)
      self._progress['eventing']['processed'] = False
      return {k: self._progress[k] for k in ('number', 'running', 'completed', 'aborted')}


class HTTPIUpload(_MimeTypes):

  class _Compressor:
    def __init__(self, file, length, comp):
      self.file = file
      self.length = length
      self.comp = comp
      self.bbuf = ssl.MemoryBIO()
    def read(self, size):
      while self.bbuf.pending < size:
        if self.length == 0:
          break
        try:
          b = self.file.read(min(self.length, 1048576))
        except:
          b = b''
        if b:
          self.length -= len(b)
          self.bbuf.write(self.comp.compress(b))
        else:
          self.length = 0
        if self.length == 0:
          self.bbuf.write(self.comp.flush())
      return self.bbuf.read(size)

  class _Reader:
    def __init__(self, data, progress):
      self._data = data
      self._progress = progress
      self._read = 0
    def read(self, size):
      with self._progress['eventing']['condition']:
        if self._progress['size']:
          self._progress['uploaded'] = self._read
          p = self._progress['percent']
          self._progress['percent'] = min(math.floor(self._progress['uploaded'] / self._progress['size'] * 100), 100)
          if p != self._progress['percent']:
            self._progress['eventing']['progression'] = True
            self._progress['eventing']['condition'].notify_all()
        else:
          u = self._progress['uploaded']
          self._progress['uploaded'] = self._read
          if u // 1048576 != self._progress['uploaded'] // 1048576:
            self._progress['eventing']['progression'] = True
            self._progress['eventing']['condition'].notify_all()
      b = self._data.read(size)
      if b:
        self._read += len(b)
      return b

  def __new__(cls, url, data=None, headers=None, file_range=None, file_compress=None, timeout=30, max_hlength=1048576, retry=None, max_redir=5, unsecuring_redir=False, expect_100=True, ip='', basic_auth=None, process_cookies=None, proxy=None, isocket_generator=None):
    self = object.__new__(cls)
    self.isocketgen = isocket_generator if isinstance(isocket_generator, ISocketGenerator) else ISocketGenerator()
    self.url = url
    hitems = tuple(((k.strip(), v) for k, v in headers.items()) if isinstance(headers, dict) else ((k.strip(), v.strip()) for k, v in (e.split(':', 1) for e in (headers or '').splitlines() if ':' in e)))
    try:
      self.headers = {k: v for k, v in hitems if k.lower() not in {'host', 'accept-encoding', 'te', 'content-length', 'content-encoding', 'transfer-encoding', 'range', 'expect'}} if isinstance(data, (str, int)) else {k: v for k, v in hitems if k.lower() not in {'host', 'accept-encoding', 'te', 'expect'}}
      if expect_100:
        self.headers['Expect'] = '100-continue'
    except:
      return None
    self._req = lambda r=HTTPRequestConstructor(self.isocketgen, proxy): r(url, 'PUT', headers=self.headers, data=self._data, timeout=timeout, max_hlength=max_hlength, decompress=False, retry=retry, max_redir=max_redir, unsecuring_redir=unsecuring_redir, ip=ip, basic_auth=basic_auth, process_cookies=process_cookies)
    self._lock = threading.Lock()
    self._thread = None
    self._progress = {'status': 'waiting', 'size': 0, 'uploaded': 0, 'percent': 0, 'error': False, 'eventing': {'condition': threading.Condition(), 'status': False, 'progression': False}}
    self._file = None
    if url.endswith('/'):
      self._data = None
      return self
    if data is None:
      return None
    if isinstance(data, str):
      path = os.path.abspath(os.path.expandvars(data))
      if os.path.isdir(path):
        data = os.path.normpath(os.path.join(path, os.path.basename(urllib.parse.urlsplit(url).path.split(';', 1)[0]).lstrip('\\')))
        if os.path.commonpath((path, data)) != path or os.path.basename(data) in ('', '.', '..'):
          return None
      elif os.path.basename(data) in ('', '.', '..'):
        return None
      else:
        data = path
      try:
        self._file = open(data, 'rb')
      except:
        return None
      if 'content-type' not in (k.lower() for k, v in hitems):
        self.headers['Content-Type'] = cls._mimetypes.guess_type(data, strict=False)[0] or 'application/octet-stream'
    elif isinstance(data, int):
      try:
        self._file = open(data, 'rb', closefd=False)
      except:
        return None
    elif hasattr(data, 'read'):
      try:
        if not data.readable():
          return None
      except:
        return None
      try:
        if data.seekable():
          s = data.tell()
          data.seek(0, os.SEEK_END)
          self._progress['size'] = data.tell() - s
          data.seek(s, os.SEEK_SET)
      except:
        pass
      self._data = cls._Reader(data, self._progress)
    else:
      try:
        self._progress['size'] = len(data)
      except:
        return None
      self._data = data
    if isinstance(data, (str, int)):
      fsize = os.stat(self._file.fileno()).st_size
      try:
        if file_range is None:
          rrange = (0, fsize)
        else:
          rrange = ((file_range[0] if file_range[0] >= 0 else fsize + file_range[0]), (fsize if file_range[1] is None else (file_range[1] if file_range[1] >= 0 else fsize + file_range[1]) + 1))
          if rrange[0] < 0 or rrange[0] > rrange[1] or rrange[1] > fsize:
            raise
          self.headers['Range'] = 'bytes=%d-%d' % (rrange[0], rrange[1] - 1)
        self._file.seek(rrange[0], os.SEEK_SET)
      except:
        try:
          self._file.close()
        except:
          pass
        return None
      if file_compress is not None:
        file_compress = file_compress.lower()
        mt = 'application/octet-stream'
        for k, v in self.headers.items():
          if k.lower() == 'content-type':
            mt = v
        comp = None
        if cls._encode_mimetype(mt):
          if file_compress == 'deflate':
            comp = zlib.compressobj(wbits=15)
          elif file_compress == 'gzip':
            comp = zlib.compressobj(wbits=31)
          elif file_compress == 'zstd':
            comp = zstd.ZstdCompressor(level=9)
          elif file_compress == 'br':
            comp = _brotli.compressobj()
        if comp:
          self.headers['Content-Encoding' if file_range is None else 'Transfer-Encoding'] = file_compress
        else:
          file_compress = None
      if file_compress is None:
        self.headers['Content-Length'] = rrange[1] - rrange[0]
        self._data = cls._Reader(self._file, self._progress)
      else:
        self._data = cls._Compressor(cls._Reader(self._file, self._progress), rrange[1] - rrange[0], comp)
      self._progress['size'] = rrange[1] - rrange[0]
    return self

  @property
  def progress(self):
    with self._progress['eventing']['condition']:
      return {'status': self._progress['status'], 'size': self._progress['size']} if self._progress['status'] == 'waiting' else {k: v for k, v in self._progress.items() if k != 'eventing'}

  def _start(self):
    rep = None
    try:
      rep = self._req()
    except:
      pass
    finally:
      with self._progress['eventing']['condition']:
        r = isinstance(self._data, self.__class__._Reader)
        if r:
          self._progress['uploaded'] = self._data._read
        if rep and rep.code and rep.code.startswith('2'):
          self._progress['status'] = 'completed'
          if r:
            self._progress['size'] = self._progress['uploaded']
          else:
            self._progress['uploaded'] = self._progress['size']
          self._progress['percent'] = 100
        else:
          self._progress['status'] = 'aborted'
          if self._req is not None:
            self._progress['error'] = (rep and rep.code) or True
        self._progress['eventing']['status'] = True
        self._progress['eventing']['progression'] = True
        self._progress['eventing']['condition'].notify_all()
      self.stop(False)

  def start(self):
    with self._lock:
      if self._req is None:
        return
      self._thread = threading.Thread(target=self._start)
      with self._progress['eventing']['condition']:
        self._progress['status'] = 'working'
        self._progress['eventing']['status'] = True
        self._progress['eventing']['progression'] = True
        self._progress['eventing']['condition'].notify_all()
      self._thread.start()

  def stop(self, block_on_close=True):
    with self._lock:
      if self._req is None:
        return
      self._req = None
      self.isocketgen.close()
      if self._thread is None:
        with self._progress['eventing']['condition']:
          self._progress['status'] = 'aborted'
          self._progress['eventing']['status'] = True
          self._progress['eventing']['condition'].notify_all()
    if self._file:
      try:
        self._file.close()
      except:
        pass
    if block_on_close and self._thread is not None:
      self._thread.join()

  def progress_bar(self, length=100):
    with self._progress['eventing']['condition']:
      if self._progress['status'] == 'completed':
        return '█' * length
      elif self._progress['size']:
        return '█' * (b := min(math.floor(self._progress['uploaded'] * length / self._progress['size']), length)) + '░' * (length - b)
      else:
        return ''

  def wait_finish(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'}), timeout)
      self._progress['eventing']['status'] = False
      return self._progress['status']

  def wait_progression(self, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'} or self._progress['eventing']['progression']), timeout)
      self._progress['eventing']['progression'] = False
      return '%d%%' % self._progress['percent'] if self._progress['size'] or self._progress['status'] == 'completed' else '%s o' % format(self._progress['downloaded'], 'n')

  def wait_progress_bar(self, length=100, timeout=None):
    with self._progress['eventing']['condition']:
      self._progress['eventing']['condition'].wait_for((lambda : self._progress['status'] in {'waiting', 'completed', 'aborted'} or self._progress['eventing']['progression']), timeout)
      self._progress['eventing']['progression'] = False
      return '%s %3d%%' % (self.progress_bar(length), self._progress['percent']) if self._progress['size'] or self._progress['status'] == 'completed' else '%s o' % format(self._progress['uploaded'], 'n')

  def __enter__(self):
    self.start()
    return self

  def __exit__(self, et, ev, tb):
    self.stop()

  def __repr__(self):
    return '\r\n'.join(('<HTTPIUpload at %#x>\r\n----------' % id(self), 'Url: ' + self.url, 'Status: ' + self._progress['status']))


class NTPClient:

  def __init__(self, server='time.windows.com'):
    self.server = server
    self.isocketgen = ISocketGenerator()

  def query(self, timeout=None):
    try:
      isocket = self.isocketgen(type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
      if not isocket:
        raise
      isocket.settimeout(timeout)
    except:
      return None
    tc1 = time.time()
    try:
      isocket.sendto(struct.pack('>40s2L', b'\x1b', int(tc1 + 2208988800), int((tc1 % 1) * 4294967296)), (self.server, 123))
      r = isocket.recv(48)
      if len(r) < 48:
        raise
    except:
      return None
    finally:
      isocket.shutclose()
    ts = struct.unpack('>4L', r[32:48])
    ts1 = ts[0] - 2208988800 + ts[1] / 4294967296
    ts2 = ts[2] - 2208988800 + ts[3] / 4294967296
    tc2 = time.time()
    return tc1, ts1, ts2, tc2

  def get_time(self, to_local=False, timeout=None):
    try:
      tc1, ts1, ts2, tc2 = self.query(timeout)
    except:
      return None
    if to_local:
      try:
        return datetime.datetime.fromtimestamp(ts2).strftime('%x %X.%f')[:-3]
      except:
        return None
    return ts2

  def get_offset(self, timeout=None):
    try:
      tc1, ts1, ts2, tc2 = self.query(timeout)
    except:
      return None
    return (ts1 - tc1 + ts2 - tc2) / 2

  def close(self):
    try:
      self.isocketgen.close()
    except:
      pass

  def __enter__(self):
    return self

  def __exit__(self, et, ev, tb):
    self.close()


class TOTPassword:

  def __new__(cls, key, password_length=6, time_origin=0, time_interval=30, ntp_server='', ntp_timeout=None):
    if ntp_server is None:
      to = 0
    else:
      with (NTPClient(ntp_server) if ntp_server else NTPClient()) as ntpc:
        to = ntpc.get_offset(ntp_timeout)
      if to is None:
        return None
    self = object.__new__(cls)
    self.to = to
    return self

  def __init__(self, key, password_length=6, time_origin=0, time_interval=30, **kwargs):
    self.key = base64.b32decode(key)
    self.origin = time_origin
    self.interval = time_interval
    self.length = password_length

  def get(self, clipboard=False):
    t = time.time() + self.to - self.origin
    d = hmac.digest(self.key, int(t / self.interval).to_bytes(8, 'big', signed=False), 'sha1')
    o = d[-1] & 0xf
    p = str((int.from_bytes(d[o:o+4], 'big', signed=False) & 0x7fffffff) % (10 ** self.length)).rjust(self.length, '0')
    if clipboard:
      subprocess.run('<nul set /P ="%s"| clip' % p, shell=True)
    return p, self.interval - int(t % self.interval)

  def __enter__(self):
    return self

  def __exit__(self, et, ev, tb):
    self.key = b''