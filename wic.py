# WICPy v1.0.0 (https://github.com/PCigales/WICPy)
# Copyright © 2024 PCigales
# This program is licensed under the GNU GPLv3 copyleft license (see https://www.gnu.org/licenses)

import ctypes, ctypes.wintypes as wintypes
wintypes.PLPVOID = ctypes.POINTER(wintypes.LPVOID)
wintypes.PDOUBLE = ctypes.POINTER(wintypes.DOUBLE)
wintypes.BOOLE = type('BOOLE', (wintypes.BOOLEAN,), {'value': property(lambda s: bool(wintypes.BOOLEAN.value.__get__(s)), lambda s, v: wintypes.BOOLEAN.value.__set__(s, v))})
wintypes.PBOOLE = ctypes.POINTER(wintypes.BOOLE)
wintypes.ULONG_PTR = ctypes.c_size_t
wintypes.GUID = ctypes.c_char * 16
wintypes.PGUID = ctypes.POINTER(wintypes.GUID)
wintypes.BYTES16 = wintypes.BYTE * 16
wintypes.PBYTES16 = ctypes.POINTER(wintypes.BYTES16)
import struct
import threading
import math
from fractions import Fraction

kernel32 = ctypes.WinDLL('kernel32',  use_last_error=True)
ole32 = ctypes.WinDLL('ole32', use_last_error=True)
oleauto32 = ctypes.WinDLL('oleaut32', use_last_error=True)
shl = ctypes.WinDLL('shlwapi', use_last_error=True)

def IGetLastError():
  m = wintypes.LPWSTR()
  e = wintypes.DWORD(ctypes.get_last_error())
  return e.value, hex(e.value), (m.value.rstrip(' .') if kernel32.FormatMessageW(wintypes.DWORD(0x000011ff), 0, e, 0, ctypes.byref(m), 0, 0) else '')
def ISetLastError(e):
  e = ctypes.c_long(e).value
  ctypes.set_last_error(e)
  return e

def GUID(*g):
  return struct.pack('=LHH8B', *(struct.unpack('>LHH8B', bytes.fromhex(g[0].replace('-', ''))) if len(g) == 1 else g))
def GUID_S(g):
  return '%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x' % struct.unpack('=LHH8B', g)

class _IUtil:
  _local = threading.local()
  @staticmethod
  def _errcheck(r, f, a):
    ISetLastError(r)
    if r:
      return None
    return True if f._nout == 0 else (next if f._nout == 1 else tuple)(getattr(a[o], 'value', a[o]) if not isinstance(a[o], (ctypes.c_void_p, ctypes.Structure)) else a[o] for o in range(len(a) - f._nout, len(a)))

class _IMeta(type):
  @classmethod
  def __prepare__(mcls, name, bases, **kwds):
    kwds['_protos'] = {**getattr(bases[0], '_protos', {})} if len(bases) > 0 else {}
    return kwds
  def __init__(cls, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for n, (p, i, o) in tuple((n, pro) for n, pro in cls._protos.items() if isinstance(pro, tuple)):
      cls._protos[n] = ctypes.WINFUNCTYPE(wintypes.ULONG, *i, *o)(p, n, (*((1,) for _i in i), *((2,) for _o in o)))
      cls._protos[n]._nout = len(o)
      cls._protos[n].errcheck = _IUtil._errcheck

class IUnknown(metaclass=_IMeta):
  IID = GUID('00000000-0000-0000-c000-000000000046')
  _protos['QueryInterface'] = 0, (wintypes.LPCSTR,), (wintypes.PLPVOID,)
  _protos['AddRef'] = ctypes.WINFUNCTYPE(wintypes.ULONG)(1, 'AddRef')
  _protos['Release'] = ctypes.WINFUNCTYPE(wintypes.ULONG)(2, 'Release')
  def __new__(cls, clsid_component=False, factory=None):
    if clsid_component is None:
      return None
    if not clsid_component:
      if (clsid_component := getattr(cls, 'CLSID', None)) is None:
        raise TypeError('%s does not have an implicit constructor' % cls.__name__)
    if isinstance(clsid_component, wintypes.LPVOID):
      pI = clsid_component
    else:
      pI = wintypes.LPVOID()
      if ISetLastError(ole32.CoCreateInstance(wintypes.LPCSTR(clsid_component), None, wintypes.DWORD(1), wintypes.LPCSTR(cls.IID), ctypes.byref(pI))):
        return None
    self = object.__new__(cls)
    self.pI = pI
    self.refs = 1
    self.factory = factory
    return self
  def AddRef(self):
    if self.pI is None:
      return None
    self.refs += 1
    return self.__class__._protos['AddRef'](self.pI), self.refs
  def Release(self):
    if self.pI is None:
      return None
    if (r := self.__class__._protos['Release'](self.pI)) == 0:
      self.refs = 0
    else:
      self.refs -= 1
    if self.refs == 0:
      self.pI = None
    return r, self.refs
  def QueryInterface(self, icls, factory=None):
    if self.pI is None:
      return None
    if (i := icls(self.__class__._protos['QueryInterface'](self.pI, icls.IID))) is None:
      return None
    i.factory = factory if factory is not None else self.factory
    return i
  @property
  def _as_parameter_(self):
    return self.pI
  def __del__(self):
    __IUtil = globals().get('_IUtil')
    if __IUtil and hasattr(__IUtil._local, 'initialized'):
      while self.pI and self.refs > 0:
        self.Release()

class IClassFactory(IUnknown):
  IID = GUID('00000001-0000-0000-c000-000000000046')
  _protos['CreateInstance'] = 3, (wintypes.LPVOID, wintypes.LPCSTR,), (wintypes.PLPVOID,)
  def __new__(cls, clsid):
    if not clsid:
      raise TypeError('%s does not have an implicit constructor' % cls.__name__)
    pI = wintypes.LPVOID()
    if ISetLastError(ole32.CoGetClassObject(wintypes.LPCSTR(clsid), wintypes.DWORD(1), None, wintypes.LPCSTR(cls.IID), ctypes.byref(pI))):
      return None
    self = object.__new__(cls)
    self.pI = pI
    self.refs = 1
    self.factory = None
    return self
  def CreateInstance(self, icls):
    if self.pI is None:
      return None
    return icls(self.__class__._protos['CreateInstance'](self.pI, None, icls.IID), self)

class IEnumString(IUnknown):
  IID = GUID('00000101-0000-0000-c000-000000000046')
  _protos['Next'] = ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG, ctypes.POINTER(wintypes.LPOLESTR), wintypes.PULONG)(3, 'Next')
  _protos['Skip'] = ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG)(4, 'Skip')
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    a = (wintypes.LPOLESTR * number)()
    if self.__class__._protos['Next'](self.pI, number, a, r) > 1:
      return None
    return tuple(a[s] for s in range(r.value))
  def Skip(self, number):
    try:
      if self.__class__._protos['Skip'](self.pI, number) > 1:
        return None
    except:
      ISetLastError(0x80070057)
      return None
    return True
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    if not (n := self.Next(1)):
      raise StopIteration
    return n[0]

class IEnumUnknown(IUnknown):
  IID = GUID('00000100-0000-0000-c000-000000000046')
  _protos['Next'] = ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG, wintypes.PLPVOID, wintypes.PULONG)(3, 'Next')
  _protos['Skip'] = ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG)(4, 'Skip')
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  IClass = IUnknown
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    a = (wintypes.LPVOID * number)()
    if self.__class__._protos['Next'](self.pI, number, a, r) > 1:
      return None
    if self.__class__.IClass is IUnknown:
      return tuple(IUnknown(wintypes.LPVOID(a[i]), self.factory) for i in range(r.value))
    else:
      return tuple(IUnknown(wintypes.LPVOID(a[i]), self.factory).QueryInterface(self.__class__.IClass) for i in range(r.value))
  def Skip(self, number):
    try:
      if self.__class__._protos['Skip'](self.pI, number) > 1:
        return None
    except:
      ISetLastError(0x80070057)
      return None
    return True
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    if not (n := self.Next(1)):
      raise StopIteration
    return n[0]

class PBUFFER(wintypes.LPVOID):
  @staticmethod
  def length(obj):
    if obj is None:
      return 0
    elif isinstance(obj, memoryview):
      return obj.nbytes
    elif isinstance(obj, ctypes.Array):
      return ctypes.sizeof(obj)
    else:
      return len(obj) * getattr(obj, 'itemsize', 1)
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, (ctypes.c_void_p, ctypes.c_char_p)):
      return obj
    elif isinstance(obj, bytes):
      return ctypes.c_char_p(obj)
    else:
      return ctypes.byref((ctypes.c_char * PBUFFER.length(obj)).from_buffer(obj))

class IStream(IUnknown):
  IID = GUID(0x0000000c, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['Read'] = 3, (PBUFFER, wintypes.ULONG), (wintypes.PULONG,)
  _protos['Write'] = 4, (PBUFFER, wintypes.ULONG), (wintypes.PULONG,)
  _protos['Seek'] = 5, (wintypes.LARGE_INTEGER, wintypes.DWORD), (wintypes.PLARGE_INTEGER,)
  _protos['SetSize'] = 6, (wintypes.LARGE_INTEGER,), ()
  _protos['CopyTo'] = 7, (wintypes.LPVOID, wintypes.LARGE_INTEGER), (wintypes.PLARGE_INTEGER, wintypes.PLARGE_INTEGER)
  _protos['Commit'] = 8, (wintypes.DWORD,), ()
  _protos['Clone'] = 13, (), (wintypes.PLPVOID,)
  def Read(self, buffer, number=None):
    if number is None or number > PBUFFER.length(buffer):
      number = PBUFFER.length(buffer)
    return self.__class__._protos['Read'](self.pI, buffer, number)
  def Write(self, buffer, number=None):
    if number is None or number > PBUFFER.length(buffer):
      number = PBUFFER.length(buffer)
    return self.__class__._protos['Write'](self.pI, buffer, number)
  def Seek(self, move=0, origin=1):
    if isinstance(origin, str):
      origin = {'b': 0, 'beginning': 0, 'c': 1, 'current': 1, 'e': 2, 'end': 2}.get(origin.lower(), 1)
    return self.__class__._protos['Seek'](self.pI, move, origin)
  def SetSize(self, size):
    return None if self.__class__._protos['SetSize'](self.pI, size) else size
  def CopyTo(self, istream, number):
    return self.__class__._protos['CopyTo'](self.pI, istream, number)
  def Commit(self):
    return self.__class__._protos['Commit'](self.pI, 0)
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  shl.SHCreateStreamOnFileEx.restype = wintypes.ULONG
  @classmethod
  def CreateOnFile(cls, file_name, desired_access=0x20):
    if isinstance(desired_access, str):
      desired_access = {'read': 0x20, 'write': 0x1021, 'readwrite': 0x12}.get(desired_access.lower(), 0x20)
    pIStream = wintypes.LPVOID()
    r = shl.SHCreateStreamOnFileEx(wintypes.LPCWSTR(file_name), wintypes.DWORD(desired_access), wintypes.DWORD(0x20), False, None, ctypes.byref(pIStream))
    if r == 0x80070002 and desired_access == 0x12:
      r = shl.SHCreateStreamOnFileEx(wintypes.LPCWSTR(file_name), wintypes.DWORD(desired_access), wintypes.DWORD(0x20), True, None, ctypes.byref(pIStream))
    if r:
      return None
    ISetLastError(0)
    return cls(pIStream)
  shl.SHCreateMemStream.restype = wintypes.LPVOID
  @classmethod
  def CreateInMemory(cls, initializer=None):
    return cls(wintypes.LPVOID(shl.SHCreateMemStream(PBUFFER.from_param(initializer), wintypes.UINT(PBUFFER.length(initializer)))))
  @classmethod
  def CreateOnMemory(cls, handle, delete_on_release=False):
    pIStream = wintypes.LPVOID()
    ole32.CreateStreamOnHGlobal(handle, wintypes.BOOL(delete_on_release), ctypes.byref(pIStream))
    if not pIStream:
      return None
    return cls(pIStream)
  def Get(self, number):
    b = bytearray(number)
    n = self.__class__._protos['Read'](self.pI, b, number)
    return None if n is None else memoryview(b)[:n]
  def GetContent(self):
    if (p := self.Seek(0)) is None or (l := self.Seek(0, 'end')) is None:
      return None
    if self.Seek(0, 'beginning') is None:
      return None
    b = bytearray(l)
    if self.Read(b, l) is None:
      return None
    self.Seek(p, 'beginning')
    return b

class IWICStream(IStream):
  IID = GUID(0x135ff860, 0x22b7, 0x4ddf, 0xb0, 0xf6, 0x21, 0x8f, 0x4f, 0x29, 0x9a, 0x43)
  _protos['InitializeFromIStream'] = 14, (wintypes.LPVOID,), ()
  _protos['InitializeFromFilename'] = 15, (wintypes.LPCWSTR, wintypes.DWORD), ()
  _protos['InitializeFromMemory'] = 16, (PBUFFER, wintypes.DWORD), ()
  _protos['InitializeFromIStreamRegion'] = 17, (wintypes.LPVOID, wintypes.ULARGE_INTEGER, wintypes.ULARGE_INTEGER), ()
  def InitializeFromIStream(self, istream):
    return self.__class__._protos['InitializeFromIStream'](self.pI, istream)
  def InitializeFromIStreamRegion(self, istream, offset, maxsize):
    return self.__class__._protos['InitializeFromIStreamRegion'](self.pI, istream, offset, maxsize)
  def InitializeFromFilename(self, file_name, desired_access=0x80000000):
    if isinstance(desired_access, str):
      desired_access = {'read': 0x80000000, 'write': 0x40000000, 'readwrite': 0xc0000000}.get(desired_access.lower(), 0x80000000)
    return self.__class__._protos['InitializeFromFilename'](self.pI, file_name, desired_access)
  def InitializeFromMemory(self, buffer):
    return self.__class__._protos['InitializeFromMemory'](self.pI, buffer, PBUFFER.length(buffer))
  @classmethod
  def CreateOnFile(cls, *args, **kwargs):
    raise AttributeError('type object %s has no attribute \'CreateOnFile\'' % cls.__name__)
  @classmethod
  def CreateInMemory(cls, *args, **kwargs):
    raise AttributeError('type object %s has no attribute \'CreateInMemory\'' % cls.__name__)

class _BGUID:
  @classmethod
  def name_guid(cls, n):
    return cls._tab_ng.get(n.lower(), cls._def) if isinstance(n, str) else n
  @classmethod
  def guid_name(cls, g):
    return cls._tab_gn.get(g, GUID_S(g))
  @classmethod
  def to_bytes(cls, obj):
    return obj.raw if isinstance(obj, cls) else (cls.name_guid(obj) or (b'\x00' * 16))
  @property
  def value(self):
    return self
  @value.setter
  def value(self, val):
    self.raw = val.raw
  @property
  def guid(self):
    return self.raw
  @guid.setter
  def guid(self, val):
    self.raw = (val or (b'\x00' * 16))
  @property
  def name(self):
    return self.__class__.guid_name(self.raw)
  @name.setter
  def name(self, val):
    self.raw = (self.__class__.name_guid(val) or (b'\x00' * 16))
  def __init__(self, val=None):
    if val is None:
      self.__class__.__bases__[1].__init__(self)
    else:
      self.__class__.__bases__[1].__init__(self, *(self.__class__.name_guid(val) or (b'\x00' * 16)))
  def __eq__(self, other):
    return self.guid == (other.guid if isinstance(other, _BGUID) else self.__class__.name_guid(other))
  def __str__(self):
    return '<b\'\\x%s\': %s>' % ('\\x'.join(b.hex() for b in self), self.__class__.guid_name(self.raw))
  def __repr__(self):
    return str(self)

class _BPGUID:
  @classmethod
  def from_param(cls, obj):
    return obj if isinstance(obj, cls) else (ctypes.byref(obj) if isinstance(obj, cls.__bases__[1]._type_) or (isinstance(obj, ctypes.Array) and issubclass(obj._type_, cls.__bases__[1]._type_)) else ctypes.c_char_p(cls._type_.name_guid(obj)))
  @classmethod
  def create_from(cls, obj):
    obj = cls._type_.name_guid(obj)
    return ctypes.cast(ctypes.c_void_p(None), cls) if obj is None else cls(cls._type_(obj))

class _GMeta(wintypes.GUID.__class__):
  def __init__(cls, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if hasattr(cls, 'value'):
      del cls.value

WICContainerFormat = {
  'Bmp': GUID(0xaf1d87e, 0xfcfe, 0x4188, 0xbd, 0xeb, 0xa7, 0x90, 0x64, 0x71, 0xcb, 0xe3),
  'Png': GUID(0x1b7cfaf4, 0x713f, 0x473c, 0xbb, 0xcd, 0x61, 0x37, 0x42, 0x5f, 0xae, 0xaf),
  'Ico': GUID(0xa3a860c4,0x338f, 0x4c17, 0x91, 0x9a, 0xfb, 0xa4, 0xb5, 0x62, 0x8f, 0x21),
  'Jpg': GUID(0x19e4a5aa, 0x5662, 0x4fc5, 0xa0, 0xc0, 0x17, 0x58, 0x2, 0x8e, 0x10, 0x57),
  'Jpeg': GUID(0x19e4a5aa, 0x5662, 0x4fc5, 0xa0, 0xc0, 0x17, 0x58, 0x2, 0x8e, 0x10, 0x57),
  'Tif': GUID(0x163bcc30, 0xe2e9, 0x4f0b, 0x96, 0x1d, 0xa3, 0xe9, 0xfd, 0xb7, 0x88, 0xa3),
  'Tiff': GUID(0x163bcc30, 0xe2e9, 0x4f0b, 0x96, 0x1d, 0xa3, 0xe9, 0xfd, 0xb7, 0x88, 0xa3),
  'Gif': GUID(0x1f8a5601, 0x7d4d, 0x4cbd, 0x9c, 0x82, 0x1b, 0xc8, 0xd4, 0xee, 0xb9, 0xa5),
  'Wmp': GUID(0x57a37caa, 0x367a, 0x4540, 0x91, 0x6b, 0xf1, 0x83, 0xc5, 0x09, 0x3a, 0x4b),
  'Heif': GUID(0xe1e62521, 0x6787, 0x405b, 0xa3, 0x39, 0x50, 0x07, 0x15, 0xb5, 0x76, 0x3f),
  'Webp': GUID(0xe094b0e2, 0x67f2, 0x45b3, 0xb0, 0xea, 0x11, 0x53, 0x37, 0xca, 0x7c, 0xf3),
  'Cur': GUID(0x0444f35f, 0x587c, 0x4570, 0x96, 0x46, 0x64, 0xdc, 0xd8, 0xf1, 0x75, 0x73),
  'Dds': GUID(0x9967cb95, 0x2e85, 0x4ac8, 0x8c, 0xa2, 0x83, 0xd7, 0xcc, 0xd4, 0x25, 0xc9),
  'Raw': GUID(0xfe99ce60, 0xf19c, 0x433c, 0xa3, 0xae, 0x00, 0xac, 0xef, 0xa9, 0xca, 0x21),
  'CameraRaw': GUID(0xc1fc85cb, 0xd64f, 0x478b, 0xa4, 0xec, 0x69, 0xad, 0xc9, 0xee, 0x13, 0x92),
  'Dng': GUID(0xf3ff6d0d, 0x38c0, 0x41c4, 0xb1, 0xfe, 0x1f, 0x38, 0x24, 0xf1, 0x7b, 0x84),
  'Adng': GUID(0xf3ff6d0d, 0x38c0, 0x41c4, 0xb1, 0xfe, 0x1f, 0x38, 0x24, 0xf1, 0x7b, 0x84)
}
WICCONTAINERFORMAT = _GMeta('WICCONTAINERFORMAT', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {n.lower(): g for n, g in WICContainerFormat.items()}, '_tab_gn': {g: n for n, g in WICContainerFormat.items()}, '_def': None})
WICPCONTAINERFORMAT = type('WICPCONTAINERFORMAT', (_BPGUID, ctypes.POINTER(WICCONTAINERFORMAT)), {'_type_': WICCONTAINERFORMAT})

WICVendorIdentification = {
  'Microsoft_': GUID(0x69fd0fdc, 0xa866, 0x4108, 0xb3, 0xb2, 0x98, 0x44, 0x7f, 0xa9, 0xed, 0xd4),
  'Microsoft': GUID(0xf0e749ca, 0xedef, 0x4589, 0xa7, 0x3a, 0xee, 0x0e, 0x62, 0x6a, 0x2a, 0x2b),
  'MicrosoftBuiltin': GUID(0x257a30fd, 0x6b6, 0x462b, 0xae, 0xa4, 0x63, 0xf7, 0xb, 0x86, 0xe5, 0x33)
}
WICVENDORIDENTIFICATION = _GMeta('WICVENDORIDENTIFICATION', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {n.lower(): g for n, g in WICVendorIdentification.items()}, '_tab_gn': {g: n for n, g in WICVendorIdentification.items()}, '_def': None})
WICPVENDORIDENTIFICATION = type('WICPVENDORIDENTIFICATION', (_BPGUID, ctypes.POINTER(WICVENDORIDENTIFICATION)), {'_type_': WICVENDORIDENTIFICATION})

WICMetadataHandler = {
  'Unknown': GUID(0xa45e592f, 0x9078, 0x4a7c, 0xad, 0xb5, 0x4e, 0xdc, 0x4f, 0xd6, 0x1b, 0x1f),
  'App0': GUID(0x79007028, 0x268d, 0x45d6, 0xa3, 0xc2, 0x35, 0x4e, 0x6a, 0x50, 0x4b, 0xc9),
  'App1': GUID(0x8fd3dfc3, 0xf951, 0x492b, 0x81, 0x7f, 0x69, 0xc2, 0xe6, 0xd9, 0xa5, 0xb0),
  'App13': GUID(0x326556a2, 0xf502, 0x4354, 0x9c, 0xc0, 0x8e, 0x3f, 0x48, 0xea, 0xf6, 0xb5),
  'Ifd': GUID(0x537396c6, 0x2d8a, 0x4bb6, 0x9b, 0xf8, 0x2f, 0x0a, 0x8e, 0x2a, 0x3a, 0xdf),
  'SubIfd': GUID(0x58A2E128, 0x2DB9, 0x4E57, 0xBB, 0x14, 0x51, 0x77, 0x89, 0x1E, 0xD3, 0x31),
  'Exif': GUID(0x1c3c4f9d, 0xb84a, 0x467d, 0x94, 0x93, 0x36, 0xcf, 0xbd, 0x59, 0xea, 0x57),
  'Gps': GUID(0x7134ab8a, 0x9351, 0x44ad, 0xaf, 0x62, 0x44, 0x8d, 0xb6, 0xb5, 0x02, 0xec),
  'Interop': GUID(0xed686f8e, 0x681f, 0x4c8b, 0xbd, 0x41, 0xa8, 0xad, 0xdb, 0xf6, 0xb3, 0xfc),
  'Thumbnail': GUID(0x243dcee9, 0x8703, 0x40ee, 0x8e, 0xf0, 0x22, 0xa6, 0x0, 0xb8, 0x5, 0x8c),
  'JpegLuminance': GUID(0x86908007, 0xedfc, 0x4860, 0x8d, 0x4b, 0x4e, 0xe6, 0xe8, 0x3e, 0x60, 0x58),
  'JpegChrominance': GUID(0xf73d0dcf, 0xcec6, 0x4f85, 0x9b, 0x0e, 0x1c, 0x39, 0x56, 0xb1, 0xbe, 0xf7),
  'IPTC': GUID(0x4fab0914, 0xe129, 0x4087, 0xa1, 0xd1, 0xbc, 0x81, 0x2d, 0x45, 0xa7, 0xb5),
  'IPTCDigest': GUID(0x1ca32285, 0x9ccd, 0x4786, 0x8b, 0xd8, 0x79, 0x53, 0x9d, 0xb6, 0xa0, 0x06),
  'IRB': GUID(0x16100d66, 0x8570, 0x4bb9, 0xb9, 0x2d, 0xfd, 0xa4, 0xb2, 0x3e, 0xce, 0x67),
  '8BIMIPTC': GUID(0x0010568c, 0x0852, 0x4e6a, 0xb1, 0x91, 0x5c, 0x33, 0xac, 0x5b, 0x04, 0x30),
  '8BIMResolutionInfo': GUID(0x739f305d, 0x81db, 0x43cb, 0xac, 0x5e, 0x55, 0x01, 0x3e, 0xf9, 0xf0, 0x03),
  '8BIMIPTCDigest': GUID(0x1ca32285, 0x9ccd, 0x4786, 0x8b, 0xd8, 0x79, 0x53, 0x9d, 0xb6, 0xa0, 0x06),
  'XMP': GUID(0xbb5acc38, 0xf216, 0x4cec, 0xa6, 0xc5, 0x5f, 0x6e, 0x73, 0x97, 0x63, 0xa9),
  'XMPStruct': GUID(0x22383cf1, 0xed17, 0x4e2e, 0xaf, 0x17, 0xd8, 0x5b, 0x8f, 0x6b, 0x30, 0xd0),
  'XMPBag': GUID(0x833cca5f, 0xdcb7, 0x4516, 0x80, 0x6f, 0x65, 0x96, 0xab, 0x26, 0xdc, 0xe4),
  'XMPSeq': GUID(0x63e8df02, 0xeb6c,0x456c, 0xa2, 0x24, 0xb2, 0x5e, 0x79, 0x4f, 0xd6, 0x48),
  'XMPAlt': GUID(0x7b08a675, 0x91aa, 0x481b, 0xa7, 0x98, 0x4d, 0xa9, 0x49, 0x08, 0x61, 0x3b),
  'JpegComment': GUID(0x220e5f33, 0xafd3, 0x474e, 0x9d, 0x31, 0x7d, 0x4f, 0xe7, 0x30, 0xf5, 0x57),
  'LSD': GUID(0xe256031e, 0x6299, 0x4929, 0xb9, 0x8d, 0x5a, 0xc8, 0x84, 0xaf, 0xba, 0x92),
  'IMD': GUID(0xbd2bb086, 0x4d52, 0x48dd, 0x96, 0x77, 0xdb, 0x48, 0x3e, 0x85, 0xae, 0x8f),
  'GCE': GUID(0x2a25cad8, 0xdeeb, 0x4c69, 0xa7, 0x88, 0xe, 0xc2, 0x26, 0x6d, 0xca, 0xfd),
  'APE': GUID(0x2e043dc2, 0xc967, 0x4e05, 0x87, 0x5e, 0x61, 0x8b, 0xf6, 0x7e, 0x85, 0xc3),
  'GifComment': GUID(0xc4b6e0e0, 0xcfb4, 0x4ad3, 0xab, 0x33, 0x9a, 0xad, 0x23, 0x55, 0xa3, 0x4a),
  'ChunktEXt': GUID(0x568d8936, 0xc0a9, 0x4923, 0x90, 0x5d, 0xdf, 0x2b, 0x38, 0x23, 0x8f, 0xbc),
  'ChunkgAMA': GUID(0xf00935a5, 0x1d5d, 0x4cd1, 0x81, 0xb2, 0x93, 0x24, 0xd7, 0xec, 0xa7, 0x81),
  'ChunkbKGD': GUID(0xe14d3571, 0x6b47, 0x4dea, 0xb6, 0xa, 0x87, 0xce, 0xa, 0x78, 0xdf, 0xb7),
  'ChunkiTXt': GUID(0xc2bec729, 0xb68, 0x4b77, 0xaa, 0xe, 0x62, 0x95, 0xa6, 0xac, 0x18, 0x14),
  'ChunkcHRM': GUID(0x9db3655b, 0x2842, 0x44b3, 0x80, 0x67, 0x12, 0xe9, 0xb3, 0x75, 0x55, 0x6a),
  'ChunkhIST': GUID(0xc59a82da, 0xdb74, 0x48a4, 0xbd, 0x6a, 0xb6, 0x9c, 0x49, 0x31, 0xef, 0x95),
  'ChunkiCCP': GUID(0xeb4349ab, 0xb685, 0x450f, 0x91, 0xb5, 0xe8, 0x2, 0xe8, 0x92, 0x53, 0x6c),
  'ChunksRGB': GUID(0xc115fd36, 0xcc6f, 0x4e3f, 0x83, 0x63, 0x52, 0x4b, 0x87, 0xc6, 0xb0, 0xd9),
  'ChunktIME': GUID(0x6b00ae2d, 0xe24b, 0x460a, 0x98, 0xb6, 0x87, 0x8b, 0xd0, 0x30, 0x72, 0xfd),
  'HeifRoot': GUID(0x817ef3e1, 0x1288, 0x45f4, 0xa8, 0x52, 0x26, 0x0d, 0x9e, 0x7c, 0xce, 0x83),
  'HeifHDR': GUID(0x568b8d8a, 0x1e65, 0x438c, 0x89, 0x68, 0xd6, 0x0e, 0x10, 0x12, 0xbe, 0xb9),
  'WebpANIM': GUID(0x6dc4fda6, 0x78e6, 0x4102, 0xae, 0x35, 0xbc, 0xfa, 0x1e, 0xdc, 0xc7, 0x8b),
  'WebpANMF': GUID(0x43c105ee, 0xb93b, 0x4abb, 0xb0, 0x3, 0xa0, 0x8c, 0xd, 0x87, 0x4, 0x71),
  'DdsRoot': GUID(0x4a064603, 0x8c33, 0x4e60, 0x9c, 0x29, 0x13, 0x62, 0x31, 0x70, 0x2d, 0x08),
  **WICContainerFormat
}
WICMETADATAHANDLER = _GMeta('WICMETADATAHANDLER', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {n.lower(): g for n, g in WICMetadataHandler.items()}, '_tab_gn': {g: n for n, g in WICMetadataHandler.items()}, '_def': None})
WICPMETADATAHANDLER = type('WICPMETADATAHANDLER', (_BPGUID, ctypes.POINTER(WICMETADATAHANDLER)), {'_type_': WICMETADATAHANDLER})

WICPixelFormat = {
 'DontCare': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x00),
 'Undefined': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x00),
 '1bppIndexed': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x01),
 '2bppIndexed': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x02),
 '4bppIndexed': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x03),
 '8bppIndexed': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x04),
 'BlackWhite': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x05),
 '2bppGray': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x06),
 '4bppGray': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x07),
 '8bppGray': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x08),
 '16bppGray': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x0b),
 '16bppGrayFixedPoint': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x13),
 '16bppGrayHalf': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x3e),
 '32bppGrayFixedPoint': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x3f),
 '32bppGrayFloat': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x11),
 '8bppAlpha': GUID(0xe6cd0116 ,0xeeba ,0x4161 ,0xaa ,0x85 ,0x27 ,0xdd ,0x9f ,0xb3 ,0xa8 ,0x95),
 '16bppBGR555': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x09),
 '16bppBGR565': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x0a),
 '16bppBGRA5551': GUID(0x05ec7c2b, 0xf1e6, 0x4961, 0xad, 0x46, 0xe1, 0xcc, 0x81, 0x0a, 0x87, 0xd2),
 '24bppBGR': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x0c),
 '24bppRGB': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x0d),
 '32bppBGR': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x0e),
 '32bppRGB': GUID(0xd98c6b95 ,0x3efe ,0x47d6 ,0xbb ,0x25 ,0xeb ,0x17 ,0x48 ,0xab ,0x0c ,0xf1),
 '32bppBGRA': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x0f),
 '32bppRGBA': GUID(0xf5c7ad2d ,0x6a8d ,0x43dd ,0xa7 ,0xa8 ,0xa2 ,0x99 ,0x35 ,0x26 ,0x1a ,0xe9),
 '32bppPBGRA': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x10),
 '32bppPRGBA': GUID(0x3cc4a650 ,0xa527 ,0x4d37 ,0xa9 ,0x16 ,0x31 ,0x42 ,0xc7 ,0xeb ,0xed ,0xba),
 '32bppBGR101010': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x14),
 '32bppRGBA1010102': GUID(0x25238d72, 0xfcf9, 0x4522, 0xb5, 0x14, 0x55, 0x78, 0xe5, 0xad, 0x55, 0xe0),
 '32bppRGBA1010102XR': GUID(0x00de6b9a, 0xc101, 0x434b, 0xb5, 0x02, 0xd0, 0x16, 0x5e, 0xe1, 0x12, 0x2c),
 '32bppR10G10B10A2': GUID(0x604e1bb5, 0x8a3c, 0x4b65, 0xb1, 0x1c, 0xbc, 0x0b, 0x8d, 0xd7, 0x5b, 0x7f),
 '32bppR10G10B10A2HDR10': GUID(0x9c215c5d, 0x1acc, 0x4f0e, 0xa4, 0xbc, 0x70, 0xfb, 0x3a, 0xe8, 0xfd, 0x28),
 '32bppRGBE': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x3d),
 '48bppBGR': GUID(0xe605a384 ,0xb468 ,0x46ce ,0xbb ,0x2e ,0x36 ,0xf1 ,0x80 ,0xe6 ,0x43 ,0x13),
 '48bppRGB': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x15),
 '48bppBGRFixedPoint': GUID(0x49ca140e, 0xcab6, 0x493b, 0x9d, 0xdf, 0x60, 0x18, 0x7c, 0x37, 0x53, 0x2a),
 '48bppRGBFixedPoint': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x12),
 '48bppRGBHalf': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x3b),
 '64bppRGB': GUID(0xa1182111, 0x186d, 0x4d42, 0xbc, 0x6a, 0x9c, 0x83, 0x03, 0xa8, 0xdf, 0xf9),
 '64bppBGRA': GUID(0x1562ff7c ,0xd352 ,0x46f9 ,0x97 ,0x9e ,0x42 ,0x97 ,0x6b ,0x79 ,0x22 ,0x46),
 '64bppRGBA': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x16),
 '64bppPBGRA': GUID(0x8c518e8e ,0xa4ec ,0x468b ,0xae ,0x70 ,0xc9 ,0xa3 ,0x5a ,0x9c ,0x55 ,0x30),
 '64bppPRGBA': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x17),
 '64bppRGBFixedPoint': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x40),
 '64bppBGRAFixedPoint': GUID(0x356de33c ,0x54d2 ,0x4a23 ,0xbb ,0x4 ,0x9b ,0x7b ,0xf9 ,0xb1 ,0xd4 ,0x2d),
 '64bppRGBAFixedPoint': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x1d),
 '64bppRGBHalf': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x42),
 '64bppRGBAHalf': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x3a),
 '64bppPRGBAHalf': GUID(0x58ad26c2, 0xc623, 0x4d9d, 0xb3, 0x20, 0x38, 0x7e, 0x49, 0xf8, 0xc4, 0x42),
 '96bppRGBFixedPoint': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x18),
 '96bppRGBFloat': GUID(0xe3fed78f, 0xe8db, 0x4acf, 0x84, 0xc1, 0xe9, 0x7f, 0x61, 0x36, 0xb3, 0x27),
 '128bppRGBFixedPoint': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x41),
 '128bppRGBAFixedPoint': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x1e),
 '128bppRGBFloat': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x1b),
 '128bppRGBAFloat': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x19),
 '128bppPRGBAFloat': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x1a),
 '32bppCMYK': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x1c),
 '40bppCMYKAlpha': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x2c),
 '64bppCMYK': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x1f),
 '80bppCMYKAlpha': GUID(0x6fddc324 ,0x4e03 ,0x4bfe ,0xb1 ,0x85 ,0x3d ,0x77 ,0x76 ,0x8d ,0xc9 ,0x2d),
 '8bppY': GUID(0x91b4db54, 0x2df9, 0x42f0, 0xb4, 0x49, 0x29, 0x09, 0xbb, 0x3d, 0xf8, 0x8e),
 '8bppCb': GUID(0x1339f224, 0x6bfe, 0x4c3e, 0x93, 0x02, 0xe4, 0xf3, 0xa6, 0xd0, 0xca, 0x2a),
 '8bppCr': GUID(0xb8145053, 0x2116, 0x49f0, 0x88, 0x35, 0xed, 0x84, 0x4b, 0x20, 0x5c, 0x51),
 '16bppCbCr': GUID(0xff95ba6e, 0x11e0, 0x4263, 0xbb, 0x45, 0x01, 0x72, 0x1f, 0x34, 0x60, 0xa4),
 '16bppYQuantizedDctCoefficients': GUID(0xa355f433, 0x48e8, 0x4a42, 0x84, 0xd8, 0xe2, 0xaa, 0x26, 0xca, 0x80, 0xa4),
 '16bppCbQuantizedDctCoefficients': GUID(0xd2c4ff61, 0x56a5, 0x49c2, 0x8b, 0x5c, 0x4c, 0x19, 0x25, 0x96, 0x48, 0x37),
 '16bppCrQuantizedDctCoefficients': GUID(0x2fe354f0, 0x1680, 0x42d8, 0x92, 0x31, 0xe7, 0x3c, 0x05, 0x65, 0xbf, 0xc1),
 '24bpp3Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x20),
 '48bpp3Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x26),
 '32bpp4Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x21),
 '64bpp4Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x27),
 '40bpp5Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x22),
 '80bpp5Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x28),
 '48bpp6Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x23),
 '96bpp6Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x29),
 '56bpp7Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x24),
 '112bpp7Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x2a),
 '64bpp8Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x25),
 '128bpp8Channels': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x2b),
 '32bpp3ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x2e),
 '64bpp3ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x34),
 '40bpp4ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x2f),
 '80bpp4ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x35),
 '48bpp5ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x30),
 '96bpp5ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x36),
 '56bpp6ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x31),
 '112bpp6ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x37),
 '64bpp7ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x32),
 '128bpp7ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x38),
 '72bpp8ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x33),
 '144bpp8ChannelsAlpha': GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x39)
}
WICPIXELFORMAT = _GMeta('WICPIXELFORMAT', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {n.lower(): g for n, g in WICPixelFormat.items()}, '_tab_gn': {g: n for n, g in WICPixelFormat.items()}, '_def': None})
WICPPIXELFORMAT = type('WICPPIXELFORMAT', (_BPGUID, ctypes.POINTER(WICPIXELFORMAT)), {'_type_': WICPIXELFORMAT})

WICComponent = {
  'BmpDecoder': GUID(0x6b462062, 0x7cbf, 0x400d, 0x9f, 0xdb, 0x81, 0x3d, 0xd1, 0xf, 0x27, 0x78),
  'PngDecoder_': GUID(0x389ea17b, 0x5078, 0x4cde, 0xb6, 0xef, 0x25, 0xc1, 0x51, 0x75, 0xc7, 0x51),
  'PngDecoder': GUID(0xe018945b, 0xaa86, 0x4008, 0x9b, 0xd4, 0x67, 0x77, 0xa1, 0xe4, 0x0c, 0x11),
  'IcoDecoder': GUID(0xc61bfcdf, 0x2e0f, 0x4aad, 0xa8, 0xd7, 0xe0, 0x6b, 0xaf, 0xeb, 0xcd, 0xfe),
  'JpgDecoder': GUID(0x9456a480, 0xe88b, 0x43ea, 0x9e, 0x73, 0xb, 0x2d, 0x9b, 0x71, 0xb1, 0xca),
  'JpegDecoder': GUID(0x9456a480, 0xe88b, 0x43ea, 0x9e, 0x73, 0xb, 0x2d, 0x9b, 0x71, 0xb1, 0xca),
  'TifDecoder': GUID(0xb54e85d9, 0xfe23, 0x499f, 0x8b, 0x88, 0x6a, 0xce, 0xa7, 0x13, 0x75, 0x2b),
  'TiffDecoder': GUID(0xb54e85d9, 0xfe23, 0x499f, 0x8b, 0x88, 0x6a, 0xce, 0xa7, 0x13, 0x75, 0x2b),
  'GifDecoder': GUID(0x381dda3c, 0x9ce9, 0x4834, 0xa2, 0x3e, 0x1f, 0x98, 0xf8, 0xfc, 0x52, 0xbe),
  'WmpDecoder': GUID(0xa26cec36, 0x234c, 0x4950, 0xae, 0x16, 0xe3, 0x4a, 0xac, 0xe7, 0x1d, 0x0d),
  'HeifDecoder': GUID(0xe9a4a80a, 0x44fe, 0x4de4, 0x89, 0x71, 0x71, 0x50, 0xb1, 0x0a, 0x51, 0x99),
  'WebpDecoder': GUID(0x7693e886, 0x51c9, 0x4070, 0x84, 0x19, 0x9f, 0x70, 0x73, 0x8e, 0xc8, 0xfa),
  'CurDecoder': GUID(0x22696b76, 0x881b, 0x48d7, 0x88, 0xf0, 0xdc, 0x61, 0x11, 0xff, 0x9f, 0x0b),
  'DdsDecoder': GUID(0x9053699f, 0xa341, 0x429d, 0x9e, 0x90, 0xee, 0x43, 0x7c, 0xf8, 0x0c, 0x73),
  'RawDecoder': GUID(0x41945702, 0x8302, 0x44a6, 0x94, 0x45, 0xac, 0x98, 0xe8, 0xaf, 0xa0, 0x86),
  'CameraRawDecoder': GUID(0x5fdd51e2, 0xa9d0, 0x44ce, 0x8c, 0x8d, 0x16, 0x2b, 0xa0, 0xc5, 0x91, 0xa0),
  'DngDecoder': GUID(0x981d9411, 0x909e, 0x42a7, 0x8f, 0x5d, 0xa7, 0x47, 0xff, 0x05, 0x2e, 0xdb),
  'AdngDecoder': GUID(0x981d9411, 0x909e, 0x42a7, 0x8f, 0x5d, 0xa7, 0x47, 0xff, 0x05, 0x2e, 0xdb),
  'BmpEncoder': GUID(0x69be8bb4, 0xd66d, 0x47c8, 0x86, 0x5a, 0xed, 0x15, 0x89, 0x43, 0x37, 0x82),
  'PngEncoder': GUID(0x27949969, 0x876a, 0x41d7, 0x94, 0x47, 0x56, 0x8f, 0x6a, 0x35, 0xa4, 0xdc),
  'JpgEncoder': GUID(0x1a34f5c1, 0x4a5a, 0x46dc, 0xb6, 0x44, 0x1f, 0x45, 0x67, 0xe7, 0xa6, 0x76),
  'JpegEncoder': GUID(0x1a34f5c1, 0x4a5a, 0x46dc, 0xb6, 0x44, 0x1f, 0x45, 0x67, 0xe7, 0xa6, 0x76),
  'TifEncoder': GUID(0x0131be10, 0x2001, 0x4c5f, 0xa9, 0xb0, 0xcc, 0x88, 0xfa, 0xb6, 0x4c, 0xe8),
  'TiffEncoder': GUID(0x0131be10, 0x2001, 0x4c5f, 0xa9, 0xb0, 0xcc, 0x88, 0xfa, 0xb6, 0x4c, 0xe8),
  'GifEncoder': GUID(0x114f5598, 0xb22, 0x40a0, 0x86, 0xa1, 0xc8, 0x3e, 0xa4, 0x95, 0xad, 0xbd),
  'WmpEncoder': GUID(0xac4ce3cb, 0xe1c1, 0x44cd, 0x82, 0x15, 0x5a, 0x16, 0x65, 0x50, 0x9e, 0xc2),
  'HeifEncoder': GUID(0x0dbecec1, 0x9eb3, 0x4860, 0x9c, 0x6f, 0xdd, 0xbe, 0x86, 0x63, 0x45, 0x75),
  'DdsEncoder': GUID(0xa61dde94, 0x66ce, 0x4ac1, 0x88, 0x1b, 0x71, 0x68, 0x05, 0x88, 0x89, 0x5e),
  'DefaultFormatConverter': GUID(0x1a3f11dc, 0xb514, 0x4b17, 0x8c, 0x5f, 0x21, 0x54, 0x51, 0x38, 0x52, 0xf1),
  'FormatConverterHighColor': GUID(0xac75d454, 0x9f37, 0x48f8, 0xb9, 0x72, 0x4e, 0x19, 0xbc, 0x85, 0x60, 0x11),
  'FormatConverterNChannel': GUID(0xc17cabb2, 0xd4a3, 0x47d7, 0xa5, 0x57, 0x33, 0x9b, 0x2e, 0xfb, 0xd4, 0xf1),
  'FormatConverterWMPhoto': GUID(0x9cb5172b, 0xd600, 0x46ba, 0xab, 0x77, 0x77, 0xbb, 0x7e, 0x3a, 0x00, 0xd9),
  'PlanarFormatConverter': GUID(0x184132b8, 0x32f8, 0x4784, 0x91, 0x31, 0xdd, 0x72, 0x24, 0xb2, 0x34, 0x38),
  **{'PixelFormat' + n: g for n, g in WICPixelFormat.items()},
  'UnknownMetadataReader': GUID(0x699745c2, 0x5066, 0x4b82, 0xa8, 0xe3, 0xd4, 0x04, 0x78, 0xdb, 0xec, 0x8c),
  'UnknownMetadataWriter': GUID(0xa09cca86, 0x27ba, 0x4f39, 0x90, 0x53, 0x12, 0x1f, 0xa4, 0xdc, 0x08, 0xfc),
  'App0MetadataReader': GUID(0x43324b33, 0xa78f, 0x480f, 0x91, 0x11, 0x96, 0x38, 0xaa, 0xcc, 0xc8, 0x32),
  'App0MetadataWriter': GUID(0xf3c633a2, 0x46c8, 0x498e, 0x8f, 0xbb, 0xcc, 0x6f, 0x72, 0x1b, 0xbc, 0xde),
  'App1MetadataReader': GUID(0xdde33513, 0x774e, 0x4bcd, 0xae, 0x79, 0x02, 0xf4, 0xad, 0xfe, 0x62, 0xfc),
  'App1MetadataWriter': GUID(0xee366069, 0x1832, 0x420f, 0xb3, 0x81, 0x04, 0x79, 0xad, 0x06, 0x6f, 0x19),
  'App13MetadataReader': GUID(0xaa7e3c50, 0x864c, 0x4604, 0xbc, 0x04, 0x8b, 0x0b, 0x76, 0xe6, 0x37, 0xf6),
  'App13MetadataWriter': GUID(0x7b19a919, 0xa9d6, 0x49e5, 0xbd, 0x45, 0x02, 0xc3, 0x4e, 0x4e, 0x4c, 0xd5),
  'IfdMetadataReader': GUID(0x8f914656, 0x9d0a, 0x4eb2, 0x90, 0x19, 0x0b, 0xf9, 0x6d, 0x8a, 0x9e, 0xe6),
  'IfdMetadataWriter': GUID(0xb1ebfc28, 0xc9bd, 0x47a2, 0x8d, 0x33, 0xb9, 0x48, 0x76, 0x97, 0x77, 0xa7),
  'SubIfdMetadataReader': GUID(0x50d42f09, 0xecd1, 0x4b41, 0xb6, 0x5d, 0xda, 0x1f, 0xda, 0xa7, 0x56, 0x63),
  'SubIfdMetadataWriter': GUID(0x8ade5386, 0x8e9b, 0x4f4c, 0xac, 0xf2, 0xf0, 0x00, 0x87, 0x06, 0xb2, 0x38),
  'ExifMetadataReader': GUID(0xd9403860, 0x297f, 0x4a49, 0xbf, 0x9b, 0x77, 0x89, 0x81, 0x50, 0xa4, 0x42),
  'ExifMetadataWriter': GUID(0xc9a14cda, 0xc339, 0x460b, 0x90, 0x78, 0xd4, 0xde, 0xbc, 0xfa, 0xbe, 0x91),
  'GpsMetadataReader': GUID(0x3697790b, 0x223b, 0x484e, 0x99, 0x25, 0xc4, 0x86, 0x92, 0x18, 0xf1, 0x7a),
  'GpsMetadataWriter': GUID(0xcb8c13e4, 0x62b5, 0x4c96, 0xa4, 0x8b, 0x6b, 0xa6, 0xac, 0xe3, 0x9c, 0x76),
  'InteropMetadataReader': GUID(0xb5c8b898, 0x0074, 0x459f, 0xb7, 0x00, 0x86, 0x0d, 0x46, 0x51, 0xea, 0x14),
  'InteropMetadataWriter': GUID(0x122ec645, 0xcd7e, 0x44d8, 0xb1, 0x86, 0x2c, 0x8c, 0x20, 0xc3, 0xb5, 0x0f),
  'ThumbnailMetadataReader': GUID(0xfb012959, 0xf4f6, 0x44d7, 0x9d, 0x09, 0xda, 0xa0, 0x87, 0xa9, 0xdb, 0x57),
  'ThumbnailMetadataWriter': GUID(0xd049b20c, 0x5dd0, 0x44fe, 0xb0, 0xb3, 0x8f, 0x92, 0xc8, 0xe6, 0xd0, 0x80),
  'JpegChrominanceMetadataReader': GUID(0x50b1904b, 0xf28f, 0x4574, 0x93, 0xf4, 0x0b, 0xad, 0xe8, 0x2c, 0x69, 0xe9),
  'JpegChrominanceMetadataWriter': GUID(0x3ff566f0, 0x6e6b, 0x49d4, 0x96, 0xe6, 0xb7, 0x88, 0x86, 0x69, 0x2c, 0x62),
  'JpegLuminanceMetadataReader': GUID(0x356f2f88, 0x05a6, 0x4728, 0xb9, 0xa4, 0x1b, 0xfb, 0xce, 0x04, 0xd8, 0x38),
  'JpegLuminanceMetadataWriter': GUID(0x1d583abc, 0x8a0e, 0x4657, 0x99, 0x82, 0xa3, 0x80, 0xca, 0x58, 0xfb, 0x4b),
  'IPTCMetadataReader': GUID(0x03012959, 0xf4f6, 0x44d7, 0x9d, 0x09, 0xda, 0xa0, 0x87, 0xa9, 0xdb, 0x57),
  'IPTCMetadataWriter': GUID(0x1249b20c, 0x5dd0, 0x44fe, 0xb0, 0xb3, 0x8f, 0x92, 0xc8, 0xe6, 0xd0, 0x80),
  'IPTCDigestReader': GUID(0x02805f1e, 0xd5aa, 0x415b, 0x82, 0xc5, 0x61, 0xc0, 0x33, 0xa9, 0x88, 0xa6),
  'IPTCDigestWriter': GUID(0x2db5e62b, 0x0d67, 0x495f, 0x8f, 0x9d, 0xc2, 0xf0, 0x18, 0x86, 0x47, 0xac),
  'IRBMetadataReader': GUID(0xd4dcd3d7, 0xb4c2, 0x47d9, 0xa6, 0xbf, 0xb8, 0x9b, 0xa3, 0x96, 0xa4, 0xa3),
  'IRBMetadataWriter': GUID(0x5c5c1935, 0x0235, 0x4434, 0x80, 0xbc, 0x25, 0x1b, 0xc1, 0xec, 0x39, 0xc6),
  '8BIMIPTCMetadataReader': GUID(0x0010668c, 0x0801, 0x4da6, 0xa4, 0xa4, 0x82, 0x65, 0x22, 0xb6, 0xd2, 0x8f),
  '8BIMIPTCMetadataWriter': GUID(0x00108226, 0xee41, 0x44a2, 0x9e, 0x9c, 0x4b, 0xe4, 0xd5, 0xb1, 0xd2, 0xcd),
  '8BIMResolutionInfoMetadataReader': GUID(0x5805137a, 0xe348, 0x4f7c, 0xb3, 0xcc, 0x6d, 0xb9, 0x96, 0x5a, 0x05, 0x99),
  '8BIMResolutionInfoMetadataWriter': GUID(0x4ff2fe0e, 0xe74a, 0x4b71, 0x98, 0xc4, 0xab, 0x7d, 0xc1, 0x67, 0x07, 0xba),
  'XMPMetadataReader': GUID(0x72b624df, 0xae11, 0x4948, 0xa6, 0x5c, 0x35, 0x1e, 0xb0, 0x82, 0x94, 0x19),
  'XMPMetadataWriter': GUID(0x1765e14e, 0x1bd4, 0x462e, 0xb6, 0xb1, 0x59, 0x0b, 0xf1, 0x26, 0x2a, 0xc6),
  'XMPStructMetadataReader': GUID(0x01b90d9a, 0x8209, 0x47f7, 0x9c, 0x52, 0xe1, 0x24, 0x4b, 0xf5, 0x0c, 0xed),
  'XMPStructMetadataWriter': GUID(0x22c21f93, 0x7ddb, 0x411c, 0x9b, 0x17, 0xc5, 0xb7, 0xbd, 0x06, 0x4a, 0xbc),
  'XMPBagMetadataReader': GUID(0xe7e79a30, 0x4f2c, 0x4fab, 0x8d, 0x00, 0x39, 0x4f, 0x2d, 0x6b, 0xbe, 0xbe),
  'XMPBagMetadataWriter': GUID(0xed822c8c, 0xd6be, 0x4301, 0xa6, 0x31, 0x0e, 0x14, 0x16, 0xba, 0xd2, 0x8f),
  'XMPSeqMetadataReader': GUID(0x7f12e753, 0xfc71, 0x43d7, 0xa5, 0x1d, 0x92, 0xf3, 0x59, 0x77, 0xab, 0xb5),
  'XMPSeqMetadataWriter': GUID(0x6d68d1de, 0xd432, 0x4b0f, 0x92, 0x3a, 0x09, 0x11, 0x83, 0xa9, 0xbd, 0xa7),
  'XMPAltMetadataReader': GUID(0xaa94dcc2, 0xb8b0, 0x4898, 0xb8, 0x35, 0x00, 0x0a, 0xab, 0xd7, 0x43, 0x93),
  'XMPAltMetadataWriter': GUID(0x076c2a6c, 0xf78f, 0x4c46, 0xa7, 0x23, 0x35, 0x83, 0xe7, 0x08, 0x76, 0xea),
  'JpegCommentMetadataReader': GUID(0x9f66347c, 0x60c4, 0x4c4d, 0xab, 0x58, 0xd2, 0x35, 0x86, 0x85, 0xf6, 0x07),
  'JpegCommentMetadataWriter': GUID(0xe573236f, 0x55b1, 0x4eda, 0x81, 0xea, 0x9f, 0x65, 0xdb, 0x02, 0x90, 0xd3),
  'LSDMetadataReader': GUID(0x41070793, 0x59e4, 0x479a, 0xa1, 0xf7, 0x95, 0x4a, 0xdc, 0x2e, 0xf5, 0xfc),
  'LSDMetadataWriter': GUID(0x73c037e7, 0xe5d9, 0x4954, 0x87, 0x6a, 0x6d, 0xa8, 0x1d, 0x6e, 0x57, 0x68),
  'IMDMetadataReader': GUID(0x7447a267, 0x0015, 0x42c8, 0xa8, 0xf1, 0xfb, 0x3b, 0x94, 0xc6, 0x83, 0x61),
  'IMDMetadataWriter': GUID(0x8c89071f, 0x452e, 0x4e95, 0x96, 0x82, 0x9d, 0x10, 0x24, 0x62, 0x71, 0x72),
  'GCEMetadataReader': GUID(0xb92e345d, 0xf52d, 0x41f3, 0xb5, 0x62, 0x08, 0x1b, 0xc7, 0x72, 0xe3, 0xb9),
  'GCEMetadataWriter': GUID(0xaf95dc76, 0x16b2, 0x47f4, 0xb3, 0xea, 0x3c, 0x31, 0x79, 0x66, 0x93, 0xe7),
  'APEMetadataReader': GUID(0x1767b93a, 0xb021, 0x44ea, 0x92, 0x0f, 0x86, 0x3c, 0x11, 0xf4, 0xf7, 0x68),
  'APEMetadataWriter': GUID(0xbd6edfca, 0x2890, 0x482f, 0xb2, 0x33, 0x8d, 0x73, 0x39, 0xa1, 0xcf, 0x8d),
  'GifCommentMetadataReader': GUID(0x32557d3b, 0x69dc, 0x4f95, 0x83, 0x6e, 0xf5, 0x97, 0x2b, 0x2f, 0x61, 0x59),
  'GifCommentMetadataWriter': GUID(0xa02797fc, 0xc4ae, 0x418c, 0xaf, 0x95, 0xe6, 0x37, 0xc7, 0xea, 0xd2, 0xa1),
  'PngTextMetadataReader': GUID(0x4b59afcc, 0xb8c3, 0x408a, 0xb6, 0x70, 0x89, 0xe5, 0xfa, 0xb6, 0xfd, 0xa7),
  'PngTextMetadataWriter': GUID(0xb5ebafb9, 0x253e, 0x4a72, 0xa7, 0x44, 0x07, 0x62, 0xd2, 0x68, 0x56, 0x83),
  'PngGamaMetadataReader': GUID(0x3692ca39, 0xe082, 0x4350, 0x9e, 0x1f, 0x37, 0x04, 0xcb, 0x08, 0x3c, 0xd5),
  'PngGamaMetadataWriter': GUID(0xff036d13, 0x5d4b, 0x46dd, 0xb1, 0x0f, 0x10, 0x66, 0x93, 0xd9, 0xfe, 0x4f),
  'PngBkgdMetadataReader': GUID(0x0ce7a4a6, 0x03e8, 0x4a60, 0x9d, 0x15, 0x28, 0x2e, 0xf3, 0x2e, 0xe7, 0xda),
  'PngBkgdMetadataWriter': GUID(0x68e3f2fd, 0x31ae, 0x4441, 0xbb, 0x6a, 0xfd, 0x70, 0x47, 0x52, 0x5f, 0x90),
  'PngItxtMetadataReader': GUID(0xaabfb2fa, 0x3e1e, 0x4a8f, 0x89, 0x77, 0x55, 0x56, 0xfb, 0x94, 0xea, 0x23),
  'PngItxtMetadataWriter': GUID(0x31879719, 0xe751, 0x4df8, 0x98, 0x1d, 0x68, 0xdf, 0xf6, 0x77, 0x04, 0xed),
  'PngChrmMetadataReader': GUID(0xf90b5f36, 0x367b, 0x402a, 0x9d, 0xd1, 0xbc, 0x0f, 0xd5, 0x9d, 0x8f, 0x62),
  'PngChrmMetadataWriter': GUID(0xe23ce3eb, 0x5608, 0x4e83, 0xbc, 0xef, 0x27, 0xb1, 0x98, 0x7e, 0x51, 0xd7),
  'PngHistMetadataReader': GUID(0x877a0bb7, 0xa313, 0x4491, 0x87, 0xb5, 0x2e, 0x6d, 0x05, 0x94, 0xf5, 0x20),
  'PngHistMetadataWriter': GUID(0x8a03e749, 0x672e, 0x446e, 0xbf, 0x1f, 0x2c, 0x11, 0xd2, 0x33, 0xb6, 0xff),
  'PngIccpMetadataReader': GUID(0xf5d3e63b, 0xcb0f, 0x4628, 0xa4, 0x78, 0x6d, 0x82, 0x44, 0xbe, 0x36, 0xb1),
  'PngIccpMetadataWriter': GUID(0x16671e5f, 0x0ce6, 0x4cc4, 0x97, 0x68, 0xe8, 0x9f, 0xe5, 0x01, 0x8a, 0xde),
  'PngSrgbMetadataReader': GUID(0xfb40360c, 0x547e, 0x4956, 0xa3, 0xb9, 0xd4, 0x41, 0x88, 0x59, 0xba, 0x66),
  'PngSrgbMetadataWriter': GUID(0xa6ee35c6, 0x87ec, 0x47df, 0x9f, 0x22, 0x1d, 0x5a, 0xad, 0x84, 0x0c, 0x82),
  'PngTimeMetadataReader': GUID(0xd94edf02, 0xefe5, 0x4f0d, 0x85, 0xc8, 0xf5, 0xa6, 0x8b, 0x30, 0x00, 0xb1),
  'PngTimeMetadataWriter': GUID(0x1ab78400, 0xb5a3, 0x4d91, 0x8a, 0xce, 0x33, 0xfc, 0xd1, 0x49, 0x9b, 0xe6),
  'HeifMetadataReader': GUID(0xacddfc3f, 0x85ec, 0x41bc, 0xbd, 0xef, 0x1b, 0xc2, 0x62, 0xe4, 0xdb, 0x05),
  'HeifMetadataWriter': GUID(0x3ae45e79, 0x40bc, 0x4401, 0xac, 0xe5, 0xdd, 0x3c, 0xb1, 0x6e, 0x6a, 0xfe),
  'HeifHDRMetadataReader': GUID(0x2438de3d, 0x94d9, 0x4be8, 0x84, 0xa8, 0x4d, 0xe9, 0x5a, 0x57, 0x5e, 0x75),
  'WebpAnimMetadataReader': GUID(0x76f9911, 0xa348, 0x465c, 0xa8, 0x7, 0xa2, 0x52, 0xf3, 0xf2, 0xd3, 0xde),
  'WICWebpAnmfMetadataReader': GUID(0x85a10b03, 0xc9f6, 0x439f, 0xbe, 0x5e, 0xc0, 0xfb, 0xef, 0x67, 0x80, 0x7c),
  'DdsMetadataReader': GUID(0x276c88ca, 0x7533, 0x4a86, 0xb6, 0x76, 0x66, 0xb3, 0x60, 0x80, 0xd4, 0x84),
  'DdsMetadataWriter': GUID(0xfd688bbd, 0x31ed, 0x4db7, 0xa7, 0x23, 0x93, 0x49, 0x27, 0xd3, 0x83, 0x67)
}
WICCOMPONENT = _GMeta('WICCOMPONENT', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {n.lower(): g for n, g in WICComponent.items()}, '_tab_gn': {g: n for n, g in WICComponent.items()}, '_def': None})
WICPCOMPONENT = type('WICPCOMPONENT', (_BPGUID, ctypes.POINTER(WICCOMPONENT)), {'_type_': WICCOMPONENT})

class _BCode:
  @classmethod
  def name_code(cls, n):
    return cls._tab_nc.get(n.lower(), cls._def) if isinstance(n, str) else n
  @classmethod
  def code_name(cls, c):
    return cls._tab_cn.get(c, str(c))
  @classmethod
  def from_param(cls, obj):
    return obj if isinstance(obj, cls.__bases__[1]) else cls.__bases__[1](cls.name_code(obj))
  @classmethod
  def to_int(cls, obj):
    return obj.code if isinstance(obj, cls) else cls.name_code(obj)
  @property
  def value(self):
    return self
  @value.setter
  def value(self, val):
    self.__class__.__bases__[1].value.__set__(self, val.__class__.__bases__[1].value.__get__(self))
  @property
  def code(self):
    return self.__class__.__bases__[1].value.__get__(self)
  @code.setter
  def code(self, val):
    self.__class__.__bases__[1].value.__set__(self, val)
  @property
  def name(self):
    return self.__class__.code_name(self.__class__.__bases__[1].value.__get__(self))
  @name.setter
  def name(self, val):
    self.__class__.__bases__[1].value.__set__(self, self.__class__.name_code(val))
  def __init__(self, val=None):
    if val is None:
      self.__class__.__bases__[1].__init__(self)
    else:
      self.__class__.__bases__[1].__init__(self, self.__class__.to_int(val))
  def __eq__(self, other):
    return self.code == (other.code if isinstance(other, _BCode) else self.__class__.name_code(other))
  def __str__(self):
    c = self.__class__.__bases__[1].value.__get__(self)
    return '<%d: %s>' % (c, self.__class__.code_name(c))
  def __repr__(self):
    return str(self)

class _BCodeOr(_BCode):
  @classmethod
  def name_code(cls, n):
    if not isinstance(n, str):
      return n
    c = 0
    for n_ in filter(None, n.lower().replace(' ', '|').replace('+', '|').split('|')):
      c |= cls._tab_nc.get(n_, cls._def)
    return c
  @classmethod
  def code_name(cls, c):
    return ' | '.join((n_ for c_, n_ in cls._tab_cn.items() if c_ == 0) if c == 0 else (n_ for c_, n_ in cls._tab_cn.items() if c_ & c == c_ and c_ != 0))
  def __or__(self, other):
    return self.__class__(self.code | (other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other)))
  def __ror__(self, other):
    return self.__class__((other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other)) | self.code)
  def __ior__(self, other):
    self.code |= (other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other))
    return self
  def __and__(self, other):
    return self.__class__(self.code & (other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other)))
  def __rand__(self, other):
    return self.__class__((other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other)) & self.code)
  def __iand__(self, other):
    self.code &= (other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other))
    return self
  def __xor__(self, other):
    return self.__class__(self.code ^ (other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other)))
  def __rxor__(self, other):
    return self.__class__((other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other)) ^ self.code)
  def __ixor__(self, other):
    self.code ^= (other.code if isinstance(other, _BCodeOr) else self.__class__.name_code(other))
    return self

class _BCodeT(_BCodeOr):
  @classmethod
  def code_name(cls, c):
    n = []
    for c_, n_ in reversed(cls._tab_cn.items()):
      if c_ & c == c_:
        n.append(n_)
        if n_.startswith('Rotate'):
          break
    return ' | '.join(n)

class Components(wintypes.DWORD):
  def __init__(self, val=0):
    self.value = self.__class__.to_int(val)
  @property
  def components(self):
    return tuple(iter(self.value.to_bytes(4).lstrip(b'\x00')))
  @property
  def code(self):
    return self.value
  @classmethod
  def to_int(cls, val):
    return int.from_bytes(bytes(val)) if isinstance(val, (list, tuple, bytes)) else int(getattr(val, 'value', val))
  def __eq__(self, other):
    return self.__class__.to_int(self) == self.__class__.to_int(other)
  def __str__(self):
    return '<%d: %s>' % (self.value, self.components)
  def __repr__(self):
    return str(self)

class _WSMeta(ctypes.Structure.__class__):
  def __init__(cls, *args, **kwargs):
    super(_WSMeta, _WSMeta).__init__(cls, *args, **kwargs)
    for f in cls._fields_:
      if issubclass(f[1], (_BGUID, _BCode, Components)):
        setattr(cls, '_' + f[0], getattr(cls, f[0]))
        setattr(cls, f[0], property(lambda s, _n='_'+f[0], _t=f[1]: _t(getattr(s, _n)), lambda s, v, _n='_'+f[0], _t=f[1]: setattr(s, _n, (_t.to_bytes if issubclass(_t, _BGUID) else _t.to_int)(v))))

WICColorContextType = {'Uninitialized': 0, 'Profile': 1, 'ExifColorSpace': 2}
WICCOLORCONTEXTTYPE = type('WICCOLORCONTEXTTYPE', (_BCode, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WICColorContextType.items()}, '_tab_cn': {c: n for n, c in WICColorContextType.items()}, '_def': 0})
WICPCOLORCONTEXTTYPE = ctypes.POINTER(WICCOLORCONTEXTTYPE)

WICEXIFColorSpace = {'sRGB': 1, 'AdobeRGB': 2, 'Adobe RGB': 2, 'Uncalibrated': 65535}
WICEXIFCOLORSPACE = type('WICEXIFCOLORSPACE', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in WICEXIFColorSpace.items()}, '_tab_cn': {c: n for n, c in WICEXIFColorSpace.items()}, '_def': 1})
WICPEXIFCOLORSPACE = ctypes.POINTER(WICEXIFCOLORSPACE)

WICPaletteType = {'Custom': 0, 'MedianCut': 1, 'FixedBW': 2, 'FixedHalftone8': 3, 'FixedHalftone27': 4, 'FixedHalftone64': 5, 'FixedHalftone125': 6, 'FixedHalftone216': 7, 'FixedHalftone252': 8, 'FixedHalftone256': 9, 'FixedGray4': 10, 'FixedGray16': 11, 'FixedGray256': 12}
WICPALETTETYPE = type('WICPALETTETYPE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICPaletteType.items()}, '_tab_cn': {c: n for n, c in WICPaletteType.items()}, '_def': 0})
WICPPALETTETYPE = ctypes.POINTER(WICPALETTETYPE)

WICDecoderCapabilities = {'None': 0, 'SameEncoder': 1, 'CanDecodeAllImages': 2, 'CanDecodeSomeImages': 4, 'CanEnumerateMetadata': 8, 'CanDecodeThumbnail': 16}
WICDECODERCAPABILITIES = type('WICDECODERCAPABILITIES', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICDecoderCapabilities.items()}, '_tab_cn': {c: n for n, c in WICDecoderCapabilities.items()}, '_def': 0})
WICPDECODERCAPABILITIES = ctypes.POINTER(WICDECODERCAPABILITIES)

WICDecodeOption = {'Demand': 0, 'OnDemand': 0, 'Load': 1, 'OnLoad': 1}
WICDECODEOPTION = type('WICDECODEOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICDecodeOption.items()}, '_tab_cn': {c: n for n, c in WICDecodeOption.items()}, '_def': 0})

WICBitmapEncoderCacheOption = {'InMemory': 0, 'TempFile': 1, 'None': 2, 'No': 2}
WICBITMAPENCODERCACHEOPTION = type('WICBITMAPENCODERCACHEOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICBitmapEncoderCacheOption.items()}, '_tab_cn': {c: n for n, c in WICBitmapEncoderCacheOption.items()}, '_def': 2})

WICJpegYCrCbSubsamplingOption = {'Default': 0, '420': 1, '422': 2, '444': 3, '440': 4}
WICJPEGYCRCBSUBSAMPLINGOPTION = type('WICJPEGYCRCBSUBSAMPLINGOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICJpegYCrCbSubsamplingOption.items()}, '_tab_cn': {c: n for n, c in WICJpegYCrCbSubsamplingOption.items()}, '_def': 0})

WICJpegIndexingOption = {'Demand': 0, 'OnDemand': 0, 'Load': 1, 'OnLoad': 1}
WICJPEGINDEXINGOPTION = type('WICJPEGINDEXINGOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICJpegIndexingOption.items()}, '_tab_cn': {c: n for n, c in WICJpegIndexingOption.items()}, '_def': 0})

WICJpegTransferMatrix = {'Identity': 0, 'BT601': 1}
WICJPEGTRANSFERMATRIX = type('WICJPEGTRANSFERMATRIX', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICJpegTransferMatrix.items()}, '_tab_cn': {c: n for n, c in WICJpegTransferMatrix.items()}, '_def': 0})

WICJpegScanType = {'Interleaved': 0, 'PlanarComponents': 1, 'Progressive': 2}
WICJPEGSCANTYPE = type('WICJPEGSCANTYPE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICJpegScanType.items()}, '_tab_cn': {c: n for n, c in WICJpegScanType.items()}, '_def': 0})

WICJpegSampleFactors = {'One': 0x11, 'Three_420': 0x111122, 'Three_422': 0x111121, 'Three_440': 0x111112, 'Three_444': 0x111111}
WICJPEGSAMPLEFACTORS = type('WICJPEGSAMPLEFACTORS', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICJpegSampleFactors.items()}, '_tab_cn': {c: n for n, c in WICJpegSampleFactors.items()}, '_def': 0x111122})

WICJpegQuantizationBaseline = {'One': 0x0, 'Three': 0x10100}
WICJPEGQUANTIZATIONBASELINE = type('WICJPEGQUANTIZATIONBASELINE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICJpegQuantizationBaseline.items()}, '_tab_cn': {c: n for n, c in WICJpegQuantizationBaseline.items()}, '_def': 0x10100})

WICJpegHuffmanBaseline = {'One': 0x0, 'Three': 0x111100}
WICJPEGHUFFMANBASELINE = type('WICJPEGHUFFMANBASELINE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICJpegHuffmanBaseline.items()}, '_tab_cn': {c: n for n, c in WICJpegHuffmanBaseline.items()}, '_def': 0x111100})

class WICJPEGFRAMEHEADER(ctypes.Structure):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('TransferMatrix', WICJPEGTRANSFERMATRIX), ('ScanType', WICJPEGSCANTYPE), ('cComponents', wintypes.UINT), ('ComponentIdentifiers', Components), ('SampleFactors', WICJPEGSAMPLEFACTORS), ('QuantizationTableIndices', WICJPEGQUANTIZATIONBASELINE)]
  def to_dict(self):
    return {k[0]: getattr(self, k[0]) for k in self.__class__._fields_}

WICPJPEGFRAMEHEADER = ctypes.POINTER(WICJPEGFRAMEHEADER)

class WICJPEGDCHUFFMANTABLE(ctypes.Structure):
  _fields_ = [('CodeCounts', wintypes.BYTE * 12), ('CodeValues', wintypes.BYTE * 12)]
  def to_dict(self):
    return {'CodeCounts': self.CodeCounts, 'CodeValues': self.CodeValues}
WICPJPEGDCHUFFMANTABLE = ctypes.POINTER(WICJPEGDCHUFFMANTABLE)

class WICJPEGACHUFFMANTABLE(ctypes.Structure):
  _fields_ = [('CodeCounts', wintypes.BYTE * 16), ('CodeValues', wintypes.BYTE * 162)]
  def to_dict(self):
    return {'CodeCounts': self.CodeCounts, 'CodeValues': self.CodeValues}
WICPJPEGACHUFFMANTABLE = ctypes.POINTER(WICJPEGACHUFFMANTABLE)

class WICJPEGQUANTIZATIONTABLE(ctypes.Structure):
  _fields_ = [('Elements', wintypes.BYTE * 64),]
WICPJPEGQUANTIZATIONTABLE = ctypes.POINTER(WICJPEGQUANTIZATIONTABLE)

class WICJPEGSCANHEADER(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cComponents', wintypes.UINT), ('RestartInterval', wintypes.UINT), ('ComponentSelectors', Components), ('HuffmanTableIndices', WICJPEGHUFFMANBASELINE), ('StartSpectralSelection', wintypes.BYTE), ('EndSpectralSelection', wintypes.BYTE), ('SuccessiveApproximationHigh', wintypes.BYTE), ('SuccessiveApproximationLow', wintypes.BYTE)]
  def to_dict(self):
    return {k[0]: getattr(self, k[0]) for k in self.__class__._fields_}
WICPJPEGSCANHEADER = ctypes.POINTER(WICJPEGSCANHEADER)

DXGIFormat = {'UNKNOWN': 0, 'R32G32B32A32_TYPELESS': 1, 'R32G32B32A32_FLOAT': 2, 'R32G32B32A32_UINT': 3, 'R32G32B32A32_SINT': 4, 'R32G32B32_TYPELESS': 5, 'R32G32B32_FLOAT': 6, 'R32G32B32_UINT': 7, 'R32G32B32_SINT': 8, 'R16G16B16A16_TYPELESS': 9, 'R16G16B16A16_FLOAT': 10, 'R16G16B16A16_UNORM': 11, 'R16G16B16A16_UINT': 12, 'R16G16B16A16_SNORM': 13, 'R16G16B16A16_SINT': 14, 'R32G32_TYPELESS': 15, 'R32G32_FLOAT': 16, 'R32G32_UINT': 17, 'R32G32_SINT': 18, 'R32G8X24_TYPELESS': 19, 'D32_FLOAT_S8X24_UINT': 20, 'R32_FLOAT_X8X24_TYPELESS': 21, 'X32_TYPELESS_G8X24_UINT': 22, 'R10G10B10A2_TYPELESS': 23, 'R10G10B10A2_UNORM': 24, 'R10G10B10A2_UINT': 25, 'R11G11B10_FLOAT': 26, 'R8G8B8A8_TYPELESS': 27, 'R8G8B8A8_UNORM': 28, 'R8G8B8A8_UNORM_SRGB': 29, 'R8G8B8A8_UINT': 30, 'R8G8B8A8_SNORM': 31, 'R8G8B8A8_SINT': 32, 'R16G16_TYPELESS': 33, 'R16G16_FLOAT': 34, 'R16G16_UNORM': 35, 'R16G16_UINT': 36, 'R16G16_SNORM': 37, 'R16G16_SINT': 38, 'R32_TYPELESS': 39, 'D32_FLOAT': 40, 'R32_FLOAT': 41, 'R32_UINT': 42, 'R32_SINT': 43, 'R24G8_TYPELESS': 44, 'D24_UNORM_S8_UINT': 45, 'R24_UNORM_X8_TYPELESS': 46, 'X24_TYPELESS_G8_UINT': 47, 'R8G8_TYPELESS': 48, 'R8G8_UNORM': 49, 'R8G8_UINT': 50, 'R8G8_SNORM': 51, 'R8G8_SINT': 52, 'R16_TYPELESS': 53, 'R16_FLOAT': 54, 'D16_UNORM': 55, 'R16_UNORM': 56, 'R16_UINT': 57, 'R16_SNORM': 58, 'R16_SINT': 59, 'R8_TYPELESS': 60, 'R8_UNORM': 61, 'R8_UINT': 62, 'R8_SNORM': 63, 'R8_SINT': 64, 'A8_UNORM': 65, 'R1_UNORM': 66, 'R9G9B9E5_SHAREDEXP': 67, 'R8G8_B8G8_UNORM': 68, 'G8R8_G8B8_UNORM': 69, 'BC1_TYPELESS': 70, 'BC1_UNORM': 71, 'BC1_UNORM_SRGB': 72, 'BC2_TYPELESS': 73, 'BC2_UNORM': 74, 'BC2_UNORM_SRGB': 75, 'BC3_TYPELESS': 76, 'BC3_UNORM': 77, 'BC3_UNORM_SRGB': 78, 'BC4_TYPELESS': 79, 'BC4_UNORM': 80, 'BC4_SNORM': 81, 'BC5_TYPELESS': 82, 'BC5_UNORM': 83, 'BC5_SNORM': 84, 'B5G6R5_UNORM': 85, 'B5G5R5A1_UNORM': 86, 'B8G8R8A8_UNORM': 87, 'B8G8R8X8_UNORM': 88, 'R10G10B10_XR_BIAS_A2_UNORM': 89, 'B8G8R8A8_TYPELESS': 90, 'B8G8R8A8_UNORM_SRGB': 91, 'B8G8R8X8_TYPELESS': 92, 'B8G8R8X8_UNORM_SRGB': 93, 'BC6H_TYPELESS': 94, 'BC6H_UF16': 95, 'BC6H_SF16': 96, 'BC7_TYPELESS': 97, 'BC7_UNORM': 98, 'BC7_UNORM_SRGB': 99, 'AYUV': 100, 'Y410': 101, 'Y416': 102, 'NV12': 103, 'P010': 104, 'P016': 105, '420_OPAQUE': 106, 'YUY2': 107, 'Y210': 108, 'Y216': 109, 'NV11': 110, 'AI44': 111, 'IA44': 112, 'P8': 113, 'A8P8': 114, 'B4G4R4A4_UNORM': 115, 'P208': 130, 'V208': 131, 'V408': 132, 'SAMPLER_FEEDBACK_MIN_MIP_OPAQUE': 189, 'SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE': 190, 'A4B4G4R4_UNORM': 191}
DXGIFORMAT = type('DXGIFORMAT', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIFormat.items()}, '_tab_cn': {c: n for n, c in DXGIFormat.items()}, '_def': 0})

WICDdsDimension = {'1D': 0, '2D': 1, '3D': 2, 'Cube': 3}
WICDDSDIMENSION = type('WICDDSDIMENSION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICDdsDimension.items()}, '_tab_cn': {c: n for n, c in WICDdsDimension.items()}, '_def': 0})

WICDdsAlphaMode = {'Unknown': 0, 'Straight': 1, 'Premultiplied': 2, 'Opaque': 3, 'Custom': 4}
WICDDSALPHAMODE = type('WICDDSALPHAMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICDdsAlphaMode.items()}, '_tab_cn': {c: n for n, c in WICDdsAlphaMode.items()}, '_def': 0})

class WICDDSFORMATINFO(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('DxgiFormat', DXGIFORMAT), ('BytesPerBlock', wintypes.UINT), ('BlockWidth', wintypes.UINT), ('BlockHeight', wintypes.UINT)]
  def to_dict(self):
    return {k[0]: getattr(self, k[0]) for k in self.__class__._fields_}
WICPDDSFORMATINFO = ctypes.POINTER(WICDDSFORMATINFO)

class WICDDSPARAMETERS(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('Depth', wintypes.UINT), ('MipLevels', wintypes.UINT), ('ArraySize', wintypes.UINT), ('DxgiFormat', DXGIFORMAT), ('Dimension', WICDDSDIMENSION), ('AlphaMode', WICDDSALPHAMODE)]
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, dict):
      return cls(obj.get('Width', 0), obj.get('Height', 0), obj.get('Depth', 0), obj.get('MipLevels', 0), obj.get('ArraySize', 0), obj.get('DxgiFormat', 'UNKNOWN'), obj.get('Dimension', 0), obj.get('AlphaMode', 0))
    else:
      return cls(*obj)
  def to_dict(self):
    return {k[0]: getattr(self, k[0]) for k in self.__class__._fields_}
WICPDDSPARAMETERS = ctypes.POINTER(WICDDSPARAMETERS)

class WICBITMAPPLANE(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Format', WICPIXELFORMAT), ('pbBuffer', wintypes.LPVOID), ('cbStride', wintypes.UINT), ('cbBufferSize', wintypes.UINT)]
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, IWICBitmapLock):
      return cls(obj.GetPixelFormat(), ctypes.cast((dp := obj.GetDataPointer()), wintypes.LPVOID), obj.GetStride(), len(dp))
    elif isinstance(obj, dict):
      return cls(obj.get('Format', 'DontCare'), ctypes.cast(PBUFFER.from_param(obj.get('pbBuffer', None)), wintypes.LPVOID), obj.get('cbStride', 0), PBUFFER.length(obj.get('pbBuffer', None)))
    else:
      return cls(obj[0], ctypes.cast(PBUFFER.from_param(obj[1]), wintypes.LPVOID), obj[2], PBUFFER.length(obj[1]))
WICPBITMAPPLANE = ctypes.POINTER(WICBITMAPPLANE)

WICPngFilterOption = {'Unspecified': 0, 'None': 1, 'Sub': 2, 'Up': 3, 'Average': 4, 'Paeth': 5, 'Adaptive': 6}
WICPNGFILTEROPTION = type('WICPNGFILTEROPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICPngFilterOption.items()}, '_tab_cn': {c: n for n, c in WICPngFilterOption.items()}, '_def': 0})

WICTiffCompressionOption = {'DontCare': 0, 'None': 1, 'CCITT3': 2, 'CCITT4': 3, 'LZW': 4, 'RLE': 5, 'ZIP': 6, 'Differencing': 7}
WICTIFFCOMPRESSIONOPTION = type('WICTIFFCOMPRESSIONOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICTiffCompressionOption.items()}, '_tab_cn': {c: n for n, c in WICTiffCompressionOption.items()}, '_def': 0})

WICHeifCompressionOption = {'DontCare': 0, 'None': 1, 'HEVC': 2, 'AV1': 3}
WICHEIFCOMPRESSIONOPTION = type('WICHEIFCOMPRESSIONOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICHeifCompressionOption.items()}, '_tab_cn': {c: n for n, c in WICHeifCompressionOption.items()}, '_def': 0})

WICCreateCacheOption = {'None': 0, 'No': 0, 'Demand': 1, 'OnDemand': 1, 'Load': 2, 'OnLoad': 2}
WICCREATECACHEOPTION = type('WICCREATECACHEOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICCreateCacheOption.items()}, '_tab_cn': {c: n for n, c in WICCreateCacheOption.items()}, '_def': 0})

D2D1AlphaMode = {'Unknown': 0, 'Premultiplied': 1, 'Straight': 2, 'Ignore': 3}
D2D1ALPHAMODE = type('D2D1ALPHAMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1AlphaMode.items()}, '_tab_cn': {c: n for n, c in D2D1AlphaMode.items()}, '_def': 0})

class D2D1PIXELFORMAT(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('format', DXGIFORMAT), ('alphaMode', D2D1ALPHAMODE)]

class WICIMAGEPARAMETERS(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('PixelFormat', D2D1PIXELFORMAT), ('DpiX', wintypes.FLOAT), ('DpiY', wintypes.FLOAT), ('Top', wintypes.FLOAT), ('Left', wintypes.FLOAT), ('PixelWidth', wintypes.UINT), ('PixelHeight', wintypes.UINT)]
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, dict):
      return cls((pf if isinstance((pf := obj.get('PixelFormat', D2D1PIXELFORMAT())), D2D1PIXELFORMAT) else D2D1PIXELFORMAT(pf.get('format', 0), pf.get('alphaMode', 0))), obj.get('DpiX', 0), obj.get('DpiY', 0), obj.get('Top', 0), obj.get('Left', 0), obj.get('PixelWidth', 0), obj.get('PixelHeight', 0))
    else:
      return cls((pf if isinstance((pf := obj[0]), D2D1PIXELFORMAT) else D2D1PIXELFORMAT(pf[0], pf[1])), obj[1], obj[2], obj[3], obj[4], obj[5], obj[6])
WICPIMAGEPARAMETERS = ctypes.POINTER(WICIMAGEPARAMETERS)

WICBitmapAlphaChannelOption = {'Use': 0, 'UseAlpha': 0, 'UsePremultiplied': 1, 'UsePremultipliedAlpha': 1, 'Ignore': 2, 'IgnoreAlpha': 2}
WICBITMAPALPHACHANNELOPTION = type('WICBITMAPALPHACHANNELOPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICBitmapAlphaChannelOption.items()}, '_tab_cn': {c: n for n, c in WICBitmapAlphaChannelOption.items()}, '_def': 0})

WICPersistOptions = {'Default': 0, 'LittleEndian': 0, 'BigEndian': 1, 'StrictFormat': 2, 'NoCacheStream': 4, 'PreferUTF8': 8}
WICPERSISTOPTIONS = type('WICPERSISTOPTIONS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICPersistOptions.items()}, '_tab_cn': {c: n for n, c in WICPersistOptions.items()}, '_def': 0})
WICPPERSISTOPTIONS = ctypes.POINTER(WICPERSISTOPTIONS)

WICMetadataCreationOptions = {**WICPersistOptions, 'Default': 0x0, 'AllowUnknown': 0x0, 'FailUnknown': 0x10000}
WICMETADATACREATIONOPTIONS = type('WICMETADATACREATIONOPTIONS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICMetadataCreationOptions.items()}, '_tab_cn': {c: n for n, c in WICMetadataCreationOptions.items()}, '_def': 0})

WICDitherType = {'None': 0, 'Solid': 0, 'Ordered4x4': 1, 'Ordered8x8': 2, 'Ordered16x16': 3, 'Spiral4x4': 4, 'Spiral8x8': 5, 'DualSpiral4x4': 6, 'DualSpiral8x8': 7, 'ErrorDiffusion': 8}
WICDITHERTYPE = type('WICDITHERTYPE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICDitherType.items()}, '_tab_cn': {c: n for n, c in WICDitherType.items()}, '_def': 0})

WICInterpolationMode = {'Nearest': 0, 'NearestNeighbor': 0, 'Linear': 1, 'Cubic': 2, 'Fant': 3, 'HighQualityCubic': 4}
WICINTERPOLATIONMODE = type('WICINTERPOLATIONMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICInterpolationMode.items()}, '_tab_cn': {c: n for n, c in WICInterpolationMode.items()}, '_def': 3})

WICTransformOptions = {'Rotate0': 0, 'Rotate90': 1, 'Rotate180': 2, 'Rotate270': 3, 'FlipHorizontal': 8, 'FlipVertical': 16}
WICTRANSFORMOPTIONS = type('WICTRANSFORMOPTIONS', (_BCodeT, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICTransformOptions.items()}, '_tab_cn': {c: n for n, c in WICTransformOptions.items()}, '_def': 0})

WICPlanarOption = {'Default': 0, 'PreserveSubsampling': 1}
WICPLANAROPTION = type('WICPLANAROPTION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICPlanarOption.items()}, '_tab_cn': {c: n for n, c in WICPlanarOption.items()}, '_def': 0})

class WICBITMAPPLANEDESCRIPTION(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Format', WICPIXELFORMAT), ('Width', wintypes.UINT), ('Height', wintypes.UINT)]
  def to_dict(self):
    return {k[0]: getattr(self, k[0]) for k in self.__class__._fields_}
WICPBITMAPPLANEDESCRIPTION = ctypes.POINTER(WICBITMAPPLANEDESCRIPTION)

WICComponentType = {'BitmapDecoder': 0x1, 'Decoder': 0x1, 'BitmapEncoder': 0x2, 'Encoder': 0x2, 'FormatConverter': 0x4 , 'PixelFormatConverter': 0x4, 'MetadataReader': 0x8, 'MetadataWriter': 0x10, 'PixelFormat': 0x20, 'Component': 0x3f, 'AllComponents': 0x3f}
WICCOMPONENTTYPE = type('WICCOMPONENTTYPE', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICComponentType.items()}, '_tab_cn': {c: n for n, c in WICComponentType.items()}, '_def': 0x3f})
WICPCOMPONENTTYPE = ctypes.POINTER(WICCOMPONENTTYPE)

WICComponentSigning = {'Signed': 0x1, 'Unsigned': 0x2, 'Safe': 0x4, 'Disabled': 0x80000000}
WICCOMPONENTSIGNING = type('WICCOMPONENTSIGNING', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICComponentSigning.items()}, '_tab_cn': {c: n for n, c in WICComponentSigning.items()}, '_def': 0x4})
WICPCOMPONENTSIGNING = ctypes.POINTER(WICCOMPONENTSIGNING)

WICComponentEnumerateOptions = {'Default': 0x0, 'Refresh': 0x1, 'Disabled': 0x80000000, 'Unsigned': 0x40000000, 'BuiltInOnly': 0x20000000}
WICCOMPONENTENUMERATEOPTIONS = type('WICCOMPONENTENUMERATEOPTIONS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICComponentEnumerateOptions.items()}, '_tab_cn': {c: n for n, c in WICComponentEnumerateOptions.items()}, '_def': 0x0})

class WICBITMAPPATTERN(ctypes.Structure):
  _fields_ = [('Position', wintypes.ULARGE_INTEGER), ('Length', wintypes.ULONG), ('Pattern', wintypes.LPVOID), ('Mask', wintypes.LPVOID), ('EndOfStream', wintypes.BOOLE)]
  def to_dict(self):
    return {'Position': self.Position, 'Pattern': ctypes.string_at(self.Pattern, self.Length), 'Mask': ctypes.string_at(self.Mask, self.Length), 'EndofStream': self.EndOfStream.value}

WICPixelFormatNumericRepresentation = {'Unspecified': 0, 'Indexed': 1, 'UnsignedInteger': 2, 'SignedInteger': 3, 'Fixed': 4, 'Float': 5}
WICPIXELFORMATNUMERICREPRESENTATION = type('WICPIXELFORMATNUMERICREPRESENTATION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICPixelFormatNumericRepresentation.items()}, '_tab_cn': {c: n for n, c in WICPixelFormatNumericRepresentation.items()}, '_def': 0})
WICPPIXELFORMATNUMERICREPRESENTATION = ctypes.POINTER(WICPIXELFORMATNUMERICREPRESENTATION)

class WICMETADATAPATTERN(ctypes.Structure):
  _fields_ = [('Position', wintypes.ULARGE_INTEGER), ('Length', wintypes.ULONG), ('Pattern', wintypes.LPVOID), ('Mask', wintypes.LPVOID), ('DataOffset', wintypes.ULARGE_INTEGER)]
  def to_dict(self):
    return {'Position': self.Position, 'Pattern': ctypes.string_at(self.Pattern, self.Length), 'Mask': ctypes.string_at(self.Mask, self.Length), 'DataOffset': self.DataOffset}

class WICMETADATAHEADER(ctypes.Structure):
  _fields_ = [('Position', wintypes.ULARGE_INTEGER), ('Length', wintypes.ULONG), ('Header', wintypes.LPVOID), ('DataOffset', wintypes.ULARGE_INTEGER)]
  def to_dict(self):
    return {'Position': self.Position, 'Header': ctypes.string_at(self.Header, self.Length), 'DataOffset': self.DataOffset}

class PXYWH(wintypes.INT * 4):
  @classmethod
  def from_param(cls, obj):
    return None if obj is None else ctypes.byref((wintypes.INT * 4)(*obj))

class IWICBitmapSource(IUnknown):
  IID = GUID(0x00000120, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['GetSize'] = 3, (), (wintypes.PUINT, wintypes.PUINT)
  _protos['GetPixelFormat'] = 4, (), (WICPPIXELFORMAT,)
  _protos['GetResolution'] = 5, (), (wintypes.PDOUBLE, wintypes.PDOUBLE)
  _protos['CopyPalette'] = 6, (wintypes.LPVOID,), ()
  _protos['CopyPixels'] = 7, (PXYWH, wintypes.UINT, wintypes.UINT, PBUFFER), ()
  def GetSize(self):
    return self.__class__._protos['GetSize'](self.pI)
  def GetResolution(self):
    return self.__class__._protos['GetResolution'](self.pI)
  def GetPixelFormat(self):
    return self.__class__._protos['GetPixelFormat'](self.pI)
  def CopyPixels(self, xywh, stride, buffer):
    return self.__class__._protos['CopyPixels'](self.pI, xywh, stride, PBUFFER.length(buffer), buffer)
  def CopyPalette(self, palette):
    return self.__class__._protos['CopyPalette'](self.pI, palette)

class IWICColorContext(IUnknown):
  IID = GUID(0x3c613a02, 0x34b2, 0x44ea, 0x9a, 0x7c, 0x45, 0xae, 0xa9, 0xc6, 0xfd, 0x6d)
  _protos['InitializeFromFilename'] = 3, (wintypes.LPCWSTR,), ()
  _protos['InitializeFromMemory'] = 4, (PBUFFER, wintypes.UINT), ()
  _protos['InitializeFromExifColorSpace'] = 5, (WICEXIFCOLORSPACE,), ()
  _protos['GetType'] = 6, (), (WICPCOLORCONTEXTTYPE,)
  _protos['GetProfileBytes'] = 7, (wintypes.UINT, PBUFFER), (wintypes.PUINT,)
  _protos['GetExifColorSpace'] = 8, (), (WICPEXIFCOLORSPACE,)
  def GetType(self):
    return self.__class__._protos['GetType'](self.pI)
  def GetExifColorSpace(self):
    return self.__class__._protos['GetExifColorSpace'](self.pI)
  def GetProfileBytes(self):
    if (al := self.__class__._protos['GetProfileBytes'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return bytearray()
    b = bytearray(al)
    return None if self.__class__._protos['GetProfileBytes'](self.pI, al, b) is None else b
  def InitializeFromExifColorSpace(self, color_space=1):
    return self.__class__._protos['InitializeFromExifColorSpace'](self.pI, color_space)
  def InitializeFromFilename(self, file_name):
    return self.__class__._protos['InitializeFromFilename'](self.pI, file_name)
  def InitializeFromMemory(self, buffer):
    return self.__class__._protos['InitializeFromMemory'](self.pI, buffer, PBUFFER.length(buffer))

class IWICPalette(IUnknown):
  IID = GUID(0x00000040, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['InitializePredefined'] = 3, (WICPALETTETYPE, wintypes.BOOL), ()
  _protos['InitializeCustom'] = 4, (wintypes.PUINT, wintypes.UINT), ()
  _protos['InitializeFromBitmap'] = 5, (wintypes.LPVOID, wintypes.UINT, wintypes.BOOL), ()
  _protos['InitializeFromPalette'] = 6, (wintypes.LPVOID,), ()
  _protos['GetType'] = 7, (), (WICPPALETTETYPE,)
  _protos['GetColorCount'] = 8, (), (wintypes.PUINT,)
  _protos['GetColors'] = 9, (wintypes.UINT, wintypes.PUINT,), (wintypes.PUINT,)
  _protos['IsBlackWhite'] = 10, (), (wintypes.PBOOLE,)
  _protos['IsGrayscale'] = 11, (), (wintypes.PBOOLE,)
  _protos['HasAlpha'] = 12, (), (wintypes.PBOOLE,)
  def GetType(self):
    return self.__class__._protos['GetType'](self.pI)
  def GetColorCount(self):
    return self.__class__._protos['GetColorCount'](self.pI)
  def IsBlackWhite(self):
    return self.__class__._protos['IsBlackWhite'](self.pI)
  def IsGrayscale(self):
    return self.__class__._protos['IsGrayscale'](self.pI)
  def HasAlpha(self):
    return self.__class__._protos['HasAlpha'](self.pI)
  def GetColors(self, number=None):
    if number is None:
      if (number := self.GetColorCount()) is None:
        return None
    c = (wintypes.UINT * number)()
    ac = self.__class__._protos['GetColors'](self.pI, number, c)
    return None if ac is None else (wintypes.UINT * ac).from_buffer(c)
  def InitializePredefined(self, palette_type, add_transparent=False):
    return self.__class__._protos['InitializePredefined'](self.pI, palette_type, add_transparent)
  def InitializeCustom(self, colors):
    if isinstance(colors, (list, tuple)):
      c = (wintypes.UINT * len(colors))(*colors)
    else:
      c = (wintypes.UINT * len(colors)).from_buffer(colors)
    return self.__class__._protos['InitializeCustom'](self.pI, c, len(colors))
  def InitializeFromBitmap(self, source, number, add_transparent=False):
    return self.__class__._protos['InitializeFromBitmap'](self.pI, source, number, add_transparent)
  def InitializeFromPalette(self, palette):
    return self.__class__._protos['InitializeFromPalette'](self.pI, palette)

class _BLOBMeta(ctypes.Structure.__class__):
  def __mul__(bcls, size):
    return type('BLOB_Array_%d' % size, (ctypes.Structure.__class__.__mul__(bcls, size),), {'__init__': lambda s, *args, **kwargs: s.__class__.__bases__[0].__init__(s, *map(BLOB, args), **kwargs)})

class BLOB(ctypes.Structure, metaclass=_BLOBMeta):
  _fields_ = [('cbSize', wintypes.ULONG), ('pBlobdata', wintypes.LPVOID)]
  @property
  def content(self):
   return ctypes.string_at(self.pBlobdata, self.cbSize) if self.pBlobdata else None
  @content.setter
  def content(self, data):
    self.cbSize = len(data)
    self.pBlobdata = ctypes.cast(ctypes.pointer(ctypes.create_string_buffer(data if isinstance(data, bytes) else bytes(data), self.cbSize)), wintypes.LPVOID)
  def __init__(self, data=None):
    super().__init__()
    if data is not None:
      self.content = data

class _BSTRMeta(ctypes._Pointer.__class__):
  def __mul__(bcls, size):
    return type('BSTR_Array_%d' % size, (ctypes._Pointer.__class__.__mul__(bcls, size),), {'__init__': lambda s, *args, **kwargs: s.__class__.__bases__[0].__init__(s, *map(BSTR, args), **kwargs)})

class BSTR(ctypes.POINTER(wintypes.WCHAR), metaclass=_BSTRMeta):
  _type_ = wintypes.WCHAR
  oleauto32.SysAllocString.restype = wintypes.LPVOID
  oleauto32.SysAllocStringByteLen.restype = wintypes.LPVOID
  def __new__(cls, data=None):
    self = ctypes.POINTER(wintypes.WCHAR).__new__(cls)
    if isinstance(data, BSTR):
      self._needsfree = False
      bstr = data.bstr
    elif isinstance(data, wintypes.LPVOID):
      self._needsfree = False
      bstr = data
    elif isinstance(data, int):
      self._needsfree = False
      bstr = wintypes.LPVOID(data)
    elif isinstance(data, wintypes.LPCWSTR):
      self._needsfree = True
      bstr = wintypes.LPVOID(oleauto32.SysAllocString(data))
    elif isinstance(data, ctypes.Array) and getattr(data, '_type_') == wintypes.WCHAR:
      self._needsfree = True
      bstr = wintypes.LPVOID(oleauto32.SysAllocString(ctypes.byref(data)))
    elif isinstance(data, str):
      self._needsfree = True
      bstr = wintypes.LPVOID(oleauto32.SysAllocString(wintypes.LPCWSTR(data)))
    else:
      self._needsfree = True
      bstr = wintypes.LPVOID(oleauto32.SysAllocStringByteLen(PBUFFER.from_param(data),PBUFFER.length(data)))
    ctypes.c_void_p.from_address(ctypes.addressof(self)).value = bstr.value
    self.bstr = ctypes.cast(self, ctypes.c_void_p)
    return self
  @property
  def value(self):
    return getattr(getattr(self, 'bstr', ctypes.cast(self, ctypes.c_void_p)), 'value', 0)
  @property
  def content(self):
    if not hasattr(self, 'bstr'):
      self.bstr = ctypes.cast(self, ctypes.c_void_p)
    if not self.bstr:
      return None
    l = wintypes.UINT(oleauto32.SysStringLen(self.bstr))
    return ctypes.wstring_at(self.bstr, l.value)
  def __init__(self, *args, **kwargs):
    super().__init__()
  def __del__(self):
    if (bstr := getattr(self, 'bstr', ctypes.cast(self, ctypes.c_void_p))) and getattr(self, '_needsfree', False):
      oleauto32.SysFreeString(bstr)
      self.bstr = None

class CA(ctypes.Structure):
  _fields_ = [('vc', wintypes.DWORD), ('vp', wintypes.LPVOID)]
  def content(self, etype):
    if isinstance(etype, (int, str)):
      etype = _BVType.vtype_code(etype)
      etype = None if etype is None else _BVARIANT.code_ctype.get(etype & 4095)
    return (etype * self.vc).from_buffer_copy(ctypes.cast(self.vp, ctypes.POINTER(etype * self.vc)).contents) if etype is not None and self.vp else None
  def __new__(cls, etype=None, data=None):
    self = ctypes.Structure.__new__(cls)
    if data is not None:
      if isinstance(etype, (int, str)):
        etype = _BVType.vtype_code(etype)
        etype = None if etype is None else _BVARIANT.code_ctype.get(etype & 4095)
      if etype is None:
        return None
      self.vc = len(data)
      self.vp = ctypes.cast(ctypes.pointer(data) if isinstance(data, etype * self.vc) else ctypes.pointer((etype * self.vc)(*data)), wintypes.LPVOID)
    return self
  def __init__(self, etype=None, data=None):
    super().__init__()

class SAFEARRAYBOUND(ctypes.Structure):
  _fields_ = [('cElements', wintypes.ULONG), ('lLbound', wintypes.LONG)]

class PSAFEARRAY(ctypes.POINTER(wintypes.USHORT)):
  _type_ = wintypes.USHORT
  oleauto32.SafeArrayCreate.restype = wintypes.LPVOID
  def __new__(cls, *args):
    if len(args) == 1:
      if (psafearray := (args[0].psafearray if isinstance(args[0], PSAFEARRAY) else args[0])) is None:
        return None
      self = ctypes.POINTER(wintypes.USHORT).__new__(cls)
      vtype = ctypes.c_ushort()
      if oleauto32.SafeArrayGetVartype(psafearray, ctypes.byref(vtype)):
        return None
      self.vtype = vtype.value
      self.ndims = oleauto32.SafeArrayGetDim(psafearray)
      if self.ndims == 0:
        return None
      self.esize = oleauto32.SafeArrayGetElemsize(psafearray)
      if self.esize == 0:
        return None
      shape = []
      for dim in range(1, self.ndims + 1):
        lbound = wintypes.LONG()
        if oleauto32.SafeArrayGetLBound(psafearray, wintypes.UINT(dim), ctypes.byref(lbound)):
          return None
        ubound = wintypes.LONG()
        if oleauto32.SafeArrayGetUBound(psafearray, wintypes.UINT(dim), ctypes.byref(ubound)):
          return None
        shape.append(ubound.value - lbound.value + 1)
      self.shape = tuple(shape)
      self.size = self.esize
      for dim in range(self.ndims):
        self.size *= shape[dim]
    elif len(args) == 2:
      vtype, data = args
      if (vtype := _BVType.vtype_code(vtype)) is None:
        return None
      self = ctypes.POINTER(wintypes.USHORT).__new__(cls)
      vtype &= 4095
      self.vtype = vtype
      if isinstance(data, ctypes.Array):
        shape = []
        size = 1
        d = type(data)
        while issubclass(d, ctypes.Array):
          shape.append(d._length_)
          size *= shape[-1]
          d = d._type_
        self.shape = tuple(shape)
        self.esize = ctypes.sizeof(d)
        self.size = size * self.esize
      else:
        self.shape = data.shape if isinstance(data, memoryview) else (len(data), )
        self.esize = data.itemsize
        self.size = data.nbytes if isinstance(data, memoryview) else (len(data) * data.itemsize)
      sabs = (SAFEARRAYBOUND * len(self.shape))()
      for sab, dim in zip(sabs, self.shape):
        sab.cElements = dim
        sab.lLbound = 0
      psafearray = wintypes.LPVOID(oleauto32.SafeArrayCreate(vtype, len(self.shape), ctypes.byref(sabs)))
      if not psafearray:
        return None
      self._needsdestroy = True
      if self.size > 0:
        pdata = wintypes.LPVOID()
        if oleauto32.SafeArrayAccessData(psafearray, ctypes.byref(pdata)):
          return None
        ctypes.memmove(pdata, ctypes.pointer(ctypes.c_byte.from_buffer(data)), self.size)
        if oleauto32.SafeArrayUnaccessData(psafearray):
          return None
    else:
      return None
    ctypes.c_void_p.from_address(ctypes.addressof(self)).value = psafearray.value
    self.psafearray = ctypes.cast(self, ctypes.c_void_p)
    return self
  def __init__(self, *args, **kwargs):
    super().__init__()
  @property
  def content(self):
    if self.psafearray is None:
      return None
    data = ctypes.create_string_buffer(self.size)
    if self.size > 0:
      pdata = wintypes.LPVOID()
      if oleauto32.SafeArrayAccessData(self.psafearray, ctypes.byref(pdata)):
        return None
      ctypes.memmove(data, pdata, self.size)
      oleauto32.SafeArrayUnaccessData(self.psafearray)
    atype = _BVARIANT.code_ctype[self.vtype]
    for d in self.shape[::-1]:
      atype = atype * d
    return atype.from_buffer(data)
  def __del__(self):
    if getattr(self, 'psafearray', None) is not None and getattr(self, '_needsdestroy', False):
      oleauto32.SafeArrayDestroy(self.psafearray)
      self.psafearray = None

class _BVType(int):
  @classmethod
  def vtype_code(cls, vt):
    return cls._vcls.vt_co(vt) if isinstance(vt, str) else int(vt)
  @classmethod
  def code_vtype(cls, co):
    return cls._vcls.co_vt(co) or str(co)
  @property
  def code(self):
    return int(self)
  @property
  def vtype(self):
    return self.__class__.code_vtype(int(self))
  def __new__(cls, val=None):
    if val is None:
      self = int.__new__(cls)
    else:
      c = cls.vtype_code(val)
      self = None if c is None else int.__new__(cls, c)
    return self
  def __eq__(self, other):
    return int(self) == self.__class__.vtype_code(other)
  def __str__(self):
    c = int(self)
    return '<%d: %s>' % (c, self.__class__.code_vtype(c))
  def __repr__(self):
    return str(self)
  def __or__(self, other):
    return self.__class__(int(self) | c) if (c := self.__class__.vtype_code(other)) is not None else None
  def __ror__(self, other):
    return self.__class__(c | int(self)) if (c := self.__class__.vtype_code(other)) is not None else None
  def __ior__(self, other):
    return self.__class__(int(self) | c) if (c := self.__class__.vtype_code(other)) is not None else None
  def __and__(self, other):
    return self.__class__(int(self) & c) if (c := self.__class__.vtype_code(other)) is not None else None
  def __rand__(self, other):
    return self.__class__(c & int(self)) if (c := self.__class__.vtype_code(other)) is not None else None
  def __iand__(self, other):
    return self.__class__(int(self) & c) if (c := self.__class__.vtype_code(other)) is not None else None
  def __xor__(self, other):
    return self.__class__(int(self) ^ c) if (c := self.__class__.vtype_code(other)) is not None else None
  def __rxor__(self, other):
    return self.__class__(c ^ int(self)) if (c := self.__class__.vtype_code(other)) is not None else None
  def __ixor__(self, other):
    return self.__class__(int(self) ^ c) if (c := self.__class__.vtype_code(other)) is not None else None

class VariantType(_BVType):
  pass

class PropVariantType(_BVType):
  pass

class _BVUtil:
  @staticmethod
  def _adel(arr):
    if getattr(arr, '_needsclear', False):
      for s in arr:
        s.__class__._clear(ctypes.byref(s))
    getattr(arr.__class__.__bases__[0], '__del__', id)(arr)
  @staticmethod
  def _idup(addr, icls):
    i = icls(wintypes.LPVOID(addr))
    if i is not None and i.AddRef() is not None:
      i.refs -= 1
    return i
  @staticmethod
  def _padup(parr):
    return parr._type_.from_buffer_copy(parr.contents) if parr else None
  @staticmethod
  def _adup(arr):
    return arr.__class__.from_buffer_copy(arr)
  @staticmethod
  def _ptie(addr, bvar):
    p = wintypes.LPVOID(addr)
    p._bvariant = bvar
    return p

class _BVMeta(ctypes.Structure.__class__):
  def __mul__(bcls, size):
    return type('VARIANT_Array_%d' % size, (ctypes.Structure.__class__.__mul__(bcls, size),), {'__del__': _BVUtil._adel})
  def __new__(mcls, name, bases, namespace, **kwds):
    if (code_name := namespace.get('code_name')) is not None:
      cls_iu = ctypes.Union.__class__(name + '_IU', (ctypes.Union, ), {'_fields_': [*((na, _BVARIANT.code_ctype[co]) for na, co in {na: co for co, na in code_name.items() if co != 14}.items()), ('pad', wintypes.BYTES16)]})
      cls_i = ctypes.Structure.__class__(name + '_I', (ctypes.Structure, ), {'_anonymous_' : ('vn',), '_fields_': [('vt', ctypes.c_ushort), ('wReserved1', wintypes.WORD), ('wReserved2', wintypes.WORD), ('wReserved3', wintypes.WORD), ('vn', cls_iu)]})
      cls_ou = ctypes.Union.__class__(name + '_OU', (ctypes.Union, ), {'_anonymous_' : ('vn',), '_fields_': [('vn', cls_i), ('decVal', wintypes.BYTES16)]})
      namespace.update({'_anonymous_': ('vn',), '_fields_': [('vn', cls_ou)], 'code_ctype': {co: ct for co, ct in _BVARIANT.code_ctype.items() if co in code_name or co == 12}, 'vtype_code': {vt: co for vt, co in _BVARIANT.vtype_code.items() if co in code_name or co in (0, 1, 12)}, 'code_vtype': {co: vt for co, vt in _BVARIANT.code_vtype.items() if co in code_name or co in (0, 1, 12)}})
    cls = ctypes.Structure.__class__.__new__(mcls, name, bases, namespace, **kwds)
    if name == 'VARIANT':
      _BVARIANT.code_ctype[12] = cls
      cls.code_ctype[12] = cls
    if (vtype := namespace.get('_vtype')) is not None:
      vtype._vcls = cls
    return cls
  def __init__(cls, *args, **kwargs):
    super(_BVMeta, _BVMeta).__init__(cls, *args, **kwargs)
    if hasattr(cls, 'vt'):
      cls._vt = cls.vt
      cls.vt = property(lambda s: cls._vtype(s._vt), lambda s, v: setattr(s, '_vt', cls._vtype.vtype_code(v) or 0), cls._vt.__delete__)
    if hasattr(cls, 'blob'):
      cls._blob = cls.blob
      cls.blob = property(lambda s: s._blob.content, lambda s, v: setattr(s, '_blob', BLOB(v)), cls._blob.__delete__)
    if hasattr(cls, 'bstrVal'):
      cls._bstrVal = cls.bstrVal
      cls.bstrVal = property(lambda s: s._bstrVal.content, lambda s, v: setattr(s, '_bstrVal', BSTR(v)), cls._bstrVal.__delete__)
    if hasattr(cls, 'filetime'):
      cls._filetime = cls.filetime
      cls.filetime = property(lambda s: wintypes.FILETIME.from_buffer_copy(s._filetime), cls._filetime.__set__, cls._filetime.__delete__)
    for n in ('punkVal', 'pdispVal', 'pStorage', 'pStream'):
      if hasattr(cls, n):
        setattr(cls, '_' + n, getattr(cls, n))
        setattr(cls, n, property(lambda s, _n='_'+n: _BVUtil._idup(getattr(s, _n), IStream if _n == '_pStream' else IUnknown), lambda s, v, _n='_'+n: setattr(s, _n, v.pI if isinstance(v, IUnknown) else v), getattr(cls, '_' + n, '__delete__')))
    if hasattr(cls, 'pclipdata'):
      cls._pclipdata = cls.pclipdata
      cls.pclipdata = property(lambda s: _BVUtil._padup(s._pclipdata), lambda s, v: setattr(s, '_pclipdata', v if isinstance(v, wintypes.PBYTES16) else ((ctypes.pointer(v) if isinstance(v, wintypes.BYTES16) else ctypes.cast(ctypes.c_char_p(v), wintypes.PBYTES16)))), cls._pclipdata.__delete__)
    if hasattr(cls, 'puuid'):
      cls._puuid = cls.puuid
      cls.puuid = property(lambda s: _BVUtil._padup(s._puuid), lambda s, v: setattr(s, '_puuid', v if isinstance(v, wintypes.PGUID) else ((ctypes.pointer(v) if isinstance(v, wintypes.GUID) else ctypes.cast(ctypes.c_char_p(v), wintypes.PGUID)))), cls._puuid.__delete__)
    if hasattr(cls, 'pad'):
      cls._pad = cls.pad
      cls.pad = property(lambda s: _BVUtil._adup(s._pad), lambda s, v: setattr(s, '_pad', v if isinstance(v, wintypes.BYTES16) else ctypes.cast(ctypes.c_char_p(v), wintypes.PBYTES16).contents), cls._pad.__delete__)
    if hasattr(cls, 'decVal'):
      cls._decVal = cls.decVal
      cls.decVal = property(lambda s: _BVUtil._adup(s._decVal), lambda s, v: setattr(s, '_decVal', v if isinstance(v, wintypes.BYTES16) else ctypes.cast(ctypes.c_char_p(v), wintypes.PBYTES16).contents), cls._decVal.__delete__)
    if hasattr(cls, 'pVersionedStream'):
      cls._pVersionedStream = cls.pVersionedStream
      cls.pVersionedStream = property(lambda s: _BVUtil._ptie(s._pVersionedStream, s), cls._pVersionedStream.__set__, cls._pVersionedStream.__delete__)

class _BVARIANT(metaclass=_BVMeta):
  vtype_code = {'VT_EMPTY': 0, 'VT_NULL': 1, 'VT_I1': 16, 'VT_UI1': 17, 'VT_I2': 2, 'VT_UI2': 18, 'VT_I4': 3, 'VT_UI4': 19, 'VT_INT': 22, 'VT_UINT': 23, 'VT_I8': 20, 'VT_UI8': 21, 'VT_R4': 4, 'VT_R8': 5, 'VT_BOOL': 11, 'VT_ERROR': 10, 'VT_CY': 6, 'VT_DATE': 7, 'VT_FILETIME': 64, 'VT_CLSID': 72, 'VT_CF': 71, 'VT_BSTR': 8, 'VT_BLOB': 65, 'VT_BLOBOBJECT': 70, 'VT_LPSTR': 30, 'VT_LPWSTR': 31, 'VT_UNKNOWN': 13, 'VT_DISPATCH': 9, 'VT_STREAM': 66, 'VT_STREAMED_OBJECT': 68, 'VT_STORAGE': 67, 'VT_STORED_OBJECT': 69, 'VT_VERSIONED_STREAM': 73, 'VT_DECIMAL': 14, 'VT_VECTOR': 4096, 'VT_ARRAY': 8192, 'VT_BYREF': 16384, 'VT_VARIANT': 12}
  code_vtype = {co: vt for vt, co in vtype_code.items()}
  code_ctype = {16: wintypes.CHAR, 17: wintypes.BYTE, 2: wintypes.SHORT, 18: wintypes.USHORT, 3: wintypes.LONG, 19: wintypes.ULONG, 22: wintypes.INT, 23: wintypes.UINT, 20: wintypes.LARGE_INTEGER, 21: wintypes.ULARGE_INTEGER, 4: wintypes.FLOAT, 5: wintypes.DOUBLE, 11: wintypes.VARIANT_BOOL, 10: wintypes.ULONG, 6: wintypes.LARGE_INTEGER, 7: wintypes.DOUBLE, 64: wintypes.FILETIME, 72: wintypes.PGUID, 71: wintypes.PBYTES16, 8: BSTR, 65: BLOB, 70: BLOB, 30: wintypes.LPSTR, 31: wintypes.LPWSTR, 13: wintypes.LPVOID, 9: wintypes.LPVOID, 66: wintypes.LPVOID, 68: wintypes.LPVOID, 67: wintypes.LPVOID, 69: wintypes.LPVOID, 73: wintypes.LPVOID, 14: wintypes.BYTES16, 12: None, 4096: CA, 8192: wintypes.LPVOID, 16384: wintypes.LPVOID}
  _vtype = _BVType
  @classmethod
  def vt_co(cls, vt):
    co = 0
    for t in filter(None, vt.upper().replace(' ', '|').replace('+', '|').split('|')):
      if (c := cls.vtype_code.get(t)) is None:
        return None
      co |= c
    return co
  @classmethod
  def co_vt(cls, co):
    return ' | '.join(filter(None, (cls.code_vtype.get(co & 16384 or -1), cls.code_vtype.get(co & 8192 or -1), cls.code_vtype.get(co & 4096 or -1), cls.code_vtype.get(co & 4095))))
  @property
  def value(self):
    cls = self.__class__
    vt = self._vt
    if vt & 4095 <= 1:
      return None
    if vt < 4096:
      n = cls.code_name.get(vt, 'pad')
      return getattr(self, n)
    elif vt > 4096 and vt < 8192:
      if 'VT_VECTOR' not in cls.vtype_code:
        return None
      vt ^= 4096
      if (t := cls.code_ctype.get(vt)) is None:
        return None
      if (v := self.ca.content(t)) is None:
        return None
      if issubclass(t, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_wchar_p, ctypes._Pointer, VARIANT)):
        v._bvariant = self
      return v
    elif vt > 8192 and vt < 16384:
      if 'VT_ARRAY' not in cls.vtype_code:
        return None
      vt ^= 8192
      if (t := cls.code_ctype.get(vt)) is None:
        return None
      if (v := PSAFEARRAY(wintypes.LPVOID(self.parray))) is None:
        return None
      if (v := v.content) is None:
        return None
      if issubclass(t, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_wchar_p, ctypes._Pointer, VARIANT)):
        v._bvariant = self
      return v
    elif vt > 16384:
      vt ^= 16384
      if (t := cls.code_ctype.get(vt & 4095)) is None:
        return None
      v = ctypes.cast(wintypes.LPVOID(self.byref), ctypes.POINTER(wintypes.LPVOID if vt > 8192 else t))
      v._bvariant = self
      return v
  def set(self, vtype=None, data=None):
    cls = self.__class__
    vtype = cls._vtype.vtype_code(vtype)
    if vtype is None:
      return False
    if getattr(self, '_needsclear', False):
      if vtype in (0, 1):
        self.__class__._clear(ctypes.byref(self))
      else:
        return False
    if vtype in (0, 1):
      ctypes.memset(ctypes.addressof(self), 0, ctypes.sizeof(cls))
      self._vt = vtype
      return True
    if (vtype & 4095) not in cls.code_ctype or vtype == 12:
      return False
    self._vt = vtype
    if vtype < 4096:
      setattr(self, cls.code_name[vtype], data)
    elif vtype > 4096 and vtype < 8192:
      if 'VT_VECTOR' not in cls.vtype_code:
        return False
      if (ca := CA(cls.code_ctype.get(vtype ^ 4096), data)) is None:
        return False
      self.ca = ca
    elif vtype > 8192 and vtype < 16384:
      if 'VT_ARRAY' not in cls.vtype_code:
        return False
      if (psafearray := PSAFEARRAY(vtype ^ 8192, data)) is None:
        return False
      self.parray = psafearray.psafearray
    elif vtype > 16384:
      self.byref = ctypes.cast(data, wintypes.LPVOID)
    return True
  @value.setter
  def value(self, val):
    if val is not None:
      self.set(*val)
  def __new__(cls, vtype=None, data=None):
    self = ctypes.Structure.__new__(cls)
    if vtype is not None and not cls.set(self, vtype, data):
      return None
    return self
  def __init__(self, vtype=None, data=None):
    ctypes.Structure.__init__(self)
  def __del__(self):
    if getattr(self, '_needsclear', False):
      self.__class__._clear(ctypes.byref(self))
    getattr(self.__class__.__bases__[1], '__del__', id)(self)

class VARIANT(_BVARIANT, ctypes.Structure):
  code_name = {20: 'llVal', 3: 'lVal', 17: 'bVal', 2: 'iVal', 4: 'fltVal', 5: 'dblVal', 11: 'boolVal', 10: 'scode', 6: 'cyVal', 7: 'date', 8: 'bstrVal', 13: 'punkVal', 9: 'pdispVal', 16: 'cVal', 18: 'uiVal', 19: 'ulVal', 21: 'ullVal', 22: 'intVal', 23: 'uintVal', 14: 'decVal', 8192: 'parray', 16384: 'byref'}
  _vtype = VariantType
  _clear = oleauto32.VariantClear
PVARIANT = ctypes.POINTER(VARIANT)

class PROPVARIANT(_BVARIANT, ctypes.Structure):
  code_name = {16: 'cVal', 17: 'bVal', 2: 'iVal',  18: 'uiVal', 3: 'lVal', 19: 'ulVal', 22: 'intVal', 23: 'uintVal', 20: 'hVal', 21: 'uhVal', 4: 'fltVal', 5: 'dblVal', 11: 'boolVal', 10: 'scode', 6: 'cyVal', 7: 'date', 64: 'filetime', 72: 'puuid', 71: 'pclipdata', 8: 'bstrVal', 65: 'blob', 70: 'blob', 30: 'pszVal', 31: 'pwszVal', 13: 'punkVal', 9: 'pdispVal', 66: 'pStream', 68: 'pStream', 67: 'pStorage', 69: 'pStorage', 73: 'pVersionedStream', 14: 'decVal', 4096: 'ca', 8192: 'parray', 16384: 'byref'}
  _vtype = PropVariantType
  _clear = ole32.PropVariantClear
PPROPVARIANT = ctypes.POINTER(PROPVARIANT)

class PROPBAG2(ctypes.Structure):
  _fields_ = [('dwType', wintypes.DWORD), ('_vt', ctypes.c_ushort), ('cfType', wintypes.DWORD), ('dwHint', wintypes.DWORD), ('pstrName', wintypes.LPOLESTR), ('clsid', wintypes.GUID)]
  @property
  def vt(self):
    return VariantType(self._vt)
  @vt.setter
  def vt(self, value):
    self._vt = VariantType.vtype_code(value) or 0
  @vt.deleter
  def vt(self):
    self.__class__._vt.__delete__(self)
  def set(self, name, vtype, hint=0):
    vtype = VariantType.vtype_code(vtype)
    if vtype is None:
      return False
    self.dwType = 0
    self.pstrName = wintypes.LPOLESTR(name)
    self._vt = vtype
    self.dwHint = hint
    return True
PPROPBAG2 = ctypes.POINTER(PROPBAG2)

class IPropertyBag2(IUnknown):
  IID = GUID('22f55882-280b-11d0-a8a9-00a0c90c2004')
  _protos['Read'] = 3, (wintypes.ULONG, PPROPBAG2, wintypes.LPVOID, PVARIANT, wintypes.PULONG), ()
  _protos['Write'] = 4, (wintypes.ULONG, PPROPBAG2, PVARIANT), ()
  _protos['CountProperties'] = 5, (), (wintypes.PULONG,)
  _protos['GetPropertyInfo'] = 6, (wintypes.ULONG, wintypes.ULONG, PPROPBAG2), (wintypes.PULONG,)
  def CountProperties(self):
    return self.__class__._protos['CountProperties'](self.pI)
  def GetPropertyInfo(self, first=0, number=None):
    if number is None:
      number = self.CountProperties() - first
    propbags = (PROPBAG2 * number)()
    n = self.__class__._protos['GetPropertyInfo'](self.pI, first, number, propbags)
    return None if n is None else {pb.pstrName: (pb.vt, pb.dwHint) for pb in propbags[:n]}
  def Read(self, property_infos):
    n = len(property_infos)
    propbags = (PROPBAG2 * n)()
    values = (VARIANT * n)()
    results = (wintypes.ULONG * n)()
    for pb, prop in zip(propbags, property_infos.items()):
      if not (pb.set(prop[0], *prop[1]) if isinstance(prop[1], (tuple, list)) else pb.set(prop[0], prop[1])):
        ISetLastError(0x80070057)
        return None
    if self.__class__._protos['Read'](self.pI, n, propbags, None, values, results) is None:
      return None
    values._needsclear = True
    return {pb.pstrName: ((pb.vt, pb.dwHint), val.value) for pb, val in zip(propbags, values)}
  def Write(self, properties):
    n = len(properties)
    propbags = (PROPBAG2 * n)()
    values = (VARIANT * n)()
    for pb, val, prop in zip(propbags, values, properties.items()):
      if not (pb.set(prop[0], *prop[1][0]) if isinstance(prop[1][0], (tuple, list)) else pb.set(prop[0], prop[1][0])) or not val.set(pb.vt, prop[1][1]):
        ISetLastError(0x80070057)
        return None
    if self.__class__._protos['Write'](self.pI, n, propbags, values) is None:
      return None
    return True
  def GetPropertiesWithType(self, property_infos=None):
    if property_infos is None:
      if (property_infos := self.GetPropertyInfo()) is None:
        return None
    return self.Read(property_infos)
  def GetProperties(self, property_infos=None):
    props = self.GetPropertiesWithType(property_infos)
    if props is None:
      return None
    for n, tv in props.items():
      props[n] = tv[1]
    return props
  def SetProperties(self, property_values, property_infos=None):
    if property_infos is None:
      if (property_infos := self.GetPropertyInfo()) is None:
        return None
    n = len(property_values)
    properties = {}
    for n, v in property_values.items():
      if n not in property_infos:
        ISetLastError(0x80070057)
        return None
      properties[n] = (property_infos[n], v)
    return self.Write(properties)

class _WICEncoderOption:
  def __set_name__(self, owner, name):
    self.name = name
    self.option = owner.__class__._options[name]
  def __get__(self, obj, cls=None):
    n = self.name
    o = self.option
    props = obj.Read({n: o[0]})
    return None if props is None else (props[n][1] if (o[1] is None or props[n][1] is None) else o[1](props[n][1]))
  def __set__(self, obj, value):
    n = self.name
    o = self.option
    obj.Write({n: ((0 if value is None else o[0]), (value if (o[2] is None or value is None) else o[2](value)))})

class _IWICEPBMeta(_IMeta):
  _options = {
    'ImageQuality': ('VT_R4', None, None),
    'JpegYCrCbSubsampling': ('VT_UI1', WICJPEGYCRCBSUBSAMPLINGOPTION, (lambda s: s.code if isinstance(s, WICJPEGYCRCBSUBSAMPLINGOPTION) else WICJPEGYCRCBSUBSAMPLINGOPTION.name_code(s))),
    'BitmapTransform': ('VT_UI1', WICTRANSFORMOPTIONS, (lambda s: s.code if isinstance(s, WICTRANSFORMOPTIONS) else WICTRANSFORMOPTIONS.name_code(s))),
    'SuppressApp0': ('VT_BOOL', None, None),
    'Luminance': ('VT_ARRAY | VT_I4', None, (lambda s: (wintypes.LONG * 64)(*s) if isinstance(s, wintypes.BYTE * 64) else s)),
    'Chrominance': ('VT_ARRAY | VT_I4', None, (lambda s: (wintypes.LONG * 64)(*s) if isinstance(s, wintypes.BYTE * 64) else s)),
    'JpegLumaDcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 12).from_buffer(s), 'CodeValues': (wintypes.BYTE * 12).from_buffer(s, 12)}, (lambda s: (wintypes.BYTE * 24)(*sum(map(tuple, s.values()),())) if isinstance(s, dict) else s)),
    'JpegLumaAcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 16).from_buffer(s), 'CodeValues': (wintypes.BYTE * 162).from_buffer(s, 16)}, (lambda s: (wintypes.BYTE * 178)(*sum(map(tuple, s.values()),())) if isinstance(s, dict) else s)),
    'JpegChromaDcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 12).from_buffer(s), 'CodeValues': (wintypes.BYTE * 12).from_buffer(s, 12)}, (lambda s: (wintypes.BYTE * 24)(*sum(map(tuple, s.values()),())) if isinstance(s, dict) else s)),
    'JpegChromaAcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 16).from_buffer(s), 'CodeValues': (wintypes.BYTE * 162).from_buffer(s, 16)}, (lambda s: (wintypes.BYTE * 178)(*sum(map(tuple, s.values()),())) if isinstance(s, dict) else s)),
    'InterlaceOption': ('VT_BOOL', None, None),
    'FilterOption': ('VT_UI1', WICPNGFILTEROPTION, (lambda s: s.code if isinstance(s, WICPNGFILTEROPTION) else WICPNGFILTEROPTION.name_code(s))),
    'CompressionQuality': ('VT_R4', None, None),
    'TiffCompressionMethod': ('VT_UI1', WICTIFFCOMPRESSIONOPTION, (lambda s: s.code if isinstance(s, WICTIFFCOMPRESSIONOPTION) else WICTIFFCOMPRESSIONOPTION.name_code(s))),
    'EnableV5Header32bppBGRA': ('VT_BOOL', None, None),
    'HeifCompressionMethod': ('VT_UI1', WICHEIFCOMPRESSIONOPTION, (lambda s: s.code if isinstance(s, WICHEIFCOMPRESSIONOPTION) else WICHEIFCOMPRESSIONOPTION.name_code(s))),
    'Lossless': ('VT_BOOL', None, None)
  }
  @classmethod
  def __prepare__(mcls, name, bases, **kwds):
    for n in mcls._options:
      kwds[n] = _WICEncoderOption()
    return kwds

class IWICEncoderPropertyBag(IPropertyBag2, metaclass=_IWICEPBMeta):
  def GetPropertyInfo(self, first=0, number=None):
    if first == 0 and number is None:
      property_infos = getattr(self, '_property_infos', None)
      if property_infos is None:
        if (property_infos := super().GetPropertyInfo()) is not None:
          setattr(self, '_property_infos', property_infos)
    else:
      property_infos = super().GetPropertyInfo(first, number)
    return property_infos
  def GetProperties(self, property_infos=None):
    props = super().GetProperties(getattr(self, '_property_infos', None) if property_infos is None else property_infos)
    if props is None:
      return None
    for n, v in props.items():
      o = self.__class__._options.get(n)
      if o is not None:
        props[n] = (v if (o[1] is None or v is None) else o[1](v))
    return props
  def SetProperties(self, property_values, property_infos=None):
    props = {}
    for n, v in property_values.items():
      o = self.__class__._options.get(n)
      if o is not None:
        props[n] = v if (o[2] is None or v is None) else o[2](v)
    return super().SetProperties(props, getattr(self, '_property_infos', None) if property_infos is None else property_infos)

class IWICEnumMetadataItem(IUnknown):
  IID = GUID(0xdc2bb46d, 0x3f07, 0x481e, 0x86, 0x25, 0x22, 0x0c, 0x4a, 0xed, 0xbb, 0x33)
  _protos['Next'] = ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG, PPROPVARIANT, PPROPVARIANT, PPROPVARIANT, wintypes.PULONG)(3, 'Next')
  _protos['Skip'] = ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG)(4, 'Skip')
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  WithType = False
  IClass = IUnknown
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    schemas = (PROPVARIANT * number)()
    idents = (PROPVARIANT * number)()
    values = (PROPVARIANT * number)()
    if self.__class__._protos['Next'](self.pI, number, schemas, idents, values, r) > 1:
      return None
    if (r := r.value) == 0:
      return ()
    schemas._needsclear = True
    idents._needsclear = True
    values._needsclear = True
    return tuple((s.value, i.value, (v.value.QueryInterface(self.__class__.IClass, self.factory) if v.vt == 13 else v.value)) for s, i, v, _r in zip(schemas, idents, values, range(r))) if not self.__class__.WithType else tuple(((s.vt , s.value), (i.vt, i.value), (v.vt, (v.value.QueryInterface(self.__class__.IClass, self.factory) if v.vt == 13 else v.value))) for s, i, v, _r in zip(schemas, idents, values, range(r)))
  def Skip(self, number):
    try:
      if self.__class__._protos['Skip'](self.pI, number) > 1:
        return None
    except:
      ISetLastError(0x80070057)
      return None
    return True
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    n = self.Next(1)
    if not n:
      raise StopIteration
    return n[0]

class IPersistStream(IUnknown):
  IID = GUID(0x00000109, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['GetClassID'] = 3, (), (WICPCOMPONENT,)
  _protos['IsDirty'] = 4, (), (wintypes.PBOOLE,)
  _protos['Load'] = 5, (wintypes.LPVOID,), ()
  _protos['Save'] = 6, (wintypes.LPVOID, wintypes.BOOLE), ()
  _protos['GetSizeMax'] = 7, (), (wintypes.PULARGE_INTEGER,)
  def GetClassID(self):
    return self.__class__._protos['GetClassID'](self.pI)
  def IsDirty(self):
    return self.__class__._protos['IsDirty'](self.pI)
  def Load(self, istream):
    return self.__class__._protos['Load'](self.pI, istream)
  def GetSizeMax(self):
    return self.__class__._protos['GetSizeMax'](self.pI)
  def Save(self, istream, clear_dirty=True):
    return self.__class__._protos['Save'](self.pI, istream, clear_dirty)

class IWICPersistStream(IPersistStream):
  IID = GUID(0x00675040, 0x6908, 0x45f8, 0x86, 0xa3, 0x49, 0xc7, 0xdf, 0xd6, 0xd9, 0xad)
  _protos['LoadEx'] = 8, (wintypes.LPVOID, WICPVENDORIDENTIFICATION, WICPERSISTOPTIONS), ()
  _protos['SaveEx'] = 9, (wintypes.LPVOID, WICPERSISTOPTIONS, wintypes.BOOLE), ()
  def LoadEx(self, istream, load_vendor=None, options=0):
    return self.__class__._protos['LoadEx'](self.pI, istream, load_vendor, options)
  def SaveEx(self, istream, options=0, clear_dirty=True):
    return self.__class__._protos['SaveEx'](self.pI, istream, options, clear_dirty)

class IWICStreamProvider(IUnknown):
  IID = GUID(0x449494bc, 0xb468, 0x4927, 0x96, 0xd7, 0xba, 0x90, 0xd3, 0x1a, 0xb5, 0x05)
  _protos['GetStream'] = 3, (), (wintypes.PLPVOID,)
  _protos['GetPersistOptions'] = 4, (), (WICPPERSISTOPTIONS,)
  _protos['GetPreferredVendorGUID'] = 5, (), (WICPVENDORIDENTIFICATION,)
  _protos['RefreshStream'] = 6, (), ()
  def GetStream(self):
    return IStream(self.__class__._protos['GetStream'](self.pI), self.factory)
  def GetPersistOptions(self):
    return self.__class__._protos['GetPersistOptions'](self.pI)
  def GetPreferredVendorGUID(self):
    return self.__class__._protos['GetPreferredVendorGUID'](self.pI)
  def RefreshStream(self):
    return self.__class__._protos['RefreshStream'](self.pI)

MetadataOrientation = {'TopLeft': 1, 'TopRight': 2, 'BottomRight': 3, 'BottomLeft': 4, 'LeftTop': 5, 'RightTop': 6, 'RightBottom': 7, 'LeftBottom': 8}
METADATAORIENTATION = type('METADATAORIENTATION', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataOrientation.items()}, '_tab_cn': {c: n for n, c in MetadataOrientation.items()}, '_def': 1})

MetadataResolutionUnit = {'No': 1, 'None': 1, 'Inch': 2, 'Centimeter': 3}
METADATARESOLUTIONUNIT = type('METADATARESOLUTIONUNIT', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataResolutionUnit.items()}, '_tab_cn': {c: n for n, c in MetadataResolutionUnit.items()}, '_def': 1})

MetadataYCbCrPositioning = {'Centered': 1, 'Cosited': 2}
METADATAYCBCRPOSITIONING = type('METADATAYCBCRPOSITIONING', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataYCbCrPositioning.items()}, '_tab_cn': {c: n for n, c in MetadataYCbCrPositioning.items()}, '_def': 1})

MetadataComponentsConfiguration = {'None': 0, 'Y': 1, 'Cb': 2, 'Cr': 3, 'R': 4, 'G': 5, 'B': 6}
METADATACOMPONENTSCONFIGURATION = type('METADATACOMPONENTSCONFIGURATION', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataComponentsConfiguration.items()}, '_tab_cn': {c: n for n, c in MetadataComponentsConfiguration.items()}, '_def': 0})

MetadataExposureProgram = {'NotDefined': 0, 'Manual': 1, 'Normal': 2, 'AperturePriority': 3, 'ShutterPriority': 4, 'Creative': 5, 'Action': 6, 'Portrait': 7, 'Landscape': 8}
METADATAEXPOSUREPROGRAM = type('METADATAEXPOSUREPROGRAM', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataExposureProgram.items()}, '_tab_cn': {c: n for n, c in MetadataExposureProgram.items()}, '_def': 0})

MetadataMeteringMode = {'Unknown': 0, 'Average': 1, 'CenterWeightedAverage': 2, 'Spot': 3, 'MultiSpot': 4, 'MultiSegment': 5, 'Pattern': 5, 'Partial': 6, 'Other': 255}
METADATAMETERINGMODE = type('METADATAMETERINGMODE', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataMeteringMode.items()}, '_tab_cn': {c: n for n, c in MetadataMeteringMode.items()}, '_def': 0})

MetadataLightSource = {'Unknown': 0, 'Daylight': 1, 'Fluorescent': 2, 'Tungsten': 3, 'Flash': 4, 'FineWeather': 9, 'CloudyWeather': 10, 'Shade': 11, 'DaylightFluorescent': 12, 'DayWhiteFluorescent': 13, 'CoolWhiteFluorescent': 14, 'WhiteFluorescent': 15, 'StandardLightA': 17, 'StandardLightB': 18, 'StandardLightC': 19, 'D55': 20, 'D65': 21, 'D75': 22, 'D50': 23, 'ISOStudioTungsten': 24, 'Other': 255}
METADATALIGHTSOURCE = type('METADATALIGHTSOURCE', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataLightSource.items()}, '_tab_cn': {c: n for n, c in MetadataLightSource.items()}, '_def': 0})

MetadataFlash = {'NotFired': 0x0, 'Fired': 0x1, 'Fired-ReturnNotDetected': 0x5, 'Fired-ReturnDetected': 0x7, 'Fired-Compulsory': 0x9, 'Fired-ReturnNotDetected-Compulsory': 0xd, 'Fired-ReturnDetected-Compulsory': 0xf, 'NotFired-Compulsory': 0x10, 'NotFired-Auto': 0x18, 'Fired-Auto': 0x19, 'Fired-ReturnNotDetected-Auto': 0x1d, 'Fired-ReturnDetected-Auto': 0x1f, 'NoFlashFunction': 0x20, 'Fired-RedEyeReduction': 0x41, 'Fired-ReturnNotDetected-RedEyeReduction': 0x45, 'Fired-ReturnDetected-RedEyeReduction': 0x47, 'Fired-Compulsory-RedEyeReduction': 0x49, 'Fired-ReturnNotDetected-Compulsory-RedEyeReduction': 0x4d, 'Fired-ReturnDetected-Compulsory-RedEyeReduction': 0x4f, 'Fired-Auto-RedEyeReduction': 0x59, 'Fired-ReturnNotDetected-Auto-RedEyeReduction': 0x5d, 'Fired-ReturnDetected-Auto-RedEyeReduction': 0x5f}
METADATAFLASH = type('METADATAFLASH', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataFlash.items()}, '_tab_cn': {c: n for n, c in MetadataFlash.items()}, '_def': 0x20})

MetadataExposureMode = {'Auto': 0, 'Manual': 1, 'AutoBracket': 2}
METADATAEXPOSUREMODE = type('METADATAEXPOSUREMODE', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataExposureMode.items()}, '_tab_cn': {c: n for n, c in MetadataExposureMode.items()}, '_def': 0})

MetadataWhiteBalance = {'Auto': 0, 'Manual': 1}
METADATAWHITEBALANCE = type('METADATAWHITEBALANCE', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataWhiteBalance.items()}, '_tab_cn': {c: n for n, c in MetadataWhiteBalance.items()}, '_def': 0})

MetadataSceneCaptureType = {'Standard': 0, 'Landscape': 1, 'Portrait': 2, 'Night': 3}
METADATASCENECAPTURETYPE = type('METADATASCENECAPTURETYPE', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataSceneCaptureType.items()}, '_tab_cn': {c: n for n, c in MetadataSceneCaptureType.items()}, '_def': 0})

MetadataAltitudeRef = {'AboveSeaLevel': 0, 'BelowSeaLevel': 1}
METADATAALTITUDEREF = type('METADATAALTITUDEREF', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataAltitudeRef.items()}, '_tab_cn': {c: n for n, c in MetadataAltitudeRef.items()}, '_def': 0})

MetadataTiffCompression = {'Uncompressed': 1, 'CCIT-RLE': 2, 'CCIT-T.4': 3, 'CCIT-T.5': 4, 'LZW': 5, 'OldJpeg': 6, 'Jpeg': 7, 'AdobeDeflate': 8, 'JBIG-T.85': 9, 'JBIG-T.43': 10, 'PKZIPDeflate': 32946, 'PackBits': 32773, 'Jpeg2000': 34712}
METADATATIFFCOMPRESSION = type('METADATATIFFCOMPRESSION', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataTiffCompression.items()}, '_tab_cn': {c: n for n, c in MetadataTiffCompression.items()}, '_def': 5})

MetadataTiffPredictor = {'No': 1, 'None': 1, 'HorizontalDifferencing': 2, 'FloatingPointHorizontalDifferencing': 3}
METADATATIFFPREDICTOR = type('METADATATIFFPREDICTOR', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataTiffPredictor.items()}, '_tab_cn': {c: n for n, c in MetadataTiffPredictor.items()}, '_def': 5})

MetadataTiffPlanarConfiguration = {'Chunky': 0, 'Interleaved': 0, 'Planar': 1}
METADATATIFFPLANARCONFIGURATION = type('METADATATIFFPLANARCONFIGURATION', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataTiffPlanarConfiguration.items()}, '_tab_cn': {c: n for n, c in MetadataTiffPlanarConfiguration.items()}, '_def': 0})

MetadataTiffSampleFormat = {'UnsignedInteger': 1, 'SignedInteger': 2, 'FloatingPoint': 3, 'Undefined': 4}
METADATATIFFSAMPLEFORMAT = type('METADATATIFFSAMPLEFORMAT', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataTiffSampleFormat.items()}, '_tab_cn': {c: n for n, c in MetadataTiffSampleFormat.items()}, '_def': 4})

MetadataTiffPhotometricInterpretation = {'WhiteIsZero': 0, 'BlackIsZero': 1, 'RGB': 2, 'Palette': 3, 'Mask': 4, 'CMYK': 5, 'YCbCr': 6, 'CIELab': 8, 'ICCLab': 9, 'ITULab': 10, 'LogL': 32844, 'LogLuv': 32845}
METADATATIFFPHOTOMETRICINTERPRETATION = type('METADATATIFFPHOTOMETRICINTERPRETATION', (_BCode, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in MetadataTiffPhotometricInterpretation.items()}, '_tab_cn': {c: n for n, c in MetadataTiffPhotometricInterpretation.items()}, '_def': 2})

class _BMFraction(Fraction):
  def __iter__(self):
    return iter((self.numerator, self.denominator))
  def limit(self, max=1<<30):
    if abs(self.numerator) <= max and abs(self.denominator) <= max:
      return self
    f = self.limit_denominator(max if abs(self) <= 1 else (max - 0.5) / abs(self))
    return self.__class__(f.numerator, f.denominator)
  @classmethod
  def from_rational(cls, r):
    if isinstance(r, (tuple, list, ctypes.Array)):
      return tuple(map(cls.from_rational, r))
    else:
      n, d = struct.unpack('=LL', struct.pack('=Q', r))
      return None if d == 0 else cls(n, d)
  @classmethod
  def from_srational(cls, r):
    if isinstance(r, (tuple, list, ctypes.Array)):
      return tuple(map(cls.from_srational, r))
    else:
      n, d = struct.unpack('=ll', struct.pack('=Q', r))
      return None if d == 0 else cls(n, d)
  @classmethod
  def to_rational(cls, f):
    return tuple(map(cls.to_rational, f)) if isinstance(f, (tuple, list, ctypes.Array)) else struct.unpack('=Q', struct.pack('=LL', *(f if isinstance(f, _BMFraction) else cls(f)).limit()))[0]
  @classmethod
  def to_srational(cls, f):
    return tuple(map(cls.to_srational, f)) if isinstance(f, (tuple, list, ctypes.Array)) else struct.unpack('=Q', struct.pack('=ll', *(f if isinstance(f, _BMFraction) else cls(f)).limit()))[0]
  def __repr__(self):
    return str(self)

class MetadataFloatFraction(_BMFraction):
  def __str__(self):
    return str(float(self)).rstrip('0').rstrip('.')

class MetadataTimeFraction(_BMFraction):
  def __str__(self):
    return ('1/%d s' % round(1 / self)) if self != 0 else '0'

class MetadataLengthFraction(_BMFraction):
  def __str__(self):
    return ('%.2f' % self).rstrip('0').rstrip('.') + ' mm'

class MetadataLength(int):
  def __str__(self):
    return '%d mm' % self
  def __repr__(self):
    return str(self)

class MetadataAltitudeFraction(_BMFraction):
  def __str__(self):
    return super().__str__() + ' m'

class MetadataExposureFraction(_BMFraction):
  def __str__(self):
    return ('%.2f' % self).rstrip('0').rstrip('.') + ' EV'

class MetadataSpeedFraction(_BMFraction):
  @classmethod
  def to_rational(cls, f):
    return super().to_rational(-math.log2(Fraction(f)) if isinstance(f, str) and f.replace(' ','')[:2] == '1/' else f)
  @classmethod
  def to_srational(cls, f):
    return super().to_srational(-math.log2(Fraction(f)) if isinstance(f, str) and f.replace(' ','')[:2] == '1/' else f)
  def __str__(self):
    return '1/%d s' % round(2 ** self)

class MetadataApertureFraction(_BMFraction):
  @classmethod
  def to_rational(cls, f):
    return super().to_rational(2 * math.log2(Fraction(f.lstrip(' fF'))) if isinstance(f, str) and f.replace(' ','')[:1] in ('f', 'F') else f)
  @classmethod
  def to_srational(cls, f):
    return super().to_srational(2 * math.log2(Fraction(f.lstrip(' fF'))) if isinstance(f, str) and f.replace(' ','')[:1] in ('f', 'F') else f)
  def __str__(self):
    return ('F %.2f' % math.sqrt(2) ** self).rstrip('0').rstrip('.')

class MetadataResolution(tuple):
  @classmethod
  def from_components(cls, rx, ry, ru):
    return cls((rx, ry, ru))
  @classmethod
  def to_components(cls, res):
    if isinstance(res, cls):
      return tuple(res)
    elif isinstance(res, str):
      res = res.lower().replace('(', ' ').replace(')', ' ').replace(',', ' ').strip()
      e = len(res) - 1
      while e >= 0 and not res[e].isdecimal():
        e -= 1
      rxy = map(str.strip, res[:e+1].split(' ', 1))
      return (*map(MetadataFloatFraction, rxy), 2 if res.endswith('dpi') else (3 if res.endswith('dpc') else 1))
    elif isinstance(res, (int, float)):
      return (MetadataFloatFraction(res), MetadataFloatFraction(res), 1)
    elif isinstance(res, (tuple, list)):
      if len(res) == 1:
        return (MetadataFloatFraction(res[0]), MetadataFloatFraction(res[0]), 1)
      elif len(res) == 2:
        return (MetadataFloatFraction(res[0]), MetadataFloatFraction(res[1]), 1)
      elif len(res) >= 3:
        ru = res[2]
        if isinstance(ru, str):
          ru = res[2].strip().lower()
          ru = 2 if ru == 'dpi' else (3 if ru == 'dpc' else 1)
        return (MetadataFloatFraction(res[0]), MetadataFloatFraction(res[1]), ru)
    else:
      return res
  def __str__(self):
    return '(%s, %s)%s' % (('%.2f' % self[0]).rstrip('0').rstrip('.'), ('%.2f' % self[1]).rstrip('0').rstrip('.'), (' dpi' if self[2] == 2 else (' dpc' if self[2] == 3 else '')))
  def __repr__(self):
    return str(self)

class _MetadataPositionComponent(tuple):
  @classmethod
  def from_components(cls, ref, dms):
    return cls((ref.upper(), dms))
  @property
  def dec(self):
    return (-1 if self[0] == self.__class__._neg else 1) * sum(float(n) / d for n, d in zip(self[1], (1, 60, 3600)))
  @property
  def dms(self):
    return '%s"%s' % (('%.0f°%02.0f\'%06.3f' % self[1]).rstrip('0').rstrip('.'), self[0])
  @classmethod
  def to_components(cls, pos):
    if isinstance(pos, _MetadataPositionComponent):
      return tuple(pos)
    elif isinstance(pos, str):
      return ((cls._neg if pos[-1:].upper() == cls._neg else cls._pos), (MetadataFloatFraction(pos.split('°')[0]), MetadataFloatFraction(pos.split('°')[1].split('\'')[0]), MetadataFloatFraction(pos.split('\'')[1].split('"')[0])))
    else:
      return (cls._neg if pos < 0 else cls._pos, (MetadataFloatFraction(int(abs(pos))), MetadataFloatFraction(int(abs(pos) * 60 % 60)), MetadataFloatFraction(abs(pos) * 3600 % 60)))
  def __str__(self):
    return '%s (%s)' % (('%0.7f' % self.dec).rstrip('0').rstrip('.'), self.dms)
  def __repr__(self):
    return str(self)

class MetadataLatitude(_MetadataPositionComponent):
  _pos = 'N'
  _neg = 'S'

class MetadataLongitude(_MetadataPositionComponent):
  _pos = 'E'
  _neg = 'W'

class _WICMetadataQuery:
  def __set_name__(self, owner, name):
    self.name = name[3:]
    self.reader = name.startswith('Get')
    self.query = owner.__class__._queries[self.name]
  def __get__(self, obj, cls=None):
    q = self.query
    if (f := obj.GetContainerFormat()) is not None:
      f = {'Thumbnail': '/thumb/', 'JpegLuminance': '/luminance/', 'JpegChrominance': '/chrominance/'}.get(f.name, '/%s/' % f.name.lower())
      p = next((s[2] for p_ in q[0] if (s := p_.partition(f))[1]), None)
    else:
      p = None
    if self.reader:
      return lambda _o=obj, _p=p, _f=q[2]: (ISetLastError(0x88982f90) and None) if _p is None else (m if ((m := _o.GetMetadataByName('/' + _p)) is None or _f is None) else _f(m))
    else:
      return lambda v, _o=obj, _p=p, _t=q[1], _f=q[3]: (ISetLastError(0x88982f90) and None) if _p is None else _o.SetMetadataByName('/' + _p, (_t, (v if (v is None or _f is None) else _f(v))))

class _IWICMQRUtil:
  @staticmethod
  def _writer(handler):
    return handler.factory.CreateQueryWriterFromReader(handler) if isinstance(handler, IWICMetadataQueryReader) else handler
  @staticmethod
  def _tuple(cls=None):
    if cls is None:
      return (lambda s: tuple(s) if hasattr(s, '__len__') else (s,),) * 2
    else:
      return lambda s: tuple(map(cls, (s if hasattr(s, '__len__') else (s,)))), lambda s: tuple(map(cls.to_int, (s if hasattr(s, '__len__') and not isinstance(s, str) else (s,))))
  @staticmethod
  def _blob(cls):
    return lambda s: tuple(map(cls, s)), lambda s: bytes(map(cls.to_int, s))
  @staticmethod
  def _res(handler, reader=True):
    if reader:
      return lambda _h=handler: None if None in ((ru := (_h.GetResolutionUnit() or 1)), (rx := _h.GetXResolution()), (ry := _h.GetYResolution())) else (MetadataResolution.from_components(rx, ry, ru))
    else:
      return lambda res, _h=handler: None if None in (sc(s) for s, sc in zip(MetadataResolution.to_components(res), (_h.SetXResolution, _h.SetYResolution, _h.SetResolutionUnit))) else True
  @staticmethod
  def _pos(handler, reader=True):
    if reader:
      return lambda _h=handler: None if None in ((latr := _h.GetLatitudeRef()), (lat := _h.GetLatitude()), (lonr := _h.GetLongitudeRef()), (lon := _h.GetLongitude())) else (MetadataLatitude.from_components(latr, lat), MetadataLongitude.from_components(lonr, lon))
    else:
      return lambda pos, _h=handler: None if None in (sc(s) for s, sc in zip(MetadataLatitude.to_components(pos[0]), (_h.SetLatitudeRef, _h.SetLatitude))) or None in (sc(s) for s, sc in zip(MetadataLongitude.to_components(pos[1]), (_h.SetLongitudeRef, _h.SetLongitude))) else True

class _IWICMQRMeta(_IMeta):
  _queries = {
    'Unknown': (('/jpeg/unknown',), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'App0': (('/jpeg/app0',), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'App1': (('/jpeg/app1',), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'Ifd': (('/jpeg/app1/ifd', '/tiff/ifd'), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'Exif': (('/jpeg/app1/ifd/exif', '/tiff/ifd/exif'), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'Gps': (('/jpeg/app1/ifd/gps', '/tiff/ifd/gps'), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'Thumbnail': (('/jpeg/app1/thumb', '/tiff/ifd/thumb'), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'IRB': (('/jpeg/app13/irb',), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'IPTC': (('/jpeg/app13/irb/8bimiptc/iptc', '/tiff/ifd/iptc'), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    '8BIMIPTC': (('/jpeg/app13/irb/8bimiptc',), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    '8BIMResolutionInfo': (('/jpeg/app13/irb/8bimResInfo',), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'XMP': (('/jpeg/xmp', '/tiff/ifd/xmp'), 'VT_UNKNOWN', None, _IWICMQRUtil._writer),
    'JpegComment':  (('/jpeg/com/TextEntry',), 'VT_LPSTR', bytes.decode, str.encode),
    'Luminance': (('/jpeg/luminance/TableEntry',), 'VT_VECTOR | VT_UI2', None, None),
    'Chrominance': (('/jpeg/chrominance/TableEntry',), 'VT_VECTOR | VT_UI2', None, None),
    'ImageWidth': (('/tiff/ifd/{ushort=256}', '/thumb/{ushort=256}'), 'VT_UI4', None, None),
    'ImageLength': (('/tiff/ifd/{ushort=257}', '/thumb/{ushort=257}'), 'VT_UI4', None, None),
    'BitsPerSample': (('/tiff/ifd/{ushort=258}', '/thumb/{ushort=258}'), 'VT_VECTOR | VT_UI2', *_IWICMQRUtil._tuple()),
    'Compression': (('/tiff/ifd/{ushort=259}', '/thumb/{ushort=259}'), 'VT_UI2', METADATATIFFCOMPRESSION, METADATATIFFCOMPRESSION.to_int),
    'PhotometricInterpretation': (('/tiff/ifd/{ushort=262}', '/thumb/{ushort=262}'), 'VT_UI2', METADATATIFFPHOTOMETRICINTERPRETATION, METADATATIFFPHOTOMETRICINTERPRETATION.to_int),
    'ImageDescription': (('/jpeg/app1/ifd/{ushort=270}', '/tiff/ifd/{ushort=270}'), 'VT_LPSTR', bytes.decode, str.encode),
    'Make': (('/jpeg/app1/ifd/{ushort=271}', '/tiff/ifd/{ushort=271}'), 'VT_LPSTR', bytes.decode, str.encode),
    'Model': (('/jpeg/app1/ifd/{ushort=272}', '/tiff/ifd/{ushort=272}'), 'VT_LPSTR', bytes.decode, str.encode),
    'StripOffsets': (('/tiff/ifd/{ushort=273}', '/thumb/{ushort=273}'), 'VT_VECTOR | VT_UI4', None, None),
    'Orientation': (('/jpeg/app1/ifd/{ushort=274}', '/tiff/ifd/{ushort=274}', '/thumb/{ushort=274}'), 'VT_UI2', METADATAORIENTATION, METADATAORIENTATION.to_int),
    'SamplesPerPixel': (('/tiff/ifd/{ushort=277}', '/thumb/{ushort=277}'), 'VT_UI2', None, None),
    'RowsPerStrip': (('/tiff/ifd/{ushort=278}', '/thumb/{ushort=278}'), 'VT_UI4', None, None),
    'StripByteCounts': (('/tiff/ifd/{ushort=279}', '/thumb/{ushort=279}'), 'VT_VECTOR | VT_UI4', None, None),
    'XResolution': (('/jpeg/app1/ifd/{ushort=282}', '/tiff/ifd/{ushort=282}', '/thumb/{ushort=282}'), 'VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'YResolution': (('/jpeg/app1/ifd/{ushort=283}', '/tiff/ifd/{ushort=283}', '/thumb/{ushort=283}'), 'VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'PlanarConfiguration': (('/tiff/ifd/{ushort=284}', '/thumb/{ushort=284}'), 'VT_UI2', METADATATIFFPLANARCONFIGURATION, METADATATIFFPLANARCONFIGURATION.to_int),
    'ResolutionUnit': (('/jpeg/app1/ifd/{ushort=296}', '/tiff/ifd/{ushort=296}', '/thumb/{ushort=296}'), 'VT_UI2', METADATARESOLUTIONUNIT, METADATARESOLUTIONUNIT.to_int),
    'Software': (('/jpeg/app1/ifd/{ushort=305}', '/tiff/ifd/{ushort=305}'), 'VT_LPSTR', bytes.decode, str.encode),
    'DateTime': (('/jpeg/app1/ifd/{ushort=306}', '/tiff/ifd/{ushort=306}'), 'VT_LPSTR', bytes.decode, str.encode),
    'Predictor': (('/tiff/ifd/{ushort=317}',), 'VT_UI2', METADATATIFFPREDICTOR, METADATATIFFPREDICTOR.to_int),
    'ColorMap': (('/tiff/ifd/{ushort=320}',), 'VT_VECTOR | VT_UI2', None, None),
    'TileWidth': (('/tiff/ifd/{ushort=322}',), 'VT_UI4', None, None),
    'TileLength': (('/tiff/ifd/{ushort=323}',), 'VT_UI4', None, None),
    'TileOffsets': (('/tiff/ifd/{ushort=324}',), 'VT_VECTOR | VT_UI4', None, None),
    'TileByteCounts': (('/tiff/ifd/{ushort=325}',), 'VT_VECTOR | VT_UI4', None, None),
    'SampleFormat': (('/tiff/ifd/{ushort=339}',), 'VT_VECTOR | VT_UI2', *_IWICMQRUtil._tuple(METADATATIFFSAMPLEFORMAT)),
    'YCbCrPositioning': (('/jpeg/app1/ifd/{ushort=531}', '/tiff/ifd/{ushort=531}'), 'VT_UI2', METADATAYCBCRPOSITIONING, METADATAYCBCRPOSITIONING.to_int),
    'ExposureTime': (('/jpeg/app1/ifd/exif/{ushort=33434}', '/tiff/ifd/exif/{ushort=33434}'), 'VT_UI8', MetadataTimeFraction.from_rational, MetadataTimeFraction.to_rational),
    'FNumber': (('/jpeg/app1/ifd/exif/{ushort=33437}', '/tiff/ifd/exif/{ushort=33437}'), 'VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'ExposureProgram': (('/jpeg/app1/ifd/exif/{ushort=34850}', '/tiff/ifd/exif/{ushort=34850}'), 'VT_UI2', METADATAEXPOSUREPROGRAM, METADATAEXPOSUREPROGRAM.to_int),
    'PhotographicSensitivity': (('/jpeg/app1/ifd/exif/{ushort=34855}', '/tiff/ifd/exif/{ushort=34855}'), 'VT_UI2', None, None),
    'ISOSpeedRatings': (('/jpeg/app1/ifd/exif/{ushort=34855}', '/tiff/ifd/exif/{ushort=34855}'), 'VT_UI2', None, None),
    'DateTimeOriginal': (('/jpeg/app1/ifd/exif/{ushort=36867}', '/tiff/ifd/exif/{ushort=36867}'), 'VT_LPSTR', bytes.decode, str.encode),
    'DateTimeDigitized': (('/jpeg/app1/ifd/exif/{ushort=36868}', '/tiff/ifd/exif/{ushort=36868}'), 'VT_LPSTR', bytes.decode, str.encode),
   'ComponentsConfiguration': (('/jpeg/app1/ifd/exif/{ushort=37121}', '/tiff/ifd/exif/{ushort=37121}'), 'VT_BLOB', *_IWICMQRUtil._blob(METADATACOMPONENTSCONFIGURATION)),
    'CompressedBitsPerPixel': (('/jpeg/app1/ifd/exif/{ushort=37122}', '/tiff/ifd/exif/{ushort=37122}'), 'VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'ShutterSpeedValue': (('/jpeg/app1/ifd/exif/{ushort=37377}', '/tiff/ifd/exif/{ushort=37377}'), 'VT_I8', MetadataSpeedFraction.from_rational, MetadataSpeedFraction.to_rational),
    'ApertureValue': (('/jpeg/app1/ifd/exif/{ushort=37378}', '/tiff/ifd/exif/{ushort=37378}'), 'VT_UI8', MetadataApertureFraction.from_rational, MetadataApertureFraction.to_rational),
    'BrightnessValue': (('/jpeg/app1/ifd/exif/{ushort=37379}', '/tiff/ifd/exif/{ushort=37379}'), 'VT_I8', MetadataExposureFraction.from_srational, MetadataExposureFraction.to_srational),
    'ExposureBiasValue': (('/jpeg/app1/ifd/exif/{ushort=37380}', '/tiff/ifd/exif/{ushort=37380}'), 'VT_I8', MetadataExposureFraction.from_srational, MetadataExposureFraction.to_srational),
    'MaxApertureValue': (('/jpeg/app1/ifd/exif/{ushort=37381}', '/tiff/ifd/exif/{ushort=37381}'), 'VT_UI8', MetadataApertureFraction.from_rational, MetadataApertureFraction.to_rational),
    'SubjectDistance': (('/jpeg/app1/ifd/exif/{ushort=37382}', '/tiff/ifd/exif/{ushort=37382}'), 'VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'MeteringMode': (('/jpeg/app1/ifd/exif/{ushort=37383}', '/tiff/ifd/exif/{ushort=37383}'), 'VT_UI2', METADATAMETERINGMODE, METADATAMETERINGMODE.to_int),
    'LightSource': (('/jpeg/app1/ifd/exif/{ushort=37384}', '/tiff/ifd/exif/{ushort=37384}'), 'VT_UI2', METADATALIGHTSOURCE, METADATALIGHTSOURCE.to_int),
    'Flash': (('/jpeg/app1/ifd/exif/{ushort=37385}', '/tiff/ifd/exif/{ushort=37385}'), 'VT_UI2', METADATAFLASH, METADATAFLASH.to_int),
    'FocalLength': (('/jpeg/app1/ifd/exif/{ushort=37386}', '/tiff/ifd/exif/{ushort=37386}'), 'VT_I8', MetadataLengthFraction.from_srational, MetadataLengthFraction.to_srational),
    'MakerNote': (('/jpeg/app1/ifd/exif/{ushort=37500}', '/tiff/ifd/exif/{ushort=37500}'), 'VT_BLOB', None, None),
    'UserComment': (('/jpeg/app1/ifd/exif/{ushort=37510}', '/tiff/ifd/exif/{ushort=37510}'), 'VT_BLOB', None, None),
    'ColorSpace': (('/jpeg/app1/ifd/exif/{ushort=40961}', '/tiff/ifd/exif/{ushort=40961}'), 'VT_UI2', WICEXIFCOLORSPACE, WICEXIFCOLORSPACE.to_int),
    'PixelXDimension': (('/jpeg/app1/ifd/exif/{ushort=40962}', '/tiff/ifd/exif/{ushort=40962}'), 'VT_UI4', None, None),
    'PixelYDimension': (('/jpeg/app1/ifd/exif/{ushort=40963}', '/tiff/ifd/exif/{ushort=40963}'), 'VT_UI4', None, None),
    'ExposureMode': (('/jpeg/app1/ifd/exif/{ushort=41986}', '/tiff/ifd/exif/{ushort=41986}'), 'VT_UI2', METADATAEXPOSUREMODE, METADATAEXPOSUREMODE.to_int),
    'WhiteBalance': (('/jpeg/app1/ifd/exif/{ushort=41987}', '/tiff/ifd/exif/{ushort=41987}'), 'VT_UI2', METADATAWHITEBALANCE, METADATAWHITEBALANCE.to_int),
    'FocalLengthIn35mmFilm': (('/jpeg/app1/ifd/exif/{ushort=41989}', '/tiff/ifd/exif/{ushort=41989}'), 'VT_UI2', MetadataLength, None),
    'SceneCaptureType': (('/jpeg/app1/ifd/exif/{ushort=41990}', '/tiff/ifd/exif/{ushort=41990}'), 'VT_UI2', METADATASCENECAPTURETYPE, METADATASCENECAPTURETYPE.to_int),
    'LatitudeRef': (('/jpeg/app1/ifd/gps/{ushort=1}', '/tiff/ifd/gps/{ushort=1}'), 'VT_LPSTR', bytes.decode, str.encode),
    'Latitude': (('/jpeg/app1/ifd/gps/{ushort=2}', '/tiff/ifd/gps/{ushort=2}'), 'VT_VECTOR | VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'LongitudeRef': (('/jpeg/app1/ifd/gps/{ushort=3}', '/tiff/ifd/gps/{ushort=3}'), 'VT_LPSTR', bytes.decode, str.encode),
    'Longitude': (('/jpeg/app1/ifd/gps/{ushort=4}', '/tiff/ifd/gps/{ushort=4}'), 'VT_VECTOR | VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'AltitudeRef': (('/jpeg/app1/ifd/gps/{ushort=5}', '/tiff/ifd/gps/{ushort=5}'), 'VT_UI1', METADATAALTITUDEREF, METADATAALTITUDEREF.to_int),
    'Altitude': (('/jpeg/app1/ifd/gps/{ushort=6}', '/tiff/ifd/gps/{ushort=6}'), 'VT_UI8', MetadataAltitudeFraction.from_rational, MetadataAltitudeFraction.to_rational),
    'TimeStamp': (('/jpeg/app1/ifd/gps/{ushort=7}', '/tiff/ifd/gps/{ushort=7}'), 'VT_VECTOR | VT_UI8', MetadataFloatFraction.from_rational, MetadataFloatFraction.to_rational),
    'DateStamp': (('/jpeg/app1/ifd/gps/{ushort=29}', '/tiff/ifd/gps/{ushort=29}'), 'VT_LPSTR', bytes.decode, str.encode),
    'ThumbnailBytes': (('/jpeg/app1/thumb/{}', '/tiff/ifd/thumb/{}'), 'VT_BLOB', None, None),
    'ICCProfile': (('/jpeg/unknown/{}', '/tiff/ifd/{ushort=34675}'), 'VT_BLOB', None, None),
  }
  @classmethod
  def __prepare__(mcls, name, bases, **kwds):
    kwds = super(mcls, mcls).__prepare__(name, bases, **kwds)
    if 'Reader' in name:
      for n in mcls._queries:
        kwds['Get' + n] = _WICMetadataQuery()
      kwds['GetPosition'] = property(lambda s: _IWICMQRUtil._pos(s, True))
      kwds['GetResolution'] = property(lambda s: _IWICMQRUtil._res(s, True))
    elif 'Writer' in name:
      for n in mcls._queries:
        kwds['Set' + n] = _WICMetadataQuery()
      kwds['SetPosition'] = property(lambda s: _IWICMQRUtil._pos(s, False))
      kwds['SetResolution'] = property(lambda s: _IWICMQRUtil._res(s, False))
    return kwds

class IWICMetadataQueryReader(IUnknown, metaclass=_IWICMQRMeta):
  IID = GUID(0x30989668, 0xe1c9, 0x4597, 0xb3, 0x95, 0x45, 0x8e, 0xed, 0xb8, 0x08, 0xdf)
  _protos['GetContainerFormat'] = 3, (), (WICPMETADATAHANDLER,)
  _protos['GetLocation'] = 4, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetMetadataByName'] = 5, (wintypes.LPCWSTR,), (PPROPVARIANT,)
  _protos['GetEnumerator'] = 6, (), (wintypes.PLPVOID,)
  def GetContainerFormat(self):
    return self.__class__._protos['GetContainerFormat'](self.pI)
  def GetLocation(self):
    if (al := self.__class__._protos['GetLocation'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    l = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetLocation'](self.pI, al, l) is None else (ctypes.c_wchar * al).from_buffer(l).value
  def GetEnumerator(self):
    return IEnumString(self.__class__._protos['GetEnumerator'](self.pI), self.factory)
  def GetMetadataNames(self):
    if (e := self.GetEnumerator()) is None:
      return None
    n = []
    while True:
      if not (ns := e.Next(10)):
        return n
      n.extend(ns)
  def GetMetadataByName(self, name):
    if (v := self.__class__._protos['GetMetadataByName'](self.pI, name)) is None:
      return None
    v._needsclear = True
    return v.value.QueryInterface(self.__class__, self.factory) if v.vt == 13 else v.value
  def GetMetadataTypeByName(self, name):
    if (v := self.__class__._protos['GetMetadataByName'](self.pI, name)) is None:
      return None
    v._needsclear = True
    return v.vt
  def GetMetadataWithTypeByName(self, name):
    if (v := self.__class__._protos['GetMetadataByName'](self.pI, name)) is None:
      return None
    v._needsclear = True
    return v.vt, (v.value.QueryInterface(self.__class__, self.factory) if v.vt == 13 else v.value)

class IWICMetadataReader(IUnknown):
  IID = GUID(0x9204fe99, 0xd8fc, 0x4fd5, 0xa0, 0x01, 0x95, 0x36, 0xb0, 0x67, 0xa8, 0x99)
  _protos['GetMetadataFormat'] = 3, (), (WICPMETADATAHANDLER,)
  _protos['GetMetadataHandlerInfo'] = 4, (), (wintypes.PLPVOID,)
  _protos['GetCount'] = 5, (), (wintypes.PUINT,)
  _protos['GetValueByIndex'] = 6, (wintypes.UINT,), (PPROPVARIANT, PPROPVARIANT, PPROPVARIANT)
  _protos['GetValue'] = 7, (PPROPVARIANT, PPROPVARIANT), (PPROPVARIANT,)
  _protos['GetEnumerator'] = 8, (), (wintypes.PLPVOID,)
  def GetMetadataFormat(self):
    return self.__class__._protos['GetMetadataFormat'](self.pI)
  def GetCount(self):
    return self.__class__._protos['GetCount'](self.pI)
  def GetEnumerator(self):
    return IWICEnumMetadataItemReader(self.__class__._protos['GetEnumerator'](self.pI), self.factory)
  def GetEnumeratorWithType(self):
    return IWICEnumMetadataWithTypeItemReader(self.__class__._protos['GetEnumerator'](self.pI), self.factory)
  def GetValue(self, schema, ident):
    if isinstance(schema, (tuple, list)):
      schema = PROPVARIANT(*schema)
    if isinstance(ident, (tuple, list)):
      ident = PROPVARIANT(*ident)
    if (v := self.__class__._protos['GetValue'](self.pI, schema, ident)) is None:
      return None
    v._needsclear = True
    return v.value.QueryInterface(self.__class__, self.factory) if v.vt == 13 else v.value
  def GetValueByIndex(self, index):
    if (siv := self.__class__._protos['GetValueByIndex'](self.pI, index)) is None:
      return None
    siv[0]._needsclear = siv[1]._needsclear = siv[2]._needsclear = True
    return tuple(p.value.QueryInterface(self.__class__, self.factory) if p.vt == 13 else p.value for p in siv)
  def GetValueWithTypeByIndex(self, index):
    if (siv := self.__class__._protos['GetValueByIndex'](self.pI, index)) is None:
      return None
    siv[0]._needsclear = siv[1]._needsclear = siv[2]._needsclear = True
    return tuple((p.vt, (p.value.QueryInterface(self.__class__, self.factory) if p.vt == 13 else p.value)) for p in siv)
  def GetMetadataHandlerInfo(self):
    return IWICMetadataHandlerInfo(self.__class__._protos['GetMetadataHandlerInfo'](self.pI)).QueryInterface(IWICMetadataReaderInfo, self.factory)
  def GetPersistStream(self):
    return self.QueryInterface(IWICPersistStream, self.factory)
  def GetStreamProvider(self):
    return self.QueryInterface(IWICStreamProvider, self.factory)

class IWICEnumMetadataItemReader(IWICEnumMetadataItem):
  IClass = IWICMetadataReader
  WithType = False

class IWICEnumMetadataWithTypeItemReader(IWICEnumMetadataItem):
  IClass = IWICMetadataReader
  WithType = True

class IEnumWICMetadataReader(IEnumUnknown):
  IClass = IWICMetadataReader

class IWICMetadataBlockReader(IUnknown):
  IID = GUID(0xfeaa2a8d, 0xb3f3, 0x43e4, 0xb2, 0x5c, 0xd1, 0xde, 0x99, 0x0a, 0x1a, 0xe1)
  _protos['GetContainerFormat'] = 3, (), (WICPCONTAINERFORMAT,)
  _protos['GetCount'] = 4, (), (wintypes.PUINT,)
  _protos['GetReaderByIndex'] = 5, (wintypes.UINT,), (wintypes.PLPVOID,)
  _protos['GetEnumerator'] = 6, (), (wintypes.PLPVOID,)
  def GetContainerFormat(self):
    return self.__class__._protos['GetContainerFormat'](self.pI)
  def GetCount(self):
    return self.__class__._protos['GetCount'](self.pI)
  def GetEnumerator(self):
    return IEnumWICMetadataReader(self.__class__._protos['GetEnumerator'](self.pI), self.factory)
  def GetReaderByIndex(self, index):
    return IWICMetadataReader(self.__class__._protos['GetReaderByIndex'](self.pI, index), self.factory)
  def GetReaders(self):
    e = self.GetEnumerator()
    return None if e is None else tuple(e)
  def GetStreamProvider(self):
    return self.QueryInterface(IWICStreamProvider, self.factory)

class IWICBitmapFrameDecode(IWICBitmapSource):
  IID = GUID(0x3b16811b, 0x6a43, 0x4ec9, 0xa8, 0x13, 0x3d, 0x93, 0x0c, 0x13, 0xb9, 0x40)
  _protos['GetMetadataQueryReader'] = 8, (), (wintypes.PLPVOID,)
  _protos['GetColorContexts'] = 9, (wintypes.UINT, wintypes.PLPVOID), (wintypes.PUINT,)
  _protos['GetThumbnail'] = 10, (), (wintypes.PLPVOID,)
  def GetColorContexts(self):
    if (ac := self.__class__._protos['GetColorContexts'](self.pI, 0, None)) is None:
      return None
    if ac == 0:
      return ()
    IColorContexts = tuple(self.factory.CreateColorContext() for c in range(ac))
    pColorContexts = (wintypes.LPVOID * ac)(*(cc.pI for cc in IColorContexts))
    return None if self.__class__._protos['GetColorContexts'](self.pI, ac, pColorContexts) is None else IColorContexts
  def GetMetadataQueryReader(self):
    return IWICMetadataQueryReader(self.__class__._protos['GetMetadataQueryReader'](self.pI), self.factory)
  def GetThumbnail(self):
    return IWICBitmapSource(self.__class__._protos['GetThumbnail'](self.pI), self.factory)
  def GetPalette(self):
    IPalette = self.factory.CreatePalette()
    return None if self.CopyPalette(IPalette) is None else IPalette
  def GetMetadataBlockReader(self):
    return self.QueryInterface(IWICMetadataBlockReader, self.factory)
  def GetJpegFrameDecode(self):
    return self.QueryInterface(IWICJpegFrameDecode, self.factory)
  def GetBitmapSourceTransform(self):
    return self.QueryInterface(IWICBitmapSourceTransform, self.factory)
  def GetPlanarBitmapSourceTransform(self):
    return self.QueryInterface(IWICPlanarBitmapSourceTransform, self.factory)
  def GetDdsFrameDecode(self):
    return self.QueryInterface(IWICDdsFrameDecode, self.factory)
  def GetProgressiveLevelControl(self):
    return self.QueryInterface(IWICProgressiveLevelControl, self.factory)
  def GetStreamProvider(self):
    return self.QueryInterface(IWICStreamProvider, self.factory)

class IWICBitmapSourceTransform(IUnknown):
  IID = GUID(0x3b16811b, 0x6a43, 0x4ec9, 0xb7, 0x13, 0x3d, 0x5a, 0x0c, 0x13, 0xb9, 0x40)
  _protos['CopyPixels'] = 3, (PXYWH, wintypes.UINT, wintypes.UINT, WICPPIXELFORMAT, WICTRANSFORMOPTIONS, wintypes.UINT, wintypes.UINT, PBUFFER),  ()
  _protos['GetClosestSize'] = 4, (wintypes.PUINT, wintypes.PUINT), ()
  _protos['GetClosestPixelFormat'] = 5, (WICPPIXELFORMAT,), ()
  _protos['DoesSupportTransform'] = 6, (WICTRANSFORMOPTIONS,), (wintypes.PBOOLE,)
  def GetClosestSize(self, width, height):
    w = wintypes.UINT(width)
    h = wintypes.UINT(height)
    return None if self.__class__._protos['GetClosestSize'](self.pI, w, h) is None else w.value, h.value
  def GetClosestPixelFormat(self, pixel_format=b''):
    if not (ppf := WICPPIXELFORMAT.create_from(pixel_format)):
      ISetLastError(0x80070057)
      return None
    return None if self.__class__._protos['GetClosestPixelFormat'](self.pI, ppf) is None else ppf.contents
  def DoesSupportTransform(self, transform_options):
    return self.__class__._protos['DoesSupportTransform'](self.pI, transform_options)
  def CopyPixels(self, xywh, width, height, pixel_format, transform_options, stride, buffer):
    return self.__class__._protos['CopyPixels'](self.pI, xywh, width, height, pixel_format, transform_options, stride, PBUFFER.length(buffer), buffer)

class IWICPlanarBitmapSourceTransform(IUnknown):
  IID = GUID(0x3aff9cce, 0xbe95, 0x4303, 0xb9, 0x27, 0xe7, 0xd1, 0x6f, 0xf4, 0xa6, 0x13)
  _protos['DoesSupportTransform'] = 3, (wintypes.PUINT, wintypes.PUINT, WICTRANSFORMOPTIONS, WICPLANAROPTION, WICPPIXELFORMAT, WICPBITMAPPLANEDESCRIPTION, wintypes.UINT), (wintypes.PBOOLE,)
  _protos['CopyPixels'] = 4, (PXYWH, wintypes.UINT, wintypes.UINT, WICTRANSFORMOPTIONS, WICPLANAROPTION, WICPBITMAPPLANE, wintypes.UINT),  ()
  def DoesSupportTransform(self, width, height, transform_options, planar_option, pixel_formats):
    planes_number = len(pixel_formats) if pixel_formats is not None else 0
    w = wintypes.UINT(width)
    h = wintypes.UINT(height)
    if pixel_formats is not None and not isinstance(pixel_formats, ctypes.Array):
      pixel_formats = (WICPIXELFORMAT * planes_number)(*(WICPIXELFORMAT(pf) for pf in pixel_formats))
    planes_descriptions = (WICBITMAPPLANEDESCRIPTION * planes_number)()
    r = self.__class__._protos['DoesSupportTransform'](self.pI, w, h, transform_options, planar_option, pixel_formats, planes_descriptions, planes_number)
    return None if r is None else r, w.value, h.value, tuple(pd.to_dict() for pd in planes_descriptions)
  def CopyPixels(self, xywh, width, height, transform_options, planar_option, planes_buffers):
    planes_number = len(planes_buffers) if planes_buffers is not None else 0
    if planes_buffers is not None and not isinstance(planes_buffers, ctypes.Array):
      planes_buffers = (WICBITMAPPLANE * planes_number)(*(WICBITMAPPLANE.from_param(pb) for pb in planes_buffers))
    return self.__class__._protos['CopyPixels'](self.pI, xywh, width, height, transform_options, planar_option, planes_buffers, planes_number)

class IWICBitmapDecoder(IUnknown):
  IID = GUID(0x9edde9e7, 0x8dee, 0x47ea, 0x99, 0xdf, 0xe6, 0xfa, 0xf2, 0xed, 0x44, 0xbf)
  _protos['QueryCapability'] = 3, (wintypes.LPVOID,), (WICPDECODERCAPABILITIES,)
  _protos['Initialize'] = 4, (wintypes.LPVOID, WICDECODEOPTION), ()
  _protos['GetContainerFormat'] = 5, (), (WICPCONTAINERFORMAT,)
  _protos['GetDecoderInfo'] = 6, (), (wintypes.PLPVOID,)
  _protos['CopyPalette'] = 7, (wintypes.LPVOID,), ()
  _protos['GetMetadataQueryReader'] = 8, (), (wintypes.PLPVOID,)
  _protos['GetPreview'] = 9, (), (wintypes.PLPVOID,)
  _protos['GetColorContexts'] = 10, (wintypes.UINT, wintypes.PLPVOID), (wintypes.PUINT,)
  _protos['GetThumbnail'] = 11, (), (wintypes.PLPVOID,)
  _protos['GetFrameCount'] = 12, (), (wintypes.PUINT,)
  _protos['GetFrame'] = 13, (wintypes.UINT,), (wintypes.PLPVOID,)
  def QueryCapability(self, istream):
    if (p := istream.Seek()) is None:
      return None
    ca = self.__class__._protos['QueryCapability'](self.pI, istream)
    istream.Seek(p, 'beginning')
    return ca
  def Initialize(self, istream, metadata_option=0):
    return self.__class__._protos['Initialize'](self.pI, istream, metadata_option)
  def GetContainerFormat(self):
    return self.__class__._protos['GetContainerFormat'](self.pI)
  def GetColorContexts(self):
    if (ac := self.__class__._protos['GetColorContexts'](self.pI, 0, None)) is None:
      return None
    if ac == 0:
      return ()
    IColorContexts = tuple(self.factory.CreateColorContext() for c in range(ac))
    pColorContexts = (wintypes.LPVOID * ac)(*(cc.pI for cc in IColorContexts))
    return None if self.__class__._protos['GetColorContexts'](self.pI, ac, pColorContexts) is None else IColorContexts
  def GetMetadataQueryReader(self):
    return IWICMetadataQueryReader(self.__class__._protos['GetMetadataQueryReader'](self.pI), self.factory)
  def GetThumbnail(self):
    return IWICBitmapSource(self.__class__._protos['GetThumbnail'](self.pI), self.factory)
  def GetPreview(self):
    return IWICBitmapSource(self.__class__._protos['GetPreview'](self.pI), self.factory)
  def CopyPalette(self, palette):
    return self.__class__._protos['CopyPalette'](self.pI, palette)
  def GetPalette(self):
    IPalette = self.factory.CreatePalette()
    return None if self.CopyPalette(IPalette) is None else IPalette
  def GetFrameCount(self):
    return self.__class__._protos['GetFrameCount'](self.pI)
  def GetFrame(self, index):
    return IWICBitmapFrameDecode(self.__class__._protos['GetFrame'](self.pI, index), self.factory)
  def GetDecoderInfo(self):
    return IWICBitmapDecoderInfo(self.__class__._protos['GetDecoderInfo'](self.pI), self.factory)
  def GetDdsDecoder(self):
    return self.QueryInterface(IWICDdsDecoder, self.factory)
  def GetStreamProvider(self):
    return self.QueryInterface(IWICStreamProvider, self.factory)

class IWICJpegFrameDecode(IUnknown):
  IID = GUID(0x8939f66e, 0xc46a, 0x4c21, 0xa9, 0xd1, 0x98, 0xb3, 0x27, 0xce, 0x16, 0x79)
  _protos['DoesSupportIndexing'] = 3, (), (wintypes.PBOOLE,)
  _protos['SetIndexing'] = 4, (WICJPEGINDEXINGOPTION, wintypes.UINT), ()
  _protos['ClearIndexing'] = 5, (), ()
  _protos['GetAcHuffmanTable'] = 6, (wintypes.UINT, wintypes.UINT), (WICPJPEGACHUFFMANTABLE,)
  _protos['GetDcHuffmanTable'] = 7, (wintypes.UINT, wintypes.UINT), (WICPJPEGDCHUFFMANTABLE,)
  _protos['GetQuantizationTable'] = 8, (wintypes.UINT, wintypes.UINT), (WICPJPEGQUANTIZATIONTABLE,)
  _protos['GetFrameHeader'] = 9, (), (WICPJPEGFRAMEHEADER,)
  _protos['GetScanHeader'] = 10, (wintypes.UINT,), (WICPJPEGSCANHEADER,)
  _protos['CopyScan'] = 11, (wintypes.UINT, wintypes.UINT, wintypes.UINT, PBUFFER), (wintypes.PUINT,)
  def DoesSupportIndexing(self):
    return self.__class__._protos['DoesSupportIndexing'](self.pI)
  def SetIndexing(self, indexing_option=0, index_granularity=16):
    return self.__class__._protos['SetIndexing'](self.pI, indexing_option, index_granularity)
  def ClearIndexing(self):
    return self.__class__._protos['ClearIndexing'](self.pI)
  def GetFrameHeader(self):
    fh = self.__class__._protos['GetFrameHeader'](self.pI)
    return None if fh is None else fh.to_dict()
  def GetAcHuffmanTable(self, scan_index, table_index):
    ht = self.__class__._protos['GetAcHuffmanTable'](self.pI, scan_index, table_index)
    return None if ht is None else ht.to_dict()
  def GetDcHuffmanTable(self, scan_index, table_index):
    ht = self.__class__._protos['GetDcHuffmanTable'](self.pI, scan_index, table_index)
    return None if ht is None else ht.to_dict()
  def GetQuantizationTable(self, scan_index, table_index):
    qt = self.__class__._protos['GetQuantizationTable'](self.pI, scan_index, table_index)
    return None if qt is None else qt.Elements
  def GetScanHeader(self, scan_index):
    sh = self.__class__._protos['GetScanHeader'](self.pI, scan_index)
    return None if sh is None else sh.to_dict()
  def CopyScan(self, scan_index):
    s = []
    scan_offset = 0
    while True:
      b = bytearray(1048576)
      if (al := self.__class__._protos['CopyScan'](self.pI, scan_index, scan_offset, 1048576, b)) is None:
        return None
      elif al == 1048576:
        s.append(b)
        scan_offset += al
      else:
        s.append(memoryview(b)[:al])
        return b''.join(s)
  def GetPlanarBitmapSourceTransform(self):
    return self.QueryInterface(IWICPlanarBitmapSourceTransform, self.factory)
  def GetProgressiveLevelControl(self):
    return self.QueryInterface(IWICProgressiveLevelControl, self.factory)

class IWICDdsFrameDecode(IUnknown):
  IID = GUID(0x3d4c0c61, 0x18a4, 0x41e4, 0xbd, 0x80, 0x48, 0x1a, 0x4f, 0xc9, 0xf4, 0x64)
  _protos['GetSizeInBlocks'] = 3, (), (wintypes.PUINT, wintypes.PUINT)
  _protos['GetFormatInfo'] = 4, (), (WICPDDSFORMATINFO,)
  _protos['CopyBlocks'] = 5, (PXYWH, wintypes.UINT, wintypes.UINT, PBUFFER), ()
  def GetFormatInfo(self):
    fi = self.__class__._protos['GetFormatInfo'](self.pI)
    return None if fi is None else fi.to_dict()
  def GetSizeInBlocks(self):
    return self.__class__._protos['GetSizeInBlocks'](self.pI)
  def CopyBlocks(self, xywh, stride, buffer):
    return self.__class__._protos['CopyBlocks'](self.pI, xywh, stride, PBUFFER.length(buffer), buffer)

class IWICDdsDecoder(IUnknown):
  IID = GUID(0x409cd537, 0x8532, 0x40cb, 0x97, 0x74, 0xe2, 0xfe, 0xb2, 0xdf, 0x4e, 0x9c)
  _protos['GetParameters'] = 3, (), (WICPDDSPARAMETERS,)
  _protos['GetFrame'] = 4, (wintypes.UINT, wintypes.UINT, wintypes.UINT), (wintypes.PLPVOID,)
  def GetParameters(self):
    p = self.__class__._protos['GetParameters'](self.pI)
    return None if p is None else p.to_dict()
  def GetFrame(self, array_index, mip_level, slice_index):
    return IWICBitmapFrameDecode(self.__class__._protos['GetFrame'](self.pI, array_index, mip_level, slice_index), self.factory)

class IWICProgressiveLevelControl(IUnknown):
  IID = GUID(0xdaac296f, 0x7aa5, 0x4dbf, 0x8d, 0x15, 0x22, 0x5c, 0x59, 0x76, 0xf8, 0x91)
  _protos['GetLevelCount'] = 3, (), (wintypes.PUINT,)
  _protos['GetCurrentLevel'] = 4, (), (wintypes.PUINT,)
  _protos['SetCurrentLevel'] = 5, (wintypes.UINT,), ()
  def GetLevelCount(self):
    return self.__class__._protos['GetLevelCount'](self.pI)
  def GetCurrentLevel(self):
    return self.__class__._protos['GetCurrentLevel'](self.pI)
  def SetCurrentLevel(self, level):
    return self.__class__._protos['SetCurrentLevel'](self.pI, level)

class IWICMetadataQueryWriter(IWICMetadataQueryReader):
  IID = GUID(0xa721791a, 0x0def, 0x4d06, 0xbd, 0x91, 0x21, 0x18, 0xbf, 0x1d, 0xb1, 0x0b)
  _protos['SetMetadataByName'] = 7, (wintypes.LPCWSTR, PPROPVARIANT), ()
  _protos['RemoveMetadataByName'] = 8, (wintypes.LPCWSTR,), ()
  def SetMetadataByName(self, name, data):
    v = None
    if isinstance(data, PROPVARIANT):
      v = data
    elif isinstance(data, (list, tuple)) and len(data) == 2:
      v = PROPVARIANT(*data)
    elif isinstance(data, IWICMetadataQueryWriter):
      v = PROPVARIANT(13, data)
    if v is None:
      ISetLastError(0x80070057)
      return None
    return self.__class__._protos['SetMetadataByName'](self.pI, name, v)
  def RemoveMetadataByName(self, name):
    return self.__class__._protos['RemoveMetadataByName'](self.pI, name)

class IWICMetadataWriter(IWICMetadataReader):
  IID = GUID(0xf7836e16, 0x3be0, 0x470b, 0x86, 0xbb, 0x16, 0x0d, 0x0a, 0xec, 0xd7, 0xde)
  _protos['SetValue'] = 9, (PPROPVARIANT, PPROPVARIANT, PPROPVARIANT), ()
  _protos['SetValueByIndex'] = 10, (wintypes.UINT, PPROPVARIANT, PPROPVARIANT, PPROPVARIANT), ()
  _protos['RemoveValue'] = 11, (PPROPVARIANT, PPROPVARIANT), ()
  _protos['RemoveValueByIndex'] = 12, (wintypes.UINT,), ()
  def GetEnumerator(self):
    return IWICEnumMetadataItemWriter(self.__class__._protos['GetEnumerator'](self.pI), self.factory)
  def GetEnumeratorWithType(self, code=False):
    return IWICEnumMetadataWithTypeItemWriter(self.__class__._protos['GetEnumerator'](self.pI), self.factory)
  def SetValue(self, schema, ident, value):
    if isinstance(schema, (tuple, list)):
      schema = PROPVARIANT(*schema)
    if isinstance(ident, (tuple, list)):
      ident = PROPVARIANT(*ident)
    if isinstance(value, (tuple, list)):
      value = PROPVARIANT(*value)
    return self.__class__._protos['SetValue'](self.pI, schema, ident, value)
  def SetValueByIndex(self, index, schema, ident, value):
    if isinstance(schema, (tuple, list)):
      schema = PROPVARIANT(*schema)
    if isinstance(ident, (tuple, list)):
      ident = PROPVARIANT(*ident)
    if isinstance(value, (tuple, list)):
      value = PROPVARIANT(*value)
    return self.__class__._protos['SetValueByIndex'](self.pI, index, schema, ident, value)
  def RemoveValue(self, schema, ident):
    if isinstance(schema, (tuple, list)):
      schema = PROPVARIANT(*schema)
    if isinstance(ident, (tuple, list)):
      ident = PROPVARIANT(*ident)
    return self.__class__._protos['RemoveValue'](self.pI, schema, ident)
  def RemoveValueByIndex(self, index):
    return self.__class__._protos['RemoveValueByIndex'](self.pI, index)
  def GetMetadataHandlerInfo(self):
    return IWICMetadataHandlerInfo(self.__class__._protos['GetMetadataHandlerInfo'](self.pI)).QueryInterface(IWICMetadataWriterInfo, self.factory)
  def GetPersistStream(self):
    return self.QueryInterface(IWICPersistStream, self.factory)
  def GetStreamProvider(self):
    return self.QueryInterface(IWICStreamProvider, self.factory)

class IWICEnumMetadataItemWriter(IWICEnumMetadataItem):
  IClass = IWICMetadataWriter
  WithType = False

class IWICEnumMetadataWithTypeItemWriter(IWICEnumMetadataItem):
  IClass = IWICMetadataWriter
  WithType = True

class IEnumWICMetadataWriter(IEnumUnknown):
  IClass = IWICMetadataWriter

class IWICMetadataBlockWriter(IWICMetadataBlockReader):
  IID = GUID(0x08fb9676, 0xb444, 0x41e8, 0x8d, 0xbe, 0x6a, 0x53, 0xa5, 0x42, 0xbf, 0xf1)
  _protos['InitializeFromBlockReader'] = 7, (wintypes.LPVOID,), ()
  _protos['GetWriterByIndex'] = 8, (wintypes.UINT,), (wintypes.PLPVOID,)
  _protos['AddWriter'] = 9, (wintypes.LPVOID,), ()
  _protos['SetWriterByIndex'] = 10, (wintypes.UINT, wintypes.LPVOID), ()
  _protos['RemoveWriterByIndex'] = 11, (wintypes.UINT,), ()
  def GetEnumerator(self):
    return IEnumWICMetadataWriter(self.__class__._protos['GetEnumerator'](self.pI), self.factory)
  def InitializeFromBlockReader(self, reader):
    return self.__class__._protos['InitializeFromBlockReader'](self.pI, reader)
  def GetWriterByIndex(self, index):
    return IWICMetadataWriter(self.__class__._protos['GetWriterByIndex'](self.pI, index), self.factory)
  def AddWriter(self, writer):
    return self.__class__._protos['AddWriter'](self.pI, writer)
  def SetWriterByIndex(self, index, writer):
    return self.__class__._protos['SetWriterByIndex'](self.pI, index, writer)
  def RemoveWriterByIndex(self, index):
    return self.__class__._protos['RemoveWriterByIndex'](self.pI, index)
  def GetWriters(self):
    e = self.GetEnumerator()
    return None if e is None else tuple(e)

class IWICFastMetadataEncoder(IUnknown):
  IID = GUID(0xb84e2c09, 0x78c9, 0x4ac4, 0x8b, 0xd3, 0x52, 0x4a, 0xe1, 0x66, 0x3a, 0x2f)
  _protos['Commit'] = 3, (), ()
  _protos['GetMetadataQueryWriter'] = 4, (), (wintypes.PLPVOID,)
  def Commit(self):
    return self.__class__._protos['Commit'](self.pI)
  def GetMetadataQueryWriter(self):
    return IWICMetadataQueryWriter(self.__class__._protos['GetMetadataQueryWriter'](self.pI), self.factory)

class IWICBitmapFrameEncode(IUnknown):
  IID = GUID(0x00000105, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['Initialize'] = 3, (wintypes.LPVOID,), ()
  _protos['SetSize'] = 4, (wintypes.UINT, wintypes.UINT), ()
  _protos['SetResolution'] = 5, (wintypes.DOUBLE, wintypes.DOUBLE), ()
  _protos['SetPixelFormat'] = 6, (WICPPIXELFORMAT,), ()
  _protos['SetColorContexts'] = 7, (wintypes.UINT, wintypes.LPVOID), ()
  _protos['SetPalette'] = 8, (wintypes.LPVOID,), ()
  _protos['SetThumbnail'] = 9, (wintypes.LPVOID,), ()
  _protos['WritePixels'] = 10, (wintypes.UINT, wintypes.UINT, wintypes.UINT, PBUFFER), ()
  _protos['WriteSource'] = 11, (wintypes.LPVOID, PXYWH), ()
  _protos['Commit'] = 12, (), ()
  _protos['GetMetadataQueryWriter'] = 13, (), (wintypes.PLPVOID,)
  def Initialize(self, options=None):
    return self.__class__._protos['Initialize'](self.pI, options)
  def SetSize(self, width, height):
    return self.__class__._protos['SetSize'](self.pI, width, height)
  def SetResolution(self, dpix, dpiy):
    return self.__class__._protos['SetResolution'](self.pI, dpix, dpiy)
  def SetPixelFormat(self, pixel_format=b''):
    if not (ppf := WICPPIXELFORMAT.create_from(pixel_format)):
      ISetLastError(0x80070057)
      return None
    return None if self.__class__._protos['SetPixelFormat'](self.pI, ppf) is None else ppf.contents
  def SetColorContexts(self, color_contexts):
    return None if self.__class__._protos['SetColorContexts'](self.pI, len(color_contexts), ctypes.byref((wintypes.LPVOID * len(color_contexts))(*(cc.pI for cc in color_contexts)) if isinstance(color_contexts, (tuple, list)) else color_contexts)) is None else len(color_contexts)
  def SetPalette(self, palette):
    return self.__class__._protos['SetPalette'](self.pI, palette)
  def GetMetadataQueryWriter(self):
    return IWICMetadataQueryWriter(self.__class__._protos['GetMetadataQueryWriter'](self.pI), self.factory)
  def SetThumbnail(self, thumbnail):
    return self.__class__._protos['SetThumbnail'](self.pI, thumbnail)
  def WriteSource(self, source, xywh=None):
    return self.__class__._protos['WriteSource'](self.pI, source, xywh)
  def WritePixels(self, lines_number, stride, buffer):
    return self.__class__._protos['WritePixels'](self.pI, lines_number, stride, PBUFFER.length(buffer), buffer)
  def Commit(self):
    return self.__class__._protos['Commit'](self.pI)
  def GetMetadataBlockWriter(self):
    return self.QueryInterface(IWICMetadataBlockWriter, self.factory)
  def GetJpegFrameEncode(self):
    return self.QueryInterface(IWICJpegFrameEncode, self.factory)
  def GetPlanarBitmapFrameEncode(self):
    return self.QueryInterface(IWICPlanarBitmapFrameEncode, self.factory)

class IWICBitmapEncoder(IUnknown):
  IID = GUID(0x00000103, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['Initialize'] = 3, (wintypes.LPVOID, WICBITMAPENCODERCACHEOPTION), ()
  _protos['GetContainerFormat'] = 4, (), (WICPCONTAINERFORMAT,)
  _protos['GetEncoderInfo'] = 5, (), (wintypes.PLPVOID,)
  _protos['SetColorContexts'] = 6, (wintypes.UINT, wintypes.LPVOID), ()
  _protos['SetPalette'] = 7, (wintypes.LPVOID,), ()
  _protos['SetThumbnail'] = 8, (wintypes.LPVOID,), ()
  _protos['SetPreview'] = 9, (wintypes.LPVOID,), ()
  _protos['CreateNewFrame'] = 10, (), (wintypes.PLPVOID, wintypes.PLPVOID)
  _protos['Commit'] = 11, (), ()
  _protos['GetMetadataQueryWriter'] = 12, (), (wintypes.PLPVOID,)
  def Initialize(self, istream, cache_option=2):
    return self.__class__._protos['Initialize'](self.pI, istream, cache_option)
  def GetContainerFormat(self):
    return self.__class__._protos['GetContainerFormat'](self.pI)
  def SetColorContexts(self, color_contexts):
    return None if self.__class__._protos['SetColorContexts'](self.pI, len(color_contexts), ctypes.byref((wintypes.LPVOID * len(color_contexts))(*(cc.pI for cc in color_contexts)) if isinstance(color_contexts, (tuple, list)) else color_contexts)) is None else len(color_contexts)
  def SetPalette(self, palette):
    return self.__class__._protos['SetPalette'](self.pI, palette)
  def GetMetadataQueryWriter(self):
    return IWICMetadataQueryWriter(self.__class__._protos['GetMetadataQueryWriter'](self.pI), self.factory)
  def SetThumbnail(self, thumbnail):
    return self.__class__._protos['SetThumbnail'](self.pI, thumbnail)
  def SetPreview(self, preview):
    return self.__class__._protos['SetPreview'](self.pI, preview)
  def CreateNewFrame(self):
    if (pIBitmapFrameEncode_pIEncoderOptions := self.__class__._protos['CreateNewFrame'](self.pI)) is None:
      return None
    return IWICBitmapFrameEncode(pIBitmapFrameEncode_pIEncoderOptions[0], self.factory), IWICEncoderPropertyBag(pIBitmapFrameEncode_pIEncoderOptions[1], self.factory)
  def Commit(self):
    return self.__class__._protos['Commit'](self.pI)
  def GetEncoderInfo(self):
    return IWICBitmapEncoderInfo(self.__class__._protos['GetEncoderInfo'](self.pI), self.factory)
  def GetDdsEncoder(self):
    return self.QueryInterface(IWICDdsEncoder, self.factory)

class IWICJpegFrameEncode(IUnknown):
  IID = GUID(0x2f0c601f, 0xd2c6, 0x468c, 0xab, 0xfa, 0x49, 0x49, 0x5d, 0x98, 0x3e, 0xd1)
  _protos['GetAcHuffmanTable'] = 3, (wintypes.UINT, wintypes.UINT), (WICPJPEGACHUFFMANTABLE,)
  _protos['GetDcHuffmanTable'] = 4, (wintypes.UINT, wintypes.UINT), (WICPJPEGDCHUFFMANTABLE,)
  _protos['GetQuantizationTable'] = 5, (wintypes.UINT, wintypes.UINT), (WICPJPEGQUANTIZATIONTABLE,)
  _protos['WriteScan'] = 6, (wintypes.UINT, PBUFFER), ()
  def GetAcHuffmanTable(self, table_index):
    ht = self.__class__._protos['GetAcHuffmanTable'](self.pI, table_index, 0)
    return None if ht is None else {'CodeCounts': ht.CodeCounts, 'CodeValues': ht.CodeValues}
  def GetDcHuffmanTable(self, table_index):
    ht = self.__class__._protos['GetDcHuffmanTable'](self.pI, table_index, 0)
    return None if ht is None else {'CodeCounts': ht.CodeCounts, 'CodeValues': ht.CodeValues}
  def GetQuantizationTable(self, table_index):
    qt = self.__class__._protos['GetQuantizationTable'](self.pI, table_index, 0)
    return None if qt is None else qt.Elements
  def WriteScan(self, buffer):
    return self.__class__._protos['WriteScan'](self.pI, PBUFFER.length(buffer), buffer)
  def GetPlanarBitmapFrameEncode(self):
    return self.QueryInterface(IWICPlanarBitmapFrameEncode, self.factory)

class IWICPlanarBitmapFrameEncode(IUnknown):
  IID = GUID(0xf928b7b8, 0x2221, 0x40c1, 0xb7, 0x2e, 0x7e, 0x82, 0xf1, 0x97, 0x4d, 0x1a)
  _protos['WritePixels'] = 3, (wintypes.UINT, WICPBITMAPPLANE, wintypes.UINT), ()
  _protos['WriteSource'] = 4, (wintypes.PLPVOID, wintypes.UINT, PXYWH), ()
  def WriteSource(self, planes_sources, xywh=None):
    planes_number = len(planes_sources) if planes_sources is not None else 0
    if planes_sources is not None and not isinstance(planes_sources, ctypes.Array):
      planes_sources = (wintypes.LPVOID * planes_number)(*((ps.pI if isinstance(ps, IUnknown) else ps) for ps in planes_sources))
    return self.__class__._protos['WriteSource'](self.pI, planes_sources, planes_number, xywh)
  def WritePixels(self, lines_number, planes_buffers):
    planes_number = len(planes_buffers) if planes_buffers is not None else 0
    if planes_buffers is not None and not isinstance(planes_buffers, ctypes.Array):
      planes_buffers = (WICBITMAPPLANE * planes_number)(*(WICBITMAPPLANE.from_param(pb) for pb in planes_buffers))
    return self.__class__._protos['WritePixels'](self.pI, lines_number, planes_buffers, planes_number)

class IWICDdsEncoder(IUnknown):
  IID = GUID(0x5cacdb4c, 0x407e, 0x41b3, 0xb9, 0x36, 0xd0, 0xf0, 0x10, 0xcd, 0x67, 0x32)
  _protos['SetParameters'] = 3, (WICPDDSPARAMETERS,), ()
  _protos['GetParameters'] = 4, (), (WICPDDSPARAMETERS,)
  _protos['CreateNewFrame'] = 5, (), (wintypes.PLPVOID, wintypes.PUINT, wintypes.PUINT, wintypes.PUINT)
  def GetParameters(self):
    p = self.__class__._protos['GetParameters'](self.pI)
    return None if p is None else p.to_dict()
  def SetParameters(self, parameters):
    return self.__class__._protos['SetParameters'](self.pI, WICDDSPARAMETERS.from_param(parameters))
  def CreateNewFrame(self):
    pIBitmapFrameEncode_ai_ml_si = self.__class__._protos['CreateNewFrame'](self.pI)
    return None if pIBitmapFrameEncode_ai_ml_si is None else (IWICBitmapFrameEncode(pIBitmapFrameEncode_ai_ml_si[0], self.factory), dict(zip(('ArrayIndex', 'MipLevel', 'SliceIndex'), pIBitmapFrameEncode_ai_ml_si[1:4])))

class IWICImageEncoder(IUnknown):
  IID = GUID(0x04c75bf8, 0x3ce1, 0x473b, 0xac, 0xc5, 0x3c, 0xc4, 0xf5, 0xe9, 0x49, 0x99)
  _protos['WriteFrame'] = 3, (wintypes.LPVOID, wintypes.LPVOID, WICPIMAGEPARAMETERS), ()
  _protos['WriteFrameThumbnail'] = 4, (wintypes.LPVOID, wintypes.LPVOID, WICPIMAGEPARAMETERS), ()
  _protos['WriteThumbnail'] = 5, (wintypes.LPVOID, wintypes.LPVOID, WICPIMAGEPARAMETERS), ()
  def WriteThumbnail(self, image, encoder, image_parameters=None):
    return self.__class__._protos['WriteThumbnail'](self.pI, image, encoder, WICIMAGEPARAMETERS.from_param(image_parameters))
  def WriteFrame(self, image, frame_encode, image_parameters=None):
    return self.__class__._protos['WriteFrame'](self.pI, image, frame_encode, WICIMAGEPARAMETERS.from_param(image_parameters))
  def WriteFrameThumbnail(self, image, frame_encode, image_parameters=None):
    return self.__class__._protos['WriteFrameThumbnail'](self.pI, image, frame_encode, WICIMAGEPARAMETERS.from_param(image_parameters))

class IWICFormatConverter(IWICBitmapSource):
  IID = GUID(0x00000301, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['Initialize'] = 8, (wintypes.LPVOID, WICPPIXELFORMAT, WICDITHERTYPE, wintypes.LPVOID, wintypes.DOUBLE, WICPALETTETYPE), ()
  _protos['CanConvert'] = 9, (WICPPIXELFORMAT, WICPPIXELFORMAT), (wintypes.PBOOLE,)
  def CanConvert(self, source_pixel_format, destination_pixel_format):
    return self.__class__._protos['CanConvert'](self.pI, source_pixel_format, destination_pixel_format)
  def Initialize(self, source, destination_pixel_format, dither_type=0, palette=None, alpha_threshold=0, palette_type=0):
    return self.__class__._protos['Initialize'](self.pI, source, destination_pixel_format, dither_type, palette, alpha_threshold, palette_type)
  def GetPlanarFormatConverter(self):
    return self.QueryInterface(IWICPlanarFormatConverter, self.factory)

class IWICPlanarFormatConverter(IWICBitmapSource):
  IID = GUID(0xbebee9cb, 0x83b0, 0x4dcc, 0x81, 0x32, 0xb0, 0xaa, 0xa5, 0x5e, 0xac, 0x96)
  _protos['Initialize'] = 8, (wintypes.PLPVOID, wintypes.UINT, WICPPIXELFORMAT, WICDITHERTYPE, wintypes.LPVOID, wintypes.DOUBLE, WICPALETTETYPE), ()
  _protos['CanConvert'] = 9, (WICPPIXELFORMAT, wintypes.UINT, WICPPIXELFORMAT), (wintypes.PBOOLE,)
  def CanConvert(self, source_pixel_formats, destination_pixel_format):
    planes_number = len(source_pixel_formats) if source_pixel_formats is not None else 0
    if source_pixel_formats is not None and not isinstance(source_pixel_formats, ctypes.Array):
      source_pixel_formats = (WICPIXELFORMAT * planes_number)(*(WICPIXELFORMAT(pf) for pf in source_pixel_formats))
    return self.__class__._protos['CanConvert'](self.pI, source_pixel_formats, planes_number, destination_pixel_format)
  def Initialize(self, planes_sources, destination_pixel_format, dither_type=0, palette=None, alpha_threshold=0, palette_type=0):
    planes_number = len(planes_sources) if planes_sources is not None else 0
    if planes_sources is not None and not isinstance(planes_sources, ctypes.Array):
      planes_sources = (wintypes.LPVOID * planes_number)(*((ps.pI if isinstance(ps, IUnknown) else ps) for ps in planes_sources))
    return self.__class__._protos['Initialize'](self.pI, planes_sources, planes_number, destination_pixel_format, dither_type, palette, alpha_threshold, palette_type)

class IWICColorTransform(IWICBitmapSource):
  IID = GUID(0xb66f034f, 0xd0e2, 0x40ab, 0xb4, 0x36, 0x6d, 0xe3, 0x9e, 0x32, 0x1a, 0x94)
  _protos['Initialize'] = 8, (wintypes.LPVOID, wintypes.LPVOID, wintypes.LPVOID, WICPPIXELFORMAT), ()
  def Initialize(self, source, source_color_context, destination_color_context, destination_pixel_format):
    return self.__class__._protos['Initialize'](self.pI, source, source_color_context, destination_color_context, destination_pixel_format)
  def GetPlanarBitmapSourceTransform(self):
    return self.QueryInterface(IWICPlanarBitmapSourceTransform, self.factory)

class IWICBitmapLock(IUnknown):
  IID = GUID(0x00000123, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['GetSize'] = 3, (), (wintypes.PUINT, wintypes.PUINT)
  _protos['GetStride'] = 4, (), (wintypes.PUINT,)
  _protos['GetDataPointer'] = 5, (), (wintypes.PUINT, wintypes.PLPVOID)
  _protos['GetPixelFormat'] = 6, (), (WICPPIXELFORMAT,)
  def GetSize(self):
    return self.__class__._protos['GetSize'](self.pI)
  def GetStride(self):
    return self.__class__._protos['GetStride'](self.pI)
  def GetPixelFormat(self):
    return self.__class__._protos['GetPixelFormat'](self.pI)
  def GetDataPointer(self):
    s_d = self.__class__._protos['GetDataPointer'](self.pI)
    if s_d is None or s_d[0] == 0:
      return None
    return (wintypes.BYTE * s_d[0]).from_address(s_d[1].value)

class IWICBitmap(IWICBitmapSource):
  IID = GUID(0x00000120, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['Lock'] = 8, (PXYWH, wintypes.DWORD), (wintypes.PLPVOID,)
  _protos['SetPalette'] = 9, (wintypes.LPVOID,), ()
  _protos['SetResolution'] = 10, (wintypes.DOUBLE, wintypes.DOUBLE), ()
  def SetResolution(self, dpix, dpiy):
    return self.__class__._protos['SetResolution'](self.pI, dpix, dpiy)
  def SetPalette(self, palette):
    return self.__class__._protos['SetPalette'](self.pI, palette)
  def Lock(self, xywh, access_mode=1):
    if isinstance(access_mode, str):
      access_mode = {'read': 1, 'write': 2, 'readwrite': 3}.get(access_mode.lower(), 1)
    return IWICBitmapLock(self.__class__._protos['Lock'](self.pI, xywh, access_mode), self.factory)

class IWICBitmapScaler(IWICBitmapSource):
  IID = GUID(0x00000302, 0xa8f2, 0x4877, 0xba, 0x0a, 0xfd, 0x2b, 0x66, 0x45, 0xfb, 0x94)
  _protos['Initialize'] = 8, (wintypes.LPVOID, wintypes.UINT, wintypes.UINT, WICINTERPOLATIONMODE), ()
  def Initialize(self, source, width, height, interpolation_mode=3):
    return self.__class__._protos['Initialize'](self.pI, source, width, height, interpolation_mode)
  def GetPlanarBitmapSourceTransform(self):
    return self.QueryInterface(IWICPlanarBitmapSourceTransform, self.factory)

class IWICBitmapClipper(IWICBitmapSource):
  IID = GUID(0xe4fbcf03, 0x223d, 0x4e81, 0x93, 0x33, 0xd6, 0x35, 0x55, 0x6d, 0xd1, 0xb5)
  _protos['Initialize'] = 8, (wintypes.LPVOID, PXYWH), ()
  def Initialize(self, source, xywh):
    return self.__class__._protos['Initialize'](self.pI, source, xywh)

class IWICBitmapFlipRotator(IWICBitmapSource):
  IID = GUID(0x5009834f, 0x2d6a, 0x41ce, 0x9e, 0x1b, 0x17, 0xc5, 0xaf, 0xf7, 0xa7, 0x82)
  _protos['Initialize'] = 8, (wintypes.LPVOID, WICTRANSFORMOPTIONS), ()
  def Initialize(self, source, transform_options):
    return self.__class__._protos['Initialize'](self.pI, source, transform_options)
  def InitializeOnOrientation(self, source, orientation):
    return self.__class__._protos['Initialize'](self.pI, source, {1: 0, 2: 8, 3: 2, 4: 16, 5: 11, 6: 1, 7: 9, 8: 3}.get(METADATAORIENTATION.to_int(orientation), 0))
  def GetPlanarBitmapSourceTransform(self):
    return self.QueryInterface(IWICPlanarBitmapSourceTransform, self.factory)

class IWICComponentInfo(IUnknown):
  IID = GUID(0x23bc3f0a, 0x698b, 0x4357, 0x88, 0x6b, 0xf2, 0x4d, 0x50, 0x67, 0x13, 0x34)
  _protos['GetComponentType'] = 3, (), (WICPCOMPONENTTYPE,)
  _protos['GetCLSID'] = 4, (), (WICPCOMPONENT,)
  _protos['GetSigningStatus'] = 5, (), (WICPCOMPONENTSIGNING,)
  _protos['GetAuthor'] = 6, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetVendorGUID'] = 7, (), (WICPVENDORIDENTIFICATION,)
  _protos['GetVersion'] = 8, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetSpecVersion'] = 9, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetFriendlyName'] = 10, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  def GetComponentType(self):
    return self.__class__._protos['GetComponentType'](self.pI)
  def GetCLSID(self):
    return self.__class__._protos['GetCLSID'](self.pI)
  def GetSigningStatus(self):
    return self.__class__._protos['GetSigningStatus'](self.pI)
  def GetAuthor(self):
    if (al := self.__class__._protos['GetAuthor'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    a = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetAuthor'](self.pI, al, a) is None else (ctypes.c_wchar * al).from_buffer(a).value
  def GetVendorGUID(self):
    return self.__class__._protos['GetVendorGUID'](self.pI)
  def GetVersion(self):
    if (al := self.__class__._protos['GetVersion'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    v = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetVersion'](self.pI, al, v) is None else (ctypes.c_wchar * al).from_buffer(v).value
  def GetSpecVersion(self):
    if (al := self.__class__._protos['GetSpecVersion'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    v = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetSpecVersion'](self.pI, al, v) is None else (ctypes.c_wchar * al).from_buffer(v).value
  def GetFriendlyName(self):
    if (al := self.__class__._protos['GetFriendlyName'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    n = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetFriendlyName'](self.pI, al, n) is None else (ctypes.c_wchar * al).from_buffer(n).value

class IWICBitmapCodecInfo(IWICComponentInfo):
  IID = GUID(0xe87a44c4, 0xb76e, 0x4c47, 0x8b, 0x09, 0x29, 0x8e, 0xb1, 0x2a, 0x27, 0x14)
  _protos['GetContainerFormat'] = 11, (), (WICPCONTAINERFORMAT,)
  _protos['GetPixelFormats'] = 12, (wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT,)
  _protos['GetColorManagementVersion'] = 13, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetDeviceManufacturer'] = 14, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetDeviceModels'] = 15, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetMimeTypes'] = 16, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetFileExtensions'] = 17, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['DoesSupportAnimation'] = 18, (), (wintypes.PBOOLE,)
  _protos['DoesSupportChromaKey'] = 19, (), (wintypes.PBOOLE,)
  _protos['DoesSupportLossless'] = 20, (), (wintypes.PBOOLE,)
  _protos['DoesSupportMultiframe'] = 21, (), (wintypes.PBOOLE,)
  _protos['MatchesMimeType'] = 22, (wintypes.LPCWSTR,), (wintypes.PBOOLE,)
  def GetContainerFormat(self):
    return self.__class__._protos['GetContainerFormat'](self.pI)
  def GetPixelFormats(self):
    if (ac := self.__class__._protos['GetPixelFormats'](self.pI, 0, None)) is None:
      return None
    if ac == 0:
      return ()
    f = (WICPIXELFORMAT * ac)()
    return None if self.__class__._protos['GetPixelFormats'](self.pI, ac, ctypes.byref(f)) is None else tuple(f[p] for p in range(ac))
  def GetDeviceManufacturer(self):
    if (al := self.__class__._protos['GetDeviceManufacturer'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceManufacturer'](self.pI, al, m) is None else (ctypes.c_wchar * al).from_buffer(m).value
  def GetDeviceModels(self):
    if (al := self.__class__._protos['GetDeviceModels'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ()
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceModels'](self.pI, al, m) is None else tuple((ctypes.c_wchar * al).from_buffer(m).value.split(','))
  def GetMimeTypes(self):
    if (al := self.__class__._protos['GetMimeTypes'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    t = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetMimeTypes'](self.pI, al, t) is None else tuple((ctypes.c_wchar * al).from_buffer(t).value.split(','))
  def GetFileExtensions(self):
    if (al := self.__class__._protos['GetFileExtensions'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    e = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetFileExtensions'](self.pI, al, e) is None else tuple((ctypes.c_wchar * al).from_buffer(e).value.split(','))
  def GetColorManagementVersion(self):
    if (al := self.__class__._protos['GetColorManagementVersion'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    v = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetColorManagementVersion'](self.pI, al, v) is None else (ctypes.c_wchar * al).from_buffer(v).value
  def DoesSupportAnimation(self):
    return self.__class__._protos['DoesSupportAnimation'](self.pI)
  def DoesSupportChromaKey(self):
    return self.__class__._protos['DoesSupportChromaKey'](self.pI)
  def DoesSupportLossless(self):
    return self.__class__._protos['DoesSupportLossless'](self.pI)
  def DoesSupportMultiframe(self):
    return self.__class__._protos['DoesSupportMultiframe'](self.pI)
  def MatchesMimeType(self, mime_type):
    return self.__class__._protos['MatchesMimeType'](self.pI, mime_type)

class IWICBitmapDecoderInfo(IWICBitmapCodecInfo):
  IID = GUID(0xd8cd007f, 0xd08f, 0x4191, 0x9b, 0xfc, 0x23, 0x6e, 0xa7, 0xf0, 0xe4, 0xb5)
  _protos['GetPatterns'] = 23, (wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT, wintypes.PUINT)
  _protos['MatchesPattern'] = 24, (wintypes.LPVOID,), (wintypes.PBOOLE,)
  _protos['CreateInstance'] = 25, (), (wintypes.PLPVOID,)
  def GetPatterns(self):
    if (acs := self.__class__._protos['GetPatterns'](self.pI, 0, None)) is None:
      return None
    if acs[1] == 0:
      return ()
    p = ctypes.create_string_buffer(acs[1])
    f = (WICBITMAPPATTERN * acs[0]).from_buffer(p)
    return None if self.__class__._protos['GetPatterns'](self.pI, acs[1], ctypes.byref(p)) is None else tuple(f[p].to_dict() for p in range(acs[0]))
  def MatchesPattern(self, istream):
    return self.__class__._protos['MatchesPattern'](self.pI, istream)
  def CreateInstance(self):
    return IWICBitmapDecoder(self.__class__._protos['CreateInstance'](self.pI), self.factory)

class IWICBitmapEncoderInfo(IWICBitmapCodecInfo):
  IID = GUID(0x94c9b4ee, 0xa09f, 0x4f92, 0x8a, 0x1e, 0x4a, 0x9b, 0xce, 0x7e, 0x76, 0xfb)
  _protos['CreateInstance'] = 23, (), (wintypes.PLPVOID,)
  def CreateInstance(self):
    return IWICBitmapEncoder(self.__class__._protos['CreateInstance'](self.pI), self.factory)

class IWICFormatConverterInfo(IWICComponentInfo):
  IID = GUID(0x9f34fb65, 0x13f4, 0x4f15, 0xbc, 0x57, 0x37, 0x26, 0xb5, 0xe5, 0x3d, 0x9f)
  _protos['GetPixelFormats'] = 11, (wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT,)
  _protos['CreateInstance'] = 12, (), (wintypes.PLPVOID,)
  def GetPixelFormats(self):
    if (ac := self.__class__._protos['GetPixelFormats'](self.pI, 0, None)) is None:
      return None
    if ac == 0:
      return ()
    f = (WICPIXELFORMAT * ac)()
    return None if self.__class__._protos['GetPixelFormats'](self.pI, ac, ctypes.byref(f)) is None else tuple(f[p] for p in range(ac))
  def CreateInstance(self):
    return IWICFormatConverter(self.__class__._protos['CreateInstance'](self.pI), self.factory)

class IWICPixelFormatInfo(IWICComponentInfo):
  IID = GUID(0xa9db33a2, 0xaf5f, 0x43c7, 0xb6, 0x79, 0x74, 0xf5, 0x98, 0x4b, 0x5a, 0xa4)
  _protos['GetFormatGUID'] = 11, (), (WICPPIXELFORMAT,)
  _protos['GetColorContext'] = 12, (), (wintypes.PLPVOID,)
  _protos['GetBitsPerPixel'] = 13, (), (wintypes.PUINT,)
  _protos['GetChannelCount'] = 14, (), (wintypes.PUINT,)
  _protos['GetChannelMask'] = 15, (wintypes.UINT, wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT,)
  _protos['SupportsTransparency'] = 16, (), (wintypes.PBOOLE,)
  _protos['GetNumericRepresentation'] = 17, (), (WICPPIXELFORMATNUMERICREPRESENTATION,)
  def GetFormatGUID(self):
    return self.__class__._protos['GetFormatGUID'](self.pI)
  def GetBitsPerPixel(self):
    return self.__class__._protos['GetBitsPerPixel'](self.pI)
  def GetChannelCount(self):
    return self.__class__._protos['GetChannelCount'](self.pI)
  def GetChannelMask(self, index):
    if (al := self.__class__._protos['GetChannelMask'](self.pI, index, 0, None)) is None:
      return None
    if al == 0:
      return b''
    m = ctypes.create_string_buffer(al)
    return None if self.__class__._protos['GetChannelMask'](self.pI, index, al, m) is None else m.raw
  def GetColorContext(self):
    return IWICColorContext(self.__class__._protos['GetColorContext'](self.pI), self.factory)
  def SupportsTransparency(self):
    return self.__class__._protos['SupportsTransparency'](self.pI)
  def GetNumericRepresentation(self):
    return self.__class__._protos['GetNumericRepresentation'](self.pI)
IWICPixelFormatInfo2 = IWICPixelFormatInfo

class IWICMetadataHandlerInfo(IWICComponentInfo):
  IID = GUID(0xaba958bf, 0xc672, 0x44d1, 0x8d, 0x61, 0xce, 0x6d, 0xf2, 0xe6, 0x82, 0xc2)
  _protos['GetMetadataFormat'] = 11, (), (WICPMETADATAHANDLER,)
  _protos['GetContainerFormats'] = 12, (wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT,)
  _protos['GetDeviceManufacturer'] = 13, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['GetDeviceModels'] = 14, (wintypes.UINT, wintypes.LPWSTR), (wintypes.PUINT,)
  _protos['DoesRequireFullStream'] = 15, (), (wintypes.PBOOLE,)
  _protos['DoesSupportPadding'] = 16, (), (wintypes.PBOOLE,)
  _protos['DoesRequireFixedSize'] = 17, (), (wintypes.PBOOLE,)
  def GetMetadataFormat(self):
    return self.__class__._protos['GetMetadataFormat'](self.pI)
  def GetContainerFormats(self):
    if (ac := self.__class__._protos['GetContainerFormats'](self.pI, 0, None)) is None:
      return None
    if ac == 0:
      return ()
    f = (WICMETADATAHANDLER * ac)()
    return None if self.__class__._protos['GetContainerFormats'](self.pI, ac, ctypes.byref(f)) is None else tuple(f[p] for p in range(ac))
  def GetDeviceManufacturer(self):
    if (al := self.__class__._protos['GetDeviceManufacturer'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceManufacturer'](self.pI, al, m) is None else (ctypes.c_wchar * al).from_buffer(m).value
  def GetDeviceModels(self):
    if (al := self.__class__._protos['GetDeviceModels'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ()
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceModels'](self.pI, al, m) is None else tuple((ctypes.c_wchar * al).from_buffer(m).value.split(','))
  def DoesRequireFullStream(self):
    return self.__class__._protos['DoesRequireFullStream'](self.pI)
  def DoesSupportPadding(self):
    return self.__class__._protos['DoesSupportPadding'](self.pI)
  def DoesRequireFixedSize(self):
    return self.__class__._protos['DoesRequireFixedSize'](self.pI)

class IWICMetadataReaderInfo(IWICMetadataHandlerInfo):
  IID = GUID(0xeebf1f5b, 0x07c1, 0x4447, 0xa3, 0xab, 0x22, 0xac, 0xaf, 0x78, 0xa8, 0x04)
  _protos['GetPatterns'] = 18, (WICPMETADATAHANDLER, wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT, wintypes.PUINT)
  _protos['MatchesPattern'] = 19, (WICPMETADATAHANDLER, wintypes.LPVOID), (wintypes.PBOOLE,)
  _protos['CreateInstance'] = 20, (), (wintypes.PLPVOID,)
  def GetPatterns(self, container_format):
    if (acs := self.__class__._protos['GetPatterns'](self.pI, container_format, 0, None)) is None:
      return None
    if acs[1] == 0:
      return ()
    p = ctypes.create_string_buffer(acs[1])
    f = (WICMETADATAPATTERN * acs[0]).from_buffer(p)
    return None if self.__class__._protos['GetPatterns'](self.pI, container_format, acs[1], ctypes.byref(p)) is None else tuple(f[p].to_dict() for p in range(acs[0]))
  def MatchesPattern(self, container_format, istream):
    return self.__class__._protos['MatchesPattern'](self.pI, container_format, istream)
  def CreateInstance(self):
    return IWICMetadataReader(self.__class__._protos['CreateInstance'](self.pI), self.factory)

class IWICMetadataWriterInfo(IWICMetadataHandlerInfo):
  IID = GUID(0xb22e3fba, 0x3925, 0x4323, 0xb5, 0xc1, 0x9e, 0xbf, 0xc4, 0x30, 0xf2, 0x36)
  _protos['GetHeader'] = 18, (WICPMETADATAHANDLER, wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT,)
  _protos['CreateInstance'] = 19, (), (wintypes.PLPVOID,)
  def GetHeader(self, container_format):
    if (al := self.__class__._protos['GetHeader'](self.pI, container_format, 0, None)) is None:
      return None
    if al == 0:
      return {}
    h = ctypes.create_string_buffer(al)
    f = WICMETADATAHEADER.from_buffer(h)
    return None if self.__class__._protos['GetHeader'](self.pI, container_format, al, ctypes.byref(h)) is None else f.to_dict()
  def CreateInstance(self):
    return IWICMetadataWriter(self.__class__._protos['CreateInstance'](self.pI), self.factory)

class IWICImagingFactory(IUnknown):
  # CLSID = GUID(0xcacaf262, 0x9370, 0x4615, 0xa1, 0x3b, 0x9f, 0x55, 0x39, 0xda, 0x4c, 0x0a)
  CLSID = GUID(0x317d06e8, 0x5f24, 0x433d, 0xbd, 0xf7, 0x79, 0xce, 0x68, 0xd8, 0xab, 0xc2)
  #IID = GUID(0xec5ec8a9, 0xc395, 0x4314, 0x9c, 0x77, 0x54, 0xd7, 0xa9, 0x35, 0xff, 0x70)
  IID = GUID(0x7b816b45, 0x1996, 0x4476, 0xb1, 0x32, 0xde, 0x9e, 0x24, 0x7c, 0x8a, 0xf0)
  _protos['CreateDecoderFromFilename'] = 3, (wintypes.LPCWSTR, WICPVENDORIDENTIFICATION, wintypes.DWORD, WICDECODEOPTION), (wintypes.PLPVOID,)
  _protos['CreateDecoderFromStream'] = 4, (wintypes.LPVOID, WICPVENDORIDENTIFICATION, WICDECODEOPTION), (wintypes.PLPVOID,)
  _protos['CreateDecoderFromFileHandle'] = 5, (wintypes.ULONG_PTR, WICPVENDORIDENTIFICATION, WICDECODEOPTION), (wintypes.PLPVOID,)
  _protos['CreateComponentInfo'] = 6, (WICPCOMPONENT,), (wintypes.PLPVOID,)
  _protos['CreateDecoder'] = 7, (WICPCONTAINERFORMAT, WICPVENDORIDENTIFICATION), (wintypes.PLPVOID,)
  _protos['CreateEncoder'] = 8, (WICPCONTAINERFORMAT, WICPVENDORIDENTIFICATION), (wintypes.PLPVOID,)
  _protos['CreatePalette'] = 9, (), (wintypes.PLPVOID,)
  _protos['CreateFormatConverter'] = 10, (), (wintypes.PLPVOID,)
  _protos['CreateBitmapScaler'] = 11, (), (wintypes.PLPVOID,)
  _protos['CreateBitmapClipper'] = 12, (), (wintypes.PLPVOID,)
  _protos['CreateBitmapFlipRotator'] = 13, (), (wintypes.PLPVOID,)
  _protos['CreateStream'] = 14, (), (wintypes.PLPVOID,)
  _protos['CreateColorContext'] = 15, (), (wintypes.PLPVOID,)
  _protos['CreateColorTransformer'] = 16, (), (wintypes.PLPVOID,)
  _protos['CreateBitmap'] = 17, (wintypes.UINT, wintypes.UINT, WICPPIXELFORMAT, WICCREATECACHEOPTION), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromSource'] = 18, (wintypes.LPVOID, WICCREATECACHEOPTION), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromSourceRect'] = 19, (wintypes.LPVOID, wintypes.UINT, wintypes.UINT, wintypes.UINT, wintypes.UINT), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromMemory'] = 20, (wintypes.UINT, wintypes.UINT, WICPPIXELFORMAT, wintypes.UINT, wintypes.UINT, wintypes.LPVOID), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromHBITMAP'] = 21, (wintypes.HBITMAP, wintypes.HPALETTE, WICBITMAPALPHACHANNELOPTION), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromHICON'] = 22, (wintypes.HICON,), (wintypes.PLPVOID,)
  _protos['CreateComponentEnumerator'] = 23, (WICCOMPONENTTYPE, WICCOMPONENTENUMERATEOPTIONS), (wintypes.PLPVOID,)
  _protos['CreateFastMetadataEncoderFromDecoder'] = 24, (wintypes.LPVOID,), (wintypes.PLPVOID,)
  _protos['CreateFastMetadataEncoderFromFrameDecode'] = 25, (wintypes.LPVOID,), (wintypes.PLPVOID,)
  _protos['CreateQueryWriter'] = 26, (WICPMETADATAHANDLER, WICPVENDORIDENTIFICATION), (wintypes.PLPVOID,)
  _protos['CreateQueryWriterFromReader'] = 27, (wintypes.LPVOID, WICPVENDORIDENTIFICATION), (wintypes.PLPVOID,)
  _protos['CreateImageEncoder'] = 28, (wintypes.LPVOID,), (wintypes.PLPVOID,)
  def CreateDecoder(self, container_format, decoder_vendor=None):
    return IWICBitmapDecoder(self.__class__._protos['CreateDecoder'](self.pI, container_format, decoder_vendor), self)
  def CreateDecoderFromFilename(self, file_name, decoder_vendor=None, desired_access=0x80000000, metadata_option=0):
    if isinstance(desired_access, str):
      desired_access = {'read': 0x80000000, 'write': 0x40000000, 'readwrite': 0xc0000000}.get(desired_access.lower(), 0x80000000)
    return IWICBitmapDecoder(self.__class__._protos['CreateDecoderFromFilename'](self.pI, file_name, decoder_vendor, desired_access, metadata_option), self)
  def CreateDecoderFromFileHandle(self, file_handle, decoder_vendor=None, metadata_option=0):
    return IWICBitmapDecoder(self.__class__._protos['CreateDecoderFromFileHandle'](self.pI, file_handle, decoder_vendor, metadata_option), self)
  def CreateDecoderFromStream(self, istream, decoder_vendor=None, metadata_option=0):
    return IWICBitmapDecoder(self.__class__._protos['CreateDecoderFromStream'](self.pI, istream, decoder_vendor, metadata_option), self)
  def CreateEncoder(self, container_format, encoder_vendor=None):
    return IWICBitmapEncoder(self.__class__._protos['CreateEncoder'](self.pI, container_format, encoder_vendor), self)
  def CreateStream(self):
    return IWICStream(self.__class__._protos['CreateStream'](self.pI), self)
  def CreateColorContext(self):
    return IWICColorContext(self.__class__._protos['CreateColorContext'](self.pI), self)
  def CreatePalette(self):
    return IWICPalette(self.__class__._protos['CreatePalette'](self.pI), self)
  def CreateFormatConverter(self):
    return IWICFormatConverter(self.__class__._protos['CreateFormatConverter'](self.pI), self)
  def CreateColorTransformer(self):
    return IWICColorTransform(self.__class__._protos['CreateColorTransformer'](self.pI), self)
  def CreateFastMetadataEncoderFromDecoder(self, decoder):
    return IWICFastMetadataEncoder(self.__class__._protos['CreateFastMetadataEncoderFromDecoder'](self.pI, decoder), self)
  def CreateFastMetadataEncoderFromFrameDecode(self, frame_decode):
    return IWICFastMetadataEncoder(self.__class__._protos['CreateFastMetadataEncoderFromFrameDecode'](self.pI, frame_decode), self)
  def CreateQueryWriter(self, metadata_format, writer_vendor=None):
    return IWICMetadataQueryWriter(self.__class__._protos['CreateQueryWriter'](self.pI, metadata_format, writer_vendor), self)
  def CreateQueryWriterFromReader(self, query_reader, writer_vendor=None):
    return IWICMetadataQueryWriter(self.__class__._protos['CreateQueryWriterFromReader'](self.pI, query_reader, writer_vendor), self)
  def CreateBitmap(self, width, height, pixel_format, cache_option=1):
    return IWICBitmap(self.__class__._protos['CreateBitmap'](self.pI, width, height, pixel_format, cache_option), self)
  def CreateBitmapFromSource(self, source, cache_option=1):
    return IWICBitmap(self.__class__._protos['CreateBitmapFromSource'](self.pI, source, cache_option), self)
  def CreateBitmapFromSourceRect(self, source, xywh):
    return IWICBitmap(self.__class__._protos['CreateBitmapFromSourceRect'](self.pI, source, *xywh), self)
  def CreateBitmapFromMemory(self, width, height, pixel_format, stride, buffer):
    l = PBUFFER.length(buffer)
    return IWICBitmap(self.__class__._protos['CreateBitmapFromMemory'](self.pI, width, height, pixel_format, stride, l, buffer), self)
  def CreateBitmapFromHBITMAP(self, bitmap_handle, palette_handle=None, alpha_option=0):
    return IWICBitmap(self.__class__._protos['CreateBitmapFromHBITMAP'](self.pI, bitmap_handle, palette_handle, alpha_option), self)
  def CreateBitmapFromHICON(self, icon_handle):
    return IWICBitmap(self.__class__._protos['CreateBitmapFromHICON'](self.pI, icon_handle), self)
  def CreateBitmapScaler(self):
    return IWICBitmapScaler(self.__class__._protos['CreateBitmapScaler'](self.pI), self)
  def CreateBitmapClipper(self):
    return IWICBitmapClipper(self.__class__._protos['CreateBitmapClipper'](self.pI), self)
  def CreateBitmapFlipRotator(self):
    return IWICBitmapFlipRotator(self.__class__._protos['CreateBitmapFlipRotator'](self.pI), self)
  def CreateComponentInfo(self, clsid):
    if isinstance(clsid, WICPIXELFORMAT):
      clsid = WICCOMPONENT(clsid)
    if (ci := IWICComponentInfo(self.__class__._protos['CreateComponentInfo'](self.pI, clsid), self)) is None:
      return None
    c = ci.GetComponentType().code
    icls = globals().get('IWIC%sInfo' % next((n_ for n_, c_ in WICComponentType.items() if c_ == c), 'Component'), 'IWICComponentInfo')
    return ci.QueryInterface(icls)
  def CreateComponentEnumerator(self, types=0x3f, options=0):
    c = WICCOMPONENTTYPE.name_code(types)
    icls = globals().get('IWIC%sInfo' % next((n_ for n_, c_ in WICComponentType.items() if c_ == c), 'Component'), 'IWICComponentInfo')
    return type('IEnum' + icls.__name__[1:], (IEnumUnknown,), {'IClass': icls})(self.__class__._protos['CreateComponentEnumerator'](self.pI, types, options), self)
  def CreateImageEncoder(self, device):
    return IWICImageEncoder(self.__class__._protos['CreateImageEncoder'](self.pI, device), self)
  def CreateComponentFactory(self):
    return self.QueryInterface(IWICComponentFactory, self)
IWICImagingFactory2 = IWICImagingFactory

class IWICComponentFactory(IWICImagingFactory):
  CLSID = GUID(0x317d06e8, 0x5f24, 0x433d, 0xbd, 0xf7, 0x79, 0xce, 0x68, 0xd8, 0xab, 0xc2)
  IID = GUID(0x412d0c3a, 0x9650, 0x44fa, 0xaf, 0x5b, 0xdd, 0x2a, 0x06, 0xc8, 0xe8, 0xfb)
  _protos['CreateMetadataReader'] = 28, (WICPMETADATAHANDLER, WICPVENDORIDENTIFICATION, WICMETADATACREATIONOPTIONS, wintypes.LPVOID), (wintypes.PLPVOID,)
  _protos['CreateMetadataReaderFromContainer'] = 29, (WICPMETADATAHANDLER, WICPVENDORIDENTIFICATION, WICMETADATACREATIONOPTIONS, wintypes.LPVOID), (wintypes.PLPVOID,)
  _protos['CreateMetadataWriter'] = 30, (WICPMETADATAHANDLER, WICPVENDORIDENTIFICATION, WICMETADATACREATIONOPTIONS), (wintypes.PLPVOID,)
  _protos['CreateMetadataWriterFromReader'] = 31, (wintypes.LPVOID, WICPVENDORIDENTIFICATION), (wintypes.PLPVOID,)
  _protos['CreateQueryReaderFromBlockReader'] = 32, (wintypes.LPVOID,), (wintypes.PLPVOID,)
  _protos['CreateQueryWriterFromBlockWriter'] = 33, (wintypes.LPVOID,), (wintypes.PLPVOID,)
  _protos['CreateEncoderPropertyBag'] = 34, (wintypes.LPVOID, wintypes.UINT), (wintypes.PLPVOID,)
  def CreateMetadataReader(self, metadata_format, reader_vendor=None, options=0, istream=None):
    return IWICMetadataReader(self.__class__._protos['CreateMetadataReader'](self.pI, metadata_format, reader_vendor, options, istream), self)
  def CreateMetadataReaderFromContainer(self, container_format, reader_vendor=None, options=0, istream=None):
    return IWICMetadataReader(self.__class__._protos['CreateMetadataReaderFromContainer'](self.pI, container_format, reader_vendor, options, istream), self)
  def CreateMetadataWriter(self, metadata_format, writer_vendor=None, options=0):
    return IWICMetadataWriter(self.__class__._protos['CreateMetadataWriter'](self.pI, metadata_format, writer_vendor, options), self)
  def CreateMetadataWriterFromReader(self, reader, writer_vendor=None):
    return IWICMetadataWriter(self.__class__._protos['CreateMetadataWriterFromReader'](self.pI, reader, writer_vendor), self)
  def CreateQueryReaderFromBlockReader(self, block_reader):
    return IWICMetadataQueryReader(self.__class__._protos['CreateQueryReaderFromBlockReader'](self.pI, block_reader), self)
  def CreateQueryWriterFromBlockWriter(self, block_writer):
    return IWICMetadataQueryWriter(self.__class__._protos['CreateQueryWriterFromBlockWriter'](self.pI, block_writer), self)
  def CreateEncoderPropertyBag(self, properties):
    n = len(properties)
    propbags = (PROPBAG2 * n)()
    for pb, prop in zip(propbags, properties.items()):
      if not (pb.set(prop[0], *prop[1]) if isinstance(prop[1], (tuple, list)) else pb.set(prop[0], prop[1])):
        ISetLastError(0x80070057)
        return None
    return IWICEncoderPropertyBag(self.__class__._protos['CreateEncoderPropertyBag'](self.pI, propbags, n), self)

def Initialize(mode=6):
  if isinstance(mode, str):
    mode = 4 if mode.lower() in ('mt', 'mta') else 6
  if ISetLastError(ole32.CoInitializeEx(None, wintypes.DWORD(2))) in (0, 1):
    if not hasattr(_IUtil._local, 'initialized'):
      _IUtil._local.initialized = 0
    _IUtil._local.initialized += 1
    return True
  return None
def Uninitialize():
  if hasattr(_IUtil._local, 'initialized'):
    while _IUtil._local.initialized > 0:
      ISetLastError(ole32.CoUninitialize())
      _IUtil._local.initialized -= 1
    del _IUtil._local.initialized
    return True
  return None