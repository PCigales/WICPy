# WICPy v1.3.0 (https://github.com/PCigales/WICPy)
# Copyright © 2024 PCigales
# This program is licensed under the GNU GPLv3 copyleft license (see https://www.gnu.org/licenses)

import ctypes, ctypes.wintypes as wintypes
vars(ctypes).setdefault('CArgObject', ctypes.byref(ctypes.c_byte()).__class__)
vars(ctypes).setdefault('_Pointer', ctypes.POINTER(ctypes.c_byte).__mro__[1])
vars(ctypes).setdefault('_CData', ctypes.c_byte.__mro__[-2])
wintypes.PLPVOID = ctypes.POINTER(wintypes.LPVOID)
wintypes.PDOUBLE = ctypes.POINTER(wintypes.DOUBLE)
wintypes.PLPOLESTR = ctypes.POINTER(wintypes.LPOLESTR)
wintypes.BOOLE = type('BOOLE', (wintypes.BOOL,), {'value': property(lambda s: bool(wintypes.BOOL.value.__get__(s)), wintypes.BOOL.value.__set__), '__ctypes_from_outparam__': lambda s: s.value})
wintypes.PBOOLE = ctypes.POINTER(wintypes.BOOLE)
wintypes.SIZE_T = ctypes.c_size_t
wintypes.ULONG_PTR = ctypes.c_size_t
wintypes.PHWND = ctypes.POINTER(wintypes.HWND)
wintypes.GUID = ctypes.c_char * 16
wintypes.PGUID = ctypes.POINTER(wintypes.GUID)
wintypes.BYTES16 = wintypes.BYTE * 16
wintypes.PBYTES16 = ctypes.POINTER(wintypes.BYTES16)
vars(wintypes).setdefault('HCURSOR', wintypes.HANDLE)
vars(wintypes).setdefault('LRESULT', wintypes.LPARAM)
import struct
import threading
import math
from fractions import Fraction
import datetime
from hashlib import md5
import importlib.util
import os.path
import winreg

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
user32 = ctypes.WinDLL('user32', use_errno=True, use_last_error=True)
ole32 = ctypes.WinDLL('ole32', use_last_error=True)
oleauto32 = ctypes.WinDLL('oleaut32', use_last_error=True)
shl = ctypes.WinDLL('shlwapi', use_last_error=True)
sh32 = ctypes.WinDLL('shell32', use_last_error=True)
d2d1 = ctypes.WinDLL('d2d1', use_last_error=True)
d3d11 = ctypes.WinDLL('d3d11', use_last_error=True)
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

class WError(int):
  def __new__(cls, code):
    e = wintypes.DWORD(code)
    self = int.__new__(cls, e.value)
    self.code = int(self)
    pm = wintypes.LPWSTR()
    if kernel32.FormatMessageW(wintypes.DWORD(0x000013ff), 0, e, 0, ctypes.byref(pm), 0, 0):
      self.message = pm.value.rstrip(' .')
      kernel32.LocalFree(pm)
    else:
      self.message = ''
    return self
  def __str__(self):
    return '<%s: %s>' % (hex(self.code), self.message)
  def __repr__(self):
    return str(self)
def IGetLastError():
  return WError(ctypes.get_last_error())
def ISetLastError(e):
  ctypes.set_last_error(e := e & 0x80000000 and (e & 0x7fffffff) - 0x80000000)
  return e

class GUID(bytes):
  def __new__(cls, *g):
    return bytes.__new__(cls, (struct.pack('=LHH8B', *((struct.unpack('>LHH8B', bytes.fromhex(g.strip('{}').replace('-', ''))) if isinstance((g := g[0]), str) else struct.unpack('=LHH8B', ((g.contents if g else b'\x00' * 16) if isinstance(g, wintypes.PBYTES16) else g))) if len(g) == 1 else g))))
  def to_bytes(self):
    return bytes(self)
  def to_string(self):
    return '%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x' % struct.unpack('=LHH8B', self)
  @classmethod
  def from_name(cls, name):
    return cls(md5(name.encode(), usedforsecurity=False).digest())
  def __str__(self):
    return self.to_string()
  def __repr__(self):
    return str(self)

class _IUtil:
  _local = threading.local()
  _mul_cache = {}
  @staticmethod
  def _errcheck_no(r, f, a):
    return None if ISetLastError(r) else True
  @staticmethod
  def _errcheck_o(r, f, a):
    return None if ISetLastError(r) else a
  @staticmethod
  def _errcheck_r(r, f, a):
    return getattr(r, 'value', r) if (c := getattr(r, '__ctypes_from_outparam__', None)) is None else c()
  @staticmethod
  def CLSIDFromProgID(pid):
    return None if ISetLastError(ole32.CLSIDFromString(wintypes.LPCOLESTR(pid), ctypes.byref(clsid := wintypes.GUID()))) else GUID(clsid)
  @staticmethod
  def QueryInterface(interface, icls, factory=None):
    return None if interface is None else interface.QueryInterface(icls, factory)

class _IMeta(type):
  @classmethod
  def __prepare__(mcls, name, bases, **kwds):
    return {'_protos': {**p} if len(bases) > 0 and (p := getattr(bases[0], '_protos', None)) is not None else {}}
  def __init__(cls, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for n, pro in tuple((n, pro) for n, pro in cls._protos.items() if isinstance(pro, tuple)):
      if len(pro) == 3:
        p, i, o = pro
        cls._protos[n] = ctypes.WINFUNCTYPE(wintypes.ULONG, *i, *o)(p, n, (((1,),) * len(i)) + (((2,),) * len(o)))
        cls._protos[n].errcheck = _IUtil._errcheck_o if o else _IUtil._errcheck_no
      elif len(pro) == 4:
        p, i, o, r = pro
        cls._protos[n] = ctypes.WINFUNCTYPE(r, *i, *o, use_last_error=True)(p, n, (((1,),) * len(i)) + (((2,),) * len(o)))
        if not o:
          cls._protos[n].errcheck = _IUtil._errcheck_r
  def __mul__(bcls, size):
    return _IUtil._mul_cache.get((bcls, size)) or _IUtil._mul_cache.setdefault((bcls, size), type('%s_Array_%d' % (bcls.__name__, size), (PCOM * size, wintypes.LPVOID * size), {'_ibase': bcls}))

class _COMMeta(type):
  class _Offsetted(dict):
    def __set_name__(self, interface, name):
      self[0] = interface
    def __missing__(self, offset):
      self[offset] = cls = (interface := self[0]).__class__('%s_offset_%d' % (interface.__name__, offset), (interface,), {'_ovtbl': offset * interface.__class__._psize})
      return cls
  class _COMImplMeta(ctypes.Structure.__class__):
    _psize = ctypes.sizeof(wintypes.LPVOID)
    _refs = {}
    _clsids = {}
    class _COMThreadUnsafe:
      def __init__(self, obj=None):
        object.__setattr__(self, '_obj', obj)
      def __bool__(self):
        return bool(getattr(self._obj, 'refs', False))
      def __enter__(self):
        return self._obj
      def __exit__(self, et, ev, tb):
        pass
      def __getattr__(self, name):
        return getattr(self._obj, name) if self._obj else None
      def __setattr__(self, name, value):
        return setattr(self._obj, name, value) if hasattr(self._obj, name) else object.__setattr__(self, name, value)
      def __repr__(self):
        return '<%s.%s(%s) object at 0x%016X>' % (self.__class__.__module__, self.__class__.__qualname__, self._obj, id(self))
    class _COMThreadSafe(_COMThreadUnsafe):
      def __init__(self, obj=None):
        super().__init__(obj)
        object.__setattr__(self, '_lock', threading.RLock())
      def __enter__(self):
        self._lock.acquire()
        return self._obj
      def __exit__(self, et, ev, tb):
        self._lock.release()
    @classmethod
    def __prepare__(mcls, name, bases, interfaces=None):
      return {} if not interfaces else {'_iids': {iid: i for i, interface in reversed(tuple(enumerate(interfaces))) for iid in interface._iids}, '__new__': mcls._new}
    def __new__(mcls, name, bases, namespace, interfaces=None):
      if not interfaces or any(hasattr(interface, '_ovtbl') for interface in interfaces):
        raise ValueError('an invalid value has been provided for the \'interfaces\' argument of the declaration of %s' % name)
      if bases:
        raise ValueError('a base class has been provided in the declaration of %s' % name)
      fs = {}
      if any(fs.setdefault(n, t) != t for interface in interfaces for n, t in interface._vars.items()):
        raise AttributeError('a conflict between variables has been detected among the \'_vars\' declarations of the interfaces tied to %s' % name)
      if (v := namespace.get('_vars')):
        fs.update(v)
      namespace['_fields_'] = [('pvtbls', wintypes.LPVOID * len(interfaces)), ('refs', wintypes.ULONG), *fs.items()]
      if (clsid := namespace.get('CLSID')):
        namespace['CLSID'] = clsid = GUID.from_name(name) if clsid is True else GUID(clsid)
      cls = super().__new__(mcls, name, (ctypes.Structure,), namespace)
      if clsid:
        mcls._clsids[clsid] = cls
      return cls
    @staticmethod
    def _is_mta():
      a_t = wintypes.INT()
      a_q = wintypes.INT()
      return None if ISetLastError(ole32.CoGetApartmentType(ctypes.byref(a_t), ctypes.byref(a_q))) else a_t.value == 1 or (a_t.value == 2 and a_q.value in (2, 4))
    @staticmethod
    def _new(cls, iid=0, isize=None, **kwargs):
      if ((ind := iid) >= len(cls._pvtbls)) if isinstance(iid, int) else ((ind := cls._iids.get(GUID(iid))) is None):
        ISetLastError(0x80004002)
        return None
      cls.__class__._refs[pI := ctypes.addressof(self)] = (cls.__class__._COMThreadSafe if (mt if (mt := getattr(_IUtil._local, 'multithreaded', None)) is not None else cls.__class__._is_mta()) else cls.__class__._COMThreadUnsafe)(self := (ctypes.Structure.__new__(cls) if isize is None else cls.from_buffer(ctypes.create_string_buffer(isize))))
      self.pvtbls[:] = cls._pvtbls
      self.refs = 1
      self.__init__(**kwargs)
      ISetLastError(0)
      return pI + ind * cls.__class__._psize
    def __init__(cls, *args, interfaces=None):
      super().__init__(*args)
      if interfaces:
        cls._pvtbls = tuple(ctypes.addressof(interface._offsetted[i].vtbl) for i, interface in enumerate(interfaces))
        cls._aggregatable = all(issubclass(interface, (_COM_IUnknown if i == 0 else  _COM_IUnknown_aggregatable)) for i, interface in enumerate(interfaces)) and hasattr(cls, 'pUnkOuter')
  _psize = _COMImplMeta._psize
  _refs = _COMImplMeta._refs
  _none = _COMImplMeta._COMThreadUnsafe()
  _iid_iunknown = GUID('00000000-0000-0000-c000-000000000046')
  _iid_iclassfactory = GUID('00000001-0000-0000-c000-000000000046')
  _iid_ipsfactorybuffer = GUID(0xd5f569d0, 0x593b, 0x101a, 0xb5, 0x69, 0x08, 0x00, 0x2b, 0x2d, 0xbf, 0x7a)
  _iid_irpcproxybuffer = GUID(0xd5f56a34, 0x593b, 0x101a, 0xb5, 0x69, 0x08, 0x00, 0x2b, 0x2d, 0xbf, 0x7a)
  _iid_irpcstubbuffer = GUID(0xd5f56afc, 0x593b, 0x101a, 0xb5, 0x69, 0x08, 0x00, 0x2b, 0x2d, 0xbf, 0x7a)
  @classmethod
  def __prepare__(mcls, name, bases, interfaces=None):
    if interfaces:
      return mcls._COMImplMeta.__prepare__(name, bases, interfaces=interfaces)
    return {'_iids': {*bases[0]._iids}, '_vtbl': {**bases[0]._vtbl}, '_vars': {**bases[0]._vars}, '_offsetted': mcls._Offsetted()} if bases else {'_iids': set(), '_vtbl': {}, '_vars': {}, '_offsetted': mcls._Offsetted(), '__new__': mcls._new}
  def __new__(mcls, name, bases, namespace, interfaces=None):
    if interfaces:
      return mcls._COMImplMeta(name, bases, namespace, interfaces=interfaces)
    if bases and (len(bases) > 1 or hasattr(bases[0], '_ovtbl')):
      raise ValueError('an invalid or more than one base class has been provided in the declaration of %s' % name)
    if (v := namespace.get('_vars')) and any(n in {'_psize', '_refs', '_iids', '_siids', '_aggregatable', 'CLSID', '_pvtbls', '_fields_', '_destroy', 'pvtbls', 'refs', 'iid', 'isize', '_obj', '_lock'} for n in v):
      raise AttributeError('a reserved identifier has been used as a variable name in the \'_vars\' declarations of %s' % name)
    return super().__new__(mcls, name, bases, namespace)
  @staticmethod
  def _new(cls, iid, **kwargs):
    if hasattr(cls, '_ovtbl'):
      raise TypeError('%s does not have any constructor' % cls.__name__)
    if (GUID(iid) not in cls._iids):
      ISetLastError(0x80004002)
      return None
    if (impl := (vars(cls).get('_impl') or globals().get(n := cls.__name__ + '_impl'))) is None:
      cls._impl = impl = _COMMeta._COMImplMeta(n, (), _COMMeta._COMImplMeta.__prepare__(n, (), interfaces=(cls,)), interfaces=(cls,))
    return impl(iid, **kwargs)
  def __init__(cls, *args, interfaces=None):
    super().__init__(*args)
    cls.vtbl = v = (wintypes.LPVOID * len(cls._vtbl))()
    for i, (n, a) in enumerate(cls._vtbl.items()):
      setattr(cls, n, (f := ctypes.WINFUNCTYPE(*a)(getattr(cls, '_' + n))))
      v[i] = ctypes.cast(f, wintypes.LPVOID)
  def __getitem__(cls, pI):
    return cls.__class__._none if not pI else cls.__class__._refs.get(pI - getattr(cls, '_ovtbl', 0), cls.__class__._none)

class _COM_IUnknown(metaclass=_COMMeta):
  _iids.add(GUID('00000000-0000-0000-c000-000000000046'))
  _vtbl['QueryInterface'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PBYTES16, wintypes.PLPVOID)
  _vtbl['AddRef'] = (wintypes.ULONG, wintypes.LPVOID)
  _vtbl['Release'] = (wintypes.ULONG, wintypes.LPVOID)
  @classmethod
  def _QueryInterface(cls, pI, riid, ppObj):
    if not ppObj:
      return 0x80004003
    with cls[pI] as self:
      if not self or not riid:
        ppObj.contents.value = 0
        return 0x80004003
      if (ind := self.__class__._iids.get(GUID(riid))) is None:
        ppObj.contents.value = 0
        return 0x80004002
      ppObj.contents.value = pI = ctypes.addressof(self) + ind * cls.__class__._psize
      PCOM.AddRef(wintypes.LPVOID(pI))
      return 0
  @classmethod
  def _AddRef(cls, pI):
    with cls[pI] as self:
      if not self:
        return 0
      self.refs += 1
      return self.refs
  @classmethod
  def _Release(cls, pI):
    with cls[pI] as self:
      if not self:
        return 0
      self.refs = max(self.refs - 1, 0)
      if not self.refs:
        cls._refs.pop(ctypes.addressof(self), None)
        if (d := getattr(self, '_destroy', None)):
          d()
      return self.refs

class _COM_IUnknown_impl(metaclass=_COMMeta, interfaces=(_COM_IUnknown,)):
  CLSID = True

class IUnknown(metaclass=_IMeta):
  IID = GUID('00000000-0000-0000-c000-000000000046')
  _protos['QueryInterface'] = 0, (wintypes.LPCSTR,), (wintypes.PLPVOID,)
  _protos['AddRef'] = 1, (), (), wintypes.ULONG
  _protos['Release'] = 2, (), (), wintypes.ULONG
  def __new__(cls, clsid_component=False, factory=None):
    lw = None
    if not clsid_component:
      if clsid_component is not False:
        return None
      if (clsid_component := getattr(cls, 'CLSID', globals().get('_COM_' + cls.__name__))) is None:
        raise TypeError('%s does not have an implicit constructor' % cls.__name__)
    if isinstance(clsid_component, (_COMMeta, _COMMeta._COMImplMeta)):
      if not (pI := wintypes.LPVOID(clsid_component(cls.IID))):
        return None
      lw = True
    elif isinstance(clsid_component, int):
      pI = wintypes.LPVOID(clsid_component)
    elif isinstance(clsid_component, wintypes.LPVOID):
      pI = clsid_component
    else:
      if isinstance(clsid_component, str):
        try:
          clsid_component = GUID(clsid_component)
        except:
          if (clsid_component := _IUtil.CLSIDFromProgID(clsid_component)) is None:
            return None
      pI = wintypes.LPVOID()
      if ISetLastError(ole32.CoCreateInstance(wintypes.LPCSTR(clsid_component), None, wintypes.DWORD(1), wintypes.LPCSTR(cls.IID), ctypes.byref(pI))) or not pI:
        return None
    self = object.__new__(cls)
    self.pI = pI
    self.refs = 1
    self.factory = factory
    if lw:
      self._lightweight = True
    return self
  def AddRef(self, own_ref=True):
    if self.pI is None:
      return None
    if own_ref:
      self.refs += 1
    return self.__class__._protos['AddRef'](self.pI), self.refs
  def Release(self, own_ref=True):
    if self.pI is None:
      return None
    if (r := self.__class__._protos['Release'](self.pI)) == 0:
      self.refs = 0
    elif own_ref:
      self.refs -= 1
    if self.refs == 0:
      self.pI = None
    return r, self.refs
  def QueryInterface(self, icls, factory=None):
    if self.pI is None:
      return None
    if (i := icls(self.__class__._protos['QueryInterface'](self.pI, icls.IID), (None if factory is False else (factory if factory is not None else self.factory)))) is None:
      return None
    if getattr(self, '_lightweight', False):
      i._lightweight = True
    return i
  def __bool__(self):
    return bool(self.pI) and self.refs > 0
  @property
  def _as_parameter_(self):
    return self.pI
  def __del__(self):
    if getattr(self, '_lightweight', False) or ((__IUtil := globals().get('_IUtil')) and hasattr(__IUtil._local, 'initialized')):
      while self:
        self.Release()
  def __enter__(self):
    return self
  def __exit__(self, et, ev, tb):
    self.__del__()
  def __repr__(self):
    return '<%s.%s(%s) object at 0x%016X>' % (self.__class__.__module__, self.__class__.__qualname__, ('0x%016X' % self.pI.value if self else 'None'), id(self))

class _PCOMUtil:
  _mul_cache = {}
  @staticmethod
  def _agitem(arr, key):
    acls = arr.__class__
    e = acls.__bases__[-1].__getitem__(arr, key)
    return _PCOMUtil._interface(acls._base(e), getattr(arr, '_ibase', None)) if isinstance(key, int) else [_PCOMUtil._interface(acls._base(c), getattr(arr, '_ibase', None)) for c in e]
  @staticmethod
  def _asitem(arr, key, value):
    acls = arr.__class__
    return acls.__bases__[-1].__setitem__(arr, key, acls._base(value) if isinstance(key, int) else [acls._base(v) for v in value])
  @staticmethod
  def _interface(pcom, icls=None):
    if not hasattr(pcom, 'pcom'):
      pcom.pcom = ctypes.cast(pcom, wintypes.LPVOID)
    if (i := (icls or pcom.icls)(pcom.pcom)) is None:
      return None
    i.AddRef(False)
    return i

class _PCOMMeta(wintypes.LPVOID.__class__):
  def __mul__(bcls, size):
    return _PCOMUtil._mul_cache.get((bcls, size)) or _PCOMUtil._mul_cache.setdefault((bcls, size), type('%s_Array_%d' % (bcls.__name__, size), (wintypes.LPVOID * size,), {'__getitem__': _PCOMUtil._agitem, '__setitem__': _PCOMUtil._asitem, '_base': bcls}))

class PCOM(wintypes.LPVOID, metaclass=_PCOMMeta):
  icls = IUnknown
  def __init__(self, interface=None):
    if isinstance(interface, IUnknown):
      self._interface = interface
      self.value = getattr(interface.pI, 'value', interface.pI)
      self.icls = interface.__class__ if self.__class__.icls is IUnknown else self.__class__.icls
    elif isinstance(interface, PCOM):
      self._interface = getattr(interface, '_interface', None)
      self.value = interface.value
      self.icls = interface.icls if self.__class__.icls is IUnknown else self.__class__.icls
    else:
      self._interface = None
      self.value = getattr(interface, 'value', interface)
      self.icls = self.__class__.icls
  @property
  def value(self):
    return getattr(getattr(self, 'pcom', ctypes.cast(self, wintypes.LPVOID)), 'value', None)
  @value.setter
  def value(self, val):
    ctypes.c_void_p.from_address(ctypes.addressof(self)).value = val
    self.pcom = ctypes.cast(self, wintypes.LPVOID)
  @property
  def content(self):
    return _PCOMUtil._interface(self)
  @property
  def raw(self):
    i = object.__new__(self.icls)
    i.pI = ctypes.cast(self, wintypes.LPVOID) or None
    i.refs = 0
    i.factory = None
    i.AddRef()
    return i
  def AddRef(self):
    return IUnknown._protos['AddRef'](self) if self else 0
  def Release(self):
    return IUnknown._protos['Release'](self) if self else 0
  def QueryInterface(self, riid):
    return IUnknown._protos['QueryInterface'](self, (ctypes.cast(riid, wintypes.LPCSTR) if isinstance(riid, (wintypes.PBYTES16, wintypes.PGUID, PUUID, wintypes.LPCSTR, wintypes.LPVOID)) else GUID(riid))) if self else None
  def __repr__(self):
    return '<%s.%s(%s) object at 0x%016X>' % (self.__class__.__module__, self.__class__.__qualname__, ('0x%016X' % self.value if self else 'None'), id(self))

class _COM_IUnknown_aggregatable(_COM_IUnknown):
  _vars['pUnkOuter'] = PCOM
  @classmethod
  def _QueryInterface(cls, pI, riid, ppObj):
    with cls[pI] as self:
      if not (self and self.pUnkOuter and ppObj and riid):
        return super()._QueryInterface(pI, riid, ppObj)
      ppObj.contents.value = self.pUnkOuter.QueryInterface(riid)
      return IGetLastError()
  @classmethod
  def _AddRef(cls, pI):
    with cls[pI] as self:
      return self.pUnkOuter.AddRef() if self and self.pUnkOuter else super()._AddRef(pI)
  @classmethod
  def _Release(cls, pI):
    with cls[pI] as self:
      return self.pUnkOuter.Release() if self and self.pUnkOuter else super()._Release(pI)

class _COM_IUnknown_aggregator(_COM_IUnknown):
  _aiids = {}
  _vars['pUnkInners'] = wintypes.LPVOID * 0
  @classmethod
  def _QueryInterface(cls, pI, riid, ppObj):
    with cls[pI] as self:
      if (r := super()._QueryInterface(pI, riid, ppObj)) != 0x80004002 or GUID(riid) == _COMMeta._iid_iunknown:
        return r
      if (ind := cls._aiids.get(GUID(riid))) is None or ind >= len(self.pUnkInners) or not (pUnkInner := self.pUnkInners[ind]):
        ppObj.contents.value = 0
        return 0x80004002
      ppObj.contents.value = PCOM.QueryInterface(wintypes.LPVOID(pUnkInner), riid)
      return IGetLastError()
  @classmethod
  def _Release(cls, pI):
    with cls[pI] as self:
      if not self:
        return 0
      if super()._Release(pI) == 0:
        for pUnkInner in self.pUnkInners:
          PCOM.Release(wintypes.LPVOID(pUnkInner))
      return self.refs
  @staticmethod
  def set_inner(outer, index, impl, **kwargs):
    with _COM_IUnknown[pI := ctypes.addressof(outer) if hasattr(outer, 'pvtbls') else getattr(outer, 'value', outer)] as outer:
      if not outer or index < 0 or index >= len(outer.pUnkInners):
        return False
      PCOM.Release(wintypes.LPVOID(outer.pUnkInners[index]))
      outer.pUnkInners[index] = None
      if kwargs:
        if not isinstance(impl, _COMMeta._COMImplMeta) or not impl._aggregatable:
          return False
        outer.pUnkInners[index] = pUnkInner = impl(_COMMeta._iid_iunknown, **kwargs)
        with _COM_IUnknown[pUnkInner] as inner:
          if inner:
            inner.pUnkOuter = pI
      else:
        if (f := IClassFactory(impl)) is None:
          return False
        outer.pUnkInners[index] = pUnkInner = IClassFactory._protos['CreateInstance'](f.pI, pI, _COMMeta._iid_iunknown)
        f.Release()
      return bool(pUnkInner)

class _COM_IClassFactory(_COM_IUnknown):
  _iids.add(GUID('00000001-0000-0000-c000-000000000046'))
  _vtbl['CreateInstance'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.LPVOID, wintypes.PBYTES16, wintypes.PLPVOID)
  _vtbl['LockServer'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.BOOL)
  _vars['constr'] = ctypes.WINFUNCTYPE(wintypes.LPVOID, wintypes.PBYTES16)
  @classmethod
  def _CreateInstance(cls, pI, pUnkOuter, riid, ppObj):
    if not ppObj:
      return 0x80004003
    with cls[pI] as self:
      if not self or not riid:
        ppObj.contents.value = 0
        return 0x80004003
      if pUnkOuter and GUID(riid) != _COMMeta._iid_iunknown:
        ppObj.contents.value = 0
        return 0x80004002
      ppObj.contents.value = pI = self.constr(riid) if self.constr else None
      if not pI:
        return 0x80004002
      if pUnkOuter:
        with _COM_IUnknown[pI] as inner:
          if not inner or not inner.__class__._aggregatable:
            PCOM(pI).Release()
            ppObj.contents.value = 0
            return 0x80040110
          inner.pUnkOuter = pUnkOuter
      return 0
  @classmethod
  def _LockServer(cls, pI, fLock):
    return 0x80004001 if cls[pI] else 0x80004003

class _COM_IClassFactory_impl(metaclass=_COMMeta, interfaces=(_COM_IClassFactory,)):
  def __new__(cls, iid=0, *, _bnew=__new__, impl=0):
    return _bnew(cls, iid, constr=impl)
  def __init__(self, *, constr):
    super(self.__class__, self).__init__(constr=_COM_IClassFactory._vars['constr'](constr))

class IClassFactory(IUnknown):
  IID = GUID('00000001-0000-0000-c000-000000000046')
  _protos['CreateInstance'] = 3, (wintypes.LPVOID, wintypes.LPCSTR), (wintypes.PLPVOID,)
  def __new__(cls, clsid_component=False, factory=None):
    lw = None
    if not clsid_component:
      if clsid_component is False:
        clsid_component = 0
      else:
        return None
    elif isinstance(clsid_component, _IMeta) and (clsid_component := getattr((icls := clsid_component), 'CLSID', globals().get('_COM_' + icls.__name__))) is None:
        raise TypeError('%s does not have an implicit constructor' % icls.__name__)
    if clsid_component == 0 or isinstance(clsid_component, (_COMMeta, _COMMeta._COMImplMeta)):
      if not (pI := wintypes.LPVOID(_COM_IClassFactory(cls.IID, impl=clsid_component))):
        return None
      lw = True
    elif isinstance(clsid_component, int):
      pI = wintypes.LPVOID(clsid_component)
    elif isinstance(clsid_component, wintypes.LPVOID):
      pI = clsid_component
    else:
      if isinstance(clsid_component, str):
        try:
          clsid_component = GUID(clsid_component)
        except:
          if (clsid_component := _IUtil.CLSIDFromProgID(clsid_component)) is None:
            return None
      pI = wintypes.LPVOID()
      if ISetLastError(ole32.CoGetClassObject(wintypes.LPCSTR(clsid_component), wintypes.DWORD(1), None, wintypes.LPCSTR(cls.IID), ctypes.byref(pI))) or not pI:
        return None
    self = object.__new__(cls)
    self.pI = pI
    self.refs = 1
    self.factory = factory
    if lw:
      self._lightweight = True
    return self
  def CreateInstance(self, icls):
    if self.pI is None or (i := icls(self.__class__._protos['CreateInstance'](self.pI, None, icls.IID), self)) is None:
      return None
    if getattr(self, '_lightweight', False):
      i._lightweight = True
    return i

class _COM_IPSFactoryBuffer(_COM_IUnknown):
  _iids.add(GUID(0xd5f569d0, 0x593b, 0x101a, 0xb5, 0x69, 0x08, 0x00, 0x2b, 0x2d, 0xbf, 0x7a))
  _vtbl['CreateProxy'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.LPVOID, wintypes.PBYTES16, wintypes.PLPVOID, wintypes.PLPVOID)
  _vtbl['CreateStub'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PBYTES16, wintypes.LPVOID, wintypes.PLPVOID)
  _vars['constr_p'] = ctypes.WINFUNCTYPE(wintypes.LPVOID, wintypes.PBYTES16)
  _vars['constr_s'] = ctypes.WINFUNCTYPE(wintypes.LPVOID, wintypes.PBYTES16)
  @classmethod
  def _CreateProxy(cls, pI, pUnkOuter, riid, ppProxy, ppObj):
    with cls[pI] as self:
      if not (self and riid and ppProxy and ppObj and pUnkOuter):
        if ppProxy:
          ppProxy.contents.value = 0
        if ppObj:
          ppObj.contents.value = 0
        return 0x80004003
      ppProxy.contents.value = pP = self.constr_p(wintypes.BYTES16(*_COMMeta._iid_irpcproxybuffer)) if self.constr_p else None
      if not pP:
        ppObj.contents.value = None
        return 0x80004002
      with _COM_IRpcProxyBuffer[pP] as proxy:
        if not proxy or not proxy.__class__._aggregatable:
          PCOM.Release(wintypes.LPVOID(pP))
          ppProxy.contents.value = ppObj.contents.value = None
          return 0x80040110
        proxy.pUnkOuter = pUnkOuter
      ppObj.contents.value = pI = PCOM.QueryInterface(wintypes.LPVOID(pP), riid)
      if not pI or pI == pP:
        PCOM.Release(wintypes.LPVOID(pP))
        PCOM.Release(wintypes.LPVOID(pI))
        ppProxy.contents.value = ppObj.contents.value = None
        return 0x80004002
      return 0
  @classmethod
  def _CreateStub(cls, pI, riid, pUnkServer, ppStub):
    with cls[pI] as self:
      if not (self and riid and ppStub):
        if ppStub:
          ppStub.contents.value = 0
        return 0x80004003
      ppStub.contents.value = pS = self.constr_s(riid) if self.constr_s else None
      if not pS:
        return 0x80004002
      if pUnkServer and ISetLastError(ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.LPVOID)(3, 'Connect')(wintypes.LPVOID(pS), pUnkServer)):
        e = IGetLastError()
        PCOM.Release(wintypes.LPVOID(pS))
        ppStub.contents.value = 0
        return e
      return 0

class _COM_IPSFactoryBuffer_impl(metaclass=_COMMeta, interfaces=(_COM_IPSFactoryBuffer,)):
  def __new__(cls, iid=0, *, _bnew=__new__, ps_impl=None):
    return _bnew(cls, iid, constr_p=ps_impl.proxy_impl, constr_s=ps_impl.stub_impl)
  def __init__(self, *, constr_p, constr_s):
    super(self.__class__, self).__init__(constr_p=_COM_IPSFactoryBuffer._vars['constr_p'](constr_p), constr_s=_COM_IPSFactoryBuffer._vars['constr_s'](constr_s))

class RPCOLEMESSAGE(ctypes.Structure):
  _fields_ = [('reserved1', wintypes.LPVOID), ('dataRepresentation', wintypes.ULONG), ('Buffer', wintypes.LPVOID), ('cbBuffer', wintypes.ULONG), ('iMethod', wintypes.ULONG), ('reserved2', wintypes.LPVOID * 5), ('rpcFlags', wintypes.ULONG)]
PRPCOLEMESSAGE = ctypes.POINTER(RPCOLEMESSAGE)

class PCOMRPCCHANNEL(PCOM):
  def IsConnected(self):
    return None if not self or ISetLastError(c := ctypes.WINFUNCTYPE(wintypes.ULONG)(7, 'IsConnected')(self)) else c == 0
  def GetDestCtx(self):
    return None if not self or ISetLastError(ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PDWORD, wintypes.PLPVOID)(6, 'GetDestCtx')(self, ctypes.byref(dwDestContext := wintypes.DWORD()), None)) else dwDestContext.value
  def GetBuffer(self, iid, size, method, message=None):
    if message is None:
      message = RPCOLEMESSAGE()
    message.cbBuffer = size
    message.iMethod = method
    if not self or ISetLastError(ctypes.WINFUNCTYPE(wintypes.ULONG, PRPCOLEMESSAGE, PUUID)(3, 'GetBuffer')(self, message, iid)):
      message.cbBuffer = 0
      return None
    ctypes.memset(message.Buffer, 0, message.cbBuffer)
    return message
  def FreeBuffer(self, message):
    return None if not self or ISetLastError(ctypes.WINFUNCTYPE(wintypes.ULONG, PRPCOLEMESSAGE)(5, 'FreeBuffer')(self, message)) else True
  def SendReceive(self, message):
    return None if not self or ISetLastError(ctypes.WINFUNCTYPE(wintypes.ULONG, PRPCOLEMESSAGE, wintypes.PULONG)(4, 'SendReceive')(self, message, wintypes.ULONG())) else True

class PCOM_IID(wintypes.LPVOID):
  def __init__(self, pI=None, iid=_COMMeta._iid_iunknown):
    super().__init__(getattr(pI, 'value', pI))
    self.riid = PUUID.from_param(iid)
  @classmethod
  def from_address(cls, address, iid=_COMMeta._iid_iunknown):
    self = cls.__class__.from_address(cls, address)
    self.riid = PUUID.from_param(iid)
    return self
  @classmethod
  def from_buffer(cls, buffer, iid=_COMMeta._iid_iunknown, offset=0):
    self = cls.__class__.from_buffer(cls, buffer, offset)
    self.riid = PUUID.from_param(iid)
    return self
  @classmethod
  def tuple(cls, number, iid=_COMMeta._iid_iunknown, address=None):
    s = number * _COMMeta._psize
    if address is None:
      b = ctypes.create_string_buffer(s)
      return tuple(PCOM_IID.from_buffer(b, iid, o) for o in range(0, s, _COMMeta._psize))
    else:
      return tuple(PCOM_IID.from_address(a, iid) for a in range(address, address + s, _COMMeta._psize))

class _COM_IRpcProxyBuffer(_COM_IUnknown):
  _iids.add(GUID(0xd5f56a34, 0x593b, 0x101a, 0xb5, 0x69, 0x08, 0x00, 0x2b, 0x2d, 0xbf, 0x7a))
  _vtbl['Connect'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.LPVOID)
  _vtbl['Disconnect'] = (None, wintypes.LPVOID)
  _vars['pRpcChannelBuffer'] = PCOMRPCCHANNEL
  @classmethod
  def _Connect(cls, pI, pRpcChannelBuffer):
    with cls[pI] as self:
      if not self or not pRpcChannelBuffer:
        return 0x80004003
      if self.pRpcChannelBuffer:
        return 0x8000ffff
      self.pRpcChannelBuffer = pRpcChannelBuffer
      self.pRpcChannelBuffer.AddRef()
      return 0
  @classmethod
  def _Disconnect(cls, pI):
    with cls[pI] as self:
      if not self:
        return
      self.pRpcChannelBuffer.Release()
      self.pRpcChannelBuffer = None

class _COM_IRpcProxy(_COM_IUnknown_aggregatable):
  _vars['pRpcChannelBuffer'] = PCOMRPCCHANNEL
  @classmethod
  def _call(cls, self, method, iargs, oargs, restype=wintypes.ULONG, errcheck=0x80000000.__and__):
    if not (channel := self.pRpcChannelBuffer):
      return 0x80004003
    if (message := channel.GetBuffer(self.__class__._siids[getattr(cls, '_ovtbl', 0) // cls.__class__._psize], sum(map(ctypes.sizeof, iargs)), method)) is None:
      return IGetLastError() or 0x80004005
    r = 0
    marsh = []
    o = 0
    for arg in iargs:
      s = ctypes.sizeof(arg)
      if isinstance(arg, PCOM_IID) and arg:
        pI = wintypes.LPVOID.from_address(message.Buffer + o)
        if COMSharing.CoMarshalInterThreadInterfaceIntoStream(arg.riid, arg, pI) is None:
          r = 0x8001000b
          break
        else:
          marsh.append(pI)
      else:
        ctypes.memmove(message.Buffer + o, ctypes.addressof(arg), s)
      o += s
    if r or not channel.SendReceive(message):
      r = r or IGetLastError() or 0x8001000a
      if message.Buffer:
        for pI in marsh:
          COMSharing.CoReleaseMarshalData(pI)
          PCOM.Release(pI)
    elif message.cbBuffer < (o := (0 if restype is None else ctypes.sizeof(restype))) + sum(map(ctypes.sizeof, oargs)):
      r = 0x80010009
    else:
      r = None if restype is None else getattr((r := restype.from_address(message.Buffer)), 'value', r)
      if not (errcheck and errcheck(r)):
        marsh = []
        e = False
        for arg in oargs:
          s = ctypes.sizeof(arg)
          if isinstance(arg, PCOM_IID) and (pI := wintypes.LPVOID.from_address(message.Buffer + o)):
            if COMSharing.CoGetInterfaceIntoAndReleaseStream(pI, arg.riid, arg) is None:
              e = True
            else:
              marsh.append(arg)
          else:
            ctypes.memmove(ctypes.addressof(arg), message.Buffer + o, s)
          o += s
        if e:
          r = 0x8001000c
          for arg in marsh:
            PCOM.Release(wintypes.LPVOID(arg))
    channel.FreeBuffer(message)
    return r

class _COM_IRpcStubBuffer(_COM_IUnknown):
  _iids.add(GUID(0xd5f56afc, 0x593b, 0x101a, 0xb5, 0x69, 0x08, 0x00, 0x2b, 0x2d, 0xbf, 0x7a))
  _vtbl['Connect'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.LPVOID)
  _vtbl['Disconnect'] = (None, wintypes.LPVOID)
  _vtbl['Invoke'] = (wintypes.ULONG, wintypes.LPVOID, PRPCOLEMESSAGE, wintypes.LPVOID)
  _vtbl['IsIIDSupported'] = (wintypes.LPVOID, wintypes.LPVOID, wintypes.PBYTES16)
  _vtbl['CountRefs'] = (wintypes.ULONG, wintypes.LPVOID)
  _vtbl['DebugServerQueryInterface'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PLPVOID)
  _vtbl['DebugServerRelease'] = (None, wintypes.LPVOID, wintypes.LPVOID)
  _vars['pUnkServer'] = PCOM
  _vars['pIntServers'] = wintypes.LPVOID * 0
  @classmethod
  def _Connect(cls, pI, pUnkServer):
    with cls[pI] as self:
      if not self or not pUnkServer:
        return 0x80004003
      ind = getattr(cls, '_ovtbl', 0) // cls.__class__._psize
      if self.pIntServers[ind] or (self.pUnkServer and self.pUnkServer != pUnkServer):
        return 0x8000ffff
      self.pIntServers[ind] = pI = PCOM.QueryInterface(wintypes.LPVOID(pUnkServer), self.__class__._siids[1][ind])
      if not pI:
        return 0x80004002
      self.pUnkServer = pUnkServer
      return 0
  @classmethod
  def _Disconnect(cls, pI):
    with cls[pI] as self:
      if not self:
        return
      ind = getattr(cls, '_ovtbl', 0) // cls.__class__._psize
      PCOM.Release(wintypes.LPVOID(self.pIntServers[ind]))
      self.pIntServers[ind] = None
      if not any(self.pIntServers):
        self.pUnkServer = None
  @classmethod
  def _Invoke(cls, pI, pMsg, pRpcChannelBuffer):
    if not pMsg or not pRpcChannelBuffer:
      return 0x80004003
    message = pMsg.contents
    channel = PCOMRPCCHANNEL(pRpcChannelBuffer)
    with cls[pI] as self:
      if not self:
        return 0x80004003
      ind = getattr(cls, '_ovtbl', 0) // cls.__class__._psize
      if (pI := self.pIntServers[ind]) is None:
        return 0x8000ffff
      return ISetLastError(cls._invoke(self, wintypes.LPVOID(pI), channel, message))
  @classmethod
  def _gen_iargs(cls, channel, message, iargtypes):
    if message.cbBuffer < sum(map(ctypes.sizeof, iargtypes)):
      return 0x80010009
    o = 0
    iargs = []
    marsh = []
    e = False
    for argtype in iargtypes:
      if isinstance(argtype, PCOM_IID) and (pI := wintypes.LPVOID.from_address(message.Buffer + o)):
        if e:
          COMSharing.CoReleaseMarshalData(pI)
          PCOM.Release(pI)
        elif COMSharing.CoGetInterfaceIntoAndReleaseStream(pI, argtype.riid, argtype) is None:
          e = True
        else:
          marsh.append(argtype)
          iargs.append(argtype)
      elif not e:
        iargs.append(argtype.from_address(message.Buffer + o))
      o += ctypes.sizeof(argtype)
    if e:
      for arg in marsh:
        PCOM.Release(wintypes.LPVOID(arg))
      return 0x8001000e
    return iargs
  @classmethod
  def _gen_oargs(cls, self, channel, message, oargtypes, restype=wintypes.ULONG):
    if channel.GetBuffer(self.__class__._siids[1][getattr(cls, '_ovtbl', 0) // cls.__class__._psize], (o := (0 if restype is None else ctypes.sizeof(restype))) + sum(map(ctypes.sizeof, oargtypes)), message.iMethod, message) is None:
      return IGetLastError() or 0x80004005
    oargs = []
    for argtype in oargtypes:
      oargs.append(argtype if isinstance(argtype, PCOM_IID) else argtype.from_address(message.Buffer + o))
      o += ctypes.sizeof(argtype)
    return oargs
  @classmethod
  def _fin_message(cls, message, oargs, res, restype=wintypes.ULONG, errcheck=0x80000000.__and__):
    if restype is None:
      o = 0
    else:
      ctypes.memmove(message.Buffer, ctypes.addressof(res if isinstance(res, restype) else restype(res)), (o := ctypes.sizeof(restype)))
    if errcheck and errcheck(res):
      return 0
    marsh = []
    for arg in oargs:
      if isinstance(arg, PCOM_IID):
        pI = wintypes.LPVOID.from_address(message.Buffer + o)
        if arg:
          if COMSharing.CoMarshalInterThreadInterfaceIntoStream(arg.riid, arg, pI) is None:
            break
          else:
            marsh.append(pI)
        else:
          pI.value = None
      o += ctypes.sizeof(arg)
    else:
      return 0
    for pI in marsh:
      COMSharing.CoReleaseMarshalData(pI)
      PCOM.Release(pI)
    for arg in oargs:
      if isinstance(arg, PCOM_IID):
        PCOM.Release(arg)
    return 0x8001000d
  @classmethod
  def _gen_args(cls, self, channel, message, iargtypes, oargtypes):
    if isinstance((iargs := cls._gen_iargs(channel, message, iargtypes)), int):
      return None, iargs
    if isinstance((oargs := cls._gen_oargs(self, channel, message, oargtypes)), int):
      return None, oargs
    return (iargs, oargs)
  @classmethod
  def _IsIIDSupported(cls, pI, riid):
    with cls[pI] as self:
      if not self or not riid:
        ISetLastError(0x80004003)
        return None
      if (ind := self.__class__._siids[0].get(GUID(riid))) is None:
        ISetLastError(0x80004002)
        return None
      if self.pUnkServer and not self.pIntServers[ind]:
        self.pIntServers[ind] = pI = self.pUnkServer.QueryInterface(riid)
        if not pI:
          ISetLastError(0x80004002)
          return None
      return ctypes.addressof(self) + ind * cls.__class__._psize
  @classmethod
  def _CountRefs(cls, pI, riid):
    with cls[pI] as self:
      if not self:
        return 0
      return sum(1 if pI else 0 for pI in self.pIntServers)
  @classmethod
  def _DebugServerQueryInterface(cls, pI, ppObj):
    if not ppObj:
      return 0x80004003
    with cls[pI] as self:
      if not self:
        ppObj.contents.value = 0
        return 0x80004003
      ind = getattr(cls, '_ovtbl', 0) // cls.__class__._psize
      if not (pI := self.pIntServers[ind]):
        ppObj.contents.value = 0
        return 0x8000ffff
      ppObj.contents.value = pI
  @classmethod
  def _DebugServerRelease(cls, pI, ppObj):
    pass

class _PSImplMeta(type):
  @staticmethod
  def _new(cls, *args, **kwargs):
    ISetLastError(0x80004021)
    return None
  def __new__(mcls, name, bases, namespace, ps_interfaces):
    if not ps_interfaces:
      raise ValueError('an invalid value has been provided for the \'ps_interfaces\' argument of the declaration of %s' % name)
    p_interfaces, s_interfaces = zip(*ps_interfaces)
    if not all(issubclass(p_interface, _COM_IUnknown_aggregatable) for p_interface in p_interfaces) or not all(issubclass(s_interface, _COM_IRpcStubBuffer) for s_interface in s_interfaces):
      raise ValueError('an invalid value has been provided for the \'ps_interfaces\' argument of the declaration of %s' % name)
    _piids = {iid: i for i, p_interface in reversed(tuple(enumerate(p_interfaces))) for iid in p_interface._iids if iid != _COMMeta._iid_iunknown}
    class _COM_IRpcProxy_impl(metaclass=_COMMeta, interfaces=(_COM_IRpcProxyBuffer, *(p_interfaces[i] for i in _piids.values()))):
      _iids = {_COMMeta._iid_iunknown: 0, _COMMeta._iid_irpcproxybuffer: 0, **{iid: i + 1 for i, iid in enumerate(_piids)}}
      _siids = {i + 1: iid for i, iid in enumerate(_piids)}
    class _COM_IRpcStub_impl(metaclass=_COMMeta, interfaces=tuple(s_interfaces[i] for i in _piids.values())):
      _siids = {iid: i for i, iid in enumerate(_piids)}, dict(enumerate(_piids))
      _vars = {'pIntServers': wintypes.LPVOID * len(_siids[0])}
      def __new__(cls, iid=0, *, _bnew=__new__):
        return _bnew(cls, (iid if isinstance(iid, int) else cls._siids[0].get(GUID(iid), len(cls._siids[0]))))
    if (clsid := namespace.get('CLSID')):
      namespace['CLSID'] = clsid = GUID.from_name(name) if clsid is True else GUID(clsid)
    namespace['__new__'] = mcls._new
    cls = super().__new__(mcls, name, (), namespace)
    if clsid:
      _COMMeta._COMImplMeta._clsids[clsid] = cls
    cls.proxy_impl = _COM_IRpcProxy_impl
    cls.proxy_impl.__qualname__ = '%s.%s' % (cls.__qualname__, '_COM_IRpcProxy_impl')
    cls.stub_impl = _COM_IRpcStub_impl
    cls.stub_impl.__qualname__ = '%s.%s' % (cls.__qualname__, '_COM_IRpcStub_impl')
    return cls

class IEnumString(IUnknown):
  IID = GUID('00000101-0000-0000-c000-000000000046')
  _protos['Next'] = 3, (wintypes.ULONG, wintypes.PLPOLESTR, wintypes.PULONG), ()
  _protos['Skip'] = 4, (wintypes.ULONG,), ()
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    a = (wintypes.LPOLESTR * number)()
    if self.__class__._protos['Next'](self.pI, number, a, r) is None:
      return None
    if (r := r.value) == 0:
      return ()
    ss = tuple(a[s] for s in range(r))
    a = (wintypes.LPVOID * r).from_buffer(a)
    for p in a:
      ole32.CoTaskMemFree(wintypes.LPVOID(p))
    return ss
  def Skip(self, number):
    try:
      return self.__class__._protos['Skip'](self.pI, number)
    except:
      ISetLastError(0x80070057)
      return None
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    if not (n := self.Next(1)):
      raise StopIteration
    return n[0]

class _COM_IEnumUnknown(_COM_IUnknown):
  _iids.add(GUID('00000100-0000-0000-c000-000000000046'))
  _vtbl['Next'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.ULONG, wintypes.LPVOID, wintypes.PULONG)
  _vtbl['Skip'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.ULONG)
  _vtbl['Reset'] = (wintypes.ULONG, wintypes.LPVOID)
  _vtbl['Clone'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PLPVOID)
  _vars['count'] = wintypes.ULONG
  _vars['index'] = wintypes.ULONG
  _vars['container'] = PCOM
  _vars['_items'] = wintypes.LPVOID * 0
  @classmethod
  def _Next(cls, pI, celt, rgelt, pceltFetched):
    with cls[pI] as self:
      if not self or not rgelt or (celt > 1 and not pceltFetched):
        if pceltFetched:
          pceltFetched.contents.value = 0
        if rgelt:
          (wintypes.LPVOID * celt).from_address(rgelt)[:] = (None,) * celt
        return 0x80004003
      fcelt = min(celt, self.count - self.index)
      if pceltFetched:
        pceltFetched.contents.value = fcelt
      (wintypes.LPVOID * celt).from_address(rgelt)[:] = (*(PCOM.AddRef(wintypes.LPVOID(pI)) and pI for pI in self.items[self.index : self.index + fcelt]), *((None,) * (celt - fcelt)))
      self.index += fcelt
      return 0 if fcelt == celt else 1
  @classmethod
  def _Skip(cls, pI, celt):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      self.index = min((nindex := self.index + celt), self.count)
      return 0 if self.index == nindex else 1
  @classmethod
  def _Reset(cls, pI):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      self.index = 0
      return 0
  @classmethod
  def _Clone(cls, pI, ppenum):
    with cls[pI] as self:
      if not self or not ppenum:
        if ppenum:
          ppenum.contents.value = None
        return 0x80004003
      ppenum.contents.value = self.__class__(GUID('00000100-0000-0000-c000-000000000046'), items=self.items, index=self.index, container=self.container)
      return 0

class _COM_IEnumUnknown_impl(metaclass=_COMMeta, interfaces=(_COM_IEnumUnknown,)):
  def __new__(cls, iid=0, *, _bnew=__new__, items=(), index=0, container=None):
    return _bnew(cls, iid, cls._items.offset + len(items) * _COMMeta._psize, items=items, index=index, container=container)
  def __init__(self, *, items, index, container):
    super(self.__class__, self).__init__(count=len(items), items=items, index=index, container=PCOM(container).value)
    self.container.AddRef()
  def _destroy(self):
    self.container.Release()
  @property
  def items(self):
    return (wintypes.LPVOID * self.count).from_address(ctypes.addressof(self._items))
  @items.setter
  def items(self, value):
    (PCOM * self.count).from_address(ctypes.addressof(self._items))[:] = value

class IEnumUnknown(IUnknown):
  IID = GUID('00000100-0000-0000-c000-000000000046')
  _protos['Next'] = 3, (wintypes.ULONG, wintypes.PLPVOID, wintypes.PULONG), ()
  _protos['Skip'] = 4, (wintypes.ULONG,), ()
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  IClass = IUnknown
  def __new__(cls, clsid_component=False, factory=None):
    if isinstance(clsid_component, (tuple, list, ctypes.Array)):
      if not (pI := wintypes.LPVOID(_COM_IEnumUnknown(cls.IID, items=clsid_component, container=factory))):
        return None
      self = object.__new__(cls)
      self.pI = pI
      self.refs = 1
      self.factory = factory
      self._lightweight = True
      return self
    return super().__new__(cls, clsid_component, factory)
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    a = (wintypes.LPVOID * number)()
    if self.__class__._protos['Next'](self.pI, number, a, r) is None:
      return None
    return tuple(IUnknown(a[i], self.factory) for i in range(r.value)) if self.__class__.IClass is IUnknown else tuple(_IUtil.QueryInterface(IUnknown(a[i], self.factory), self.__class__.IClass) for i in range(r.value))
  def Skip(self, number):
    try:
      return self.__class__._protos['Skip'](self.pI, number)
    except:
      ISetLastError(0x80070057)
      return None
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    if not (n := self.Next(1)):
      raise StopIteration
    return n[0]

class _COM_IEnumInterface(_COM_IUnknown_aggregatable):
  _iids.add(_iid := GUID.from_name('_COM_IEnumInterface'))
  locals().update({n: object.__getattribute__(_COM_IEnumUnknown, n) for n in ('_vtbl', '_Next', '_Skip', '_Reset')})
  _vtbl['GetIID'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PBYTES16)
  _vtbl['Contains'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.LPVOID)
  _vars['iiid'] = wintypes.BYTES16
  _vars.update(_COM_IEnumUnknown._vars)
  @classmethod
  def _Clone(cls, pI, ppenum):
    with cls[pI] as self:
      if not self or not ppenum:
        if ppenum:
          ppenum.contents.value = None
        return 0x80004003
      ppenum.contents.value = _COM_IEnumInterface_impl(cls._iid, iiid=self.iiid, items=self.items, index=self.index, container=self.container)
      return 0
  @classmethod
  def _GetIID(cls, pI, riid):
    with cls[pI] as self:
      if not self or not riid:
        return 0x80004003
      riid.contents[:] = self.iiid
    return 0
  @classmethod
  def _Contains(cls, pI, pobj):
    with cls[pI] as self:
      if not self or not pobj:
        return 0x80004003
      return 0 if pobj in self.items else 1

class _COM_IEnumInterface_impl(metaclass=_COMMeta, interfaces=(_COM_IUnknown, _COM_IEnumInterface)):
  def __new__(cls, iid=0, *, _bnew=__new__, iiid=_COMMeta._iid_iunknown, items=(), index=0, container=None):
    return _bnew(cls, iid, cls._items.offset + len(items) * _COMMeta._psize, iiid=GUID(iiid), items=items, index=index, container=container)
  def __init__(self, *, iiid, items, index, container):
    super(self.__class__, self).__init__(count=len(items), iiid=wintypes.BYTES16(*iiid), items=items, index=index, container=PCOM(container).value)
    self.container.AddRef()
  locals().update({n: object.__getattribute__(_COM_IEnumUnknown_impl, n) for n in ('_destroy', 'items')})

class IEnumInterface(IEnumUnknown):
  IID = _COM_IEnumInterface._iid
  _protos['GetIID'] = 7, (), (wintypes.PBYTES16,)
  _protos['Contains'] = 8, (wintypes.LPVOID,), (), wintypes.ULONG
  def __new__(cls, clsid_component_items=False, factory=None, icls=IUnknown):
    if isinstance(clsid_component_items, (tuple, list, ctypes.Array)):
      if not (pI := wintypes.LPVOID(_COM_IEnumInterface_impl(cls.IID, iiid=icls.IID, items=clsid_component_items, container=factory))):
        return None
      self = object.__new__(cls)
      self.pI = pI
      self.refs = 1
      self.factory = factory
      self._lightweight = True
    elif (self := super().__new__(cls, clsid_component_items, factory)) is None:
      return None
    self.IClass = icls
    return self
  def Next(self, number):
    r = wintypes.ULONG()
    a = (wintypes.LPVOID * number)()
    if self.__class__._protos['Next'](self.pI, number, a, r) is None:
      return None
    return tuple(self.IClass(a[i], self.factory) for i in range(r.value))
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory, self.IClass)
  def GetIID(self):
    return GUID(self.__class__._protos['GetIID'](self.pI))
  def Contains(self, obj):
    return None if ISetLastError(c := self.__class__._protos['Contains'](self.pI, obj)) else c == 0

class _COM_IEnumInterfaceFactory(_COM_IUnknown_aggregator):
  _iids.add(_iid := GUID.from_name('_COM_IEnumInterfaceFactory'))
  _aiids = {_COM_IEnumInterface._iid: 0}
  _vars['pUnkInners'] = wintypes.LPVOID * 1
  _vtbl['CreateInstance'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PBYTES16, wintypes.PLPVOID)
  _vtbl['LockServer'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.BOOL)
  @classmethod
  def _CreateInstance(cls, pI, riid, ppObj):
    if not ppObj:
      return 0x80004003
    with cls[pI] as self:
      if not self or not riid:
        ppObj.contents.value = 0
        return 0x80004003
      with _COM_IUnknown[self.pUnkInners[0]] as inner:
        if not inner:
          ppObj.contents.value = 0
          return 0x80004003
        ppObj.contents.value = _COM_IEnumInterface_impl(_COM_IEnumInterface._iid, iiid=riid.contents, items=(wintypes.LPVOID * inner.count)(*(PCOM.QueryInterface(wintypes.LPVOID(item), riid) for item in inner.items)), index=inner.index, container=inner.container)
      return 0
  @classmethod
  def _LockServer(cls, pI, fLock):
    return 0x80004001 if cls[pI] else 0x80004003

class _COM_IEnumInterfaceFactory_impl(metaclass=_COMMeta, interfaces=(_COM_IEnumInterfaceFactory,)):
  def __new__(cls, iid=0, *, _bnew=__new__, iiid=_COMMeta._iid_iunknown, items=(), container=None):
    return _bnew(cls, iid, iiid=iiid, items=items, container=container)
  def __init__(self, *, iiid, items, container):
    super(self.__class__, self).__init__()
    _COM_IEnumInterfaceFactory.set_inner(self, 0, _COM_IEnumInterface_impl, iiid=iiid, items=items, container=container)

class IEnumInterfaceFactory(IUnknown):
  IID = _COM_IEnumInterfaceFactory._iid
  _protos['CreateInstance'] = 3, (wintypes.LPCSTR,), (wintypes.PLPVOID,)
  def __new__(cls, clsid_component_items=False, factory=None, icls=IUnknown):
    if isinstance(clsid_component_items, (tuple, list, ctypes.Array)):
      if not (pI := wintypes.LPVOID(_COM_IEnumInterfaceFactory_impl(cls.IID, iiid=icls.IID, items=clsid_component_items, container=factory))):
        return None
      self = object.__new__(cls)
      self.pI = pI
      self.refs = 1
      self.factory = factory
      self._lightweight = True
    elif (self := super().__new__(cls, clsid_component_items, factory)) is None:
      return None
    return self
  def CreateInstance(self, icls):
    if (i := IEnumInterface(self.__class__._protos['CreateInstance'](self.pI, icls.IID), self.factory)) is None:
      return None
    i.IClass = icls
    if getattr(self, '_lightweight', False):
      i._lightweight = True
    return i
  def QueryInterface(self, icls, factory=None):
    if (i := super().QueryInterface(icls, factory)) is not None:
      i.IClass = icls
    return i

class _COM_IEnumInterface_Proxy(_COM_IRpcProxy):
  _iids.update(_COM_IEnumInterface._iids)
  _vtbl.update(_COM_IEnumInterface._vtbl)
  _vars['iiid'] = wintypes.BYTES16
  @classmethod
  def _call(cls, self, method, iargs, oargs, restype=wintypes.ULONG, errcheck=0x80000000.__and__):
    if method != 7 and not any(self.iiid) and cls._call(self, 7, (), (self.iiid,)):
      return 0x8000ffff
    return super()._call(self, method, iargs, oargs, restype, errcheck)
  @classmethod
  def _Next(cls, pI, celt, rgelt, pceltFetched):
    with cls[pI] as self:
      if not self or not rgelt or (celt > 1 and not pceltFetched):
        if pceltFetched:
          pceltFetched.contents.value = 0
        if rgelt:
          (wintypes.LPVOID * celt).from_address(rgelt)[:] = (None,) * celt
        return 0x80004003
      if celt == 0:
        if pceltFetched:
          pceltFetched.contents.value = 0
        return 0
      return cls._call(self, 3, (wintypes.ULONG(celt),), (*PCOM_IID.tuple(celt, self.iiid, rgelt), (pceltFetched.contents if pceltFetched else wintypes.ULONG())))
  @classmethod
  def _Skip(cls, pI, celt):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      return cls._call(self, 4, (wintypes.ULONG(celt),), ())
  @classmethod
  def _Reset(cls, pI):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      return cls._call(self, 5, (), ())
  @classmethod
  def _Clone(cls, pI, ppenum):
    with cls[pI] as self:
      if not self or not ppenum:
        if ppenum:
          ppenum.contents.value = None
        return 0x80004003
      return cls._call(self, 6, (), (PCOM_IID.from_address(ctypes.cast(ppenum, wintypes.LPVOID).value, _COM_IEnumInterface._iid),))
  @classmethod
  def _GetIID(cls, pI, riid):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      return cls._call(self, 7, (), (riid.contents,))
  @classmethod
  def _Contains(cls, pI, pobj):
    with cls[pI] as self:
      if not self or not pobj:
        return 0x80004003
      return cls._call(self, 8, (PCOM_IID(pobj, self.iiid),), ())

class _COM_IEnumInterface_Stub(_COM_IRpcStubBuffer):
  _vars['iiid'] = wintypes.BYTES16
  @classmethod
  def _Connect(cls, pI, pUnkServer):
    if (r := super()._Connect(pI, pUnkServer)):
      return r
    with cls[pI] as self:
      if not self:
        return 0x80004003
      ind = getattr(cls, '_ovtbl', 0) // cls.__class__._psize
      if (pI := self.pIntServers[ind]) is None or ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PBYTES16)(7, 'GetIID')(wintypes.LPVOID(pI), ctypes.byref(self.iiid)):
        return 0x8000ffff
      return 0
  @classmethod
  def _invoke(cls, self, pI, channel, message):
    if (method := message.iMethod) == 3:
      if isinstance(iargs := cls._gen_iargs(channel, message, (wintypes.ULONG,)), int):
        return iargs
      if isinstance((oargs := cls._gen_oargs(self, channel, message, (*PCOM_IID.tuple((celt := iargs[0].value), self.iiid), wintypes.ULONG))), int):
        return oargs
      return cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG, wintypes.LPVOID, wintypes.PULONG)(3, 'Next')(pI, celt, ctypes.addressof(oargs[0]), oargs[-1]))
    elif method == 4:
      iargs, oargs = cls._gen_args(self, channel, message, (wintypes.ULONG,), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.ULONG)(4, 'Skip')(pI, iargs[0]))
    elif method == 5:
      iargs, oargs = cls._gen_args(self, channel, message, (), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG)(5, 'Reset')(pI))
    elif method == 6:
      iargs, oargs = cls._gen_args(self, channel, message, (), (PCOM_IID(None, _COM_IEnumInterface._iid),))
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PLPVOID)(6, 'Clone')(pI, oargs[0]))
    elif method == 7:
      iargs, oargs = cls._gen_args(self, channel, message, (), (wintypes.BYTES16,))
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PBYTES16)(7, 'GetIID')(pI, oargs[0]))
    elif method == 8:
      iargs, oargs = cls._gen_args(self, channel, message, (PCOM_IID(None, self.iiid),), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.LPVOID)(8, 'Contains')(pI, iargs[0]))
    else:
      iargs, oargs = cls._gen_args(self, channel, message, (), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, 0x80004001)

class _COM_IEnumInterfaceFactory_Proxy(_COM_IRpcProxy):
  _iids.update(_COM_IEnumInterfaceFactory._iids)
  _vtbl.update(_COM_IEnumInterfaceFactory._vtbl)
  @classmethod
  def _CreateInstance(cls, pI, riid, ppObj):
    if not ppObj:
      return 0x80004003
    with cls[pI] as self:
      if not self or not riid:
        ppObj.contents.value = 0
        return 0x80004003
      return cls._call(self, 3, (riid.contents,), (PCOM_IID.from_address(ctypes.cast(ppObj, wintypes.LPVOID).value, _COM_IEnumInterface._iid),))
  @classmethod
  def _LockServer(cls, pI, fLock):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      return cls._call(self, 4, (wintypes.BOOL(fLock),), ())

class _COM_IEnumInterfaceFactory_Stub(_COM_IRpcStubBuffer):
  @classmethod
  def _invoke(cls, self, pI, channel, message):
    if (method := message.iMethod) == 3:
      iargs, oargs = cls._gen_args(self, channel, message, (wintypes.BYTES16,), (PCOM_IID(None, _COM_IEnumInterface._iid),))
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PBYTES16, wintypes.PLPVOID)(3, 'CreateInstance')(pI, iargs[0], oargs[0]))
    elif method == 4:
      iargs, oargs = cls._gen_args(self, channel, message, (wintypes.BOOL,), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.BOOL)(4, 'LockServer')(pI, iargs[0]))
    else:
      iargs, oargs = cls._gen_args(self, channel, message, (), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, 0x80004001)

class _PS_IEnumInterfaceFactory_impl(metaclass=_PSImplMeta, ps_interfaces=((_COM_IEnumInterface_Proxy, _COM_IEnumInterface_Stub), (_COM_IEnumInterfaceFactory_Proxy, _COM_IEnumInterfaceFactory_Stub))):
  CLSID = True

class PBUFFER(wintypes.LPVOID):
  @staticmethod
  def length(obj):
    if obj is None:
      return 0
    elif isinstance(obj, ctypes._CData):
      if isinstance(obj, ctypes._Pointer):
        return ctypes.sizeof(obj.__class__._type_) if obj else 0
      elif isinstance(obj, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_wchar_p, ctypes.CArgObject)):
        raise TypeError('object of type \'%s\' has no length' % obj.__class__.__name__)
      else:
        return ctypes.sizeof(obj)
    elif isinstance(obj, memoryview):
      return obj.nbytes
    else:
      return len(obj) * getattr(obj, 'itemsize', 1)
  @classmethod
  def from_param(cls, obj, pointer=False):
    if obj is None:
      return None
    elif isinstance(obj, ctypes._CData):
      if isinstance(obj, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_wchar_p, ctypes._Pointer, ctypes.CArgObject)):
        return obj
      else:
        return (ctypes.pointer if pointer else ctypes.byref)(obj)
    elif isinstance(obj, bytes):
      return ctypes.c_char_p(obj)
    else:
      return (ctypes.pointer if pointer else ctypes.byref)((ctypes.c_char * PBUFFER.length(obj)).from_buffer(obj))

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
    if ISetLastError(r):
      return None
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
    if isinstance(n, str):
      g = cls._tab_ng.get(n.lower())
      if g is None:
        try:
          g = GUID(n)
        except:
          g = cls._def
    else:
      g = n
    return g
  @classmethod
  def guid_name(cls, g):
    return g if isinstance(g, str) else cls._tab_gn.get(g, GUID.to_string(g))
  @classmethod
  def to_bytes(cls, obj):
    return obj.raw if isinstance(obj, wintypes.GUID) else (cls.name_guid(obj) or (b'\x00' * 16))
  @property
  def value(self):
    return self
  @value.setter
  def value(self, val):
    self.raw = val.raw
  @property
  def guid(self):
    return GUID(self.raw)
  @guid.setter
  def guid(self, val):
    self.raw = val or (b'\x00' * 16)
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
    return '<%s: %s>' % (self.guid, self.name)
  def __repr__(self):
    return str(self)

class _BPGUID:
  @classmethod
  def from_param(cls, obj):
    return obj if isinstance(obj, (cls.__bases__[1], wintypes.PGUID, wintypes.LPVOID, ctypes.c_char_p, ctypes.CArgObject)) else (ctypes.byref(obj) if isinstance(obj, (wintypes.GUID, wintypes.BYTES16)) or (isinstance(obj, ctypes.Array) and issubclass(obj._type_, wintypes.GUID)) else ctypes.c_char_p(cls._type_.name_guid(obj)))
  @classmethod
  def create_from(cls, obj):
    obj = cls._type_.name_guid(obj)
    return ctypes.cast(ctypes.c_void_p(None), cls) if obj is None else cls(cls._type_(obj))

class _GUtil:
  _mul_cache = {}
  @staticmethod
  def _asitem(arr, key, value):
    return arr.__class__.__bases__[0].__setitem__(arr, key, arr.__class__.__bases__[0]._type_(value) if isinstance(key, int) else [arr.__class__.__bases__[0]._type_(v) for v in value])
  @staticmethod
  def _avalue(arr):
    return tuple(arr)

class _GMeta(wintypes.GUID.__class__):
  def __init__(cls, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if 'value' in vars(cls):
      del cls.value
  def __mul__(bcls, size):
    return _GUtil._mul_cache.get((bcls, size)) or _GUtil._mul_cache.setdefault((bcls, size), type('%s_Array_%d' % (bcls.__name__, size), (ctypes.wintypes.GUID.__class__.__mul__(bcls, size),), {'__setitem__': _GUtil._asitem, 'value': property(_GUtil._avalue)}))

UUID = _GMeta('UUID', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {}, '_tab_gn': {}, '_def': None, '__str__': lambda s: str(s.guid)})
PUUID = type('PUUID', (_BPGUID, ctypes.POINTER(UUID)), {'_type_': UUID})

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
    return getattr(obj, 'code', obj.value) if isinstance(obj, cls.__bases__[1]) else cls.name_code(obj)
  @property
  def value(self):
    return self
  @value.setter
  def value(self, val):
    self.__class__.__bases__[1].value.__set__(self, val.__class__.__bases__[1].value.__get__(val))
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
    return self.code == self.__class__.to_int(other)
  def __index__(self):
    return self.code
  def __str__(self):
    c = self.__class__.__bases__[1].value.__get__(self)
    return '<%d: %s>' % (c, self.__class__.code_name(c))
  def __repr__(self):
    return str(self)
  def __hash__(self):
    return int.__hash__(self.code)

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

class _BCodeU(_BCodeOr):
  @classmethod
  def code_name(cls, c):
    return ' | '.join((n_ for c_, n_ in cls._tab_cn.items() if c_ & c == c_) if c & 15 == 0 else (n_ for c_, n_ in cls._tab_cn.items() if c_ & c == c_ and c_ != 0))

class COMPONENTS(wintypes.DWORD):
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

class _BSTRUtil:
  _mul_cache = {}
  @staticmethod
  def _agitem(arr, key):
    e = arr.__class__.__bases__[0].__getitem__(arr, key)
    return e.content if isinstance(key, int) else [b.content for b in e]
  @staticmethod
  def _asitem(arr, key, value):
    return arr.__class__.__bases__[0].__setitem__(arr, key, (value if isinstance(value, BSTR) else BSTR(value)) if isinstance(key, int) else [v if isinstance(v, BSTR) else BSTR(v) for v in value])

class _BSTRMeta(ctypes._Pointer.__class__):
  def __mul__(bcls, size):
    return _BSTRUtil._mul_cache.get((bcls, size)) or _BSTRUtil._mul_cache.setdefault((bcls, size), type('BSTR_Array_%d' % size, (ctypes._Pointer.__class__.__mul__(bcls, size),), {'__getitem__': _BSTRUtil._agitem, '__setitem__': _BSTRUtil._asitem}))

class BSTR(ctypes.POINTER(wintypes.WCHAR), metaclass=_BSTRMeta):
  _type_ = wintypes.WCHAR
  oleauto32.SysAllocString.restype = wintypes.LPVOID
  oleauto32.SysAllocStringByteLen.restype = wintypes.LPVOID
  def __new__(cls, data=None):
    self = ctypes.POINTER(wintypes.WCHAR).__new__(cls)
    if isinstance(data, BSTR):
      self._needsfree = False
      bstr = getattr(data, 'bstr', ctypes.cast(data, ctypes.c_void_p))
    elif isinstance(data, wintypes.LPVOID):
      self._needsfree = False
      bstr = data
    elif data is None or isinstance(data, int):
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
    self.value = bstr.value
    return self
  @property
  def value(self):
    return getattr(getattr(self, 'bstr', ctypes.cast(self, ctypes.c_void_p)), 'value', None)
  @value.setter
  def value(self, val):
    ctypes.c_void_p.from_address(ctypes.addressof(self)).value = val
    self.bstr = ctypes.cast(self, ctypes.c_void_p)
  @property
  def content(self):
    if not hasattr(self, 'bstr'):
      self.bstr = ctypes.cast(self, ctypes.c_void_p)
    if not self.bstr:
      return None
    l = wintypes.UINT(oleauto32.SysStringLen(self.bstr))
    return ctypes.wstring_at(self.bstr, l.value)
  def __init__(self, data=None):
    super().__init__()
  def __del__(self):
    if (bstr := getattr(self, 'bstr', ctypes.cast(self, ctypes.c_void_p))) and getattr(self, '_needsfree', False):
      oleauto32.SysFreeString(bstr)
      self._needsfree = False
      self.value = None
  def __ctypes_from_outparam__(self):
    self._needsfree = True
    self.bstr = ctypes.cast(self, ctypes.c_void_p)
    return self
PBSTR = ctypes.POINTER(BSTR)
class BSTRING(BSTR):
  _type_ = wintypes.WCHAR
  @classmethod
  def from_param(cls, obj):
    return obj if isinstance(obj, BSTR) else cls(obj)
  def __ctypes_from_outparam__(self):
    return super().__ctypes_from_outparam__().content
PBSTRING = ctypes.POINTER(BSTRING)

class _DT:
  def __new__(cls, dt=0):
    if isinstance(dt, str):
      try:
        dt = datetime.datetime.strptime(dt, '%x %X %z')
      except:
        try:
          dt = datetime.datetime.strptime(dt, '%x %X')
          dt = dt.replace(tzinfo=dt.astimezone().tzinfo)
        except:
          try:
            dt = datetime.datetime.fromisoformat(dt)
          except:
            return None
    if isinstance(dt, datetime.datetime):
      dt = (dt - datetime.datetime(*cls._origin, (None if dt.tzinfo is None else datetime.timezone.utc))) / datetime.timedelta(**{cls._unit[0]: 1}) / cls._unit[1]
    if isinstance(dt, int):
      pass
    elif isinstance(dt, float):
      if issubclass(cls, int):
        dt = round(dt)
    elif isinstance(dt, cls._ctype):
      dt = (dt.dwLowDateTime + (dt.dwHighDateTime << 32)) if issubclass(cls, int) else dt.value
    else:
      return None
    self = (int if issubclass(cls, int) else float).__new__(cls, dt)
    return self
  def to_utc(self):
    return (datetime.datetime(*self.__class__._origin, datetime.timezone.utc) + datetime.timedelta(**{self.__class__._unit[0]: self * self.__class__._unit[1]}))
  def to_locale(self):
    return self.to_utc().astimezone()
  def to_string(self):
    l = self.to_locale()
    if round(l.second + l.microsecond / 1000000) > l.second:
      l = l + datetime.timedelta(seconds=1)
    return l.replace(microsecond=0).strftime('%x %X %z')
  def __str__(self):
    try:
      return ('<%%%s: %%s>' % ('d' if isinstance(self, int) else 'f')) % (self, self.to_string())
    except:
      return ('<%%%s: >' % ('d' if isinstance(self, int) else 'f')) % self
  def __repr__(self):
    return str(self)

class _DTUtil:
  @staticmethod
  def _agitem(arr, key):
    e = arr.__class__.__bases__[0].__getitem__(arr, key)
    return e.content if isinstance(key, int) else [d.content for d in e]
  @staticmethod
  def _asitem(arr, key, value):
    cls = arr.__class__.__bases__[0]._type_
    return arr.__class__.__bases__[0].__setitem__(arr, key, (value if isinstance(value, cls) else cls(value)) if isinstance(key, int) else [v if isinstance(v, cls) else cls(v) for v in value])

class FDate(_DT, float):
  _origin = (1899, 12, 30, 0, 0, 0, 0)
  _unit = ('days', 1)
  _ctype = wintypes.DOUBLE

class _DATEUtil(_DTUtil):
  _mul_cache = {}

class _DATEMeta(wintypes.DOUBLE.__class__):
  def __mul__(bcls, size):
    return _DATEUtil._mul_cache.get((bcls, size)) or _DATEUtil._mul_cache.setdefault((bcls, size), type('DATE_Array_%d' % size, (wintypes.DOUBLE.__class__.__mul__(bcls, size),), {'__getitem__': _DATEUtil._agitem, '__setitem__': _DATEUtil._asitem}))

class DATE(wintypes.DOUBLE, metaclass=_DATEMeta):
  def __init__(self, dt=0):
    wintypes.DOUBLE.__init__(self, FDate(dt))
  @property
  def content(self):
    return FDate(self)
  @content.setter
  def content(self, data):
    self.value = FDate(data)

class IFileTime(_DT, int):
  _origin = (1601, 1, 1, 0, 0, 0, 0)
  _unit = ('microseconds', 0.1)
  _ctype = wintypes.FILETIME

class _FILETIMEUtil(_DTUtil):
  _mul_cache = {}

class _FILETIMEMeta(wintypes.FILETIME.__class__):
  def __mul__(bcls, size):
    return _FILETIMEUtil._mul_cache.get((bcls, size)) or _FILETIMEUtil._mul_cache.setdefault((bcls, size), type('FILETIME_Array_%d' % size, (wintypes.FILETIME.__class__.__mul__(bcls, size),), {'__getitem__': _FILETIMEUtil._agitem, '__setitem__': _FILETIMEUtil._asitem}))

class FILETIME(wintypes.FILETIME, metaclass=_FILETIMEMeta):
  def __init__(self, dt=0):
    if isinstance(dt, wintypes.FILETIME):
      wintypes.FILETIME.__init__(self, dt.dwLowDateTime, dt.dwHighDateTime)
    else:
      fd = IFileTime(dt)
      wintypes.FILETIME.__init__(self, (fd & 0xffffffff), (fd >> 32))
  @classmethod
  def from_param(cls, obj):
    return obj if obj is None or isinstance(obj, cls) else cls(obj)
  @property
  def content(self):
    return IFileTime(self)
  @content.setter
  def content(self, data):
    self.__init__(data)
  value = content

class _WSUtil:
  _mul_cache = {}
  @staticmethod
  def _asitem(arr, key, value):
    return arr.__class__.__bases__[0].__setitem__(arr, key, arr.__class__.__bases__[0]._type_.from_param(value) if isinstance(key, int) else [arr.__class__.__bases__[0]._type_.from_param(v) for v in value])
  @staticmethod
  def _avalue(arr):
    return tuple(s.value for s in arr)

class _WSMeta(ctypes.Structure.__class__):
  def __init__(cls, *args, **kwargs):
    super(_WSMeta, _WSMeta).__init__(cls, *args, **kwargs)
    for n, t in cls._fields_:
      if (b := issubclass(t, _BGUID)) or issubclass(t, (_BCode, COMPONENTS)):
        setattr(cls, '_' + n, getattr(cls, n))
        setattr(cls, n, property(lambda s, _n='_'+n, _t=t: _t(getattr(s, _n)), lambda s, v, _n='_'+n, _c=(t.to_bytes if b else t.to_int): setattr(s, _n, _c(v)), getattr(cls, '_' + n).__delete__))
      elif (b := issubclass(t, wintypes.BOOLE)) or issubclass(t, (PCOM, BSTRING, DATE)):
        setattr(cls, '_' + n, getattr(cls, n))
        setattr(cls, n, property((lambda s, _n='_'+n, _t=t: getattr(s, _n).value) if b else (lambda s, _n='_'+n, _t=t: getattr(s, _n).content), lambda s, v, _n='_'+n, _t=t: setattr(s, _n, (v if isinstance(v, _t) else _t(v))), getattr(cls, '_' + n).__delete__))
      elif issubclass(t, (PBUFFER, _BPStruct, _BPAStruct)):
        setattr(cls, '_' + n, getattr(cls, n))
        setattr(cls, n, property(getattr(cls, '_' + n).__get__, lambda s, v, _n='_'+n, _t=t: setattr(s, _n, ctypes.cast(_t.from_param(v, True), _t)), getattr(cls, '_' + n).__delete__))
  def __mul__(bcls, size):
    return _WSUtil._mul_cache.get((bcls, size)) or _WSUtil._mul_cache.setdefault((bcls, size), type('%s_Array_%d' % (bcls.__name__, size), (ctypes.Structure.__class__.__mul__(bcls, size),), {'__setitem__': _WSUtil._asitem, 'value': property(_WSUtil._avalue)}))

class _BDStruct:
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, dict):
      return cls(*(((t.from_param(obj[n]) if n in obj else t()) if issubclass(t, ctypes.Structure) else obj.get(n, 0)) for n, t in cls._fields_))
    else:
      return cls(*((t.from_param(o) if issubclass(t, ctypes.Structure) else o) for (n, t), o in zip(cls._fields_, obj)))
  def to_dict(self):
    return {n: (getattr((v := getattr(self, n)), 'value', v) if issubclass(t, (ctypes.Structure, _BPStruct)) else getattr(self, n)) for n, t in self.__class__._fields_}
  @property
  def value(self):
    return self.to_dict()
  def __ctypes_from_outparam__(self):
    return self.to_dict()

class _BTStruct:
  @classmethod
  def from_param(cls, obj):
    return obj if obj is None or isinstance(obj, cls) else cls(*((t.from_param(o) if issubclass(t, ctypes.Structure) else o) for (n, t), o in zip(cls._fields_, obj)))
  def to_tuple(self):
    return tuple(getattr((v := getattr(self, n)), 'value', v) if issubclass(t, (ctypes.Structure, _BPStruct)) else getattr(self, n) for n, t in self.__class__._fields_)
  @property
  def value(self):
    return self.to_tuple()
  def __ctypes_from_outparam__(self):
    return self.to_tuple()

class _BPStruct:
  @classmethod
  def from_param(cls, obj, pointer=False):
    return obj if obj is None or isinstance(obj, (cls.__bases__[1], wintypes.LPVOID, ctypes.CArgObject)) else (ctypes.pointer if pointer else ctypes.byref)(obj if isinstance(obj, ctypes.Array) and issubclass(obj._type_, cls._type_) else cls._type_.from_param(obj))
  @property
  def value(self):
    return getattr((s := self.contents), 'value', s) if self else None

class _BPAStruct:
  @classmethod
  def from_param(cls, obj, pointer=False):
    return obj if obj is None or isinstance(obj, (cls.__bases__[1], wintypes.LPVOID, ctypes.CArgObject)) else (ctypes.pointer if pointer else ctypes.byref)(obj if isinstance(obj, ctypes.Array) and issubclass(obj._type_, cls._type_) else (cls._type_ * len(obj))(*obj))
  def value(self, count):
    return getattr((a := ctypes.cast(self, ctypes.POINTER(self.__class__._type_ * count)).contents), 'value', a) if self else None

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

class WICJPEGFRAMEHEADER(_BDStruct, ctypes.Structure):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('TransferMatrix', WICJPEGTRANSFERMATRIX), ('ScanType', WICJPEGSCANTYPE), ('cComponents', wintypes.UINT), ('ComponentIdentifiers', COMPONENTS), ('SampleFactors', WICJPEGSAMPLEFACTORS), ('QuantizationTableIndices', WICJPEGQUANTIZATIONBASELINE)]
WICPJPEGFRAMEHEADER = ctypes.POINTER(WICJPEGFRAMEHEADER)

class WICJPEGDCHUFFMANTABLE(_BDStruct, ctypes.Structure):
  _fields_ = [('CodeCounts', wintypes.BYTE * 12), ('CodeValues', wintypes.BYTE * 12)]
WICPJPEGDCHUFFMANTABLE = ctypes.POINTER(WICJPEGDCHUFFMANTABLE)

class WICJPEGACHUFFMANTABLE(_BDStruct, ctypes.Structure):
  _fields_ = [('CodeCounts', wintypes.BYTE * 16), ('CodeValues', wintypes.BYTE * 162)]
WICPJPEGACHUFFMANTABLE = ctypes.POINTER(WICJPEGACHUFFMANTABLE)

class WICJPEGQUANTIZATIONTABLE(ctypes.Structure):
  _fields_ = [('Elements', wintypes.BYTE * 64),]
  def __ctypes_from_outparam__(self):
    return self.Elements
WICPJPEGQUANTIZATIONTABLE = ctypes.POINTER(WICJPEGQUANTIZATIONTABLE)

class WICJPEGSCANHEADER(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cComponents', wintypes.UINT), ('RestartInterval', wintypes.UINT), ('ComponentSelectors', COMPONENTS), ('HuffmanTableIndices', WICJPEGHUFFMANBASELINE), ('StartSpectralSelection', wintypes.BYTE), ('EndSpectralSelection', wintypes.BYTE), ('SuccessiveApproximationHigh', wintypes.BYTE), ('SuccessiveApproximationLow', wintypes.BYTE)]
WICPJPEGSCANHEADER = ctypes.POINTER(WICJPEGSCANHEADER)

DXGIFormat = {'UNKNOWN': 0, 'R32G32B32A32_TYPELESS': 1, 'R32G32B32A32_FLOAT': 2, 'R32G32B32A32_UINT': 3, 'R32G32B32A32_SINT': 4, 'R32G32B32_TYPELESS': 5, 'R32G32B32_FLOAT': 6, 'R32G32B32_UINT': 7, 'R32G32B32_SINT': 8, 'R16G16B16A16_TYPELESS': 9, 'R16G16B16A16_FLOAT': 10, 'R16G16B16A16_UNORM': 11, 'R16G16B16A16_UINT': 12, 'R16G16B16A16_SNORM': 13, 'R16G16B16A16_SINT': 14, 'R32G32_TYPELESS': 15, 'R32G32_FLOAT': 16, 'R32G32_UINT': 17, 'R32G32_SINT': 18, 'R32G8X24_TYPELESS': 19, 'D32_FLOAT_S8X24_UINT': 20, 'R32_FLOAT_X8X24_TYPELESS': 21, 'X32_TYPELESS_G8X24_UINT': 22, 'R10G10B10A2_TYPELESS': 23, 'R10G10B10A2_UNORM': 24, 'R10G10B10A2_UINT': 25, 'R11G11B10_FLOAT': 26, 'R8G8B8A8_TYPELESS': 27, 'R8G8B8A8_UNORM': 28, 'R8G8B8A8_UNORM_SRGB': 29, 'R8G8B8A8_UINT': 30, 'R8G8B8A8_SNORM': 31, 'R8G8B8A8_SINT': 32, 'R16G16_TYPELESS': 33, 'R16G16_FLOAT': 34, 'R16G16_UNORM': 35, 'R16G16_UINT': 36, 'R16G16_SNORM': 37, 'R16G16_SINT': 38, 'R32_TYPELESS': 39, 'D32_FLOAT': 40, 'R32_FLOAT': 41, 'R32_UINT': 42, 'R32_SINT': 43, 'R24G8_TYPELESS': 44, 'D24_UNORM_S8_UINT': 45, 'R24_UNORM_X8_TYPELESS': 46, 'X24_TYPELESS_G8_UINT': 47, 'R8G8_TYPELESS': 48, 'R8G8_UNORM': 49, 'R8G8_UINT': 50, 'R8G8_SNORM': 51, 'R8G8_SINT': 52, 'R16_TYPELESS': 53, 'R16_FLOAT': 54, 'D16_UNORM': 55, 'R16_UNORM': 56, 'R16_UINT': 57, 'R16_SNORM': 58, 'R16_SINT': 59, 'R8_TYPELESS': 60, 'R8_UNORM': 61, 'R8_UINT': 62, 'R8_SNORM': 63, 'R8_SINT': 64, 'A8_UNORM': 65, 'R1_UNORM': 66, 'R9G9B9E5_SHAREDEXP': 67, 'R8G8_B8G8_UNORM': 68, 'G8R8_G8B8_UNORM': 69, 'BC1_TYPELESS': 70, 'BC1_UNORM': 71, 'BC1_UNORM_SRGB': 72, 'BC2_TYPELESS': 73, 'BC2_UNORM': 74, 'BC2_UNORM_SRGB': 75, 'BC3_TYPELESS': 76, 'BC3_UNORM': 77, 'BC3_UNORM_SRGB': 78, 'BC4_TYPELESS': 79, 'BC4_UNORM': 80, 'BC4_SNORM': 81, 'BC5_TYPELESS': 82, 'BC5_UNORM': 83, 'BC5_SNORM': 84, 'B5G6R5_UNORM': 85, 'B5G5R5A1_UNORM': 86, 'B8G8R8A8_UNORM': 87, 'B8G8R8X8_UNORM': 88, 'R10G10B10_XR_BIAS_A2_UNORM': 89, 'B8G8R8A8_TYPELESS': 90, 'B8G8R8A8_UNORM_SRGB': 91, 'B8G8R8X8_TYPELESS': 92, 'B8G8R8X8_UNORM_SRGB': 93, 'BC6H_TYPELESS': 94, 'BC6H_UF16': 95, 'BC6H_SF16': 96, 'BC7_TYPELESS': 97, 'BC7_UNORM': 98, 'BC7_UNORM_SRGB': 99, 'AYUV': 100, 'Y410': 101, 'Y416': 102, 'NV12': 103, 'P010': 104, 'P016': 105, '420_OPAQUE': 106, 'YUY2': 107, 'Y210': 108, 'Y216': 109, 'NV11': 110, 'AI44': 111, 'IA44': 112, 'P8': 113, 'A8P8': 114, 'B4G4R4A4_UNORM': 115, 'P208': 130, 'V208': 131, 'V408': 132, 'SAMPLER_FEEDBACK_MIN_MIP_OPAQUE': 189, 'SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE': 190, 'A4B4G4R4_UNORM': 191}
DXGIFORMAT = type('DXGIFORMAT', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIFormat.items()}, '_tab_cn': {c: n for n, c in DXGIFormat.items()}, '_def': 0})

WICDdsDimension = {'1D': 0, '2D': 1, '3D': 2, 'Cube': 3}
WICDDSDIMENSION = type('WICDDSDIMENSION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICDdsDimension.items()}, '_tab_cn': {c: n for n, c in WICDdsDimension.items()}, '_def': 0})

WICDdsAlphaMode = {'Unknown': 0, 'Straight': 1, 'Premultiplied': 2, 'Opaque': 3, 'Custom': 4}
WICDDSALPHAMODE = type('WICDDSALPHAMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICDdsAlphaMode.items()}, '_tab_cn': {c: n for n, c in WICDdsAlphaMode.items()}, '_def': 0})

class WICDDSFORMATINFO(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('DxgiFormat', DXGIFORMAT), ('BytesPerBlock', wintypes.UINT), ('BlockWidth', wintypes.UINT), ('BlockHeight', wintypes.UINT)]
WICPDDSFORMATINFO = ctypes.POINTER(WICDDSFORMATINFO)

class WICDDSPARAMETERS(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('Depth', wintypes.UINT), ('MipLevels', wintypes.UINT), ('ArraySize', wintypes.UINT), ('DxgiFormat', DXGIFORMAT), ('Dimension', WICDDSDIMENSION), ('AlphaMode', WICDDSALPHAMODE)]
WICPDDSPARAMETERS = ctypes.POINTER(WICDDSPARAMETERS)

class WICBITMAPPLANE(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Format', WICPIXELFORMAT), ('pbBuffer', PBUFFER), ('cbStride', wintypes.UINT), ('cbBufferSize', wintypes.UINT)]
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, IWICBitmapLock):
      return cls(obj.GetPixelFormat(), (dp := obj.GetDataPointer()), obj.GetStride(), len(dp))
    elif isinstance(obj, dict):
      return cls(obj.get('Format', 'DontCare'), obj.get('pbBuffer', None), obj.get('cbStride', 0), PBUFFER.length(obj.get('pbBuffer', None)))
    else:
      l = len(obj)
      return cls(('DontCare' if l < 1 else obj[0]), (None if l < 2 else obj[1]), (0 if l < 3 else obj[2]), PBUFFER.length(None if l < 2 else obj[1]))
  def to_dict(self):
    return {'Format': self.Format, 'pbBuffer': (ctypes.cast(self.pbBuffer, ctypes.POINTER(wintypes.BYTE * self.cbBufferSize)).contents if self.pbBuffer else None), 'cbStride': self.cbStride}
  @property
  def value(self):
    return self.to_dict()
WICPBITMAPPLANE = ctypes.POINTER(WICBITMAPPLANE)

WICRawCapabilities = {'NotSupported': 0, 'GetSupported': 1, 'FullySupported': 2}
WICRAWCAPABILITIES = type('WICRAWCAPABILITIES', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICRawCapabilities.items()}, '_tab_cn': {c: n for n, c in WICRawCapabilities.items()}, '_def': 0})

WICNamedWhitePoint = {'None': 0x0, 'Default': 0x1, 'AsShot': 0x1, 'Daylight': 0x2, 'Cloudy': 0x4, 'Shade': 0x8, 'Tungsten': 0x10, 'Fluorescent': 0x20, 'Flash': 0x40, 'Underwater': 0x80, 'Custom': 0x100, 'AutoWhiteBalance': 0x200}
WICNAMEDWHITEPOINT = type('WICNAMEDWHITEPOINT', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICNamedWhitePoint.items()}, '_tab_cn': {c: n for n, c in WICNamedWhitePoint.items()}, '_def': 0})
WICPNAMEDWHITEPOINT = ctypes.POINTER(WICNAMEDWHITEPOINT)

WICRawRotationCapabilities = {'NotSupported': 0, 'GetSupported': 1, 'NinetyDegreesSupported': 2, 'FullySupported': 3}
WICRAWROTATIONCAPABILITIES = type('WICRAWROTATIONCAPABILITIES', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICRawRotationCapabilities.items()}, '_tab_cn': {c: n for n, c in WICRawRotationCapabilities.items()}, '_def': 0})

class WICRAWCAPABILITIESINFO(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cbSize', wintypes.UINT), ('CodecMajorVersion', wintypes.UINT), ('CodecMinorVersion', wintypes.UINT), ('ExposureCompensationSupport', WICRAWCAPABILITIES), ('ContrastSupport', WICRAWCAPABILITIES), ('RGBWhitePointSupport', WICRAWCAPABILITIES), ('NamedWhitePointSupport', WICRAWCAPABILITIES), ('NamedWhitePointSupportMask', WICNAMEDWHITEPOINT), ('KelvinWhitePointSupport', WICRAWCAPABILITIES), ('GammaSupport', WICRAWCAPABILITIES), ('TintSupport', WICRAWCAPABILITIES), ('SaturationSupport', WICRAWCAPABILITIES), ('SharpnessSupport', WICRAWCAPABILITIES), ('NoiseReductionSupport', WICRAWCAPABILITIES), ('NDestinationColorProfileSupport', WICRAWCAPABILITIES), ('ToneCurveSupport', WICRAWCAPABILITIES), ('RotationSupport', WICRAWROTATIONCAPABILITIES), ('RenderModeSupport', WICRAWCAPABILITIES)]
  def __init__(self, *args, **kwargs):
    super().__init__(ctypes.sizeof(self.__class__), *args, **kwargs)
  def to_dict(self):
    return {k[0]: getattr(self, k[0]) for k in self.__class__._fields_ if k[0] != 'cbSize'}
  @property
  def value(self):
    return self.to_dict()
  def __ctypes_from_outparam__(self):
    return self.to_dict()
WICPRAWCAPABILITIESINFO = ctypes.POINTER(WICRAWCAPABILITIESINFO)

WICRawParameterSet = {'AsShot': 1, 'UserAdjusted': 2, 'AutoAdjusted': 3}
WICRAWPARAMETERSET = type('WICRAWPARAMETERSET', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICRawParameterSet.items()}, '_tab_cn': {c: n for n, c in WICRawParameterSet.items()}, '_def': 1})

class WICRAWTONECURVEPOINT(_BTStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Input', wintypes.DOUBLE), ('Output', wintypes.DOUBLE)]

class WICRAWTONECURVE(ctypes.Structure):
  _fields_ = [('cPoints', wintypes.UINT), ('aPoints', WICRAWTONECURVEPOINT * 0)]
  def to_tuple(self):
    return (WICRAWTONECURVEPOINT * self.cPoints).from_address(ctypes.addressof(self.aPoints)).value
  @property
  def value(self):
    return self.to_tuple()

WICRawRenderMode = {'Draft': 1, 'Normal': 2, 'BestQuality': 3}
WICRAWRENDERMODE = type('WICRAWRENDERMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICRawRenderMode.items()}, '_tab_cn': {c: n for n, c in WICRawRenderMode.items()}, '_def': 2})
WICPRAWRENDERMODE = ctypes.POINTER(WICRAWRENDERMODE)

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

class D2D1PIXELFORMAT(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('format', DXGIFORMAT), ('alphaMode', D2D1ALPHAMODE)]
D2D1PPIXELFORMAT = type('D2D1PPIXELFORMAT', (_BPStruct, ctypes.POINTER(D2D1PIXELFORMAT)), {'_type_': D2D1PIXELFORMAT})

class WICIMAGEPARAMETERS(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('PixelFormat', D2D1PIXELFORMAT), ('DpiX', wintypes.FLOAT), ('DpiY', wintypes.FLOAT), ('Top', wintypes.FLOAT), ('Left', wintypes.FLOAT), ('PixelWidth', wintypes.UINT), ('PixelHeight', wintypes.UINT)]
WICPIMAGEPARAMETERS = type('WICPIMAGEPARAMETERS', (_BPStruct, ctypes.POINTER(WICIMAGEPARAMETERS)), {'_type_': WICIMAGEPARAMETERS})

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

class WICBITMAPPLANEDESCRIPTION(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Format', WICPIXELFORMAT), ('Width', wintypes.UINT), ('Height', wintypes.UINT)]
WICPBITMAPPLANEDESCRIPTION = ctypes.POINTER(WICBITMAPPLANEDESCRIPTION)

WICComponentType = {'BitmapDecoder': 0x1, 'Decoder': 0x1, 'BitmapEncoder': 0x2, 'Encoder': 0x2, 'FormatConverter': 0x4 , 'PixelFormatConverter': 0x4, 'MetadataReader': 0x8, 'MetadataWriter': 0x10, 'PixelFormat': 0x20, 'Component': 0x3f, 'AllComponents': 0x3f}
WICCOMPONENTTYPE = type('WICCOMPONENTTYPE', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICComponentType.items()}, '_tab_cn': {c: n for n, c in WICComponentType.items()}, '_def': 0x3f})
WICPCOMPONENTTYPE = ctypes.POINTER(WICCOMPONENTTYPE)

WICComponentSigning = {'Signed': 0x1, 'Unsigned': 0x2, 'Safe': 0x4, 'Disabled': 0x80000000}
WICCOMPONENTSIGNING = type('WICCOMPONENTSIGNING', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICComponentSigning.items()}, '_tab_cn': {c: n for n, c in WICComponentSigning.items()}, '_def': 0x4})
WICPCOMPONENTSIGNING = ctypes.POINTER(WICCOMPONENTSIGNING)

WICComponentEnumerateOptions = {'Default': 0x0, 'Refresh': 0x1, 'Disabled': 0x80000000, 'Unsigned': 0x40000000, 'BuiltInOnly': 0x20000000}
WICCOMPONENTENUMERATEOPTIONS = type('WICCOMPONENTENUMERATEOPTIONS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICComponentEnumerateOptions.items()}, '_tab_cn': {c: n for n, c in WICComponentEnumerateOptions.items()}, '_def': 0x0})

class WICBITMAPPATTERN(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Position', wintypes.ULARGE_INTEGER), ('Length', wintypes.ULONG), ('Pattern', wintypes.LPVOID), ('Mask', wintypes.LPVOID), ('EndOfStream', wintypes.BOOLE)]
  def to_dict(self):
    return {'Position': self.Position, 'Pattern': ctypes.string_at(self.Pattern, self.Length), 'Mask': ctypes.string_at(self.Mask, self.Length), 'EndofStream': self.EndOfStream}
  @property
  def value(self):
    return self.to_dict()

WICPixelFormatNumericRepresentation = {'Unspecified': 0, 'Indexed': 1, 'UnsignedInteger': 2, 'SignedInteger': 3, 'Fixed': 4, 'Float': 5}
WICPIXELFORMATNUMERICREPRESENTATION = type('WICPIXELFORMATNUMERICREPRESENTATION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WICPixelFormatNumericRepresentation.items()}, '_tab_cn': {c: n for n, c in WICPixelFormatNumericRepresentation.items()}, '_def': 0})
WICPPIXELFORMATNUMERICREPRESENTATION = ctypes.POINTER(WICPIXELFORMATNUMERICREPRESENTATION)

class WICMETADATAPATTERN(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Position', wintypes.ULARGE_INTEGER), ('Length', wintypes.ULONG), ('Pattern', wintypes.LPVOID), ('Mask', wintypes.LPVOID), ('DataOffset', wintypes.ULARGE_INTEGER)]
  def to_dict(self):
    return {'Position': self.Position, 'Pattern': ctypes.string_at(self.Pattern, self.Length), 'Mask': ctypes.string_at(self.Mask, self.Length), 'DataOffset': self.DataOffset}
  @property
  def value(self):
    return self.to_dict()

class WICMETADATAHEADER(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Position', wintypes.ULARGE_INTEGER), ('Length', wintypes.ULONG), ('Header', wintypes.LPVOID), ('DataOffset', wintypes.ULARGE_INTEGER)]
  def to_dict(self):
    return {'Position': self.Position, 'Header': ctypes.string_at(self.Header, self.Length), 'DataOffset': self.DataOffset}
  @property
  def value(self):
    return self.to_dict()

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

class _BLOBUtil:
  _mul_cache = {}
  @staticmethod
  def _agitem(arr, key):
    e = arr.__class__.__bases__[0].__getitem__(arr, key)
    return e.content if isinstance(key, int) else [b.content for b in e]
  @staticmethod
  def _asitem(arr, key, value):
    return arr.__class__.__bases__[0].__setitem__(arr, key, BLOB(value) if isinstance(key, int) else list(map(BLOB, value)))

class _BLOBMeta(ctypes.Structure.__class__):
  def __mul__(bcls, size):
    return _BLOBUtil._mul_cache.get((bcls, size)) or _BLOBUtil._mul_cache.setdefault((bcls, size), type('BLOB_Array_%d' % size, (ctypes.Structure.__class__.__mul__(bcls, size),), {'__getitem__': _BLOBUtil._agitem, '__setitem__': _BLOBUtil._asitem}))

class BLOB(ctypes.Structure, metaclass=_BLOBMeta):
  _fields_ = [('cbSize', wintypes.ULONG), ('pBlobdata', wintypes.LPVOID)]
  @property
  def content(self):
   return ctypes.string_at(self.pBlobdata, self.cbSize) if self.pBlobdata else None
  @content.setter
  def content(self, data):
    self.cbSize = len(data)
    self.pBlobdata = ctypes.cast(ctypes.pointer(ctypes.create_string_buffer(data if isinstance(data, bytes) else bytes(data), self.cbSize)), wintypes.LPVOID)
  value = content
  def __init__(self, data=None):
    super().__init__()
    if data is not None:
      self.content = data.content if isinstance(data, BLOB) else data
  @classmethod
  def from_param(cls, obj):
    return obj if isinstance(obj, BLOB) else cls(obj)

class PCOMSTREAM(PCOM):
  icls = IStream

class VERSIONEDSTREAM(_BTStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('guidVersion', UUID), ('pStream', PCOMSTREAM)]
  def __del__(self):
    if getattr(self, '_needsclear', False):
      if (i := self.pStream) is not None:
        i.Release()
  def __ctypes_from_outparam__(self):
    self._needsclear = True
    return self.value
PVERSIONEDSTREAM = ctypes.POINTER(VERSIONEDSTREAM)

class CA(ctypes.Structure):
  _fields_ = [('vc', wintypes.DWORD), ('vp', wintypes.LPVOID)]
  def content(self, etype):
    if isinstance(etype, (int, str)):
      etype = None if (etype := PropVariantType.vtype_code(etype)) is None else PROPVARIANT.code_ctype.get(etype & 4095)
    return (etype * self.vc).from_buffer_copy(ctypes.cast(self.vp, ctypes.POINTER(etype * self.vc)).contents) if etype is not None and self.vp else None
  def __new__(cls, etype=None, data=None):
    self = ctypes.Structure.__new__(cls)
    if data is not None:
      if isinstance(etype, (int, str)):
        etype = None if (etype := PropVariantType.vtype_code(etype)) is None else PROPVARIANT.code_ctype.get(etype & 4095)
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
    l = len(args)
    if l == 2 and isinstance(args[1], PSAFEARRAY):
      l = 1
      args = (args[1],)
    self = ctypes.POINTER(wintypes.USHORT).__new__(cls)
    if l == 0:
      psafearray = wintypes.LPVOID()
    elif l == 1:
      if (psafearray := (args[0].psafearray if isinstance(args[0], PSAFEARRAY) else (args[0] if isinstance(args[0], wintypes.LPVOID) else wintypes.LPVOID(args[0])))):
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
      self._pdata = args[0]
    elif l == 2:
      vtype, data = args
      if (vtype := VariantType.vtype_code(vtype)) is None:
        return None
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
        self.shape = data.shape if isinstance(data, memoryview) else (len(data),)
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
        if issubclass(VARIANT.code_ctype[vtype], (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_wchar_p, ctypes._Pointer, VARIANT)):
          self._pdata = ctypes.pointer(data)
    else:
      return None
    ctypes.c_void_p.from_address(ctypes.addressof(self)).value = psafearray.value
    self.psafearray = ctypes.cast(self, ctypes.c_void_p)
    return self
  def __init__(self, *args, **kwargs):
    super().__init__()
  @classmethod
  def from_address(cls, address):
    return cls(wintypes.LPVOID.from_address(address))
  @property
  def content(self):
    if not self.psafearray or (atype := VARIANT.code_ctype.get(self.vtype)) is None:
      return None
    data = ctypes.create_string_buffer(self.size)
    if self.size > 0:
      pdata = wintypes.LPVOID()
      if oleauto32.SafeArrayAccessData(self.psafearray, ctypes.byref(pdata)):
        return None
      ctypes.memmove(data, pdata, self.size)
      oleauto32.SafeArrayUnaccessData(self.psafearray)
    for d in self.shape[::-1]:
      atype = atype * d
    return atype.from_buffer(data)
  def __del__(self):
    if getattr(self, 'psafearray', None) and getattr(self, '_needsdestroy', False):
      psafearray = self.psafearray
      self.psafearray = None
      if self.size > 0 and not getattr(self, '_needsclear', False):
        pdata = wintypes.LPVOID()
        if oleauto32.SafeArrayAccessData(psafearray, ctypes.byref(pdata)):
          return
        ctypes.memset(pdata, 0, self.size)
        oleauto32.SafeArrayUnaccessData(psafearray)
      oleauto32.SafeArrayDestroy(psafearray)
  def __ctypes_from_outparam__(self):
    if (self := PSAFEARRAY(ctypes.cast(self, ctypes.c_void_p))) is not None:
      self._needsdestroy = True
      self._needsclear = True
    return self
class PPSAFEARRAY (ctypes.POINTER(PSAFEARRAY)):
  _type_ = PSAFEARRAY
  def __init__(self, psafearray=None):
    if psafearray is None:
      super().__init__()
    else:
      super().__init__(psafearray)
      self.psafearray = psafearray
  @property
  def contents(self):
    return self.psafearray if hasattr(self, 'psafearray') else (PSAFEARRAY.from_address(ctypes.cast(self, wintypes.LPVOID).value) if self else None)
PSAFEARRAY.duplicate = lambda s, _d=ctypes.WINFUNCTYPE(wintypes.ULONG, PSAFEARRAY, PPSAFEARRAY, use_last_error=True)(('SafeArrayCopy', oleauto32), ((1,), (2,))): _d(s)

class BRECORD(_BTStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('pvRecord', wintypes.LPVOID), ('pRecInfo', PCOM)]
  def to_tuple(self):
    return (wintypes.LPVOID(self.pvRecord), self.pRecInfo)

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
  _mul_cache = {}
  @staticmethod
  def _ainit(arr, *args, needsclear=False, **kwargs):
    arr.__class__.__bases__[0].__init__(arr, *args, **kwargs)
    arr._needsclear = needsclear
  @staticmethod
  def _adel(arr):
    if getattr(arr, '_needsclear', False):
      for s in arr:
        s.__class__._clear(ctypes.byref(s))
    getattr(arr.__class__.__bases__[0], '__del__', id)(arr)
  @staticmethod
  def _padup(parr):
    return parr._type_.from_buffer_copy(parr.contents) if parr else None
  @staticmethod
  def _adup(arr):
    return arr.__class__.from_buffer_copy(arr)
  @staticmethod
  def _brec(var):
    val = var._brecord.value
    val[0]._bvariant = var
    return val

class _BVMeta(ctypes.Structure.__class__):
  def __mul__(bcls, size):
    return _BVUtil._mul_cache.get((bcls, size)) or _BVUtil._mul_cache.setdefault((bcls, size), type('%s_Array_%d' % (bcls.__name__, size), (ctypes.Structure.__class__.__mul__(bcls, size),), {'__init__': _BVUtil._ainit, '__del__': _BVUtil._adel}))
  def __new__(mcls, name, bases, namespace, **kwds):
    if (code_name := namespace.get('code_name')) is not None:
      cls_iu = ctypes.Union.__class__(name + '_IU', (ctypes.Union, ), {'_fields_': [*((na, _BVARIANT.code_ctype[co]) for co, na in code_name.items() if co != 14), ('pad', (wintypes.BYTE * (2 * ctypes.sizeof(wintypes.SIZE_T))))]})
      cls_i = ctypes.Structure.__class__(name + '_I', (ctypes.Structure, ), {'_anonymous_' : ('vn',), '_fields_': [('vt', ctypes.c_ushort), ('wReserved1', wintypes.WORD), ('wReserved2', wintypes.WORD), ('wReserved3', wintypes.WORD), ('vn', cls_iu)]})
      cls_ou = ctypes.Union.__class__(name + '_OU', (ctypes.Union, ), {'_anonymous_' : ('vn',), '_fields_': [('vn', cls_i), ('decVal', wintypes.BYTES16)]})
      namespace.update({'_anonymous_': ('vn',), '_fields_': [('vn', cls_ou)], 'code_ctype': {co: ct for co, ct in _BVARIANT.code_ctype.items() if co in code_name}, 'vtype_code': {vt: co for vt, co in _BVARIANT.vtype_code.items() if co in code_name or co in (0, 1, 12)}, 'code_vtype': {co: vt for co, vt in _BVARIANT.code_vtype.items() if co in code_name or co in (0, 1, 12)}})
    cls = ctypes.Structure.__class__.__new__(mcls, name, bases, namespace, **kwds)
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
      cls.filetime = property(lambda s: FILETIME(s._filetime).content, lambda s, v: setattr(s, '_filetime', FILETIME(v)), cls._filetime.__delete__)
    if hasattr(cls, 'date'):
      cls._date = cls.date
      cls.date = property(lambda s: DATE(s._date).content, lambda s, v: setattr(s, '_date', DATE(v)), cls._date.__delete__)
    for n in ('punkVal', 'pdispVal', 'pStorage', 'pStream'):
      if hasattr(cls, n):
        setattr(cls, '_' + n, getattr(cls, n))
        setattr(cls, n, property(lambda s, _n='_'+n: getattr(s, _n).content, lambda s, v, _n='_'+n: setattr(s, _n, (v if isinstance(v, PCOM) else PCOM(v))), getattr(cls, '_' + n, '__delete__')))
    if hasattr(cls, 'pclipdata'):
      cls._pclipdata = cls.pclipdata
      cls.pclipdata = property(lambda s: _BVUtil._padup(s._pclipdata), lambda s, v: setattr(s, '_pclipdata', v if isinstance(v, wintypes.PBYTES16) else ((ctypes.pointer(v) if isinstance(v, wintypes.BYTES16) else ctypes.cast(ctypes.c_char_p(v), wintypes.PBYTES16)))), cls._pclipdata.__delete__)
    if hasattr(cls, 'puuid'):
      cls._puuid = cls.puuid
      cls.puuid = property(lambda s: UUID(_BVUtil._padup(s._puuid)), lambda s, v: setattr(s, '_puuid', v if isinstance(v, ctypes._Pointer) and issubclass(v._type_, wintypes.GUID) else (ctypes.cast(v, wintypes.PGUID)if isinstance(v, ctypes.c_char_p) else ((ctypes.cast(ctypes.pointer(v), wintypes.PGUID) if isinstance(v, wintypes.GUID) else ctypes.cast(ctypes.c_char_p(v), wintypes.PGUID))))), cls._puuid.__delete__)
    if hasattr(cls, 'pad'):
      cls._pad = cls.pad
      cls.pad = property(lambda s: _BVUtil._adup(s._pad), lambda s, v: setattr(s, '_pad', v if isinstance(v, wintypes.BYTES16) else ctypes.cast(ctypes.c_char_p(v), wintypes.PBYTES16).contents), cls._pad.__delete__)
    if hasattr(cls, 'decVal'):
      cls._decVal = cls.decVal
      cls.decVal = property(lambda s: _BVUtil._adup(s._decVal), lambda s, v: setattr(s, '_decVal', v if isinstance(v, wintypes.BYTES16) else ctypes.cast(ctypes.c_char_p(v), wintypes.PBYTES16).contents), cls._decVal.__delete__)
    if hasattr(cls, 'pVersionedStream'):
      cls._pVersionedStream = cls.pVersionedStream
      cls.pVersionedStream = property(lambda s: s._pVersionedStream.contents.value if s._pVersionedStream else None, lambda s, v: setattr(s, '_pVersionedStream', v if isinstance(v, (PVERSIONEDSTREAM)) else (ctypes.cast(v, PVERSIONEDSTREAM) if isinstance(v, wintypes.LPVOID) else PVERSIONEDSTREAM(VERSIONEDSTREAM.from_param(v)))), cls._pVersionedStream.__delete__)
    if hasattr(cls, 'brecord'):
      cls._brecord = cls.brecord
      cls.brecord = property(lambda s: _BVUtil._brec(s), lambda s, v: setattr(s, '_brecord', BRECORD.from_param(v)), cls._brecord.__delete__)

class _BVARIANT(metaclass=_BVMeta):
  vtype_code = {'VT_EMPTY': 0, 'VT_NULL': 1, 'VT_I1': 16, 'VT_UI1': 17, 'VT_I2': 2, 'VT_UI2': 18, 'VT_I4': 3, 'VT_UI4': 19, 'VT_INT': 22, 'VT_UINT': 23, 'VT_I8': 20, 'VT_UI8': 21, 'VT_R4': 4, 'VT_R8': 5, 'VT_BOOL': 11, 'VT_ERROR': 10, 'VT_CY': 6, 'VT_DATE': 7, 'VT_FILETIME': 64, 'VT_CLSID': 72, 'VT_CF': 71, 'VT_BSTR': 8, 'VT_BLOB': 65, 'VT_BLOBOBJECT': 70, 'VT_LPSTR': 30, 'VT_LPWSTR': 31, 'VT_UNKNOWN': 13, 'VT_DISPATCH': 9, 'VT_STREAM': 66, 'VT_STREAMED_OBJECT': 68, 'VT_STORAGE': 67, 'VT_STORED_OBJECT': 69, 'VT_VERSIONED_STREAM': 73, 'VT_DECIMAL': 14, 'VT_VECTOR': 4096, 'VT_ARRAY': 8192, 'VT_BYREF': 16384, 'VT_VARIANT': 12, 'VT_RECORD': 36}
  code_vtype = {co: vt for vt, co in vtype_code.items()}
  code_ctype = {16: wintypes.CHAR, 17: wintypes.BYTE, 2: wintypes.SHORT, 18: wintypes.USHORT, 3: wintypes.LONG, 19: wintypes.ULONG, 22: wintypes.INT, 23: wintypes.UINT, 20: wintypes.LARGE_INTEGER, 21: wintypes.ULARGE_INTEGER, 4: wintypes.FLOAT, 5: wintypes.DOUBLE, 11: wintypes.VARIANT_BOOL, 10: wintypes.ULONG, 6: wintypes.LARGE_INTEGER, 7: wintypes.DOUBLE, 64: wintypes.FILETIME, 72: wintypes.PGUID, 71: wintypes.PBYTES16, 8: BSTR, 65: BLOB, 70: BLOB, 30: wintypes.LPSTR, 31: wintypes.LPWSTR, 13: PCOM, 9: PCOM, 66: PCOMSTREAM, 68: PCOMSTREAM, 67: PCOM, 69: PCOM, 73: PVERSIONEDSTREAM, 14: wintypes.BYTES16, 12: None, 36: BRECORD, 4096: CA, 8192: wintypes.LPVOID, 16384: wintypes.LPVOID}
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
      if (t := PROPVARIANT.code_ctype.get(vt)) is None:
        return None
      if (v := self.ca.content(t)) is None:
        return None
      if issubclass(t, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_wchar_p, ctypes._Pointer, _BVARIANT)):
        v._bvariant = self
      return v
    elif vt > 8192 and vt < 16384:
      if 'VT_ARRAY' not in cls.vtype_code:
        return None
      vt ^= 8192
      if (t := VARIANT.code_ctype.get(vt)) is None:
        return None
      if (v := getattr(PSAFEARRAY(wintypes.LPVOID(self.parray)), 'content', None)) is None:
        return None
      if issubclass(t, (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_wchar_p, ctypes._Pointer, _BVARIANT)):
        v._bvariant = self
      return v
    elif vt > 16384:
      vt ^= 16384
      if vt >= 8192:
        if 'VT_ARRAY' not in cls.vtype_code or (t := VARIANT.code_ctype.get(vt ^ 8192)) is None:
          return None
      elif (t := cls.code_ctype.get(vt)) is None:
        return None
      v = ctypes.cast(wintypes.LPVOID(self.byref), (ctypes.POINTER(t) if vt < 8192 else PPSAFEARRAY))
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
  def __init__(self, vtype=None, data=None, needsclear=False):
    ctypes.Structure.__init__(self)
    self._needsclear = needsclear
  def __del__(self):
    if getattr(self, '_needsclear', False):
      self.__class__._clear(ctypes.byref(self))
    getattr(self.__class__.__bases__[1], '__del__', id)(self)
  def __ctypes_from_outparam__(self):
    self._needsclear = True
    return self

class _BPBVARIANT:
  @classmethod
  def from_param(cls, obj):
    return ctypes.byref(cls._type_(13, obj)) if isinstance(obj, (IUnknown, PCOM)) else (obj if obj is None or isinstance(obj, (cls.__bases__[1], wintypes.LPVOID, ctypes.CArgObject)) else (ctypes.byref(obj) if isinstance(obj, cls._type_) or (isinstance(obj, ctypes.Array) and issubclass(obj._type_, cls._type_)) else ctypes.byref(cls._type_(*obj) or cls._type_())))

class VARIANT(_BVARIANT, ctypes.Structure):
  code_name = {20: 'llVal', 3: 'lVal', 17: 'bVal', 2: 'iVal', 4: 'fltVal', 5: 'dblVal', 11: 'boolVal', 10: 'scode', 6: 'cyVal', 7: 'date', 8: 'bstrVal', 13: 'punkVal', 9: 'pdispVal', 16: 'cVal', 18: 'uiVal', 19: 'ulVal', 21: 'ullVal', 22: 'intVal', 23: 'uintVal', 36: 'brecord', 14: 'decVal', 8192: 'parray', 16384: 'byref'}
  _vtype = VariantType
  _clear = oleauto32.VariantClear
class PVARIANT(_BPBVARIANT, ctypes.POINTER(VARIANT)):
  _type_ = VARIANT

class PROPVARIANT(_BVARIANT, ctypes.Structure):
  code_name = {16: 'cVal', 17: 'bVal', 2: 'iVal',  18: 'uiVal', 3: 'lVal', 19: 'ulVal', 22: 'intVal', 23: 'uintVal', 20: 'hVal', 21: 'uhVal', 4: 'fltVal', 5: 'dblVal', 11: 'boolVal', 10: 'scode', 6: 'cyVal', 7: 'date', 64: 'filetime', 72: 'puuid', 71: 'pclipdata', 8: 'bstrVal', 65: 'blob', 70: 'blob', 30: 'pszVal', 31: 'pwszVal', 13: 'punkVal', 9: 'pdispVal', 66: 'pStream', 68: 'pStream', 67: 'pStorage', 69: 'pStorage', 73: 'pVersionedStream', 14: 'decVal', 4096: 'ca', 8192: 'parray', 16384: 'byref'}
  _vtype = PropVariantType
  _clear = ole32.PropVariantClear
class PPROPVARIANT(_BPBVARIANT, ctypes.POINTER(PROPVARIANT)):
  _type_ = PROPVARIANT

class _PBUtil:
  @staticmethod
  def _ainit(arr, *args, needsclear=False, **kwargs):
    arr.__class__.__bases__[0].__init__(arr, *args, **kwargs)
    arr._needsclear = needsclear
  @staticmethod
  def _adel(arr):
    if getattr(arr, '_needsclear', False):
      for s in arr:
        ole32.CoTaskMemFree(wintypes.LPVOID.from_buffer(s, s.__class__.pstrName.offset))
    getattr(arr.__class__.__bases__[0], '__del__', id)(arr)

class _PBMeta(ctypes.Structure.__class__):
  _mul_cache = {}
  def __mul__(bcls, size):
    return bcls.__class__._mul_cache.get((bcls, size)) or bcls.__class__._mul_cache.setdefault((bcls, size), type('%s_Array_%d' % (bcls.__name__, size), (ctypes.Structure.__class__.__mul__(bcls, size),), {'__init__': _PBUtil._ainit, '__del__': _PBUtil._adel}))

class PROPBAG2(ctypes.Structure, metaclass=_PBMeta):
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
  def set(self, name, vtype, hint=0, ptype=0):
    vtype = VariantType.vtype_code(vtype)
    if vtype is None:
      return False
    self.dwType = ptype
    self.pstrName = wintypes.LPOLESTR(name)
    self._vt = vtype
    self.dwHint = hint
    return True
  def __init__(self, needsclear=False):
    ctypes.Structure.__init__(self)
    self._needsclear = needsclear
  def  __del__(self):
    if getattr(self, '_needsclear', False):
      ole32.CoTaskMemFree(wintypes.LPVOID.from_buffer(self, self.__class__.pstrName.offset))
    getattr(self.__class__.__bases__[0], '__del__', id)(self)
  def __ctypes_from_outparam__(self):
    self._needsclear = True
    return self
PPROPBAG2 = ctypes.POINTER(PROPBAG2)

class IPropertyBag2(IUnknown):
  IID = GUID('22f55882-280b-11d0-a8a9-00a0c90c2004')
  _protos['Read'] = 3, (wintypes.ULONG, PPROPBAG2, wintypes.LPVOID, PVARIANT, wintypes.PULONG), ()
  _protos['Write'] = 4, (wintypes.ULONG, PPROPBAG2, PVARIANT), ()
  _protos['CountProperties'] = 5, (), (wintypes.PULONG,)
  _protos['GetPropertyInfo'] = 6, (wintypes.ULONG, wintypes.ULONG, PPROPBAG2), (wintypes.PULONG,)
  _ptype = 0
  def CountProperties(self):
    return self.__class__._protos['CountProperties'](self.pI)
  def GetPropertyInfo(self, first=0, number=None):
    if number is None:
      number = self.CountProperties() - first
    propbags = (PROPBAG2 * number)(needsclear=True)
    if (n := self.__class__._protos['GetPropertyInfo'](self.pI, first, number, propbags)) is None:
      return None
    return {pb.pstrName: (pb.vt, pb.dwHint) for pb in propbags[:n]}
  def Read(self, property_infos):
    n = len(property_infos)
    propbags = (PROPBAG2 * n)()
    values = (VARIANT * n)(needsclear=True)
    results = (wintypes.ULONG * n)()
    for pb, prop in zip(propbags, property_infos.items()):
      if not (pb.set(prop[0], *prop[1], ptype=self.__class__._ptype) if isinstance(prop[1], (tuple, list)) else pb.set(prop[0], prop[1], ptype=self.__class__._ptype)):
        ISetLastError(0x80070057)
        return None
    if self.__class__._protos['Read'](self.pI, n, propbags, None, values, results) is None:
      return None
    return {pb.pstrName: ((pb.vt, pb.dwHint), val.value) for pb, val, res in zip(propbags, values, results) if res == 0}
  def Write(self, properties):
    n = len(properties)
    propbags = (PROPBAG2 * n)()
    values = (VARIANT * n)()
    for pb, val, prop in zip(propbags, values, properties.items()):
      if not (pb.set(prop[0], *prop[1][0], ptype=self.__class__._ptype) if isinstance(prop[1][0], (tuple, list)) else pb.set(prop[0], prop[1][0], ptype=self.__class__._ptype)) or not val.set(pb.vt, prop[1][1]):
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
    'JpegYCrCbSubsampling': ('VT_UI1', WICJPEGYCRCBSUBSAMPLINGOPTION, WICJPEGYCRCBSUBSAMPLINGOPTION.to_int),
    'BitmapTransform': ('VT_UI1', WICTRANSFORMOPTIONS, WICTRANSFORMOPTIONS.to_int),
    'SuppressApp0': ('VT_BOOL', None, None),
    'Luminance': ('VT_ARRAY | VT_I4', None, (lambda s: (wintypes.LONG * 64)(*s) if isinstance(s, wintypes.BYTE * 64) else s)),
    'Chrominance': ('VT_ARRAY | VT_I4', None, (lambda s: (wintypes.LONG * 64)(*s) if isinstance(s, wintypes.BYTE * 64) else s)),
    'JpegLumaDcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 12).from_buffer(s), 'CodeValues': (wintypes.BYTE * 12).from_buffer(s, 12)}, (lambda s: (wintypes.BYTE * 24)(*s['CodeCounts'], *s['CodeValues']) if isinstance(s, dict) else s)),
    'JpegLumaAcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 16).from_buffer(s), 'CodeValues': (wintypes.BYTE * 162).from_buffer(s, 16)}, (lambda s: (wintypes.BYTE * 178)(*s['CodeCounts'], *s['CodeValues']) if isinstance(s, dict) else s)),
    'JpegChromaDcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 12).from_buffer(s), 'CodeValues': (wintypes.BYTE * 12).from_buffer(s, 12)}, (lambda s: (wintypes.BYTE * 24)(*s['CodeCounts'], *s['CodeValues']) if isinstance(s, dict) else s)),
    'JpegChromaAcHuffmanTable': ('VT_ARRAY | VT_UI1', lambda s: {'CodeCounts': (wintypes.BYTE * 16).from_buffer(s), 'CodeValues': (wintypes.BYTE * 162).from_buffer(s, 16)}, (lambda s: (wintypes.BYTE * 178)(*s['CodeCounts'], *s['CodeValues']) if isinstance(s, dict) else s)),
    'InterlaceOption': ('VT_BOOL', None, None),
    'FilterOption': ('VT_UI1', WICPNGFILTEROPTION, WICPNGFILTEROPTION.to_int),
    'CompressionQuality': ('VT_R4', None, None),
    'TiffCompressionMethod': ('VT_UI1', WICTIFFCOMPRESSIONOPTION, WICTIFFCOMPRESSIONOPTION.to_int),
    'EnableV5Header32bppBGRA': ('VT_BOOL', None, None),
    'HeifCompressionMethod': ('VT_UI1', WICHEIFCOMPRESSIONOPTION, WICHEIFCOMPRESSIONOPTION.to_int),
    'Lossless': ('VT_BOOL', None, None)
  }
  @classmethod
  def __prepare__(mcls, name, bases, **kwds):
    return {n: _WICEncoderOption() for n in mcls._options}

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
      if o is None:
        props[n] = v
      else:
        props[n] = v if (o[2] is None or v is None) else o[2](v)
    return super().SetProperties(props, getattr(self, '_property_infos', None) if property_infos is None else property_infos)

class IWICEnumMetadataItem(IUnknown):
  IID = GUID(0xdc2bb46d, 0x3f07, 0x481e, 0x86, 0x25, 0x22, 0x0c, 0x4a, 0xed, 0xbb, 0x33)
  _protos['Next'] = 3, (wintypes.ULONG, PPROPVARIANT, PPROPVARIANT, PPROPVARIANT, wintypes.PULONG), ()
  _protos['Skip'] = 4, (wintypes.ULONG,), ()
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  WithType = False
  IClass = IUnknown
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    schemas = (PROPVARIANT * number)(needsclear=True)
    idents = (PROPVARIANT * number)(needsclear=True)
    values = (PROPVARIANT * number)(needsclear=True)
    if self.__class__._protos['Next'](self.pI, number, schemas, idents, values, r) is None:
      return None
    if (r := r.value) == 0:
      return ()
    return tuple((s.value, i.value, (_IUtil.QueryInterface(v.value, self.__class__.IClass, self.factory) if v.vt == 13 else v.value)) for s, i, v, _r in zip(schemas, idents, values, range(r))) if not self.__class__.WithType else tuple(((s.vt , s.value), (i.vt, i.value), (v.vt, (_IUtil.QueryInterface(v.value, self.__class__.IClass, self.factory) if v.vt == 13 else v.value))) for s, i, v, _r in zip(schemas, idents, values, range(r)))
  def Skip(self, number):
    try:
      return self.__class__._protos['Skip'](self.pI, number)
    except:
      ISetLastError(0x80070057)
      return None
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
  _protos['IsDirty'] = 4, (), (), wintypes.ULONG
  _protos['Load'] = 5, (wintypes.LPVOID,), ()
  _protos['Save'] = 6, (wintypes.LPVOID, wintypes.BOOL), ()
  _protos['GetSizeMax'] = 7, (), (wintypes.PULARGE_INTEGER,)
  def GetClassID(self):
    return self.__class__._protos['GetClassID'](self.pI)
  def IsDirty(self):
    return self.__class__._protos['IsDirty'](self.pI) != 1
  def Load(self, istream):
    return self.__class__._protos['Load'](self.pI, istream)
  def GetSizeMax(self):
    return self.__class__._protos['GetSizeMax'](self.pI)
  def Save(self, istream, clear_dirty=True):
    return self.__class__._protos['Save'](self.pI, istream, clear_dirty)

class IWICPersistStream(IPersistStream):
  IID = GUID(0x00675040, 0x6908, 0x45f8, 0x86, 0xa3, 0x49, 0xc7, 0xdf, 0xd6, 0xd9, 0xad)
  _protos['LoadEx'] = 8, (wintypes.LPVOID, WICPVENDORIDENTIFICATION, WICPERSISTOPTIONS), ()
  _protos['SaveEx'] = 9, (wintypes.LPVOID, WICPERSISTOPTIONS, wintypes.BOOL), ()
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
      return (lambda s: tuple(s) if hasattr(s, '__len__') and not isinstance(s, str) else (s,),) * 2
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
    ns = super(mcls, mcls).__prepare__(name, bases, **kwds)
    if 'Reader' in name:
      for n in mcls._queries:
        ns['Get' + n] = _WICMetadataQuery()
      ns['GetPosition'] = property(lambda s: _IWICMQRUtil._pos(s, True))
      ns['GetResolution'] = property(lambda s: _IWICMQRUtil._res(s, True))
    elif 'Writer' in name:
      for n in mcls._queries:
        ns['Set' + n] = _WICMetadataQuery()
      ns['SetPosition'] = property(lambda s: _IWICMQRUtil._pos(s, False))
      ns['SetResolution'] = property(lambda s: _IWICMQRUtil._res(s, False))
    return ns

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
    return None if self.__class__._protos['GetLocation'](self.pI, al, l) is None else l.value
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
    return _IUtil.QueryInterface(v.value, self.__class__, self.factory) if v.vt == 13 else v.value
  def GetMetadataTypeByName(self, name):
    if (v := self.__class__._protos['GetMetadataByName'](self.pI, name)) is None:
      return None
    return v.vt
  def GetMetadataWithTypeByName(self, name):
    if (v := self.__class__._protos['GetMetadataByName'](self.pI, name)) is None:
      return None
    return v.vt, (_IUtil.QueryInterface(v.value, self.__class__, self.factory) if v.vt == 13 else v.value)

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
    if (v := self.__class__._protos['GetValue'](self.pI, schema, ident)) is None:
      return None
    return _IUtil.QueryInterface(v.value, self.__class__, self.factory) if v.vt == 13 else v.value
  def GetValueByIndex(self, index):
    if (siv := self.__class__._protos['GetValueByIndex'](self.pI, index)) is None:
      return None
    return tuple(_IUtil.QueryInterface(p.value, self.__class__, self.factory) if p.vt == 13 else p.value for p in siv)
  def GetValueWithTypeByIndex(self, index):
    if (siv := self.__class__._protos['GetValueByIndex'](self.pI, index)) is None:
      return None
    return tuple((p.vt, (_IUtil.QueryInterface(p.value, self.__class__, self.factory) if p.vt == 13 else p.value)) for p in siv)
  def GetMetadataHandlerInfo(self):
    return _IUtil.QueryInterface(IWICMetadataHandlerInfo(self.__class__._protos['GetMetadataHandlerInfo'](self.pI)), IWICMetadataReaderInfo, self.factory)
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
  def GetDevelopRaw(self):
    return self.QueryInterface(IWICDevelopRaw, self.factory)
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
      pixel_formats = (WICPIXELFORMAT * planes_number)(*pixel_formats)
    planes_descriptions = (WICBITMAPPLANEDESCRIPTION * planes_number)()
    r = self.__class__._protos['DoesSupportTransform'](self.pI, w, h, transform_options, planar_option, pixel_formats, planes_descriptions, planes_number)
    return None if r is None else r, w.value, h.value, planes_descriptions.value
  def CopyPixels(self, xywh, width, height, transform_options, planar_option, planes_buffers):
    planes_number = len(planes_buffers) if planes_buffers is not None else 0
    if planes_buffers is not None and not isinstance(planes_buffers, ctypes.Array):
      planes_buffers = (WICBITMAPPLANE * planes_number)(*planes_buffers)
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
    return self.__class__._protos['GetFrameHeader'](self.pI)
  def GetAcHuffmanTable(self, scan_index, table_index):
    return self.__class__._protos['GetAcHuffmanTable'](self.pI, scan_index, table_index)
  def GetDcHuffmanTable(self, scan_index, table_index):
    return self.__class__._protos['GetDcHuffmanTable'](self.pI, scan_index, table_index)
  def GetQuantizationTable(self, scan_index, table_index):
    return self.__class__._protos['GetQuantizationTable'](self.pI, scan_index, table_index)
  def GetScanHeader(self, scan_index):
    return self.__class__._protos['GetScanHeader'](self.pI, scan_index)
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
    return self.__class__._protos['GetFormatInfo'](self.pI)
  def GetSizeInBlocks(self):
    return self.__class__._protos['GetSizeInBlocks'](self.pI)
  def CopyBlocks(self, xywh, stride, buffer):
    return self.__class__._protos['CopyBlocks'](self.pI, xywh, stride, PBUFFER.length(buffer), buffer)

class IWICDdsDecoder(IUnknown):
  IID = GUID(0x409cd537, 0x8532, 0x40cb, 0x97, 0x74, 0xe2, 0xfe, 0xb2, 0xdf, 0x4e, 0x9c)
  _protos['GetParameters'] = 3, (), (WICPDDSPARAMETERS,)
  _protos['GetFrame'] = 4, (wintypes.UINT, wintypes.UINT, wintypes.UINT), (wintypes.PLPVOID,)
  def GetParameters(self):
    return self.__class__._protos['GetParameters'](self.pI)
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

class IWICDevelopRaw(IWICBitmapFrameDecode):
  IID = GUID(0xfbec5e44, 0xf7be, 0x4b65, 0xb7, 0xf8, 0xc0, 0xc8, 0x1f, 0xef, 0x02, 0x6d)
  _protos['QueryRawCapabilitiesInfo'] = 11, (), (WICPRAWCAPABILITIESINFO,)
  _protos['LoadParameterSet'] = 12, (WICRAWPARAMETERSET,), ()
  _protos['GetCurrentParameterSet'] = 13, (), (wintypes.PLPVOID,)
  _protos['SetExposureCompensation'] = 14, (wintypes.DOUBLE,), ()
  _protos['GetExposureCompensation'] = 15, (), (wintypes.PDOUBLE,)
  _protos['SetWhitePointRGB'] = 16, (wintypes.UINT, wintypes.UINT, wintypes.UINT), ()
  _protos['GetWhitePointRGB'] = 17, (), (wintypes.PUINT, wintypes.PUINT, wintypes.PUINT)
  _protos['SetNamedWhitePoint'] = 18, (WICNAMEDWHITEPOINT,), ()
  _protos['GetNamedWhitePoint'] = 19, (), (WICPNAMEDWHITEPOINT,)
  _protos['SetWhitePointKelvin'] = 20, (wintypes.UINT,), ()
  _protos['GetWhitePointKelvin'] = 21, (), (wintypes.PUINT,)
  _protos['GetKelvinRangeInfo'] = 22, (), (wintypes.PUINT, wintypes.PUINT, wintypes.PUINT)
  _protos['SetContrast'] = 23, (wintypes.DOUBLE,), ()
  _protos['GetContrast'] = 24, (), (wintypes.PDOUBLE,)
  _protos['SetGamma'] = 25, (wintypes.DOUBLE,), ()
  _protos['GetGamma'] = 26, (), (wintypes.PDOUBLE,)
  _protos['SetSharpness'] = 27, (wintypes.DOUBLE,), ()
  _protos['GetSharpness'] = 28, (), (wintypes.PDOUBLE,)
  _protos['SetSaturation'] = 29, (wintypes.DOUBLE,), ()
  _protos['GetSaturation'] = 30, (), (wintypes.PDOUBLE,)
  _protos['SetTint'] = 31, (wintypes.DOUBLE,), ()
  _protos['GetTint'] = 32, (), (wintypes.PDOUBLE,)
  _protos['SetNoiseReduction'] = 33, (wintypes.DOUBLE,), ()
  _protos['GetNoiseReduction'] = 34, (), (wintypes.PDOUBLE,)
  _protos['SetDestinationColorContext'] = 35, (wintypes.LPVOID,), ()
  _protos['SetToneCurve'] = 36, (wintypes.UINT, wintypes.LPVOID), ()
  _protos['GetToneCurve'] = 37, (wintypes.UINT, wintypes.LPVOID), (wintypes.PUINT,)
  _protos['SetRotation'] = 38, (wintypes.DOUBLE,), ()
  _protos['GetRotation'] = 39, (), (wintypes.PDOUBLE,)
  _protos['SetRenderMode'] = 40, (WICRAWRENDERMODE,), ()
  _protos['GetRenderMode'] = 41, (), (WICPRAWRENDERMODE,)
  def QueryRawCapabilitiesInfo(self):
    return self.__class__._protos['QueryRawCapabilitiesInfo'](self.pI)
  def GetCurrentParameterSet(self):
    return IPropertyBag2(self.__class__._protos['GetCurrentParameterSet'](self.pI))
  def LoadParameterSet(self, parameter_set):
    return self.__class__._protos['LoadParameterSet'](self.pI, parameter_set)
  def GetExposureCompensation(self):
    return self.__class__._protos['GetExposureCompensation'](self.pI)
  def SetExposureCompensation(self, exposure_compensation):
    return self.__class__._protos['SetExposureCompensation'](self.pI, exposure_compensation)
  def GetContrast(self):
    return self.__class__._protos['GetContrast'](self.pI)
  def SetContrast(self, contrast):
    return self.__class__._protos['SetContrast'](self.pI, contrast)
  def GetWhitePointRGB(self):
    return self.__class__._protos['GetWhitePointRGB'](self.pI)
  def SetWhitePointRGB(self, red, green, blue):
    return self.__class__._protos['SetWhitePointRGB'](self.pI, red, green, blue)
  def GetNamedWhitePoint(self):
    return self.__class__._protos['GetNamedWhitePoint'](self.pI)
  def SetNamedWhitePoint(self, white_point):
    return self.__class__._protos['SetNamedWhitePoint'](self.pI, white_point)
  def GetWhitePointKelvin(self):
    return self.__class__._protos['GetWhitePointKelvin'](self.pI)
  def SetWhitePointKelvin(self, white_point):
    return self.__class__._protos['SetWhitePointKelvin'](self.pI, white_point)
  def GetKelvinRangeInfo(self):
    return self.__class__._protos['GetKelvinRangeInfo'](self.pI)
  def GetGamma(self):
    return self.__class__._protos['GetGamma'](self.pI)
  def SetGamma(self, gamma):
    return self.__class__._protos['SetGamma'](self.pI, gamma)
  def GetTint(self):
    return self.__class__._protos['GetTint'](self.pI)
  def SetTint(self, tint):
    return self.__class__._protos['SetTint'](self.pI, tint)
  def GetSaturation(self):
    return self.__class__._protos['GetSaturation'](self.pI)
  def SetSaturation(self, saturation):
    return self.__class__._protos['SetSaturation'](self.pI, saturation)
  def GetSharpness(self):
    return self.__class__._protos['GetSharpness'](self.pI)
  def SetSharpness(self, sharpness):
    return self.__class__._protos['SetSharpness'](self.pI, sharpness)
  def GetNoiseReduction(self):
    return self.__class__._protos['GetNoiseReduction'](self.pI)
  def SetNoiseReduction(self, noise_reduction):
    return self.__class__._protos['SetNoiseReduction'](self.pI, noise_reduction)
  def SetDestinationColorContext(self, color_context):
    return self.__class__._protos['SetDestinationColorContext'](self.pI, color_context)
  def GetToneCurve(self):
    if (al := self.__class__._protos['GetToneCurve'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ()
    c = ctypes.create_string_buffer(al)
    return None if self.__class__._protos['GetToneCurve'](self.pI, al, c) is None else WICRAWTONECURVE.from_buffer(c).value
  def SetToneCurve(self, tone_curve):
    l = len(tone_curve)
    cps = WICRAWTONECURVEPOINT * l
    al = ctypes.sizeof(WICRAWTONECURVE) + ctypes.sizeof(cps)
    c = ctypes.create_string_buffer(al)
    tc = WICRAWTONECURVE.from_buffer(c)
    tc.cPoints = l
    cps.from_address(ctypes.addressof(tc.aPoints)).__init__(*tone_curve)
    return self.__class__._protos['SetToneCurve'](self.pI, al, c)
  def GetRotation(self):
    return self.__class__._protos['GetRotation'](self.pI)
  def SetRotation(self, rotation_angle):
    return self.__class__._protos['SetRotation'](self.pI, rotation_angle)
  def GetRenderMode(self):
    return self.__class__._protos['GetRenderMode'](self.pI)
  def SetRenderMode(self, render_mode):
    return self.__class__._protos['SetRenderMode'](self.pI, render_mode)

class IWICMetadataQueryWriter(IWICMetadataQueryReader):
  IID = GUID(0xa721791a, 0x0def, 0x4d06, 0xbd, 0x91, 0x21, 0x18, 0xbf, 0x1d, 0xb1, 0x0b)
  _protos['SetMetadataByName'] = 7, (wintypes.LPCWSTR, PPROPVARIANT), ()
  _protos['RemoveMetadataByName'] = 8, (wintypes.LPCWSTR,), ()
  def SetMetadataByName(self, name, data):
    return self.__class__._protos['SetMetadataByName'](self.pI, name, data)
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
    return self.__class__._protos['SetValue'](self.pI, schema, ident, value)
  def SetValueByIndex(self, index, schema, ident, value):
    return self.__class__._protos['SetValueByIndex'](self.pI, index, schema, ident, value)
  def RemoveValue(self, schema, ident):
    return self.__class__._protos['RemoveValue'](self.pI, schema, ident)
  def RemoveValueByIndex(self, index):
    return self.__class__._protos['RemoveValueByIndex'](self.pI, index)
  def GetMetadataHandlerInfo(self):
    return _IUtil.QueryInterface(IWICMetadataHandlerInfo(self.__class__._protos['GetMetadataHandlerInfo'](self.pI)), IWICMetadataWriterInfo, self.factory)
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
    return self.__class__._protos['GetAcHuffmanTable'](self.pI, table_index, 0)
  def GetDcHuffmanTable(self, table_index):
    return self.__class__._protos['GetDcHuffmanTable'](self.pI, table_index, 0)
  def GetQuantizationTable(self, table_index):
    return self.__class__._protos['GetQuantizationTable'](self.pI, table_index, 0)
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
      planes_buffers = (WICBITMAPPLANE * planes_number)(*planes_buffers)
    return self.__class__._protos['WritePixels'](self.pI, lines_number, planes_buffers, planes_number)

class IWICDdsEncoder(IUnknown):
  IID = GUID(0x5cacdb4c, 0x407e, 0x41b3, 0xb9, 0x36, 0xd0, 0xf0, 0x10, 0xcd, 0x67, 0x32)
  _protos['SetParameters'] = 3, (WICPDDSPARAMETERS,), ()
  _protos['GetParameters'] = 4, (), (WICPDDSPARAMETERS,)
  _protos['CreateNewFrame'] = 5, (), (wintypes.PLPVOID, wintypes.PUINT, wintypes.PUINT, wintypes.PUINT)
  def GetParameters(self):
    return self.__class__._protos['GetParameters'](self.pI)
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
    return self.__class__._protos['WriteThumbnail'](self.pI, image, encoder, image_parameters)
  def WriteFrame(self, image, frame_encode, image_parameters=None):
    return self.__class__._protos['WriteFrame'](self.pI, image, frame_encode, image_parameters)
  def WriteFrameThumbnail(self, image, frame_encode, image_parameters=None):
    return self.__class__._protos['WriteFrameThumbnail'](self.pI, image, frame_encode, image_parameters)

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
      source_pixel_formats = (WICPIXELFORMAT * planes_number)(*source_pixel_formats)
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
    return (wintypes.BYTE * s_d[0]).from_address(s_d[1])

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
    return None if self.__class__._protos['GetAuthor'](self.pI, al, a) is None else a.value
  def GetVendorGUID(self):
    return self.__class__._protos['GetVendorGUID'](self.pI)
  def GetVersion(self):
    if (al := self.__class__._protos['GetVersion'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    v = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetVersion'](self.pI, al, v) is None else v.value
  def GetSpecVersion(self):
    if (al := self.__class__._protos['GetSpecVersion'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    v = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetSpecVersion'](self.pI, al, v) is None else v.value
  def GetFriendlyName(self):
    if (al := self.__class__._protos['GetFriendlyName'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    n = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetFriendlyName'](self.pI, al, n) is None else n.value

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
    return None if self.__class__._protos['GetPixelFormats'](self.pI, ac, f) is None else tuple(f[p] for p in range(ac))
  def GetDeviceManufacturer(self):
    if (al := self.__class__._protos['GetDeviceManufacturer'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceManufacturer'](self.pI, al, m) is None else m.value
  def GetDeviceModels(self):
    if (al := self.__class__._protos['GetDeviceModels'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ()
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceModels'](self.pI, al, m) is None else tuple(m.value.split(','))
  def GetMimeTypes(self):
    if (al := self.__class__._protos['GetMimeTypes'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    t = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetMimeTypes'](self.pI, al, t) is None else tuple(t.value.split(','))
  def GetFileExtensions(self):
    if (al := self.__class__._protos['GetFileExtensions'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    e = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetFileExtensions'](self.pI, al, e) is None else tuple(e.value.split(','))
  def GetColorManagementVersion(self):
    if (al := self.__class__._protos['GetColorManagementVersion'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    v = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetColorManagementVersion'](self.pI, al, v) is None else v.value
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
    return None if self.__class__._protos['GetPatterns'](self.pI, acs[1], p) is None else f.value
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
    return None if self.__class__._protos['GetPixelFormats'](self.pI, ac, f) is None else f.value
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
  _protos['GetContainerFormats'] = 12, (wintypes.UINT, WICPMETADATAHANDLER), (wintypes.PUINT,)
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
    return None if self.__class__._protos['GetContainerFormats'](self.pI, ac, f) is None else f.value
  def GetDeviceManufacturer(self):
    if (al := self.__class__._protos['GetDeviceManufacturer'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ''
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceManufacturer'](self.pI, al, m) is None else m.value
  def GetDeviceModels(self):
    if (al := self.__class__._protos['GetDeviceModels'](self.pI, 0, None)) is None:
      return None
    if al == 0:
      return ()
    m = ctypes.create_unicode_buffer(al)
    return None if self.__class__._protos['GetDeviceModels'](self.pI, al, m) is None else tuple(m.value.split(','))
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
    return None if self.__class__._protos['GetPatterns'](self.pI, container_format, acs[1], p) is None else f.value
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
    return None if self.__class__._protos['GetHeader'](self.pI, container_format, al, h) is None else f.value
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
    return IWICBitmap(self.__class__._protos['CreateBitmapFromMemory'](self.pI, width, height, pixel_format, stride, PBUFFER.length(buffer), buffer), self)
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

class DXGISAMPLEDESC(_BDStruct, ctypes.Structure):
  _fields_ = [('Count', wintypes.UINT), ('Quality', wintypes.UINT)]

class DXGISURFACEDESC(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('Format', DXGIFORMAT), ('SampleDesc', DXGISAMPLEDESC)]
DXGIPSURFACEDESC = ctypes.POINTER(DXGISURFACEDESC)

DXGIUsage = {'CPUAccessNone': 0, 'CPUAccessDynamic': 1, 'CPUAccessReadWrite': 2, 'CPUAccessScratch': 3, 'BackBuffer': 64, 'DiscardOnPresent': 512, 'ReadOnly': 256, 'RenderTargetOutput': 32, 'ShaderInput': 16, 'Shared': 128, 'UnorderedAccess': 1024}
DXGIUSAGE = type('DXGIUSAGE', (_BCodeU, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIUsage.items()}, '_tab_cn': {c: n for n, c in DXGIUsage.items()}, '_def': 0})
DXGIPUSAGE = ctypes.POINTER(DXGIUSAGE)

DXGIMapFlags = {'None': 0, 'Read': 1, 'Write': 2, 'Discard': 4}
DXGIMAPFLAGS = type('DXGIMAPFLAGS', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIMapFlags.items()}, '_tab_cn': {c: n for n, c in DXGIMapFlags.items()}, '_def': 0})

class DXGIMAPPEDRECT(ctypes.Structure):
  _fields_ = [('Pitch', wintypes.UINT), ('pBits', wintypes.LPVOID)]
DXGIPMAPPEDRECT = ctypes.POINTER(DXGIMAPPEDRECT)

DXGIScaling = {'Stretch': 0, 'None': 1, 'AspectRatioStretch': 2}
DXGISCALING = type('DXGIMAPFLAGS', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIScaling.items()}, '_tab_cn': {c: n for n, c in DXGIScaling.items()}, '_def': 0})

DXGISwapEffect = {'Discard': 0, 'Sequential': 1, 'FlipSequential': 2, 'FlipDiscard': 3}
DXGISWAPEFFECT = type('DXGISWAPEFFECT', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGISwapEffect.items()}, '_tab_cn': {c: n for n, c in DXGISwapEffect.items()}, '_def': 0})

DXGIAlphaMode = {'Unspecified': 0, 'Premultiplied': 1, 'Straight': 2, 'Ignore': 3}
DXGIALPHAMODE = type('DXGIALPHAMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in DXGIAlphaMode.items()}, '_tab_cn': {c: n for n, c in DXGIAlphaMode.items()}, '_def': 0})

class DXGISWAPCHAINDESC(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('Format', DXGIFORMAT), ('Stereo', wintypes.BOOLE), ('SampleDesc', DXGISAMPLEDESC), ('BufferUsage', DXGIUSAGE), ('BufferCount', wintypes.UINT), ('Scaling', DXGISCALING), ('SwapEffect', DXGISWAPEFFECT), ('AlphaMode', DXGIALPHAMODE), ('Flags', wintypes.UINT)]
DXGIPSWAPCHAINDESC = type('DXGIPSWAPCHAINDESC', (_BPStruct, ctypes.POINTER(DXGISWAPCHAINDESC)), {'_type_': DXGISWAPCHAINDESC})

class DXGIRATIONAL(_BTStruct, ctypes.Structure):
  _fields_ = [('Numerator', wintypes.UINT), ('Denominator', wintypes.UINT)]
  @classmethod
  def from_param(cls, obj):
    return super().from_param(tuple(_BMFraction(obj).limit()) if isinstance(obj, (int, float)) else obj)

DXGIModeScanlineOrder = {'Unspecified': 0, 'Progressive': 1, 'UpperFieldFirst': 2, 'LowerFieldFirst': 3}
DXGIMODESCANLINEORDER = type('DXGIMODESCANLINEORDER', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIModeScanlineOrder.items()}, '_tab_cn': {c: n for n, c in DXGIModeScanlineOrder.items()}, '_def': 0})

DXGIModeScaling = {'Unspecified': 0, 'Centered': 1, 'Stretched': 2}
DXGIMODESCALING = type('DXGIMODESCALING', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIModeScaling.items()}, '_tab_cn': {c: n for n, c in DXGIModeScaling.items()}, '_def': 0})

class DXGISWAPCHAINDESCFULLSCREEN(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('RefreshRate', DXGIRATIONAL), ('ScanlineOrdering', DXGIMODESCANLINEORDER), ('Scaling', DXGIMODESCALING), ('Windowed', wintypes.BOOLE)]
DXGIPSWAPCHAINDESCFULLSCREEN = type('DXGIPSWAPCHAINDESCFULLSCREEN', (_BPStruct, ctypes.POINTER(DXGISWAPCHAINDESCFULLSCREEN)), {'_type_': DXGISWAPCHAINDESCFULLSCREEN})

DXGIPresent = {'Present': 0, 'PresentTest': 0x1, 'DoNotSequence': 0x2, 'PresentRestart': 0x4, 'DoNotWait': 0x8, 'RestrictToOutput': 0x10, 'StereoPreferRight': 0x20, 'StereoTemporaryMono': 0x40, 'UseDuration': 0x100, 'AllowTearing': 2}
DXGIPRESENT = type('DXGIPRESENT', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in DXGIPresent.items()}, '_tab_cn': {c: n for n, c in DXGIPresent.items()}, '_def': 0})

RECT = _WSMeta('RECT', (_BTStruct, wintypes.RECT), {})
PRECT = type('PRECT', (_BPStruct, ctypes.POINTER(RECT)), {'_type_': RECT})
PARECT = type('ARECT', (_BPAStruct, ctypes.POINTER(RECT)), {'_type_': RECT})

POINT = _WSMeta('POINT', (_BTStruct, wintypes.POINT), {})
PPOINT = type('PPOINT', (_BPStruct, ctypes.POINTER(POINT)), {'_type_': POINT})

class DXGIPRESENTPARAMETERS(ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('DirtyRectsCount', wintypes.UINT), ('pDirtyRects', PARECT), ('pScrollRect', PRECT), ('pScrollOffset', PPOINT)]
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, dict):
      return cls(len(obj.get('pDirtyRects') or ()), *(obj.get(n) for n, t in cls._fields_[1:]))
    else:
      return cls((0 if not obj or not obj[0] else len(obj[0])), *(o for f, o in zip(cls._fields_[1:], obj)))
  def to_dict(self):
    return {'pDirtyRects': self.pDirtyRects.value(self.DirtyRectsCount), 'pScrollRect': self.pScrollRect.value, 'pScrollOffset': self.pScrollOffset.value}
  @property
  def value(self):
    return self.to_dict()
DXGIPPRESENTPARAMETERS = type('DXGIPPRESENTPARAMETERS', (_BPStruct, ctypes.POINTER(DXGIPRESENTPARAMETERS)), {'_type_': DXGIPRESENTPARAMETERS})

class DXGIRGBA(_BTStruct, ctypes.Structure):
  _fields_ = [('r', wintypes.FLOAT), ('g', wintypes.FLOAT), ('b', wintypes.FLOAT), ('a', wintypes.FLOAT)]
DXGIPRGBA = type('DXGIPRGBA', (_BPStruct, ctypes.POINTER(DXGIRGBA)), {'_type_': DXGIRGBA})

class DXGIMODEDESC(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('RefreshRate', DXGIRATIONAL), ('Format', DXGIFORMAT), ('ScanlineOrdering', DXGIMODESCANLINEORDER), ('Scaling', DXGIMODESCALING)]
DXGIPMODEDESC = type('DXGIPMODEDESC', (_BPStruct, ctypes.POINTER(DXGIMODEDESC)), {'_type_': DXGIMODEDESC})

class IDXGIObject(IUnknown):
  _lightweight = True
  IID = GUID(0xaec22fb8, 0x76f3, 0x4639, 0x9b, 0xe0, 0x28, 0xeb, 0x43, 0xa6, 0x7a, 0x2e)
  _protos['GetParent'] = 6, (PUUID,), (wintypes.PLPVOID,)
  def __new__(cls, clsid_component=False, factory=None):
    self = IUnknown.__new__(cls, clsid_component, factory)
    if cls not in (IDXGIObject, IDXGIFactory) and self is not None and factory is None:
      parent = self.GetParent()
      if parent is not None:
        self.factory = parent if isinstance(parent, IDXGIFactory) else parent.factory
    return self
  def GetParent(self, interface):
    return interface(self._protos['GetParent'](self.pI, interface.IID), self.factory)
  def GetFactory(self):
    return self.factory

class IDXGIAdapter(IDXGIObject):
  IID = GUID(0x0aa1ae0a, 0xfa0e, 0x4b84, 0x86, 0x44, 0xe0, 0x5f, 0xf8, 0xe5, 0xac, 0xb5)
  def GetParent(self):
    return super().GetParent(IDXGIFactory)
IDXGIAdapter2 = IDXGIAdapter

class IDXGIDevice(IDXGIObject):
  IID = GUID(0x05008617, 0xfbfd, 0x4051, 0xa7, 0x90, 0x14, 0x48, 0x84, 0xb4, 0xf6, 0xa9)
  _protos['SetGPUThreadPriority'] = 10, (wintypes.INT,), ()
  _protos['GetGPUThreadPriority'] = 11, (), (wintypes.PINT,)
  _protos['SetMaximumFrameLatency'] = 12, (wintypes.UINT,), ()
  _protos['GetMaximumFrameLatency'] = 13, (), (wintypes.PUINT,)
  def GetParent(self):
    return super().GetParent(IDXGIAdapter)
  def GetAdapter(self):
    return self.GetParent()
  def GetMaximumFrameLatency(self):
    return self._protos['GetMaximumFrameLatency'](self.pI)
  def SetMaximumFrameLatency(self, max_latency):
    return self._protos['SetMaximumFrameLatency'](self.pI, max_latency)
  def GetGPUThreadPriority(self):
    return self._protos['GetGPUThreadPriority'](self.pI)
  def SetGPUThreadPriority(self, priority):
    return self._protos['SetGPUThreadPriority'](self.pI, priority)
IDXGIDevice2 = IDXGIDevice

class IDXGIDeviceSubObject(IDXGIObject):
  IID = GUID(0x3d3e0379, 0xf9de, 0x4d58, 0xbb, 0x6c, 0x18, 0xd6, 0x29, 0x92, 0xf1, 0xa6)
  _protos['GetDevice'] = 7, (PUUID,), (wintypes.PLPVOID,)
  def GetDevice(self):
    return IDXGIDevice(self._protos['GetDevice'](self.pI, IDXGIDevice.IID), self.factory)
  def GetParent(self):
    return self.GetDevice()

class IDXGIResource(IDXGIDeviceSubObject):
  IID = GUID(0x30961379, 0x4609, 0x4a41, 0x99, 0x8e, 0x54, 0xfe, 0x56, 0x7e, 0xe0, 0xc1)
  _protos['GetUsage'] = 9, (), (DXGIPUSAGE,)
  def GetUsage(self):
    return self._protos['GetUsage'](self.pI)
IDXGIResource1 = IDXGIResource

class IDXGISurface(IDXGIDeviceSubObject):
  IID = GUID(0xaba496dd, 0xb617, 0x4cb8, 0xa8, 0x66, 0xbc, 0x44, 0xd7, 0xeb, 0x1f, 0xa2)
  _protos['GetDesc'] = 8, (), (DXGIPSURFACEDESC,)
  _protos['Map'] = 9, (DXGIPMAPPEDRECT, DXGIMAPFLAGS), ()
  _protos['Unmap'] = 10, (), ()
  _protos['GetResource'] = 13, (PUUID,), (wintypes.PLPVOID, wintypes.PUINT)
  def GetDesc(self):
    return self._protos['GetDesc'](self.pI)
  def GetFormat(self):
    if (d := self.GetDesc()) is None:
      return None
    return d.get('Format')
  def GetResource(self):
    return None if (r_i := self._protos['GetResource'](self.pI, IDXGIResource.IID)) is None else IDXGIResource(r_i[0], self.factory)
  def GetUsage(self):
    return None if (r := self.GetResource()) is None else r.GetUsage()
  def Map(self, map_flags):
    if (d := self.GetDesc()) is None:
      return None
    mr = DXGIMAPPEDRECT()
    return None if self._protos['Map'](self.pI, mr, map_flags) is None else ((wintypes.BYTE * mr.Pitch) * d['Height']).from_address(mr.pBits)
  def Unmap(self):
    return self._protos['Unmap'](self.pI)
IDXGISurface2 = IDXGISurface

class IDXGIOutput(IDXGIObject):
  IID = GUID(0x00cddea8, 0x939b, 0x4b83, 0xa3, 0x40, 0xa6, 0x85, 0x22, 0x66, 0x66, 0xcc)
  def GetParent(self):
    return super().GetParent(IDXGIAdapter)
IDXGIOutput1 = IDXGIOutput

class IDXGISwapChain(IDXGIDeviceSubObject):
  IID = GUID(0x790a45f7, 0x0d42, 0x4876, 0x98, 0x3a, 0x0a, 0x55, 0xcf, 0xe6, 0xf4, 0xaa)
  _protos['GetBuffer'] = 9, (wintypes.UINT, PUUID), (wintypes.PLPVOID,)
  _protos['SetFullscreenState'] = 10, (wintypes.BOOLE, wintypes.LPVOID), ()
  _protos['GetFullscreenState'] = 11, (), (wintypes.PBOOLE, wintypes.PLPVOID)
  _protos['ResizeBuffers'] = 13, (wintypes.UINT, wintypes.UINT, wintypes.UINT, DXGIFORMAT, wintypes.UINT), ()
  _protos['ResizeTarget'] = 14, (DXGIPMODEDESC,), ()
  _protos['GetContainingOutput'] = 15, (), (wintypes.PLPVOID,)
  _protos['GetDesc1'] = 18, (), (DXGIPSWAPCHAINDESC,)
  _protos['GetFullscreenDesc'] = 19, (), (DXGIPSWAPCHAINDESCFULLSCREEN,)
  _protos['GetHwnd'] = 20, (), (wintypes.PHWND,)
  _protos['Present1'] = 22, (wintypes.UINT, DXGIPRESENT, DXGIPPRESENTPARAMETERS), ()
  _protos['SetBackgroundColor'] = 25, (DXGIPRGBA,), ()
  _protos['GetBackgroundColor'] = 26, (), (DXGIPRGBA,)
  def GetDesc(self):
    return self._protos['GetDesc1'](self.pI)
  GetDesc1 = GetDesc
  def GetFullscreenDesc(self):
    return self._protos['GetFullscreenDesc'](self.pI)
  def GetHwnd(self):
    return self._protos['GetHwnd'](self.pI)
  def GetBuffer(self, index, interface):
    return interface(self._protos['GetBuffer'](self.pI, index, interface.IID), self.factory)
  def GetTexture2D(self, index=0):
    return self.GetBuffer(index, ID3D11Texture2D)
  def GetSurface(self, index=0):
    return self.GetBuffer(index, IDXGISurface)
  def Present(self, sync_interval=1, flags=0, parameters=((), None, None)):
    return self._protos['Present1'](self.pI, sync_interval, flags, parameters)
  def GetBackgroundColor(self):
    return self._protos['GetBackgroundColor'](self.pI)
  def SetBackgroundColor(self, background_color=(0, 0, 0, 0)):
    return self._protos['SetBackgroundColor'](self.pI, background_color)
  def GetContainingOutput(self):
    return IDXGIOutput(self._protos['GetContainingOutput'](self.pI), self.factory)
  def GetFullscreenState(self):
    if (f_o := self._protos['GetFullscreenState'](self.pI)) is None:
      return None
    return f_o[0], IDXGIOutput(f_o[1], self.factory)
  def SetFullscreenState(self, fullscreen, output=None):
    return self._protos['SetFullscreenState'](self.pI, fullscreen, output)
  def ResizeTarget(self, parameters):
    return self._protos['ResizeTarget'](self.pI, parameters)
  def ResizeTargetWindow(self, width, height):
    return self.ResizeTarget({'Width': width, 'Height': height})
  def ResizeBuffers(self, buffer_count=0, width=0, height=0, dxgi_format=0, flags=0):
    return self._protos['ResizeBuffers'](self.pI, buffer_count, width, height, dxgi_format, flags)
  Present1 = Present
IDXGISwapChain1 = IDXGISwapChain

class IDXGIFactory(IDXGIObject):
  IID = GUID(0x50c83a1c, 0xe072, 0x4c48, 0x87, 0xb0, 0x36, 0x30, 0xfa, 0x36, 0xa6, 0xd0)
  _protos['CreateSwapChainForHwnd'] = 15, (wintypes.LPVOID, wintypes.HWND, DXGIPSWAPCHAINDESC, DXGIPSWAPCHAINDESCFULLSCREEN, wintypes.LPVOID), (wintypes.PLPVOID,)
  def CreateSwapChainForHwnd(self, device, hwnd, description, fullscreen_description=None, output=None):
    if isinstance(device, IDXGIDevice):
      if (device := device.QueryInterface(ID3D11Device)) is None:
        return None
    return IDXGISwapChain(self._protos['CreateSwapChainForHwnd'](self.pI, device, hwnd, description, fullscreen_description, output), self)
IDXGIFactory2 = IDXGIFactory

D3D11ResourceDimension = {'Unknown': 0, 'Buffer': 1, 'Texture1D': 2, 'Texture2D': 3, 'Texture3D': 4}
D3D11RESOURCEDIMENSION = type('D3D11RESOURCEDIMENSION', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D3D11ResourceDimension.items()}, '_tab_cn': {c: n for n, c in D3D11ResourceDimension.items()}, '_def': 0})
D3D11PRESOURCEDIMENSION = ctypes.POINTER(D3D11RESOURCEDIMENSION)

D3D11Usage = {'Default': 0, 'Immutable': 1, 'Dynamic': 2, 'Staging': 3}
D3D11USAGE = type('D3D11USAGE', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D3D11Usage.items()}, '_tab_cn': {c: n for n, c in D3D11Usage.items()}, '_def': 0})

D3D11BindFlag = {'None': 0, 'No': 0, 'VertexBuffer': 0x1, 'IndexBuffer': 0x2, 'ConstantBuffer': 0x4, 'ShaderResource': 0x8, 'StreamOutput': 0x10, 'RenderTarget': 0x20, 'DepthStencil': 0x40, 'UnorderedAccess': 0x80, 'Decoder': 0x200, 'VideoEncoder': 0x400}
D3D11BINDFLAG = type('D3D11BINDFLAG', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D3D11BindFlag.items()}, '_tab_cn': {c: n for n, c in D3D11BindFlag.items()}, '_def': 0})

D3D11CPUAccessFlag = {'None': 0, 'No': 0, 'Write': 0x10000, 'Read': 0x20000}
D3D11CPUACCESSFLAG = type('D3D11CPUACCESSFLAG', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D3D11CPUAccessFlag.items()}, '_tab_cn': {c: n for n, c in D3D11CPUAccessFlag.items()}, '_def': 0})

D3D11ResourceMiscFlag = {'None': 0, 'No': 0, 'GenerateMips': 0x1, 'Shared': 0x2, 'TextureCube': 0x4, 'DrawIndirectArgs': 0x10, 'BufferAllowRawViews': 0x20, 'BufferStructured': 0x40, 'ResourceClamp': 0x80, 'SharedKeyedMutex': 0x100, 'GDICompatible': 0x200, 'SharedNTHandle': 0x800, 'RestrictedContent': 0x1000, 'RestrictSharedResource': 0x2000, 'RestrictSharedResourceDriver': 0x4000, 'Guarded': 0x8000, 'TilePool': 0x20000, 'Tiled': 0x40000, 'HWProtected': 0x40000}
D3D11RESOURCEMISCFLAG = type('D3D11RESOURCEMISCFLAG', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D3D11ResourceMiscFlag.items()}, '_tab_cn': {c: n for n, c in D3D11ResourceMiscFlag.items()}, '_def': 0})

class D3D11TEXTURE2DDESC(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('Width', wintypes.UINT), ('Height', wintypes.UINT), ('MipLevels', wintypes.UINT), ('ArraySize', wintypes.UINT), ('Format', DXGIFORMAT), ('SampleDesc', DXGISAMPLEDESC), ('Usage', D3D11USAGE), ('BindFlags', D3D11BINDFLAG), ('CPUAccessFlags', D3D11CPUACCESSFLAG), ('MiscFlags', D3D11RESOURCEMISCFLAG)]
D3D11PTEXTURE2DDESC = type('D3D11PTEXTURE2DDESC', (_BPStruct, ctypes.POINTER(D3D11TEXTURE2DDESC)), {'_type_': D3D11TEXTURE2DDESC})

class D3D11SUBRESOURCEDATA(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('pSysMem', PBUFFER), ('SysMemPitch', wintypes.UINT), ('SysMemSlicePitch', wintypes.UINT)]
D3D11PASUBRESOURCEDATA = type('D3D11PASUBRESOURCEDATA', (_BPAStruct, ctypes.POINTER(D3D11SUBRESOURCEDATA)), {'_type_': D3D11SUBRESOURCEDATA})

D3D11FeatureLevel = {'1.0_Generic': 0x100, '1.0_Core': 0x1000, '9.1': 0x9100, '9.2': 0x9200, '9.3': 0x9300, '10.0': 0xa000, '10.1': 0xa100, '11.0': 0xb000, '11.1': 0xb100, '12.0': 0xc000, '12.1': 0xc100, '12.2': 0xc200}
D3D11FEATURELEVEL = type('D3D11FEATURELEVEL', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D3D11FeatureLevel.items()}, '_tab_cn': {c: n for n, c in D3D11FeatureLevel.items()}, '_def': 0xb100})
D3D11PFEATURELEVEL = ctypes.POINTER(D3D11FEATURELEVEL)

class ID3D11DeviceChild(IUnknown):
  _lightweight = True
  IID = GUID(0x1841e5c8, 0x16b0, 0x489b, 0xbc, 0xc8, 0x44, 0xcf, 0xb0, 0xd5, 0xde, 0xae)
  _protos['GetDevice'] = 3, (), (wintypes.PLPVOID,), None
  def GetDevice(self):
    return ID3D11Device(self._protos['GetDevice'](self.pI), self.factory)

class ID3D11Resource(ID3D11DeviceChild):
  IID = GUID(0xdc8e63f3, 0xd12b, 0x4952, 0xb4, 0x7b, 0x5e, 0x45, 0x02, 0x6a, 0x86, 0x2d)
  _protos['GetType'] = 7, (), (D3D11PRESOURCEDIMENSION,), None
  def GetType(self):
    return self._protos['GetType'](self.pI)

class ID3D11Texture2D(ID3D11Resource):
  IID = GUID(0x6f15aaf2, 0xd208, 0x4e89, 0x9a, 0xb4, 0x48, 0x95, 0x35, 0xd3, 0x4f, 0x9c)
  _protos['GetDesc'] = 10, (), (D3D11PTEXTURE2DDESC,)
  def GetDesc(self):
    return self._protos['GetDesc'](self.pI)
  def GetSurface(self):
    return self.QueryInterface(IDXGISurface, False)

class ID3D11Device(IUnknown):
  _lightweight = True
  IID = GUID(0xdb6f6ddb, 0xac77, 0x4e88, 0x82, 0x53, 0x81, 0x9d, 0xf9, 0xbb, 0xf1, 0x40)
  _protos['CreateTexture2D'] = 5, (D3D11PTEXTURE2DDESC, D3D11PASUBRESOURCEDATA), (wintypes.PLPVOID,)
  _protos['GetFeatureLevel'] = 37, (), (), D3D11FEATURELEVEL
  def __new__(cls, clsid_component=False, factory=None):
    if isinstance(clsid_component, str):
      if (driver_type := clsid_component.lower()) in ('software', 'hardware'):
        driver_type = wintypes.DWORD(5 if driver_type == 'software' else 1)
        clsid_component = False
    else:
      driver_type = wintypes.DWORD(1)
    if clsid_component is False:
      pI = wintypes.LPVOID()
      if ISetLastError(d3d11.D3D11CreateDevice(None, driver_type, None, wintypes.DWORD(0x20 if getattr(_IUtil._local, 'multithreaded', False) else 0x21), ctypes.byref((wintypes.UINT * 7)(*map(D3D11FEATURELEVEL.name_code, ('11.1', '11.0', '10.1', '10.0', '9.3', '9.2', '9.1')))), wintypes.UINT(7), wintypes.UINT(7), ctypes.byref(pI), None, None)):
        if ISetLastError(d3d11.D3D11CreateDevice(None, driver_type, None, wintypes.DWORD(0x20 if getattr(_IUtil._local, 'multithreaded', False) else 0x21), None, wintypes.UINT(0), wintypes.UINT(7), ctypes.byref(pI), None, None)):
          return None
    else:
      pI = clsid_component
    return IUnknown.__new__(cls, pI, factory)
  def GetFeatureLevel(self):
    return self._protos['GetFeatureLevel'](self.pI)
  def CreateTexture2D(self, texture_desc, initial_data=None):
    return ID3D11Texture2D(self._protos['CreateTexture2D'](self.pI, texture_desc, initial_data), self)
  def CreateDXGISurface(self, width, height, format, sample_count=1, sample_quality=0, usage=0, bind_flags=0, cpu_flags=0, misc_flags=0, source_data=None, source_pitch=0):
    if (t2d := self.CreateTexture2D((width, height, 1, 1, format, (sample_count, sample_quality), usage, bind_flags, cpu_flags, misc_flags), ((source_data, source_pitch, 0),))) is None:
      return None
    return t2d.GetSurface()
  def CreateTargetDXGISurface(self, width, height, format, sample_count=1, sample_quality=0, drawable=False):
    return self.CreateDXGISurface(width, height, format, sample_count, sample_quality, bind_flags=('RenderTarget | ShaderResource' if drawable else 'RenderTarget'))
  def GetDXGIDevice(self):
    return self.QueryInterface(IDXGIDevice, False)

D2D1ColorSpace = {'Custom': 0, 'sRGB': 1, 'scRGB': 2}
D2D1COLORSPACE = type('D2D1COLORSPACE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1ColorSpace.items()}, '_tab_cn': {c: n for n, c in D2D1ColorSpace.items()}, '_def': 1})

class ID2D1Resource(IUnknown):
  _lightweight = True
  IID = GUID(0x2cd90691, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['GetFactory'] = 3, (), (wintypes.PLPVOID,), None
  def GetFactory(self):
    return ID2D1Factory(self._protos['GetFactory'](self.pI))

class ID2D1Image(ID2D1Resource):
  IID = GUID(0x65019f75, 0x8da2, 0x497c, 0xb3, 0x2c, 0xdf, 0xa3, 0x4e, 0x48, 0xed, 0xe6)

class ID2D1ColorContext(ID2D1Resource):
  IID = GUID(0x1c4820bb, 0x5771, 0x4518, 0xa5, 0x81, 0x2f, 0xe4, 0xdd, 0x0e, 0xc6, 0x57)
  _protos['GetColorSpace'] = 4, (), (), D2D1COLORSPACE
  _protos['GetProfileSize'] = 5, (), (), wintypes.UINT
  _protos['GetProfile'] = 6, (PBUFFER, wintypes.UINT), ()
  def GetColorSpace(self):
    return self._protos['GetColorSpace'](self.pI)
  def GetProfileBytes(self):
    if not (al := self.__class__._protos['GetProfileSize'](self.pI)):
      return bytearray()
    b = bytearray(al)
    return None if self.__class__._protos['GetProfile'](self.pI, b, al) is None else b

class PCOMD2D1COLORCONTEXT(PCOM):
  icls = ID2D1ColorContext

class D2D1SIZEU(_BTStruct, ctypes.Structure):
  _fields_ = [('width', wintypes.UINT), ('height', wintypes.UINT)]
D2D1PSIZEU = type('D2D1PSIZEU', (_BPStruct, ctypes.POINTER(D2D1SIZEU)), {'_type_': D2D1SIZEU})

class D2D1SIZEF(_BTStruct, ctypes.Structure):
  _fields_ = [('width', wintypes.FLOAT), ('height', wintypes.FLOAT)]
D2D1PSIZEF = type('D2D1PSIZEF', (_BPStruct, ctypes.POINTER(D2D1SIZEF)), {'_type_': D2D1SIZEF})

class D2D1POINT2U(_BTStruct, ctypes.Structure):
  _fields_ = [('x', wintypes.UINT), ('y', wintypes.UINT)]
D2D1PPOINT2U = type('D2D1PPOINT2U', (_BPStruct, ctypes.POINTER(D2D1POINT2U)), {'_type_': D2D1POINT2U})

class D2D1POINT2F(_BTStruct, ctypes.Structure):
  _fields_ = [('x', wintypes.FLOAT), ('y', wintypes.FLOAT)]
  def __getitem__(self, key):
    if key == 1:
      return self.x
    elif key == 2:
      return self.y
    elif key == 3:
      return 1
    else:
      raise IndexError('index out of range')
  def __setitem__(arr, key, value):
    if key == 1:
      self.x = value
    elif key == 2:
      self.y = value
    else:
      raise IndexError('index out of range')
D2D1PPOINT2F = type('D2D1PPOINT2F', (_BPStruct, ctypes.POINTER(D2D1POINT2F)), {'_type_': D2D1POINT2F})

class D2D1MATRIX3X2F(wintypes.FLOAT * 6):
  @classmethod
  def from_param(cls, obj):
    return obj if isinstance(obj, D2D1MATRIX3X2F.__bases__[0]) else D2D1MATRIX3X2F.__bases__[0](*obj)
  def __init__(self, *args):
    super().__init__(*((1, 0, 0, 1, 0, 0) if not args else (args[0] if len(args) == 1 else args)))
  def __getitem__(self, key):
    if isinstance(key, tuple):
      r, c = key
      if r < 0 or r > 3 or c < 0 or c > 3:
        raise IndexError('invalid index')
      return (1 if r == 3 else 0) if c == 3 else super().__getitem__(2 * r + c - 3)
    else:
      return super().__getitem__(key)
  def __setitem__(self, key, value):
    if isinstance(key, tuple):
      r, c = key
      if r < 0 or r > 3 or c < 0 or c > 2:
        raise IndexError('invalid index')
      super().__setitem__(2 * r + c - 3, value)
    else:
      super().__setitem__(key, value)
  def __matmul__(self, other):
    return D2D1MATRIX3X2F(sum(self[r, i] * other[i, c] for i in range(1, 4)) for r in range(1, 4) for c in range(1, 3))
  def __rmatmul__(self, other):
    return D2D1POINT2F(*(sum(other[r] * self[r, c] for r in range(1, 4)) for c in range(1, 3))) if isinstance(other, D2D1POINT2F) else other.__matmul__(self)
  def __imatmul__(self, other):
    self.__init__(*(self @ other))
    return self
  def __invert__(self):
    m = D2D1MATRIX3X2F(self)
    if not ID2D1Factory.InvertMatrix(m):
      raise ZeroDivisionError('matrix not invertible')
    return m
  def __eq__(self, other):
    return all(self[i] == other[i] for i in range(6))
class D2D1PMATRIX3X2F(ctypes.POINTER(D2D1MATRIX3X2F)):
  _type_ = D2D1MATRIX3X2F
  @classmethod
  def from_param(cls, obj):
    return obj if obj is None or isinstance(obj, (ctypes._Pointer, wintypes.LPVOID, ctypes.CArgObject)) else ctypes.byref(D2D1MATRIX3X2F.from_param(obj))

class D2D1MATRIX4X4F(wintypes.FLOAT * 16):
  @classmethod
  def from_param(cls, obj):
    return obj if isinstance(obj, D2D1MATRIX4X4F.__bases__[0]) else D2D1MATRIX4X4F.__bases__[0](*obj)
  def __init__(self, *args):
    super().__init__(*((1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1) if not args else (args[0] if len(args) == 1 else args)))
  def __getitem__(self, key):
    if isinstance(key, tuple):
      r, c = key
      if r < 0 or r > 4 or c < 0 or c > 4:
        raise IndexError('invalid index')
      return super().__getitem__(4 * r + c - 5)
    else:
      return super().__getitem__(key)
  def __setitem__(self, key, value):
    if isinstance(key, tuple):
      r, c = key
      if r < 0 or r > 4 or c < 0 or c > 4:
        raise IndexError('invalid index')
      super().__setitem__(4 * r + c - 5, value)
    else:
      super().__setitem__(key, value)
  def __matmul__(self, other):
    return D2D1MATRIX4X4F(sum(self[r, i] * other[i, c] for i in range(1, 5)) for r in range(1, 5) for c in range(1, 5))
  def __rmatmul__(self, other):
    return other.__matmul__(self)
  def __imatmul__(self, other):
    self.__init__(*(self @ other))
    return self
  def __eq__(self, other):
    return all(self[i] == other[i] for i in range(16))
class D2D1PMATRIX4X4F(ctypes.POINTER(D2D1MATRIX4X4F)):
  _type_ = D2D1MATRIX4X4F
  @classmethod
  def from_param(cls, obj):
    return obj if obj is None or isinstance(obj, (ctypes._Pointer, wintypes.LPVOID, ctypes.CArgObject)) else ctypes.byref(D2D1MATRIX4X4F.from_param(obj))

class D2D1RECTU(_BTStruct, ctypes.Structure):
  _fields_ = [('left', wintypes.UINT), ('top', wintypes.UINT), ('right', wintypes.UINT), ('bottom', wintypes.UINT)]
D2D1PRECTU = type('D2D1PRECTU', (_BPStruct, ctypes.POINTER(D2D1RECTU)), {'_type_': D2D1RECTU})

class D2D1RECTF(_BTStruct, ctypes.Structure):
  _fields_ = [('left', wintypes.FLOAT), ('top', wintypes.FLOAT), ('right', wintypes.FLOAT), ('bottom', wintypes.FLOAT)]
D2D1PRECTF = type('D2D1PRECTF', (_BPStruct, ctypes.POINTER(D2D1RECTF)), {'_type_': D2D1RECTF})

class D2D1ROUNDEDRECT(_BTStruct, ctypes.Structure):
  _fields_ = [('rect', D2D1RECTF), ('radiusX', wintypes.FLOAT), ('radiusY', wintypes.FLOAT)]
D2D1PROUNDEDRECT = type('D2D1PROUNDEDRECT', (_BPStruct, ctypes.POINTER(D2D1ROUNDEDRECT)), {'_type_': D2D1ROUNDEDRECT})

class D2D1ELLIPSE(_BTStruct, ctypes.Structure):
  _fields_ = [('point', D2D1POINT2F), ('radiusX', wintypes.FLOAT), ('radiusY', wintypes.FLOAT)]
D2D1PELLIPSE = type('D2D1PELLIPSE', (_BPStruct, ctypes.POINTER(D2D1ELLIPSE)), {'_type_': D2D1ELLIPSE})

class D2D1COLORF(_BTStruct, ctypes.Structure):
  _fields_ = [('r', wintypes.FLOAT), ('g', wintypes.FLOAT), ('b', wintypes.FLOAT), ('a', wintypes.FLOAT)]
D2D1PCOLORF = type('D2D1PCOLORF', (_BPStruct, ctypes.POINTER(D2D1COLORF)), {'_type_': D2D1COLORF})

D2D1BitmapInterpolationMode = {'NearestNeighbor': 0, 'Linear': 1, 'Cubic': 2, 'MultiSampleLinear': 3, 'Anisotropic': 4, 'HighQualityCubic': 5}
D2D1BITMAPINTERPOLATIONMODE = type('D2D1BITMAPINTERPOLATIONMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1BitmapInterpolationMode.items()}, '_tab_cn': {c: n for n, c in D2D1BitmapInterpolationMode.items()}, '_def': 0})

D2D1InterpolationMode = {'NearestNeighbor': 0, 'Linear': 1, 'Cubic': 2, 'MultiSampleLinear': 3, 'Anisotropic': 4, 'HighQualityCubic': 5}
D2D1INTERPOLATIONMODE = type('D2D1INTERPOLATIONMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1InterpolationMode.items()}, '_tab_cn': {c: n for n, c in D2D1InterpolationMode.items()}, '_def': 0})

D2D1AntialiasMode = {'PerPrimitive': 0, 'Aliased': 1}
D2D1ANTIALIASMODE = type('D2D1ANTIALIASMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1AntialiasMode.items()}, '_tab_cn': {c: n for n, c in D2D1AntialiasMode.items()}, '_def': 0})

D2D1PrimitiveBlend = {'SourceOver': 0, 'Copy': 1, 'Min': 2, 'Add': 3, 'Max': 4}
D2D1PRIMITIVEBLEND = type('D2D1PRIMITIVEBLEND', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1PrimitiveBlend.items()}, '_tab_cn': {c: n for n, c in D2D1PrimitiveBlend.items()}, '_def': 0})

D2D1UnitMode = {'DIPs': 0, 'Pixels': 1}
D2D1UNITMODE = type('D2D1UNITMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1UnitMode.items()}, '_tab_cn': {c: n for n, c in D2D1UnitMode.items()}, '_def': 0})

D2D1ExtendMode = {'Clamp': 0, 'Wrap': 1, 'Mirror': 2}
D2D1EXTENDMODE = type('D2D1EXTENDMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1ExtendMode.items()}, '_tab_cn': {c: n for n, c in D2D1ExtendMode.items()}, '_def': 0})

D2D1BufferPrecision = {'Unknown': 0, '8BPC_UNORM': 1, '8BPC_UNORM_SRGB': 2, '16BPC_UNORM': 3, '16BPC_FLOAT': 4, '32BPC_FLOAT': 5}
D2D1BUFFERPRECISION = type('D2D1BUFFERPRECISION', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1BufferPrecision.items()}, '_tab_cn': {c: n for n, c in D2D1BufferPrecision.items()}, '_def': 0})

class D2D1RENDERINGCONTROLS(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('bufferPrecision', D2D1BUFFERPRECISION), ('tileSize', D2D1SIZEU)]
D2D1PRENDERINGCONTROLS = type('D2D1PRENDERINGCONTROLS', (_BPStruct, ctypes.POINTER(D2D1RENDERINGCONTROLS)), {'_type_': D2D1RENDERINGCONTROLS})

class D2D1BITMAPPROPERTIESRT(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('pixelFormat', D2D1PIXELFORMAT), ('dpiX', wintypes.FLOAT), ('dpiY', wintypes.FLOAT)]
D2D1PBITMAPPROPERTIESRT = type('D2D1PBITMAPPROPERTIESRT', (_BPStruct, ctypes.POINTER(D2D1BITMAPPROPERTIESRT)), {'_type_': D2D1BITMAPPROPERTIESRT})

D2D1BitmapOptions = {'None': 0, 'Target': 1, 'CannotDraw': 2, 'CPURead': 4, 'GDICompatible': 8}
D2D1BITMAPOPTIONS = type('D2D1BITMAPOPTIONS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1BitmapOptions.items()}, '_tab_cn': {c: n for n, c in D2D1BitmapOptions.items()}, '_def': 0})

class D2D1BITMAPPROPERTIESDC(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('pixelFormat', D2D1PIXELFORMAT), ('dpiX', wintypes.FLOAT), ('dpiY', wintypes.FLOAT), ('bitmapOptions', D2D1BITMAPOPTIONS), ('colorContext', PCOMD2D1COLORCONTEXT)]
  def __del__(self):
    if getattr(self, '_needsclear', False):
      if (i := self.colorContext) is not None:
        i.Release()
  def __ctypes_from_outparam__(self):
    self._needsclear = True
    return super().__ctypes_from_outparam__()
D2D1PBITMAPPROPERTIESDC = type('D2D1PBITMAPPROPERTIESDC', (_BPStruct, ctypes.POINTER(D2D1BITMAPPROPERTIESDC)), {'_type_': D2D1BITMAPPROPERTIESDC})

class D2D1BITMAPBRUSHPROPERTIESRT(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('extendModeX', D2D1EXTENDMODE), ('extendModeY', D2D1EXTENDMODE), ('interpolationMode', D2D1BITMAPINTERPOLATIONMODE)]
D2D1PBITMAPBRUSHPROPERTIESRT = type('D2D1PBITMAPBRUSHPROPERTIESRT', (_BPStruct, ctypes.POINTER(D2D1BITMAPBRUSHPROPERTIESRT)), {'_type_': D2D1BITMAPBRUSHPROPERTIESRT})

class D2D1BITMAPBRUSHPROPERTIESDC(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('extendModeX', D2D1EXTENDMODE), ('extendModeY', D2D1EXTENDMODE), ('interpolationMode', D2D1INTERPOLATIONMODE)]
D2D1PBITMAPBRUSHPROPERTIESDC = type('D2D1PBITMAPBRUSHPROPERTIESDC', (_BPStruct, ctypes.POINTER(D2D1BITMAPBRUSHPROPERTIESDC)), {'_type_': D2D1BITMAPBRUSHPROPERTIESDC})

class D2D1IMAGEBRUSHPROPERTIES(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('sourceRectangle', D2D1RECTF), ('extendModeX', D2D1EXTENDMODE), ('extendModeY', D2D1EXTENDMODE), ('interpolationMode', D2D1INTERPOLATIONMODE)]
D2D1PIMAGEBRUSHPROPERTIES = type('D2D1PIMAGEBRUSHPROPERTIES', (_BPStruct, ctypes.POINTER(D2D1IMAGEBRUSHPROPERTIES)), {'_type_': D2D1IMAGEBRUSHPROPERTIES})

class D2D1BRUSHPROPERTIES(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('opacity', wintypes.FLOAT), ('transform', D2D1MATRIX3X2F)]
D2D1PBRUSHPROPERTIES = type('D2D1PBRUSHPROPERTIES', (_BPStruct, ctypes.POINTER(D2D1BRUSHPROPERTIES)), {'_type_': D2D1BRUSHPROPERTIES})

class D2D1GRADIENTSTOP(_BTStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('position', wintypes.FLOAT), ('color', D2D1COLORF)]
D2D1PAGRADIENTSTOP = type('D2D1PAGRADIENTSTOP', (_BPAStruct, ctypes.POINTER(D2D1GRADIENTSTOP)), {'_type_': D2D1GRADIENTSTOP})

D2D1Gamma = {'sRGB': 0, '2.2': 0, 'Linear': 1, '1.0': 1}
D2D1GAMMA = type('D2D1GAMMA', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1Gamma.items()}, '_tab_cn': {c: n for n, c in D2D1Gamma.items()}, '_def': 0})

D2D1ColorInterpolationMode = {'Straight': 0, 'Premultiplied': 1}
D2D1COLORINTERPOLATIONMODE = type('D2D1COLORINTERPOLATIONMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1ColorInterpolationMode.items()}, '_tab_cn': {c: n for n, c in D2D1ColorInterpolationMode.items()}, '_def': 0})

class D2D1LINEARGRADIENTBRUSHPROPERTIES(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('startPoint', D2D1POINT2F), ('endPoint', D2D1POINT2F)]
D2D1PLINEARGRADIENTBRUSHPROPERTIES = type('D2D1PLINEARGRADIENTBRUSHPROPERTIES', (_BPStruct, ctypes.POINTER(D2D1LINEARGRADIENTBRUSHPROPERTIES)), {'_type_': D2D1LINEARGRADIENTBRUSHPROPERTIES})

class D2D1RADIALGRADIENTBRUSHPROPERTIES(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('center', D2D1POINT2F), ('gradientOriginOffset', D2D1POINT2F), ('radiusX', wintypes.FLOAT), ('radiusY', wintypes.FLOAT)]
D2D1PRADIALGRADIENTBRUSHPROPERTIES = type('D2D1PRADIALGRADIENTBRUSHPROPERTIES', (_BPStruct, ctypes.POINTER(D2D1RADIALGRADIENTBRUSHPROPERTIES)), {'_type_': D2D1RADIALGRADIENTBRUSHPROPERTIES})

D2D1CapStyle = {'Flat': 0, 'Square': 1, 'Round': 2, 'Triangle': 3}
D2D1CAPSTYLE = type('D2D1CAPSTYLE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1CapStyle.items()}, '_tab_cn': {c: n for n, c in D2D1CapStyle.items()}, '_def': 0})

D2D1DashStyle = {'Solid': 0, 'Dash': 1, 'Dot': 2, 'DashDot': 3, 'DashDotDot': 4, 'Custom': 5}
D2D1DASHSTYLE = type('D2D1DASHSTYLE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1DashStyle.items()}, '_tab_cn': {c: n for n, c in D2D1DashStyle.items()}, '_def': 0})

D2D1LineJoin = {'Miter': 0, 'Bevel': 1, 'Round': 2, 'MiterOrBevel': 3}
D2D1LINEJOIN = type('D2D1LINEJOIN', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1LineJoin.items()}, '_tab_cn': {c: n for n, c in D2D1LineJoin.items()}, '_def': 0})

D2D1StrokeTransformType = {'Normal': 0, 'Fixed': 1, 'HairLine': 2}
D2D1STROKETRANSFORMTYPE = type('D2D1STROKETRANSFORMTYPE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1StrokeTransformType.items()}, '_tab_cn': {c: n for n, c in D2D1StrokeTransformType.items()}, '_def': 0})

class D2D1STROKESTYLEPROPERTIES(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('startCap', D2D1CAPSTYLE), ('endCap', D2D1CAPSTYLE), ('dashCap', D2D1CAPSTYLE), ('lineJoin', D2D1LINEJOIN), ('miterLimit', wintypes.FLOAT), ('dashStyle', D2D1DASHSTYLE), ('dashOffset', wintypes.FLOAT), ('transformType', D2D1STROKETRANSFORMTYPE)]
D2D1PSTROKESTYLEPROPERTIES = type('D2D1PSTROKESTYLEPROPERTIES', (_BPStruct, ctypes.POINTER(D2D1STROKESTYLEPROPERTIES)), {'_type_': D2D1STROKESTYLEPROPERTIES})

D2D1MappedOptions = {'None': 0, 'Read': 1, 'Write': 2, 'Discard': 4}
D2D1MAPPEDOPTIONS = type('D2D1MAPPEDOPTIONS', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D2D1MappedOptions.items()}, '_tab_cn': {c: n for n, c in D2D1MappedOptions.items()}, '_def': 1})

class D2D1MAPPEDRECT(ctypes.Structure):
  _fields_ = [('pitch', wintypes.UINT), ('bits', wintypes.LPVOID)]
D2D1PMAPPEDRECT = ctypes.POINTER(D2D1MAPPEDRECT)

class D2D1DRAWINGSTATEDESCRIPTION(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('antialiasMode', D2D1ANTIALIASMODE), ('textAntialiasMode', wintypes.DWORD), ('tag1', wintypes.ULARGE_INTEGER), ('tag2', wintypes.ULARGE_INTEGER), ('transform', D2D1MATRIX3X2F), ('primitiveBlend', D2D1PRIMITIVEBLEND), ('unitMode', D2D1UNITMODE)]
D2D1PDRAWINGSTATEDESCRIPTION = type('D2D1PDRAWINGSTATEDESCRIPTION', (_BPStruct, ctypes.POINTER(D2D1DRAWINGSTATEDESCRIPTION)), {'_type_': D2D1DRAWINGSTATEDESCRIPTION})

D2D1PropertyType = {'Unknown': 0, 'String': 1, 'Bool': 2, 'UInt': 3, 'UInt32': 3, 'Int': 4, 'Int32': 4, 'Float': 5, 'Vector2': 6, 'Vector3': 7, 'Vector4': 8, 'Blob': 9, 'IUnknown': 10, 'Enum': 11, 'Array': 12, 'Clsid': 13, 'Matrix3x2': 14, 'Matrix4x3': 15, 'Matrix4x4': 16, 'Matrix5x4': 17, 'ColorContext': 18}
D2D1PROPERTYTYPE = type('D2D1PROPERTYTYPE', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in D2D1PropertyType.items()}, '_tab_cn': {c: n for n, c in D2D1PropertyType.items()}, '_def': 0})

D2D1EffectId = {
  'LookupTable3D': GUID(0x349e0eda, 0x0088, 0x4a79, 0x9c, 0xa3, 0xc7, 0xe3, 0x00, 0x20, 0x20, 0x20),
  'ColorManagement': GUID(0x1a28524c, 0xfdd6, 0x4aa4, 0xae, 0x8f, 0x83, 0x7e, 0xb8, 0x26, 0x7b, 0x37),
  'ColorMatrix': GUID(0x921f03d6, 0x641c, 0x47df, 0x85, 0x2d, 0xb4, 0xbb, 0x61, 0x53, 0xae, 0x11),
  'DiscreteTransfer': GUID(0x90866fcd, 0x488e, 0x454b, 0xaf, 0x06, 0xe5, 0x04, 0x1b, 0x66, 0xc3, 0x6c),
  'DpiCompensation': GUID(0x6c26c5c7, 0x34e0, 0x46fc, 0x9c, 0xfd, 0xe5, 0x82, 0x37, 0x06, 0xe2, 0x28),
  'GammaTransfer': GUID(0x409444c4, 0xc419, 0x41a0, 0xb0, 0xc1, 0x8c, 0xd0, 0xc0, 0xa1, 0x8e, 0x42),
  'HdrToneMap': GUID(0x7b0b748d, 0x4610, 0x4486, 0xa9, 0x0c, 0x99, 0x9d, 0x9a, 0x2e, 0x2b, 0x11),
  'HueToRgb': GUID(0x7b78a6bd, 0x0141, 0x4def, 0x8a, 0x52, 0x63, 0x56, 0xee, 0x0c, 0xbd, 0xd5),
  'HueRotation': GUID(0x0f4458ec, 0x4b32, 0x491b, 0x9e, 0x85, 0xbd, 0x73, 0xf4, 0x4d, 0x3e, 0xb6),
  'LinearTransfer': GUID(0xad47c8fd, 0x63ef, 0x4acc, 0x9b, 0x51, 0x67, 0x97, 0x9c, 0x03, 0x6c, 0x06),
  'OpacityMetadata': GUID(0x6c53006a, 0x4450, 0x4199, 0xaa, 0x5b, 0xad, 0x16, 0x56, 0xfe, 0xce, 0x5e),
  'Premultiply': GUID(0x06eab419, 0xdeed, 0x4018, 0x80, 0xd2, 0x3e, 0x1d, 0x47, 0x1a, 0xde, 0xb2),
  'RgbToHue': GUID(0x23f3e5ec, 0x91e8, 0x4d3d, 0xad, 0x0a, 0xaf, 0xad, 0xc1, 0x00, 0x4a, 0xa1),
  'Saturation': GUID(0x5cb2d9cf, 0x327d, 0x459f, 0xa0, 0xce, 0x40, 0xc0, 0xb2, 0x08, 0x6b, 0xf7),
  'TableTransfer': GUID(0x5bf818c3, 0x5e43, 0x48cb, 0xb6, 0x31, 0x86, 0x83, 0x96, 0xd6, 0xa1, 0xd4),
  'Tint': GUID(0x36312b17, 0xf7dd, 0x4014, 0x91, 0x5d, 0xff, 0xca, 0x76, 0x8c, 0xf2, 0x11),
  'UnPremultiply': GUID(0xfb9ac489, 0xad8d, 0x41ed, 0x99, 0x99, 0xbb, 0x63, 0x47, 0xd1, 0x10, 0xf7),
  'WhiteLevelAdjustment': GUID(0x44a1cadb, 0x6cdd, 0x4818, 0x8f, 0xf4, 0x26, 0xc1, 0xcf, 0xe9, 0x5b, 0xdb),
  'YCbCr': GUID(0x99503cc1, 0x66c7, 0x45c9, 0xa8, 0x75, 0x8a, 0xd8, 0xa7, 0x91, 0x44, 0x01),
  'AlphaMask': GUID(0xc80ecff0, 0x3fd5, 0x4f05, 0x83, 0x28, 0xc5, 0xd1, 0x72, 0x4b, 0x4f, 0x0a),
  'ArithmeticComposite': GUID(0xfc151437, 0x049a, 0x4784, 0xa2, 0x4a, 0xf1, 0xc4, 0xda, 0xf2, 0x09, 0x87),
  'Blend': GUID(0x81c5b77b, 0x13f8, 0x4cdd, 0xad, 0x20, 0xc8, 0x90, 0x54, 0x7a, 0xc6, 0x5d),
  'Composite': GUID(0x48fc9f51, 0xf6ac, 0x48f1, 0x8b, 0x58, 0x3b, 0x28, 0xac, 0x46, 0xf7, 0x6d),
  'CrossFade': GUID(0x12f575e8, 0x4db1, 0x485f, 0x9a, 0x84, 0x03, 0xa0, 0x7d, 0xd3, 0x82, 0x9f),
  'ConvolveMatrix': GUID(0x407f8c08, 0x5533, 0x4331, 0xa3, 0x41, 0x23, 0xcc, 0x38, 0x77, 0x84, 0x3e),
  'DirectionalBlur': GUID(0x174319a6, 0x58e9, 0x49b2, 0xbb, 0x63, 0xca, 0xf2, 0xc8, 0x11, 0xa3, 0xdb),
  'DirectionalBlurKernel': GUID(0x58eb6e2a, 0xd779, 0x4b7d, 0xad, 0x39, 0x6f, 0x5a, 0x9f, 0xc9, 0xd2, 0x88),
  'EdgeDetection': GUID(0xeff583ca, 0xcb07, 0x4aa9, 0xac, 0x5d, 0x2c, 0xc4, 0x4c, 0x76, 0x46, 0x0f),
  'GaussianBlur': GUID(0x1feb6d69, 0x2fe6, 0x4ac9, 0x8c, 0x58, 0x1d, 0x7f, 0x93, 0xe7, 0xa6, 0xa5),
  'Morphology': GUID(0xeae6c40d, 0x626a, 0x4c2d, 0xbf, 0xcb, 0x39, 0x10, 0x01, 0xab, 0xe2, 0x02),
  'DisplacementMap': GUID(0xedc48364, 0x0417, 0x4111, 0x94, 0x50, 0x43, 0x84, 0x5f, 0xa9, 0xf8, 0x90),
  'DistantDiffuse': GUID(0x3e7efd62, 0xa32d, 0x46d4, 0xa8, 0x3c, 0x52, 0x78, 0x88, 0x9a, 0xc9, 0x54),
  'DistantSpecular': GUID(0x428c1ee5, 0x77b8, 0x4450, 0x8a, 0xb5, 0x72, 0x21, 0x9c, 0x21, 0xab, 0xda),
  'Emboss': GUID(0xb1c5eb2b, 0x0348, 0x43f0, 0x81, 0x07, 0x49, 0x57, 0xca, 0xcb, 0xa2, 0xae),
  'PointDiffuse': GUID(0xb9e303c3, 0xc08c, 0x4f91, 0x8b, 0x7b, 0x38, 0x65, 0x6b, 0xc4, 0x8c, 0x20),
  'PointSpecular': GUID(0x09c3ca26, 0x3ae2, 0x4f09, 0x9e, 0xbc, 0xed, 0x38, 0x65, 0xd5, 0x3f, 0x22),
  'Posterize': GUID(0x2188945e, 0x33a3, 0x4366, 0xb7, 0xbc, 0x08, 0x6b, 0xd0, 0x2d, 0x08, 0x84),
  'Shadow': GUID(0xc67ea361, 0x1863, 0x4e69, 0x89, 0xdb, 0x69, 0x5d, 0x3e, 0x9a, 0x5b, 0x6b),
  'SpotDiffuse': GUID(0x818a1105, 0x7932, 0x44f4, 0xaa, 0x86, 0x08, 0xae, 0x7b, 0x2f, 0x2c, 0x93),
  'SpotSpecular': GUID(0xedae421e, 0x7654, 0x4a37, 0x9d, 0xb8, 0x71, 0xac, 0xc1, 0xbe, 0xb3, 0xc1),
  'Brightness': GUID(0x8cea8d1e, 0x77b0, 0x4986, 0xb3, 0xb9, 0x2f, 0x0c, 0x0e, 0xae, 0x78, 0x87),
  'Contrast': GUID(0xb648a78a, 0x0ed5, 0x4f80, 0xa9, 0x4a, 0x8e, 0x82, 0x5a, 0xca, 0x6b, 0x77),
  'Exposure': GUID(0xb56c8cfa, 0xf634, 0x41ee, 0xbe, 0xe0, 0xff, 0xa6, 0x17, 0x10, 0x60, 0x04),
  'Grayscale': GUID(0x36dde0eb, 0x3725, 0x42e0, 0x83, 0x6d, 0x52, 0xfb, 0x20, 0xae, 0xe6, 0x44),
  'HighlightsShadows': GUID(0xcadc8384, 0x323f, 0x4c7e, 0xa3, 0x61, 0x2e, 0x2b, 0x24, 0xdf, 0x6e, 0xe4),
  'Histogram': GUID(0x881db7d0, 0xf7ee, 0x4d4d, 0xa6, 0xd2, 0x46, 0x97, 0xac, 0xc6, 0x6e, 0xe8),
  'Invert': GUID(0xe0c3784d, 0xcb39, 0x4e84, 0xb6, 0xfd, 0x6b, 0x72, 0xf0, 0x81, 0x02, 0x63),
  'Sepia': GUID(0x3a1af410, 0x5f1d, 0x4dbe, 0x84, 0xdf, 0x91, 0x5d, 0xa7, 0x9b, 0x71, 0x53),
  'Sharpen': GUID(0xc9b887cb, 0xc5ff, 0x4dc5, 0x97, 0x79, 0x27, 0x3d, 0xcf, 0x41, 0x7c, 0x7d),
  'Straighten': GUID(0x4da47b12, 0x79a3, 0x4fb0, 0x82, 0x37, 0xbb, 0xc3, 0xb2, 0xa4, 0xde, 0x08),
  'TemperatureTint': GUID(0x89176087, 0x8af9, 0x4a08, 0xae, 0xb1, 0x89, 0x5f, 0x38, 0xdb, 0x17, 0x66),
  'Vignette': GUID(0xc00c40be, 0x5e67, 0x4ca3, 0x95, 0xb4, 0xf4, 0xb0, 0x2c, 0x11, 0x51, 0x35),
  'BitmapSource': GUID(0x5fb6c24d, 0xc6dd, 0x4231, 0x94, 0x04, 0x50, 0xf4, 0xd5, 0xc3, 0x25, 0x2d),
  'Flood': GUID(0x61c23c20, 0xae69, 0x4d8e, 0x94, 0xcf, 0x50, 0x07, 0x8d, 0xf6, 0x38, 0xf2),
  'Turbulence': GUID(0xcf2bb6ae, 0x889a, 0x4ad7, 0xba, 0x29, 0xa2, 0xfd, 0x73, 0x2c, 0x9f, 0xc9),
  '2DAffineTransform': GUID(0x6aa97485, 0x6354, 0x4cfc, 0x90, 0x8c, 0xe4, 0xa7, 0x4f, 0x62, 0xc9, 0x6c),
  '3DTransform': GUID(0xe8467b04, 0xec61, 0x4b8a, 0xb5, 0xde, 0xd4, 0xd7, 0x3d, 0xeb, 0xea, 0x5a),
  '3DPerspectiveTransform': GUID(0xc2844d0b, 0x3d86, 0x46e7, 0x85, 0xba, 0x52, 0x6c, 0x92, 0x40, 0xf3, 0xfb),
  'Atlas': GUID(0x913e2be4, 0xfdcf, 0x4fe2, 0xa5, 0xf0, 0x24, 0x54, 0xf1, 0x4f, 0xf4, 0x8),
  'Border': GUID(0x2a2d49c0, 0x4acf, 0x43c7, 0x8c, 0x6a, 0x7c, 0x4a, 0x27, 0x87, 0x4d, 0x27),
  'Crop': GUID(0xe23f7110, 0x0e9a, 0x4324, 0xaf, 0x47, 0x6a, 0x2c, 0x0c, 0x46, 0xf3, 0x5b),
  'Scale': GUID(0x9daf9369, 0x3846, 0x4d0e, 0xa4, 0x4e, 0x0c, 0x60, 0x79, 0x34, 0xa5, 0xd7),
  'Tile': GUID(0xb0784138, 0x3b76, 0x4bc5, 0xb1, 0x3b, 0x0f, 0xa2, 0xad, 0x02, 0x65, 0x9f),
  'ChromaKey': GUID(0x74c01f5b, 0x2a0d, 0x408c, 0x88, 0xe2, 0xc7, 0xa3, 0xc7, 0x19, 0x77, 0x42),
  'LuminanceToAlpha': GUID(0x41251ab7, 0x0beb, 0x46f8, 0x9d, 0xa7, 0x59, 0xe9, 0x3f, 0xcc, 0xe5, 0xde),
  'Opacity': GUID(0x811d79a4, 0xde28, 0x4454, 0x80, 0x94, 0xc6, 0x46, 0x85, 0xf8, 0xbd, 0x4c)
}
D2D1EFFECTID = _GMeta('D2D1EFFECTID', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {n.lower(): g for n, g in D2D1EffectId.items()}, '_tab_gn': {g: n for n, g in D2D1EffectId.items()}, '_def': None})
D2D1PEFFECTID = type('D2D1PEFFECTID', (_BPGUID, ctypes.POINTER(D2D1EFFECTID)), {'_type_': D2D1EFFECTID})

D2D1CompositeMode = {'SourceOver': 0, 'DestinationOver': 1, 'SourceIn': 2, 'DestinationIn': 3, 'SourceOut': 4, 'DestinationOut': 5, 'SourceAtop': 6, 'DestinationAtop': 7, 'XOr': 8, 'Plus': 9, 'SourceCopy': 10, 'BoundedSourceCopy': 11, 'MaskInvert': 12}
D2D1COMPOSITEMODE = type('D2D1COMPOSITEMODE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1CompositeMode.items()}, '_tab_cn': {c: n for n, c in D2D1CompositeMode.items()}, '_def': 0})

D2D1DeviceContextOptions = {'None': 0, 'Multithreaded': 1}
D2D1DEVICECONTEXTOPTIONS = type('D2D1DEVICECONTEXTOPTIONS', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1DeviceContextOptions.items()}, '_tab_cn': {c: n for n, c in D2D1DeviceContextOptions.items()}, '_def': 0})

D2D1RenderTargetType = {'Default': 0, 'Software': 1, 'Hardware': 2}
D2D1RENDERTARGETTYPE = type('D2D1RENDERTARGETTYPE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1RenderTargetType.items()}, '_tab_cn': {c: n for n, c in D2D1RenderTargetType.items()}, '_def': 0})

D2D1RenderTargetUsage = {'None': 0, 'ForceBitmapRemoting': 1, 'GDICompatible': 2}
D2D1RENDERTARGETUSAGE = type('D2D1RENDERTARGETUSAGE', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1RenderTargetUsage.items()}, '_tab_cn': {c: n for n, c in D2D1RenderTargetUsage.items()}, '_def': 0})

D2D1FeatureLevel = {'Default': 0, '9': 1, '10': 2}
D2D1FEATURELEVEL = type('D2D1FEATURELEVEL', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1FeatureLevel.items()}, '_tab_cn': {c: n for n, c in D2D1FeatureLevel.items()}, '_def': 0})

class D2D1RENDERTARGETPROPERTIES(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('type', D2D1RENDERTARGETTYPE), ('pixelFormat', D2D1PIXELFORMAT), ('dpiX', wintypes.FLOAT), ('dpiY', wintypes.FLOAT), ('usage', D2D1RENDERTARGETUSAGE), ('minLevel', D2D1FEATURELEVEL)]
D2D1PRENDERTARGETPROPERTIES = type('D2D1PRENDERTARGETPROPERTIES', (_BPStruct, ctypes.POINTER(D2D1RENDERTARGETPROPERTIES)), {'_type_': D2D1RENDERTARGETPROPERTIES})

D2D1CompatibleRenderTargetOptions = {'None': 0, 'GDICompatible': 1}
D2D1COMPATIBLERENDERTARGETOPTIONS = type('D2D1COMPATIBLERENDERTARGETOPTIONS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1CompatibleRenderTargetOptions.items()}, '_tab_cn': {c: n for n, c in D2D1CompatibleRenderTargetOptions.items()}, '_def': 0})

D2D1PresentOptions = {'None': 0, 'RetainContents': 1, 'Immediately': 2}
D2D1PRESENTOPTIONS = type('D2D1PRESENTOPTIONS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1PresentOptions.items()}, '_tab_cn': {c: n for n, c in D2D1PresentOptions.items()}, '_def': 0})

class D2D1HWNDRENDERTARGETPROPERTIES(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('hwnd', wintypes.HWND), ('pixelSize', D2D1SIZEU), ('presentOptions', D2D1PRESENTOPTIONS)]
D2D1PHWNDRENDERTARGETPROPERTIES = type('D2D1PHWNDRENDERTARGETPROPERTIES', (_BPStruct, ctypes.POINTER(D2D1HWNDRENDERTARGETPROPERTIES)), {'_type_': D2D1HWNDRENDERTARGETPROPERTIES})

D2D1WindowState = {'None': 0, 'Occluded': 1}
D2D1WINDOWSTATE = type('D2D1WINDOWSTATE', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in D2D1WindowState.items()}, '_tab_cn': {c: n for n, c in D2D1WindowState.items()}, '_def': 0})

class ID2D1Bitmap(ID2D1Image):
  IID = GUID(0xa898a84c, 0x3873, 0x4588, 0xb0, 0x8b, 0xeb, 0xbf, 0x97, 0x8d, 0xf0, 0x41)
  _protos['GetSize'] = 4, (), (D2D1PSIZEF,), None
  _protos['GetPixelSize'] = 5, (), (D2D1PSIZEU,), None
  _protos['GetPixelFormat'] = 6, (), (D2D1PPIXELFORMAT,), None
  _protos['GetDpi'] = 7, (), (wintypes.PFLOAT, wintypes.PFLOAT), None
  _protos['CopyFromBitmap'] = 8, (D2D1PPOINT2U, wintypes.LPVOID, D2D1PRECTU), ()
  _protos['CopyFromRenderTarget'] = 9, (D2D1PPOINT2U, wintypes.LPVOID, D2D1PRECTU), ()
  _protos['CopyFromMemory'] = 10, (D2D1PRECTU, PBUFFER, wintypes.UINT), ()
  _protos['GetColorContext'] = 11, (), (wintypes.PLPVOID,), None
  _protos['GetOptions'] = 12, (), (), D2D1BITMAPOPTIONS
  _protos['GetSurface'] = 13, (), (wintypes.PLPVOID,)
  _protos['Map'] = 14, (D2D1MAPPEDOPTIONS,), (D2D1PMAPPEDRECT,)
  _protos['Unmap'] = 15, (), ()
  def GetSize(self):
    return self._protos['GetSize'](self.pI)
  def GetPixelSize(self):
    return self._protos['GetPixelSize'](self.pI)
  def GetPixelFormat(self):
    return self._protos['GetPixelFormat'](self.pI)
  def GetDpi(self):
    return self._protos['GetDpi'](self.pI)
  def GetColorContext(self):
    return ID2D1ColorContext(self._protos['GetColorContext'](self.pI), self.factory)
  def GetOptions(self):
    return self._protos['GetOptions'](self.pI)
  def CopyFromBitmap(self, bitmap, destination_xy=None, source_ltrb=None):
    return self._protos['CopyFromBitmap'](self.pI, destination_xy, bitmap, source_ltrb)
  def CopyFromRenderTarget(self, render_target, destination_xy=None, source_ltrb=None):
    return self._protos['CopyFromRenderTarget'](self.pI, destination_xy, render_target, source_ltrb)
  def CopyFromMemory(self, source_data, source_pitch, destination_ltrb=None):
    return self._protos['CopyFromMemory'](self.pI, destination_ltrb, source_data, source_pitch)
  def GetSurface(self):
    return IDXGISurface(self._protos['GetSurface'](self.pI))
  def Map(self, map_options):
    if (s := self.GetPixelSize()) is None:
      return None
    return None if (mr := self._protos['Map'](self.pI, map_options)) is None else ((wintypes.BYTE * mr.pitch) * s[1]).from_address(mr.bits)
  def Unmap(self):
    return self._protos['Unmap'](self.pI)
ID2D1Bitmap1 = ID2D1Bitmap

class _ID2D1PUtil:
  _BFloatArray = type('_BFloatArray', (), {'__init__': lambda self, *args: self.__class__.__bases__[1].__init__(self, *(args[0] if len(args) == 1 else args))})
  VEC2F = type('VEC2F', (_BFloatArray, wintypes.FLOAT * 2), {'value': property(tuple)})
  VEC3F = type('VEC3F', (_BFloatArray, wintypes.FLOAT * 3), {'value': property(tuple)})
  VEC4F = type('VEC4F', (_BFloatArray, wintypes.FLOAT * 4), {'value': property(tuple)})
  MATRIX4X3F = type('MATRIX4X3F', (_BFloatArray, wintypes.FLOAT * 12), {})
  MATRIX5X4F = type('MATRIX5X4F', (_BFloatArray, wintypes.FLOAT * 20), {})
  _types = (None, wintypes.WCHAR, wintypes.BOOLE, wintypes.UINT, wintypes.INT, wintypes.FLOAT, VEC2F, VEC3F, VEC4F, wintypes.CHAR, PCOM, wintypes.UINT, wintypes.UINT, UUID, D2D1MATRIX3X2F, MATRIX4X3F, D2D1MATRIX4X4F, MATRIX5X4F, PCOMD2D1COLORCONTEXT)
  D2D1PSystemRange = range(0x80000000, 0x8000000a)
  @classmethod
  def _sizeof(cls, data_type):
    return None if int(data_type) in (0, 1, 9) else ctypes.sizeof(cls._types[data_type])
  @classmethod
  def _to_value(cls, data_type, data_buffer, data_size):
    if not data_type or not data_buffer:
      return None
    if data_type == 1:
      t = wintypes.WCHAR * (data_size // ctypes.sizeof(wintypes.WCHAR))
    elif data_type == 9:
      t = wintypes.CHAR * (data_size // ctypes.sizeof(wintypes.CHAR))
    else:
      t = cls._types[data_type]
    v = t.from_buffer(data_buffer)
    return v.raw if data_type in (9, 10, 18) else getattr(v, 'value', v)
  @classmethod
  def _from_value(cls, data_type, value):
    if not data_type:
      return None
    if isinstance(value, ctypes._CData):
      v = value
    elif data_type == 1:
      v = ctypes.create_unicode_buffer(value)
    elif data_type == 9:
      v = ctypes.create_string_buffer(value, len(value))
    else:
      v = cls._types[data_type](value)
    return v, ctypes.sizeof(v)
  @staticmethod
  def _get_base_index(properties, name):
    b = properties
    i = None
    for na in name.split('.'):
      if i is not None and (b := b.GetSubProperties(i)) is None:
        return None
      if (i := b.GetPropertyIndex(na)) is None:
        return None
    return b, i
  @classmethod
  def _get_item(cls, properties, key=True):
    if key is None or isinstance(key, str):
      return _D2D1PropertySet(_D2D1Property(properties, key))
    if not isinstance(key, bool) and isinstance(key, int):
      try:
        n = properties.GetPropertyCount()
        return _D2D1PropertySet(_D2D1Property(properties, range(n)[key]))
      except:
        return _D2D1PropertySet(_D2D1Property(properties, key))
    if properties is None:
      return _D2D1PropertySet()
    n = properties.GetPropertyCount()
    g = []
    sr = cls.D2D1PSystemRange
    for k in (key if isinstance(key, (tuple, list)) else (key,)):
      if isinstance(k, bool):
        g = (range(n), sr) if k else (range(n),)
        break
      if isinstance(k, str):
        g.append((k,))
      elif isinstance(k, int):
        try:
          g.append((range(n)[k],))
        except:
          g.append((k,))
      else:
        try:
          g.append(range(n)[k])
          if (k.start is not None and k.start >= sr.start) or (k.stop is not None and k.stop >= sr.start):
            ste = 1 if k.step is None else k.step
            if ste >= 0:
              sta = sr.start if k.start is None else min(max(k.start, sr.start), sr.stop)
              sto = sr.stop if k.stop is None else min(max(k.stop, sr.start), sr.stop)
            else:
              sta = sr.stop - 1 if k.start is None else min(max(k.start, sr.start - 1), sr.stop - 1)
              sto = sr.start - 1 if k.stop is None else min(max(k.stop, sr.start - 1), sr.stop - 1)
            g.append(range(sta, sto, ste))
        except:
          pass
    return _D2D1PropertySet(tuple(_D2D1Property(properties, k) for r in g for k in r))

class _D2D1PEnumValue(int):
  def __new__(cls, code=None, label=None, name=None):
    if code is None or label is None or name is None:
      return None
    self = int.__new__(cls, code)
    self.label = label
    self.name = name
    return self
  def __init__(self, code=None, key=None, name=None):
    super().__init__()
  @property
  def code(self):
    return int(self)
  @property
  def key(self):
    return self.label
  def __eq__(self, other):
    return (self.code == other.code and self.label == other.label and self.name == other.name) if isinstance(other, _D2D1PEnumValue) else (self.code == other if isinstance(other, int) else (other.lower() in (self.label.lower(), self.name.lower()) if isinstance(other, str) else False))
  def __str__(self):
    return '<%d: %s [%s]>' % (self.code, self.label, self.name)
  def __repr__(self):
    return str(self)

class _D2D1PropertySet:
  def __init__(self, keys=None, values=None):
    self._keys = () if keys is None else keys
    self._values = self._keys if values is None else values
    self._mul = isinstance(self._keys, (tuple, list))
  def GetIndex(self):
    return tuple(p.GetIndex() for p in self._values) if self._mul else self._values.GetIndex()
  def GetName(self):
    return tuple(p.GetName() for p in self._values) if self._mul else self._values.GetName()
  def GetType(self):
    return tuple(p.GetType() for p in self._values) if self._mul else self._values.GetType()
  def GetValue(self, property_type=0, data_size=0):
    return tuple(p.GetValue(property_type, data_size) for p in self._values) if self._mul else self._values.GetValue(property_type, data_size)
  def GetSubs(self):
    return tuple(p.GetSubs() for p in self._values) if self._mul else self._values.GetSubs()
  GetSubProperties = GetSubs
  def SetValue(self, data, property_type=0):
    if self._mul:
      g = (p.SetValue(d, property_type) for p, d in zip(self._values, data))
      return tuple(next(g, None) for p in self._values)
    else:
      return self._values.SetValue(data, property_type)
  def __getitem__(self, key):
    return _D2D1PropertySet(self._keys, (tuple(p.__getitem__(key) for p in self._values) if self._mul else self._values.__getitem__(key)))
  def __iter__(self):
    return iter((na, p) for na, p in zip((p.GetName() for p in (self._keys if self._mul else (self._keys,))), (self._values if self._mul else (self._values,))) if na)
  def __len__(self):
    return sum(1 for e in self)
  def __call__(self, *args, **kwargs):
    if len(args) > 1:
      raise TypeError('call takes from 0 to 1 positional arguments but %d were given' % len(args))
    return self.SetValue(args[0], **kwargs) if args else self.GetValue(**kwargs)
  def Get(self, sub=False):
    return {na: p.Get(sub) for na, p in self}

class _D2D1Property:
  def __init__(self, properties, key):
    self._properties = properties
    if properties is None:
      self._index = None
      self._name = None
    elif isinstance(key, str):
      self._index = properties.GetPropertyIndex(key)
      self._name = None if self._index is None else key
    else:
      self._index = key
  def __bool__(self):
    return self._properties is not None and self._index is not None
  def GetIndex(self):
    return None if self.GetName() is None else self._index
  def GetName(self):
    if not hasattr(self, '_name'):
      self._name = self._properties.GetPropertyName(self._index) if self else None
    return self._name
  def GetType(self):
    if not hasattr(self, '_type'):
      self._type = self._properties.GetType(self._index) if self else None
    return self._type
  def GetValue(self, property_type=0, data_size=0):
    return self._properties.GetValue(self._index, property_type, data_size) if self else None
  def GetSubs(self):
    return self._properties.GetSubProperties(self._index) if self else None
  GetSubProperties = GetSubs
  def SetValue(self, data, property_type=0):
    return self._properties.SetValue(self._index, data, property_type) if self else None
  def __getitem__(self, key):
    return _ID2D1PUtil._get_item(self.GetSubs(), key)
  def Get(self, sub=False):
    return (self.GetValue(), _ID2D1PUtil._get_item(self.GetSubs()).Get(True)) if sub else self.GetValue()

class ID2D1Properties(IUnknown):
  _lightweight = True
  IID = GUID(0x483473d7, 0xcd46, 0x4f9d, 0x9d, 0x3a, 0x31, 0x12, 0xaa, 0x80, 0x15, 0x9d)
  _protos['GetPropertyCount'] = 3, (), (), wintypes.UINT
  _protos['GetPropertyName'] = 4, (wintypes.UINT, wintypes.LPWSTR, wintypes.UINT), ()
  _protos['GetPropertyNameLength'] = 5, (wintypes.UINT,), (), wintypes.UINT
  _protos['GetType'] = 6, (wintypes.UINT,), (), D2D1PROPERTYTYPE
  _protos['GetPropertyIndex'] = 7, (wintypes.LPCWSTR,), (), wintypes.UINT
  _protos['SetValueByName'] = 8, (wintypes.LPCWSTR, D2D1PROPERTYTYPE, wintypes.LPVOID, wintypes.UINT), ()
  _protos['SetValue'] = 9, (wintypes.UINT, D2D1PROPERTYTYPE, wintypes.LPVOID, wintypes.UINT), ()
  _protos['GetValueByName'] = 10, (wintypes.LPCWSTR, D2D1PROPERTYTYPE, wintypes.LPVOID, wintypes.UINT), ()
  _protos['GetValue'] = 11, (wintypes.UINT, D2D1PROPERTYTYPE, wintypes.LPVOID, wintypes.UINT), ()
  _protos['GetValueSize'] = 12, (wintypes.UINT,), (), wintypes.UINT
  _protos['GetSubProperties'] = 13, (wintypes.UINT,), (wintypes.PLPVOID,)
  def GetPropertyCount(self):
    return self.__class__._protos['GetPropertyCount'](self.pI)
  def GetPropertyIndex(self, name):
    return None if (i := self.__class__._protos['GetPropertyIndex'](self.pI, name)) == 4294967295 else i
  def GetPropertyNameLength(self, index):
    return self.__class__._protos['GetPropertyNameLength'](self.pI, index)
  def GetPropertyName(self, index, name_count=None):
    if name_count is None:
      if not (name_count := self.GetPropertyNameLength(index)):
        return None
    name_count += 1
    n = ctypes.create_unicode_buffer(name_count * ctypes.sizeof(wintypes.WCHAR))
    return None if self.__class__._protos['GetPropertyName'](self.pI, index, n, name_count) is None else n.value
  def GetType(self, index):
    return self.__class__._protos['GetType'](self.pI, index)
  def GetTypeByName(self, name):
    if (b_i := _ID2D1PUtil._get_base_index(self, name)) is None:
      return None
    return b_i[0].GetType(b_i[1])
  def GetValueSize(self, index):
    return self.__class__._protos['GetValueSize'](self.pI, index)
  def GetValue(self, index, property_type=0, data_size=0):
    if property_type:
      if not (property_type := D2D1PROPERTYTYPE(property_type)):
        return None
    elif not (property_type := self.GetType(index)):
      return None
    if not data_size:
      if (data_size := _ID2D1PUtil._sizeof(property_type)) is None:
        if not (data_size := self.GetValueSize(index)):
          return None
    d = ctypes.create_string_buffer(data_size)
    if self.__class__._protos['GetValue'](self.pI, index, property_type, d, data_size) is None:
      return None
    v = _ID2D1PUtil._to_value(property_type, d, data_size)
    if property_type == 12:
      if (sp := self.GetSubProperties(index)) is None:
        return None
      if index == 0x80000005 and not isinstance(self, ID2D1Effect):
        if (f := sp.GetSubProperties(0)) is not None and f.GetTypeByName('Index') == 'UInt32':
          return tuple(_D2D1PEnumValue((None if (f := sp.GetSubProperties(i)) is None else f.GetValueByName('Index', 'UInt32')), sp.GetPropertyName(i), sp.GetValue(i, 'String')) for i in range(v))
      return tuple(sp.GetValue(i) for i in range(v))
    elif property_type == 11:
      if (sp := self.GetSubProperties(index)) is None:
        return None
      if (sp := sp.GetSubProperties(0x80000005)) is None:
        return None
      if not (n := sp.GetPropertyCount()):
        return None
      ind = min(v, n)
      if (ind := next((i for r in (range(ind, -1, -1), range(ind + 1, n)) for i in r if v == (None if (f := sp.GetSubProperties(i)) is None else f.GetValueByName('Index', 'UInt32'))), None)) is None:
        return None
      return _D2D1PEnumValue(v, sp.GetPropertyName(ind), sp.GetValue(ind, 'String'))
    else:
      return v
  def GetValueByName(self, name, property_type=0, data_size=0):
    b_i = None
    if property_type:
      if not (property_type := D2D1PROPERTYTYPE(property_type)):
        return None
    else:
      if (b_i := _ID2D1PUtil._get_base_index(self, name)) is None:
        return None
      if not (property_type := b_i[0].GetType(b_i[1])):
        return None
    if not data_size:
      if (data_size := _ID2D1PUtil._sizeof(property_type)) is None:
        if b_i is None and (b_i := _ID2D1PUtil._get_base_index(self, name)) is None:
          return None
        if not (data_size := b_i[0].GetValueSize(b_i[1])):
          return None
    if property_type in (11, 12):
      if b_i is None and (b_i := _ID2D1PUtil._get_base_index(self, name)) is None:
        return None
      return b_i[0].GetValue(b_i[1], property_type, data_size)
    else:
      d = ctypes.create_string_buffer(data_size)
      if self.__class__._protos['GetValueByName'](self.pI, name, property_type, d, data_size) is None:
        return None
      return _ID2D1PUtil._to_value(property_type, d, data_size)
  def SetValue(self, index, data, property_type=0):
    if property_type:
      if not (property_type := D2D1PROPERTYTYPE(property_type)):
        return None
    elif not (property_type := self.GetType(index)):
      return None
    if property_type == 11 and isinstance(data, str):
      if (sp := self.GetSubProperties(index)) is None:
        return None
      if (sp := sp.GetSubProperties(0x80000005)) is None:
        return None
      if not (n := sp.GetPropertyCount()):
        return None
      nam = data.lower()
      if (ind := next((i for i in range(n) if nam == (None if (k := sp.GetPropertyName(i)) is None else k.lower())), None)) is None:
        if (ind := next((i for i in range(n) if nam == (None if (na := sp.GetValue(i, 'String')) is None else na.lower())), None)) is None:
          return None
      if (data := (None if (f := sp.GetSubProperties(ind)) is None else f.GetValueByName('Index', 'UInt32'))) is None:
        return None
    if (d_s := _ID2D1PUtil._from_value(property_type, data)) is None:
      return None
    return self.__class__._protos['SetValue'](self.pI, index, property_type, ctypes.byref(d_s[0]), d_s[1])
  def SetValueByName(self, name, data, property_type=0, data_size=None):
    b_i = None
    if property_type:
      if not (property_type := D2D1PROPERTYTYPE(property_type)):
        return None
    else:
      if (b_i := _ID2D1PUtil._get_base_index(self, name)) is None:
        return None
      if not (property_type := b_i[0].GetType(b_i[1])):
        return None
    if property_type == 11 and isinstance(data, str):
      if b_i is None and (b_i := _ID2D1PUtil._get_base_index(self, name)) is None:
        return None
      return b_i[0].SetValue(b_i[1], data, property_type)
    else:
      if (d_s := _ID2D1PUtil._from_value(property_type, data)) is None:
        return None
      return self.__class__._protos['SetValueByName'](self.pI, name, property_type, ctypes.byref(d_s[0]), d_s[1])
  def GetSubProperties(self, index):
    return ID2D1Properties(self.__class__._protos['GetSubProperties'](self.pI, index), self.factory)
  def GetSubPropertiesByName(self, name):
    if (b_i := _ID2D1PUtil._get_base_index(self, name)) is None:
      return None
    return b_i[0].GetSubProperties(b_i[1])
  def __getitem__(self, key):
    return _ID2D1PUtil._get_item(self, key)
  def GetAll(self, sub=False):
    return self[True].Get(sub)
  def GetCustom(self, sub=False):
    return self[False].Get(sub)
  def GetSystem(self, sub=False):
    return self[_ID2D1PUtil.D2D1PSystemRange.start:].Get(sub)

class ID2D1Effect(ID2D1Properties):
  IID = GUID(0x28211a43, 0x7d89, 0x476f, 0x81, 0x81, 0x2d, 0x61, 0x59, 0xb2, 0x20, 0xad)
  _protos['SetInput'] = 14, (wintypes.UINT, wintypes.LPVOID, wintypes.BOOLE), (), None
  _protos['SetInputCount'] = 15, (wintypes.UINT,), ()
  _protos['GetInput'] = 16, (wintypes.UINT,), (wintypes.PLPVOID,), None
  _protos['GetInputCount'] = 17, (), (), wintypes.UINT
  _protos['GetOutput'] = 18, (), (wintypes.PLPVOID,), None
  def SetInput(self, index, input=None, invalidate=True):
    self.__class__._protos['SetInput'](self.pI, index, input, invalidate)
  def SetInputCount(self, count):
    return self.__class__._protos['SetInputCount'](self.pI, count)
  def GetInput(self, index):
    return ID2D1Image(self.__class__._protos['GetInput'](self.pI, index), self.factory)
  def GetInputCount(self):
    return self.__class__._protos['GetInputCount'](self.pI)
  def GetInputs(self):
    inp = self.GetValue(0x80000005, 'Array') or ()
    c = len(inp)
    return {(inp[i] if i < c else i): self.GetInput(i) for i in range(self.GetInputCount())}
  def GetOutput(self):
    return ID2D1Image(self.__class__._protos['GetOutput'](self.pI), self.factory)
  def SetInputEffect(self, index, input_effect=None, invalidate=True):
    self.__class__._protos['SetInput'](self.pI, index, (None if input_effect is None else input_effect.GetOutput()), invalidate)

class ID2D1GradientStopCollection(ID2D1Resource):
  IID = GUID(0xae1572f4, 0x5dd0, 0x4777, 0x99, 0x8b, 0x92, 0x79, 0x47, 0x2a, 0xe6, 0x3b)
  _protos['GetGradientStopCount'] = 4, (), (), wintypes.UINT
  _protos['GetColorInterpolationGamma'] = 6, (), (), D2D1GAMMA
  _protos['GetExtendMode'] = 7, (), (), D2D1EXTENDMODE
  _protos['GetGradientStops1'] = 8, (D2D1PAGRADIENTSTOP, wintypes.UINT), (), None
  _protos['GetPreInterpolationSpace'] = 9, (), (), D2D1COLORSPACE
  _protos['GetPostInterpolationSpace'] = 10, (), (), D2D1COLORSPACE
  _protos['GetBufferPrecision'] = 11, (), (), D2D1BUFFERPRECISION
  _protos['GetColorInterpolationMode'] = 12, (), (), D2D1COLORINTERPOLATIONMODE
  def GetGradientStopCount(self):
    return self.__class__._protos['GetGradientStopCount'](self.pI)
  def GetGradientStops(self, count=None):
    if count is None:
      if (count := self.GetGradientStopCount()) is None:
        return None
    gss = (D2D1GRADIENTSTOP * count)()
    self.__class__._protos['GetGradientStops1'](self.pI, gss, count)
    return gss.value
  def GetExtendMode(self):
    return self.__class__._protos['GetExtendMode'](self.pI)
  def GetColorInterpolationGamma(self):
    return self.__class__._protos['GetColorInterpolationGamma'](self.pI)
  def GetPreInterpolationSpace(self):
    return self.__class__._protos['GetPreInterpolationSpace'](self.pI)
  def GetPostInterpolationSpace(self):
    return self.__class__._protos['GetPostInterpolationSpace'](self.pI)
  def GetBufferPrecision(self):
    return self.__class__._protos['GetBufferPrecision'](self.pI)
  def GetColorInterpolationMode(self):
    return self.__class__._protos['GetColorInterpolationMode'](self.pI)
ID2D1GradientStopCollection1 = ID2D1GradientStopCollection

class ID2D1Brush(ID2D1Resource):
  IID = GUID(0x2cd906a8, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['SetOpacity'] = 4, (wintypes.FLOAT,), (), None
  _protos['SetTransform'] = 5, (D2D1PMATRIX3X2F,), (), None
  _protos['GetOpacity'] = 6, (), (), wintypes.FLOAT
  _protos['GetTransform'] = 7, (), (D2D1PMATRIX3X2F,), None
  def GetOpacity(self):
    return self.__class__._protos['GetOpacity'](self.pI)
  def SetOpacity(self, opacity=1):
    self.__class__._protos['SetOpacity'](self.pI, opacity)
  def GetTransform(self):
    return self.__class__._protos['GetTransform'](self.pI)
  def SetTransform(self, transform):
    self.__class__._protos['SetTransform'](self.pI, transform)

class ID2D1BitmapBrush(ID2D1Brush):
  IID = GUID(0x41343a53, 0xe41a, 0x49a2, 0x91, 0xcd, 0x21, 0x79, 0x3b, 0xbb, 0x62, 0xe5)
  _protos['SetExtendModeX'] = 8, (D2D1EXTENDMODE,), (), None
  _protos['SetExtendModeY'] = 9, (D2D1EXTENDMODE,), (), None
  _protos['SetBitmap'] = 11, (wintypes.LPVOID,), (), None
  _protos['GetExtendModeX'] = 12, (), (), D2D1EXTENDMODE
  _protos['GetExtendModeY'] = 13, (), (), D2D1EXTENDMODE
  _protos['GetBitmap'] = 15, (), (wintypes.PLPVOID,), None
  _protos['SetInterpolationMode1'] = 16, (D2D1INTERPOLATIONMODE,), (), None
  _protos['GetInterpolationMode1'] = 17, (), (), D2D1INTERPOLATIONMODE
  def GetBitmap(self):
    return ID2D1Bitmap(self.__class__._protos['GetBitmap'](self.pI), self.factory)
  def SetBitmap(self, bitmap):
    self.__class__._protos['SetBitmap'](self.pI, bitmap)
  def GetInterpolationMode(self):
    return self.__class__._protos['GetInterpolationMode1'](self.pI)
  def SetInterpolationMode(self, interpolation_mode=0):
    self.__class__._protos['SetInterpolationMode1'](self.pI, interpolation_mode)
  def GetExtendModeX(self):
    return self.__class__._protos['GetExtendModeX'](self.pI)
  def SetExtendModeX(self, extend_mode=0):
    self.__class__._protos['SetExtendModeX'](self.pI, extend_mode)
  def GetExtendModeY(self):
    return self.__class__._protos['GetExtendModeY'](self.pI)
  def SetExtendModeY(self, extend_mode=0):
    self.__class__._protos['SetExtendModeY'](self.pI, extend_mode)
ID2D1BitmapBrush1 = ID2D1BitmapBrush

class ID2D1SolidColorBrush(ID2D1Brush):
  IID = GUID(0x2cd906a9, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['SetColor'] = 8, (D2D1COLORF,), (), None
  _protos['GetColor'] = 9, (), (D2D1PCOLORF,), None
  def GetColor(self):
    return self.__class__._protos['GetColor'](self.pI)
  def SetColor(self, color):
    self.__class__._protos['SetColor'](self.pI, color)

class ID2D1LinearGradientBrush(ID2D1Brush):
  IID = GUID(0x2cd906ab, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['SetStartPoint'] = 8, (D2D1POINT2F,), (), None
  _protos['SetEndPoint'] = 9, (D2D1POINT2F,), (), None
  _protos['GetStartPoint'] = 10, (), (D2D1PPOINT2F,), None
  _protos['GetEndPoint'] = 11, (), (D2D1PPOINT2F,), None
  _protos['GetGradientStopCollection'] = 12, (), (wintypes.PLPVOID,), None
  def GetStartPoint(self):
    return self.__class__._protos['GetStartPoint'](self.pI)
  def SetStartPoint(self, start_point):
    self.__class__._protos['SetStartPoint'](self.pI, start_point)
  def GetEndPoint(self):
    return self.__class__._protos['GetEndPoint'](self.pI)
  def SetEndPoint(self, end_point):
    self.__class__._protos['SetEndPoint'](self.pI, end_point)
  def GetGradientStopCollection(self):
    return ID2D1GradientStopCollection(self.__class__._protos['GetGradientStopCollection'](self.pI), self.factory)

class ID2D1RadialGradientBrush(ID2D1Brush):
  IID = GUID(0x2cd906ac, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['SetCenter'] = 8, (D2D1POINT2F,), (), None
  _protos['SetGradientOriginOffset'] = 9, (D2D1POINT2F,), (), None
  _protos['SetRadiusX'] = 10, (wintypes.FLOAT,), (), None
  _protos['SetRadiusY'] = 11, (wintypes.FLOAT,), (), None
  _protos['GetCenter'] = 12, (), (D2D1PPOINT2F,), None
  _protos['GetGradientOriginOffset'] = 13, (), (D2D1PPOINT2F,), None
  _protos['GetRadiusX'] = 14, (), (), wintypes.FLOAT
  _protos['GetRadiusY'] = 15, (), (), wintypes.FLOAT
  _protos['GetGradientStopCollection'] = 16, (), (wintypes.PLPVOID,), None
  def GetCenter(self):
    return self.__class__._protos['GetCenter'](self.pI)
  def SetCenter(self, center):
    self.__class__._protos['SetCenter'](self.pI, center)
  def GetGradientOriginOffset(self):
    return self.__class__._protos['GetGradientOriginOffset'](self.pI)
  def SetGradientOriginOffset(self, origin_offset):
    self.__class__._protos['SetGradientOriginOffset'](self.pI, origin_offset)
  def GetRadiusX(self):
    return self.__class__._protos['GetRadiusX'](self.pI)
  def SetRadiusX(self, radius_x):
    self.__class__._protos['SetRadiusX'](self.pI, radius_x)
  def GetRadiusY(self):
    return self.__class__._protos['GetRadiusY'](self.pI)
  def SetRadiusY(self, radius_y):
    self.__class__._protos['SetRadiusY'](self.pI, radius_y)
  def GetRadius(self):
    return None if (rx := self.GetRadiusX()) is None or (ry := self.GetRadiusY()) is None else (rx, ry)
  def SetRadius(self, *radius):
    rx, ry = (r if isinstance((r := radius[0]), (tuple, list)) else (r, r)) if len(radius) == 1 else radius
    self.SetRadiusX(rx)
    self.SetRadiusY(ry)
  def GetGradientStopCollection(self):
    return ID2D1GradientStopCollection(self.__class__._protos['GetGradientStopCollection'](self.pI), self.factory)

class ID2D1ImageBrush(ID2D1Brush):
  IID = GUID(0xfe9e984d, 0x3f95, 0x407c, 0xb5, 0xdb, 0xcb, 0x94, 0xd4, 0xe8, 0xf8, 0x7c)
  _protos['SetImage'] = 8, (wintypes.LPVOID,), (), None
  _protos['SetExtendModeX'] = 9, (D2D1EXTENDMODE,), (), None
  _protos['SetExtendModeY'] = 10, (D2D1EXTENDMODE,), (), None
  _protos['SetInterpolationMode'] = 11, (D2D1INTERPOLATIONMODE,), (), None
  _protos['SetSourceRectangle'] = 12, (D2D1PRECTF,), (), None
  _protos['GetImage'] = 13, (), (wintypes.PLPVOID,), None
  _protos['GetExtendModeX'] = 14, (), (), D2D1EXTENDMODE
  _protos['GetExtendModeY'] = 15, (), (), D2D1EXTENDMODE
  _protos['GetInterpolationMode'] = 16, (), (), D2D1INTERPOLATIONMODE
  _protos['GetSourceRectangle'] = 17, (), (D2D1PRECTF,), None
  def GetImage(self):
    return ID2D1Image(self.__class__._protos['GetImage'](self.pI), self.factory)
  def SetImage(self, image):
    self.__class__._protos['SetImage'](self.pI, (image.GetOutput() if isinstance(image, ID2D1Effect) else image))
  def GetInterpolationMode(self):
    return self.__class__._protos['GetInterpolationMode'](self.pI)
  def SetInterpolationMode(self, interpolation_mode=0):
    self.__class__._protos['SetInterpolationMode'](self.pI, interpolation_mode)
  def GetExtendModeX(self):
    return self.__class__._protos['GetExtendModeX'](self.pI)
  def SetExtendModeX(self, extend_mode=0):
    self.__class__._protos['SetExtendModeX'](self.pI, extend_mode)
  def GetExtendModeY(self):
    return self.__class__._protos['GetExtendModeY'](self.pI)
  def SetExtendModeY(self, extend_mode=0):
    self.__class__._protos['SetExtendModeY'](self.pI, extend_mode)
  def GetSourceRectangle(self):
    return self.__class__._protos['GetSourceRectangle'](self.pI)
  def SetSourceRectangle(self, source_rectangle):
    self.__class__._protos['SetSourceRectangle'](self.pI, source_rectangle)

class ID2D1StrokeStyle(ID2D1Resource):
  IID = GUID(0x10a72a66, 0xe91c, 0x43f4, 0x99, 0x3f, 0xdd, 0xf4, 0xb8, 0x2b, 0x0b, 0x4a)
  _protos['GetStartCap'] = 4, (), (), D2D1CAPSTYLE
  _protos['GetEndCap'] = 5, (), (), D2D1CAPSTYLE
  _protos['GetDashCap'] = 6, (), (), D2D1CAPSTYLE
  _protos['GetMiterLimit'] = 7, (), (), wintypes.FLOAT
  _protos['GetLineJoin'] = 8, (), (), D2D1LINEJOIN
  _protos['GetDashOffset'] = 9, (), (), wintypes.FLOAT
  _protos['GetDashStyle'] = 10, (), (), D2D1DASHSTYLE
  _protos['GetDashesCount'] = 11, (), (), wintypes.UINT
  _protos['GetDashes'] = 12, (wintypes.PFLOAT, wintypes.UINT), (), None
  _protos['GetStrokeTransformType'] = 13, (), (), D2D1STROKETRANSFORMTYPE
  def GetStartCap(self):
    return self.__class__._protos['GetStartCap'](self.pI)
  def GetEndCap(self):
    return self.__class__._protos['GetEndCap'](self.pI)
  def GetDashCap(self):
    return self.__class__._protos['GetDashCap'](self.pI)
  def GetMiterLimit(self):
    return self.__class__._protos['GetMiterLimit'](self.pI)
  def GetLineJoin(self):
    return self.__class__._protos['GetLineJoin'](self.pI)
  def GetDashOffset(self):
    return self.__class__._protos['GetDashOffset'](self.pI)
  def GetDashStyle(self):
    return self.__class__._protos['GetDashStyle'](self.pI)
  def GetDashesCount(self):
    return self.__class__._protos['GetDashesCount'](self.pI)
  def GetDashes(self, count=None):
    if count is None:
      if (count := self.GetDashesCount()) is None:
        return None
    d = (wintypes.FLOAT * count)()
    self.__class__._protos['GetDashes'](self.pI, d, count)
    return tuple(d)
  def GetStrokeTransformType(self):
    return self.__class__._protos['GetStrokeTransformType'](self.pI)
ID2D1StrokeStyle1 = ID2D1StrokeStyle

class ID2D1DrawingStateBlock(ID2D1Resource):
  IID = GUID(0x689f1f85, 0xc72e, 0x4e33, 0x8f, 0x19, 0x85, 0x75, 0x4e, 0xfd, 0x5a, 0xce)
  _protos['GetDescription'] = 8, (), (D2D1PDRAWINGSTATEDESCRIPTION,), None
  _protos['SetDescription'] = 9, (D2D1PDRAWINGSTATEDESCRIPTION,), (), None
  def GetDescription(self):
    return self.__class__._protos['GetDescription'](self.pI)
  def SetDescription(self, description):
    return self.__class__._protos['SetDescription'](self.pI, description)
ID2D1DrawingStateBlock1 = ID2D1DrawingStateBlock

class ID2D1RenderTarget(ID2D1Resource):
  IID = GUID(0x2cd90694, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['CreateBitmap'] = 4, (D2D1SIZEU, PBUFFER, wintypes.UINT, D2D1PBITMAPPROPERTIESRT), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromWICBitmap'] = 5, (wintypes.LPVOID, D2D1PBITMAPPROPERTIESRT), (wintypes.PLPVOID,)
  _protos['CreateSharedBitmap'] = 6, (PUUID, wintypes.LPVOID, D2D1PBITMAPPROPERTIESRT), (wintypes.PLPVOID,)
  _protos['CreateBitmapBrush'] = 7, (wintypes.LPVOID, D2D1PBITMAPBRUSHPROPERTIESRT, D2D1PBRUSHPROPERTIES), (wintypes.PLPVOID,)
  _protos['CreateSolidColorBrush'] = 8, (D2D1PCOLORF, D2D1PBRUSHPROPERTIES), (wintypes.PLPVOID,)
  _protos['CreateGradientStopCollection'] = 9, (D2D1PAGRADIENTSTOP, wintypes.UINT, D2D1GAMMA, D2D1EXTENDMODE), (wintypes.PLPVOID,)
  _protos['CreateLinearGradientBrush'] = 10, (D2D1PLINEARGRADIENTBRUSHPROPERTIES, D2D1PBRUSHPROPERTIES, wintypes.LPVOID), (wintypes.PLPVOID,)
  _protos['CreateRadialGradientBrush'] = 11, (D2D1PRADIALGRADIENTBRUSHPROPERTIES, D2D1PBRUSHPROPERTIES, wintypes.LPVOID), (wintypes.PLPVOID,)
  _protos['CreateCompatibleRenderTarget'] = 12, (D2D1PSIZEF, D2D1PSIZEU, D2D1PPIXELFORMAT, D2D1COMPATIBLERENDERTARGETOPTIONS), (wintypes.PLPVOID,)
  _protos['DrawLine'] = 15, (D2D1POINT2F, D2D1POINT2F, wintypes.LPVOID, wintypes.FLOAT, wintypes.LPVOID), (), None
  _protos['DrawRectangle'] = 16, (D2D1PRECTF, wintypes.LPVOID, wintypes.FLOAT, wintypes.LPVOID), (), None
  _protos['FillRectangle'] = 17, (D2D1PRECTF, wintypes.LPVOID), (), None
  _protos['DrawRoundedRectangle'] = 18, (D2D1PROUNDEDRECT, wintypes.LPVOID, wintypes.FLOAT, wintypes.LPVOID), (), None
  _protos['FillRoundedRectangle'] = 19, (D2D1PROUNDEDRECT, wintypes.LPVOID), (), None
  _protos['DrawEllipse'] = 20, (D2D1PELLIPSE, wintypes.LPVOID, wintypes.FLOAT, wintypes.LPVOID), (), None
  _protos['FillEllipse'] = 21, (D2D1PELLIPSE, wintypes.LPVOID), (), None
  _protos['DrawBitmap'] = 26, (wintypes.LPVOID, D2D1PRECTF, wintypes.FLOAT, D2D1BITMAPINTERPOLATIONMODE, D2D1PRECTF), (), None
  _protos['SetTransform'] = 30, (D2D1PMATRIX3X2F,), (), None
  _protos['GetTransform'] = 31, (), (D2D1PMATRIX3X2F,), None
  _protos['SetAntialiasMode'] = 32, (D2D1ANTIALIASMODE,), (), None
  _protos['GetAntialiasMode'] = 33, (), (), D2D1ANTIALIASMODE
  _protos['Flush'] = 42, (), (wintypes.PULARGE_INTEGER, wintypes.PULARGE_INTEGER)
  _protos['SaveDrawingState'] = 43, (wintypes.LPVOID,), (), None
  _protos['RestoreDrawingState'] = 44, (wintypes.LPVOID,), (), None
  _protos['PushAxisAlignedClip'] = 45, (D2D1PRECTF, D2D1ANTIALIASMODE), (), None
  _protos['PopAxisAlignedClip'] = 46, (), (), None
  _protos['Clear'] = 47, (D2D1PCOLORF,), (), None
  _protos['BeginDraw'] = 48, (), (), None
  _protos['EndDraw'] = 49, (), (wintypes.PULARGE_INTEGER, wintypes.PULARGE_INTEGER)
  _protos['GetPixelFormat'] = 50, (), (D2D1PPIXELFORMAT,), None
  _protos['SetDpi'] = 51, (wintypes.FLOAT, wintypes.FLOAT), (), None
  _protos['GetDpi'] = 52, (), (wintypes.PFLOAT, wintypes.PFLOAT), None
  _protos['GetSize'] = 53, (), (D2D1PSIZEF,), None
  _protos['GetPixelSize'] = 54, (), (D2D1PSIZEU,), None
  _protos['GetMaximumBitmapSize'] = 55, (), (), wintypes.UINT
  _protos['IsSupported'] = 56, (D2D1PRENDERTARGETPROPERTIES,), (), wintypes.BOOLE
  def CreateBitmap(self, width, height, properties, source_data=None, source_pitch=0):
    return _IUtil.QueryInterface(IUnknown(self.__class__._protos['CreateBitmap'](self.pI, (width, height), source_data, source_pitch, properties), self.factory), ID2D1Bitmap)
  def CreateBitmapFromWICBitmap(self, source, properties=None):
    return _IUtil.QueryInterface(IUnknown(self.__class__._protos['CreateBitmapFromWICBitmap'](self.pI, source, properties), self.factory), ID2D1Bitmap)
  def CreateSharedBitmap(self, source, properties=None):
    return _IUtil.QueryInterface(IUnknown(self.__class__._protos['CreateSharedBitmap'](self.pI, source.IID, source, properties), self.factory), ID2D1Bitmap)
  def CreateDefaultBitmap(self, source=None, source_pitch=0, width=0, height=0, format=0, alpha_mode=0, dpiX=0, dpiY=0):
    if isinstance(source, IWICBitmapSource):
      return self.CreateBitmapFromWICBitmap(source, ((format, alpha_mode), dpiX, dpiY))
    elif isinstance(source, IDXGISurface):
      return self.CreateSharedBitmap(source, (((format or source.GetFormat()), (alpha_mode or 'Premultiplied')), dpiX, dpiY))
    elif isinstance(source, (ID2D1Resource, IWICBitmapLock)):
      return self.CreateSharedBitmap(source, ((format, alpha_mode), dpiX, dpiY))
    else:
      return self.CreateBitmap(width, height, (((format or 'B8G8R8A8_UNORM'), (alpha_mode or 'Premultiplied')), dpiX, dpiY), source, source_pitch)
  def CreateBitmapBrush(self, bitmap, bitmap_brush_properties, brush_properties=None):
    return _IUtil.QueryInterface(IUnknown(self.__class__._protos['CreateBitmapBrush'](self.pI, bitmap, bitmap_brush_properties, brush_properties), self.factory), ID2D1BitmapBrush)
  def CreateSolidColorBrush(self, color, brush_properties=None):
    return ID2D1SolidColorBrush(self.__class__._protos['CreateSolidColorBrush'](self.pI, color, brush_properties), self.factory)
  def CreateGradientStopCollection(self, gradient_stops, color_interpolation_gamma=0, extend_mode=0):
    return _IUtil.QueryInterface(IUnknown(self.__class__._protos['CreateGradientStopCollection'](self.pI, gradient_stops, (0 if not gradient_stops else len(gradient_stops)), color_interpolation_gamma, extend_mode), self.factory), ID2D1GradientStopCollection)
  def CreateLinearGradientBrush(self, linear_gradient_brush_properties, gradient_stop_collection, brush_properties=None):
    return ID2D1LinearGradientBrush(self.__class__._protos['CreateLinearGradientBrush'](self.pI, linear_gradient_brush_properties, brush_properties, gradient_stop_collection), self.factory)
  def CreateRadialGradientBrush(self, radial_gradient_brush_properties, gradient_stop_collection, brush_properties=None):
    return ID2D1RadialGradientBrush(self.__class__._protos['CreateRadialGradientBrush'](self.pI, radial_gradient_brush_properties, brush_properties, gradient_stop_collection), self.factory)
  def CreateBrush(self, content, bitmap_interpolation_mode=None, gradient_start_point=None, gradient_end_point=None, gradient_center=None, gradient_origin_offset=None, gradient_radius=None, gradient_color_interpolation_gamma=None, extend_mode=None, opacity=None, transform=None):
    if gradient_radius is not None and not isinstance(gradient_radius, (list, tuple)):
      gradient_radius = (gradient_radius, gradient_radius)
    lg = gradient_start_point is not None and gradient_end_point is not None
    rg = gradient_center is not None and gradient_radius is not None
    if isinstance(content, (tuple, list)):
      if lg or rg:
        if (content := self.CreateGradientStopCollection(content, gradient_color_interpolation_gamma or 0, extend_mode or 0)) is None:
          return None
      elif len(content) == 4:
        content = D2D1COLORF(*content)
      else:
        return None
    bp = None if opacity is None and transform is None else ((1 if opacity is None else opacity), (transform or ID21Factory.MakeIndentityMatrix()))
    if isinstance(content, ID2D1Image):
      return self.CreateBitmapBrush(content, (*(extend_mode or (0, 0)), bitmap_interpolation_mode or 0), bp)
    elif isinstance(content, ID2D1GradientStopCollection):
      return self.CreateLinearGradientBrush((gradient_start_point, gradient_end_point), content, bp) if lg else self.CreateRadialGradientBrush((gradient_center, gradient_origin_offset, *gradient_radius), content, bp)
    elif isinstance(content, D2D1COLORF):
      return self.CreateSolidColorBrush(content, bp)
    else:
      return None
  def Clear(self, clear_color=None):
    self._protos['Clear'](self.pI, clear_color)
  def GetAntialiasMode(self):
    return self._protos['GetAntialiasMode'](self.pI)
  def SetAntialiasMode(self, antialias_mode=0):
    return self._protos['SetAntialiasMode'](self.pI, antialias_mode)
  def GetSize(self):
    return self._protos['GetSize'](self.pI)
  def GetPixelSize(self):
    return self._protos['GetPixelSize'](self.pI)
  def GetPixelFormat(self):
    return self._protos['GetPixelFormat'](self.pI)
  def GetDpi(self):
    return self._protos['GetDpi'](self.pI)
  def SetDpi(self, dpiX=0, dpiY=0):
    return self._protos['SetDpi'](self.pI, dpiX, dpiY)
  def GetMaximumBitmapSize(self):
    return self._protos['GetMaximumBitmapSize'](self.pI)
  def IsSupported(self, properties):
    return self._protos['IsSupported'](self.pI, properties)
  def GetTransform(self):
    return self._protos['GetTransform'](self.pI)
  def SetTransform(self, transform=None):
    self._protos['SetTransform'](self.pI, transform or ID2D1Factory.MakeIdentityMatrix())
  def PushAxisAlignedClip(self, clip_rect, antialias_mode=0):
    self._protos['PushAxisAlignedClip'](self.pI, clip_rect, antialias_mode)
  def PopAxisAlignedClip(self):
    self._protos['PopAxisAlignedClip'](self.pI)
  def BeginDraw(self):
    self._protos['BeginDraw'](self.pI)
  def Flush(self):
    return self._protos['Flush'](self.pI)
  def EndDraw(self):
    return self._protos['EndDraw'](self.pI)
  def SaveDrawingState(self, block=None):
    if block is None:
      if (factory := self.factory) is None:
        if (factory := self.GetFactory()) is None:
          return None
      if (block := factory.CreateDrawingStateBlock()) is None:
        return None
    self._protos['SaveDrawingState'](self.pI, block)
    return block
  def RestoreDrawingState(self, block):
    self._protos['RestoreDrawingState'](self.pI, block)
  def DrawBitmap(self, bitmap, destination_ltrb=None, opacity=1, interpolation_mode=0, source_ltrb=None):
    self.__class__._protos['DrawBitmap'](self.pI, bitmap, destination_ltrb, opacity, interpolation_mode, source_ltrb)
  def CreateStrokeStyle(self, start_cap=0, end_cap=0, dash_cap=0, line_join=0, miter_limit=1, dash_style=0, dash_offset=0, transform_type=0, dashes=None):
    if (factory := self.factory) is None:
      if (factory := self.GetFactory()) is None:
        return None
    return factory.CreateStrokeStyle((start_cap, end_cap, dash_cap, line_join, miter_limit, dash_style, dash_offset, transform_type), dashes)
  def DrawLine(self, point0, point1, brush, stroke_width, stroke_style=None):
    self.__class__._protos['DrawLine'](self.pI, point0, point1, brush, stroke_width, stroke_style)
  def DrawRectangle(self, rect, brush, stroke_width, stroke_style=None):
    self.__class__._protos['DrawRectangle'](self.pI, rect, brush, stroke_width, stroke_style)
  def FillRectangle(self, rect, brush):
    self.__class__._protos['FillRectangle'](self.pI, rect, brush)
  def DrawRoundedRectangle(self, rounded_rect, brush, stroke_width, stroke_style=None):
    self.__class__._protos['DrawRoundedRectangle'](self.pI, rounded_rect, brush, stroke_width, stroke_style)
  def FillRoundedRectangle(self, rounded_rect, brush):
    self.__class__._protos['FillRoundedRectangle'](self.pI, rounded_rect, brush)
  def DrawEllipse(self, ellipse, brush, stroke_width, stroke_style=None):
    self.__class__._protos['DrawEllipse'](self.pI, ellipse, brush, stroke_width, stroke_style)
  def FillEllipse(self, ellipse, brush):
    self.__class__._protos['FillEllipse'](self.pI, ellipse, brush)
  def CreateCompatibleRenderTarget(self, size=None, pixel_size=None, pixel_format=None, options=0):
    return ID2D1BitmapRenderTarget(self.__class__._protos['CreateCompatibleRenderTarget'](self.pI, size, pixel_size, pixel_format, options), self.factory)
  def GetDeviceContext(self):
    return self.QueryInterface(ID2D1DeviceContext, self.factory)

class ID2D1CommandList(ID2D1Image):
  IID = GUID(0xb4f34a19, 0x2383, 0x4d76, 0x94, 0xf6, 0xec, 0x34, 0x36, 0x57, 0xc3, 0xdc)
  _protos['Close'] = 5, (), ()
  def Close(self):
    return self._protos['Close'](self.pI)

class ID2D1DeviceContext(ID2D1RenderTarget):
  IID = GUID(0xe8f7fe7a, 0x191c, 0x466d, 0xad, 0x95, 0x97, 0x56, 0x78, 0xbd, 0xa9, 0x98)
  _protos['CreateBitmap'] = 57, (D2D1SIZEU, PBUFFER, wintypes.UINT, D2D1PBITMAPPROPERTIESDC), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromWICBitmap'] = 58, (wintypes.LPVOID, D2D1PBITMAPPROPERTIESDC), (wintypes.PLPVOID,)
  _protos['CreateColorContext'] = 59, (D2D1COLORSPACE, PBUFFER, wintypes.UINT), (wintypes.PLPVOID,)
  _protos['CreateColorContextFromFilename'] = 60, (wintypes.LPCWSTR,), (wintypes.PLPVOID,)
  _protos['CreateColorContextFromWicColorContext'] = 61, (wintypes.LPVOID,), (wintypes.PLPVOID,)
  _protos['CreateBitmapFromDxgiSurface'] = 62, (wintypes.LPVOID, D2D1PBITMAPPROPERTIESDC), (wintypes.PLPVOID,)
  _protos['CreateEffect'] = 63, (D2D1PEFFECTID,), (wintypes.PLPVOID,)
  _protos['CreateGradientStopCollection'] = 64, (D2D1PAGRADIENTSTOP, wintypes.UINT, D2D1COLORSPACE, D2D1COLORSPACE, D2D1BUFFERPRECISION, D2D1EXTENDMODE, D2D1COLORINTERPOLATIONMODE), (wintypes.PLPVOID,)
  _protos['CreateImageBrush'] = 65, (wintypes.LPVOID, D2D1PIMAGEBRUSHPROPERTIES, D2D1PBRUSHPROPERTIES), (wintypes.PLPVOID,)
  _protos['CreateBitmapBrush'] = 66, (wintypes.LPVOID, D2D1PBITMAPBRUSHPROPERTIESDC, D2D1PBRUSHPROPERTIES), (wintypes.PLPVOID,)
  _protos['CreateCommandList'] = 67, (), (wintypes.PLPVOID,)
  _protos['IsDxgiFormatSupported'] = 68, (DXGIFORMAT,), (), wintypes.BOOLE
  _protos['IsBufferPrecisionSupported'] = 69, (D2D1BUFFERPRECISION,), (), wintypes.BOOLE
  _protos['GetImageLocalBounds'] = 70, (wintypes.LPVOID,), (D2D1PRECTF,)
  _protos['GetImageWorldBounds'] = 71, (wintypes.LPVOID,), (D2D1PRECTF,)
  _protos['GetDevice'] = 73, (), (wintypes.PLPVOID,), None
  _protos['SetTarget'] = 74, (wintypes.LPVOID,), (), None
  _protos['GetTarget'] = 75, (), (wintypes.PLPVOID,), None
  _protos['SetRenderingControls'] = 76, (D2D1PRENDERINGCONTROLS,), (), None
  _protos['GetRenderingControls'] = 77, (), (D2D1PRENDERINGCONTROLS,), None
  _protos['SetPrimitiveBlend'] = 78, (D2D1PRIMITIVEBLEND,), (), None
  _protos['GetPrimitiveBlend'] = 79, (), (), D2D1PRIMITIVEBLEND
  _protos['SetUnitMode'] = 80, (D2D1UNITMODE,), (), None
  _protos['GetUnitMode'] = 81, (), (), D2D1UNITMODE
  _protos['DrawImage'] = 83, (wintypes.LPVOID, D2D1POINT2F, D2D1PRECTF, D2D1INTERPOLATIONMODE, D2D1COMPOSITEMODE), (), None
  _protos['DrawBitmap'] = 85, (wintypes.LPVOID, D2D1PRECTF, wintypes.FLOAT, D2D1INTERPOLATIONMODE, D2D1PRECTF, D2D1PMATRIX4X4F), (), None
  def CreateBitmap(self, width, height, properties, source_data=None, source_pitch=0):
    return ID2D1Bitmap(self.__class__._protos['CreateBitmap'](self.pI, (width, height), source_data, source_pitch, properties), self.factory)
  def CreateBitmapFromWICBitmap(self, source, properties=None):
    return ID2D1Bitmap(self.__class__._protos['CreateBitmapFromWICBitmap'](self.pI, source, properties), self.factory)
  def CreateBitmapFromDxgiSurface(self, surface, properties=None):
    return ID2D1Bitmap(self.__class__._protos['CreateBitmapFromDxgiSurface'](self.pI, surface, properties), self.factory)
  def CreateBitmapFromSwapChain(self, swapchain, index=0, properties=None):
    if (s := swapchain.GetSurface(index)) is None:
      return None
    return self.CreateBitmapFromDxgiSurface(s, properties)
  def CreateTargetBitmap(self, target=None, width=0, height=0, format=0, alpha_mode=0, dpiX=0, dpiY=0, color_context=None, drawable=False):
    if isinstance(target, IDXGISwapChain):
      if (target := target.GetSurface()) is None:
        return None
    if isinstance(target, IWICBitmapSource):
      return self.CreateBitmapFromWICBitmap(target, ((format, alpha_mode), dpiX, dpiY, ('Target' if drawable else 'Target | CannotDraw'), color_context))
    elif isinstance(target, IDXGISurface):
      return self.CreateBitmapFromDxgiSurface(target, (((format or target.GetFormat()), (alpha_mode or 'Premultiplied')), dpiX, dpiY, ('Target' if drawable else 'Target | CannotDraw'), color_context))
    elif target is None:
      return self.CreateBitmap(width, height, (((format or 'B8G8R8A8_UNORM'), (alpha_mode or 'Premultiplied')), dpiX, dpiY, ('Target' if drawable else 'Target | CannotDraw'), color_context))
    else:
      return None
  def CreateCPUReadableBitmap(self, source=None, source_pitch=0, width=0, height=0, format=0, alpha_mode=0, dpiX=0, dpiY=0, color_context=None):
    if isinstance(source, IWICBitmapSource):
      return self.CreateBitmapFromWICBitmap(source, ((format, alpha_mode), dpiX, dpiY, 'CPURead | CannotDraw', color_context))
    elif isinstance(source, IDXGISurface):
      return self.CreateBitmapFromDxgiSurface(target, (((format or source.GetFormat()), (alpha_mode or 'Premultiplied')), dpiX, dpiY, ('Target' if drawable else 'Target | CannotDraw'), color_context))
    else:
      return self.CreateBitmap(width, height, (((format or 'B8G8R8A8_UNORM'), (alpha_mode or 'Premultiplied')), dpiX, dpiY, 'CPURead | CannotDraw', color_context), source, source_pitch)
  def CreateDefaultBitmap(self, source=None, source_pitch=0, width=0, height=0, format=0, alpha_mode=0, dpiX=0, dpiY=0, color_context=None, drawable=None, share_surface=False, buffer_index=0):
    if isinstance(source, IDXGISwapChain):
      if (source := source.GetSurface(buffer_index)) is None:
        return None
    if isinstance(source, IWICBitmapSource):
      return self.CreateBitmapFromWICBitmap(source, ((format, alpha_mode), dpiX, dpiY, 'None', color_context))
    elif isinstance(source, IDXGISurface):
      if share_surface:
        return self.CreateSharedBitmap(source, (((format or source.GetFormat()), (alpha_mode or 'Premultiplied')), dpiX, dpiY))
      else:
        return self.CreateBitmapFromDxgiSurface(source, (None if not any((format, alpha_mode, dpiX, dpiY, color_context, drawable is not None)) else (((format or source.GetFormat()), (alpha_mode or 'Premultiplied')), dpiX, dpiY, ('None' if drawable else 'CannotDraw'), color_context)))
    elif isinstance(source, (ID2D1Resource, IWICBitmapLock)):
      return self.CreateSharedBitmap(source, ((format, alpha_mode), dpiX, dpiY))
    else:
      return self.CreateBitmap(width, height, (((format or 'B8G8R8A8_UNORM'), (alpha_mode or 'Premultiplied')), dpiX, dpiY, 'None', color_context), source, source_pitch)
  def CreateSwapChainAndBitmapFromHwnd(self, hwnd, format, width=0, height=0, alpha_mode=0, sample_count=1, sample_quality=0, buffer_count=1, swap_effect=0, flags=0, drawable=False):
    if self.factory is None or (dxgi_device := getattr(self.factory, 'dxgi_device', None)) is None or dxgi_device.factory is None:
      return None
    if (swap_chain := dxgi_device.factory.CreateSwapChainForHwnd(dxgi_device, hwnd, (width, height, format, False, (sample_count, sample_quality), ('BackBuffer | RenderTargetOutput | ShaderInput' if drawable else 'BackBuffer | RenderTargetOutput'), buffer_count, 'Stretch', swap_effect, alpha_mode, flags))) is None:
      return None
    if (surface := swap_chain.GetSurface()) is None:
      return None
    if (bitmap := self.CreateBitmapFromDxgiSurface(surface)) is None:
      return None
    return swap_chain, bitmap
  def CreateEffect(self, effect):
    return ID2D1Effect(self._protos['CreateEffect'](self.pI, effect), self.factory)
  def CreateBitmapBrush(self, bitmap, bitmap_brush_properties, brush_properties=None):
    return ID2D1BitmapBrush(self.__class__._protos['CreateBitmapBrush'](self.pI, bitmap,  bitmap_brush_properties, brush_properties), self.factory)
  def CreateGradientStopCollection(self, gradient_stops, pre_interpolation_space=1, post_interpolation_space=1, buffer_precision=1, extend_mode=0, color_interpolation_mode=1):
    return ID2D1GradientStopCollection(self.__class__._protos['CreateGradientStopCollection'](self.pI, gradient_stops, (0 if not gradient_stops else len(gradient_stops)), pre_interpolation_space, post_interpolation_space, buffer_precision, extend_mode, color_interpolation_mode), self.factory)
  def CreateImageBrush(self, image, image_brush_properties, brush_properties=None):
    return ID2D1ImageBrush(self.__class__._protos['CreateImageBrush'](self.pI, (image.GetOutput() if isinstance(image, ID2D1Effect) else image), image_brush_properties, brush_properties), self.factory)
  def CreateBrush(self, content, bitmap_interpolation_mode=None, gradient_start_point=None, gradient_end_point=None, gradient_center=None, gradient_origin_offset=None, gradient_radius=None, gradient_pre_interpolation_space=None, gradient_post_interpolation_space=None, gradient_buffer_precision=None, gradient_color_interpolation_mode=None, image_source_rectangle=None, image_interpolation_mode=None, extend_mode=None, opacity=None, transform=None):
    if gradient_radius is not None and not isinstance(gradient_radius, (list, tuple)):
      gradient_radius = (gradient_radius, gradient_radius)
    lg = gradient_start_point is not None and gradient_end_point is not None
    rg = gradient_center is not None and gradient_radius is not None
    if isinstance(content, (tuple, list)):
      if lg or rg:
        if (content := self.CreateGradientStopCollection(content, gradient_pre_interpolation_space or 1, gradient_post_interpolation_space or 1, gradient_buffer_precision or 1, extend_mode or 0, (1 if gradient_color_interpolation_mode is None else gradient_color_interpolation_mode))) is None:
          return None
      elif len(content) == 4:
        content = D2D1COLORF(*content)
      else:
        return None
    bp = None if opacity is None and transform is None else ((1 if opacity is None else opacity), (transform or ID21Factory.MakeIndentityMatrix()))
    if isinstance(content, ID2D1Bitmap) and (bitmap_interpolation_mode is not None or image_source_rectangle is None):
      return self.CreateBitmapBrush(content, (*(extend_mode or (0, 0)), bitmap_interpolation_mode or image_interpolation_mode or 0), bp)
    elif isinstance(content, ID2D1GradientStopCollection):
      return self.CreateLinearGradientBrush((gradient_start_point, gradient_end_point), content, bp) if lg else self.CreateRadialGradientBrush((gradient_center, gradient_origin_offset, *gradient_radius), content, bp)
    elif isinstance(content, D2D1COLORF):
      return self.CreateSolidColorBrush(content, bp)
    elif isinstance(content, (ID2D1Image, ID2D1Effect)):
      return self.CreateImageBrush(content, (image_source_rectangle or self.GetImageLocalBounds(content) or (0, 0, 0, 0), *(extend_mode or (0, 0)), image_interpolation_mode or 0), bp)
    else:
      return None
  def CreateColorContext(self, color_space=1, buffer=None):
    return ID2D1ColorContext(self.__class__._protos['CreateColorContext'](self.pI, color_space, buffer, PBUFFER.length(buffer)), self.factory)
  def CreateColorContextFromFilename(self, file_name):
    return ID2D1ColorContext(self.__class__._protos['CreateColorContextFromFilename'](self.pI, file_name), self.factory)
  def CreateColorContextFromWicColorContext(self, color_context):
    return ID2D1ColorContext(self.__class__._protos['CreateColorContextFromWicColorContext'](self.pI, color_context), self.factory)
  def CreateCommandList(self):
    return ID2D1CommandList(self._protos['CreateCommandList'](self.pI), self.factory)
  def GetDevice(self):
    return ID2D1Device(self._protos['GetDevice'](self.pI), self.factory)
  def SetTarget(self, target=None):
    self.__class__._protos['SetTarget'](self.pI, target)
  def GetTarget(self):
    return ID2D1Image(self.__class__._protos['GetTarget'](self.pI), self.factory)
  def IsDxgiFormatSupported(self, dxgi_format):
    return self.__class__._protos['IsDxgiFormatSupported'](self.pI, dxgi_format)
  def IsBufferPrecisionSupported(self, buffer_precision):
    return self.__class__._protos['IsBufferPrecisionSupported'](self.pI, buffer_precision)
  def SetRenderingControls(self, rendering_controls):
    self.__class__._protos['SetRenderingControls'](self.pI, rendering_controls)
  def GetRenderingControls(self):
    return self.__class__._protos['GetRenderingControls'](self.pI)
  def GetPrimitiveBlend(self):
    return self.__class__._protos['GetPrimitiveBlend'](self.pI)
  def SetPrimitiveBlend(self, primitive_blend=0):
    self.__class__._protos['SetPrimitiveBlend'](self.pI, primitive_blend)
  def GetUnitMode(self):
    return self.__class__._protos['GetUnitMode'](self.pI)
  def SetUnitMode(self, unit_mode=0):
    self.__class__._protos['SetUnitMode'](self.pI, unit_mode)
  def GetImageLocalBounds(self, image):
    return self.__class__._protos['GetImageLocalBounds'](self.pI, (image.GetOutput() if isinstance(image, ID2D1Effect) else image))
  def GetImageWorldBounds(self, image):
    return self.__class__._protos['GetImageWorldBounds'](self.pI, (image.GetOutput() if isinstance(image, ID2D1Effect) else image))
  def DrawBitmap(self, bitmap, destination_ltrb=None, opacity=1, interpolation_mode=0, source_ltrb=None, perspective_transform=None):
    self.__class__._protos['DrawBitmap'](self.pI, bitmap, destination_ltrb, opacity, interpolation_mode, source_ltrb, perspective_transform)
  def DrawImage(self, image, target_offset=None, image_rectangle=None, interpolation_mode=0, composite_mode=0):
    self.__class__._protos['DrawImage'](self.pI, (image.GetOutput() if isinstance(image, ID2D1Effect) else image), target_offset, image_rectangle, interpolation_mode, composite_mode)

class ID2D1BitmapRenderTarget(ID2D1RenderTarget):
  IID = GUID(0x2cd90695, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['GetBitmap'] = 57, (), (wintypes.PLPVOID,)
  def GetBitmap(self):
    return ID2D1Bitmap(self.__class__._protos['GetBitmap'](self.pI), self.factory)

class ID2D1HwndRenderTarget(ID2D1RenderTarget):
  IID = GUID(0x2cd90698, 0x12e2, 0x11dc, 0x9f, 0xed, 0x00, 0x11, 0x43, 0xa0, 0x55, 0xf9)
  _protos['CheckWindowState'] = 57, (), (), D2D1WINDOWSTATE
  _protos['Resize'] = 58, (D2D1PSIZEU,), (), None
  _protos['GetHwnd'] = 59, (), (), wintypes.HWND
  def GetHwnd(self):
    return self.__class__._protos['GetHwnd'](self.pI)
  def CheckWindowState(self):
    return self.__class__._protos['CheckWindowState'](self.pI)
  def Resize(self, width, height):
    return self.__class__._protos['Resize'](self.pI, (width, height))

class ID2D1Device(ID2D1Resource):
  IID = GUID(0x47dd575d, 0xac05, 0x4cdd, 0x80, 0x49, 0x9b, 0x02, 0xcd, 0x16, 0xf4, 0x4c)
  _protos['CreateDeviceContext'] = 4, (D2D1DEVICECONTEXTOPTIONS,), (wintypes.PLPVOID,)
  _protos['SetMaximumTextureMemory'] = 6, (wintypes.ULARGE_INTEGER,), (), None
  _protos['GetMaximumTextureMemory'] = 7, (), (), wintypes.ULARGE_INTEGER
  _protos['ClearResources'] = 8, (wintypes.UINT,), (), None
  def CreateDeviceContext(self, options=0):
    return ID2D1DeviceContext(self.__class__._protos['CreateDeviceContext'](self.pI, options), self.factory)
  def GetMaximumTextureMemory(self):
    return self.__class__._protos['GetMaximumTextureMemory'](self.pI)
  def SetMaximumTextureMemory(self, max):
    self.__class__._protos['SetMaximumTextureMemory'](self.pI, max)
  def ClearResources(self, milliseconds_since_use=0):
    self.__class__._protos['ClearResources'](self.pI, milliseconds_since_use)
  def GetDXGIDevice(self):
    if self.factory is None or (dxgi_device := getattr(self.factory, 'dxgi_device', None)) is None:
      return None
    return dxgi_device

class ID2D1Factory(IUnknown):
  _lightweight = True
  IID = GUID(0xbb12d362, 0xdaee, 0x4b9a, 0xaa, 0x1d, 0x14, 0xba, 0x40, 0x1c, 0xfa, 0x1f)
  _protos['ReloadSystemMetrics'] = 3, (), ()
  _protos['GetDesktopDpi'] = 4, (), (wintypes.PFLOAT, wintypes.PFLOAT), None
  _protos['CreateWicBitmapRenderTarget'] = 13, (wintypes.LPVOID, D2D1PRENDERTARGETPROPERTIES), (wintypes.PLPVOID,)
  _protos['CreateHwndRenderTarget'] = 14, (D2D1PRENDERTARGETPROPERTIES, D2D1PHWNDRENDERTARGETPROPERTIES), (wintypes.PLPVOID,)
  _protos['CreateDxgiSurfaceRenderTarget'] = 15, (wintypes.LPVOID, D2D1PRENDERTARGETPROPERTIES), (wintypes.PLPVOID,)
  _protos['CreateDevice'] = 17, (wintypes.LPVOID,), (wintypes.PLPVOID,)
  _protos['CreateStrokeStyle'] = 18, (D2D1PSTROKESTYLEPROPERTIES, wintypes.PFLOAT, wintypes.UINT), (wintypes.PLPVOID,)
  _protos['CreateDrawingStateBlock'] = 20, (D2D1PDRAWINGSTATEDESCRIPTION, wintypes.LPVOID), (wintypes.PLPVOID,)
  _protos['GetRegisteredEffects'] = 25, (D2D1PEFFECTID, wintypes.UINT), (wintypes.PUINT, wintypes.PUINT)
  _protos['GetEffectProperties'] = 26, (D2D1PEFFECTID,), (wintypes.PLPVOID,)
  def __new__(cls, clsid_component=False, factory=None):
    if clsid_component is False:
      pI = wintypes.LPVOID()
      if ISetLastError(d2d1.D2D1CreateFactory(wintypes.DWORD(1 if getattr(_IUtil._local, 'multithreaded', False) else 0), wintypes.LPCSTR(cls.IID), None, ctypes.byref(pI))):
        return None
    else:
      pI = clsid_component
    return IUnknown.__new__(cls, pI, factory)
  def CreateDevice(self, dxgi_device='hardware'):
    if isinstance(dxgi_device, str):
      if (d3d11_device := ID3D11Device(dxgi_device)) is None:
        return None
      if (dxgi_device := d3d11_device.GetDXGIDevice()) is None:
        return None
    f = self.QueryInterface(self.__class__)
    f.dxgi_device = dxgi_device
    return ID2D1Device(self.__class__._protos['CreateDevice'](self.pI, dxgi_device), f)
  def CreateWicBitmapRenderTarget(self, bitmap, properties):
    return ID2D1RenderTarget(self.__class__._protos['CreateWicBitmapRenderTarget'](self.pI, bitmap, properties), self)
  def CreateDxgiSurfaceRenderTarget(self, surface, properties):
    return ID2D1RenderTarget(self.__class__._protos['CreateDxgiSurfaceRenderTarget'](self.pI, surface, properties), self)
  def CreateHwndRenderTarget(self, properties, hwnd_properties):
    return ID2D1HwndRenderTarget(self.__class__._protos['CreateHwndRenderTarget'](self.pI, properties, hwnd_properties), self)
  def CreateRenderTarget(self, target, render_type=0, format=0, alpha_mode=0, dpiX=0, dpiY=0, usage=0, width=0, height=0, present_options=0):
    if isinstance(target, IWICBitmapSource):
      return self.CreateWicBitmapRenderTarget(target, ('Software', (format, alpha_mode), dpiX, dpiY, usage, 'Default'))
    elif isinstance(target, IDXGISurface):
      return self.CreateDxgiSurfaceRenderTarget(target, ('Hardware', (format, (alpha_mode or 'Premultiplied')), dpiX, dpiY, usage, 'Default'))
    elif isinstance(target, (wintypes.HWND, int)):
      return self.CreateHwndRenderTarget((render_type, (format, alpha_mode), dpiX, dpiY, usage, 'Default'), (target, (width, height), present_options))
    else:
      return None
  def CreateSurfaceAndRenderTarget(self, width, height, format=0, alpha_mode=0, sample_count=1, sample_quality=0, dpiX=0, dpiY=0, usage=0, drawable=False):
    if (d3d11_device := ID3D11Device('hardware')) is None:
      return None
    if (surface := d3d11_device.CreateTargetDXGISurface(width, height, (format or 'B8G8R8A8_UNORM'), sample_count, sample_quality, drawable)) is None:
      return None
    if (render_target := self.CreateDxgiSurfaceRenderTarget(surface, ('Hardware', (format, (alpha_mode or 'Premultiplied')), dpiX, dpiY, usage, 'Default'))) is None:
      return None
    return surface, render_target
  def CreateStrokeStyle(self, properties, dashes=None):
    return ID2D1StrokeStyle(self.__class__._protos['CreateStrokeStyle'](self.pI, properties, (dashes if dashes is None or (isinstance(dashes, ctypes.Array) and issubclass(dashes._type_, wintypes.FLOAT)) else (wintypes.FLOAT *  len(dashes))(*dashes)), (0 if dashes is None else len(dashes))), self)
  def CreateDrawingStateBlock(self, description=None):
    return ID2D1DrawingStateBlock(self.__class__._protos['CreateDrawingStateBlock'](self.pI, description, None), self)
  def GetRegisteredEffects(self):
    if (ac := self.__class__._protos['GetRegisteredEffects'](self.pI, None, 0)) is None:
      return None
    if (n := ac[1]) == 0:
      return ()
    e = (D2D1EFFECTID * n)()
    if (ac := self.__class__._protos['GetRegisteredEffects'](self.pI, e, n)) is None:
      return None
    return tuple(e[i] for i in range(ac[0]))
  def GetEffectProperties(self, effect):
    return ID2D1Properties(self.__class__._protos['GetEffectProperties'](self.pI, effect), self)
  def ReloadSystemMetrics(self):
    return self.__class__._protos['ReloadSystemMetrics'](self.pI)
  def GetDesktopDpi(self):
    return self.__class__._protos['GetDesktopDpi'](self.pI)
  MakeIdentityMatrix = staticmethod(D2D1MATRIX3X2F)
  MakeRotateMatrix = staticmethod(lambda angle, center, _mrm=ctypes.WINFUNCTYPE(None, wintypes.FLOAT, D2D1POINT2F, D2D1PMATRIX3X2F, use_last_error=True)(('D2D1MakeRotateMatrix', d2d1), ((1,), (1,), (2,))): _mrm(angle, center))
  MakeSkewMatrix = staticmethod(lambda angleX, angleY, center, _msm=ctypes.WINFUNCTYPE(None, wintypes.FLOAT, wintypes.FLOAT, D2D1POINT2F, D2D1PMATRIX3X2F, use_last_error=True)(('D2D1MakeSkewMatrix', d2d1), ((1,), (1,), (1,), (2,))): _msm(angleX, angleY, center))
  MakeTranslationMatrix = staticmethod(lambda x, y: D2D1MATRIX3X2F(1, 0, 0, 1, x, y))
  MakeScaleMatrix = staticmethod(lambda x, y, center: D2D1MATRIX3X2F(x, 0, 0, y, (1 - x) * getattr(center, 'value', center)[0], (1 - y) * getattr(center, 'value', center)[1]))
  IsMatrixInvertible = staticmethod(lambda matrix, _imi=ctypes.WINFUNCTYPE(wintypes.BOOLE, D2D1PMATRIX3X2F, use_last_error=True)(('D2D1IsMatrixInvertible', d2d1), ((1,),)): _imi(matrix).value)
  InvertMatrix = staticmethod(lambda matrix, _im=ctypes.WINFUNCTYPE(wintypes.BOOLE, D2D1PMATRIX3X2F, use_last_error=True)(('D2D1InvertMatrix', d2d1), ((1,),)): _im(matrix).value)
  MultiplyMatrix = staticmethod(lambda a, b: a @ b)
  ConvertColorSpace = staticmethod(lambda source, destination, color, _ccs=ctypes.WINFUNCTYPE(D2D1PCOLORF, D2D1COLORSPACE, D2D1COLORSPACE, D2D1PCOLORF, use_last_error=True)(('D2D1ConvertColorSpace', d2d1), ((1,), (1,), (1,))): _ccs(source, destination, color).value)
  MakeIdentityMatrix4x4 = staticmethod(D2D1MATRIX4X4F)
  MakeRotationXMatrix4x4 = staticmethod(lambda angle: (c := math.cos(math.radians(angle)), s := math.sin(math.radians(angle)), D2D1MATRIX4X4F(1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1))[2])
  MakeRotationYMatrix4x4 = staticmethod(lambda angle: (c := math.cos(math.radians(angle)), s := math.sin(math.radians(angle)), D2D1MATRIX4X4F(c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1))[2])
  MakeRotationZMatrix4x4 = staticmethod(lambda angle: (c := math.cos(math.radians(angle)), s := math.sin(math.radians(angle)), D2D1MATRIX4X4F(c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))[2])
  MakeRotationMatrix4x4 = staticmethod(lambda x, y, z, angle: (l := math.hypot(x, y, z), x := x / l, y := y / l, z := z / l, c := math.cos(math.radians(angle)), s := math.sin(math.radians(angle)), D2D1MATRIX4X4F((1 - c) * x * x + c, (1 - c) * x * y + z * s, (1 - c) * x * z - y * s, 0, (1 - c) * y * x - z * s, (1 - c) * y * y + c, (1 - c) * y * z + x * s, 0, (1 - c) * z * x + y * s, (1 - c) * z * y - x * s, (1 - c) * z * z + c, 0, 0, 0, 0, 1))[6])
  MakeSkewXMatrix4x4 = staticmethod(lambda angle: (t := math.tan(math.radians(angle)), D2D1MATRIX4X4F(1, 0, 0, 0, t, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))[1])
  MakeSkewYMatrix4x4 = staticmethod(lambda angle: (t := math.tan(math.radians(angle)), D2D1MATRIX4X4F(1, t, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1))[1])
  MakeTranslationMatrix4x4 = staticmethod(lambda x, y, z: D2D1MATRIX4X4F(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1))
  MakeScaleMatrix4x4 = staticmethod(lambda x, y, z: D2D1MATRIX4X4F(x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1))
  MakePerspectiveMatrix4x4 = staticmethod(lambda depth: D2D1MATRIX4X4F(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, - 1 / depth, 0, 0, 0, 1))
  MultiplyMatrix4x4 = staticmethod(lambda a, b: a @ b)
ID2D1Factory1 = ID2D1Factory


class _DISPIdUtil:
  _mul_cache = {}
  @staticmethod
  def _asitem(arr, key, value):
    return arr.__class__.__bases__[0].__setitem__(arr, key, DISPID(value) if isinstance(key, int) else list(map(DISPID, value)))
  @staticmethod
  def _avalue(arr):
    return None if (l := len(arr)) == 0 else (arr[0] if l == 1 else (next(iarr := iter(arr)), tuple(iarr)))

class _DISPIdMeta(wintypes.LONG.__class__):
  def __mul__(bcls, size):
    return _DISPIdUtil._mul_cache.get((bcls, size)) or _DISPIdUtil._mul_cache.setdefault((bcls, size), type(('DISPID_Array_%d' % size), (wintypes.LONG.__class__.__mul__(bcls, size),), {'__setitem__': _DISPIdUtil._asitem, 'value': property(_DISPIdUtil._avalue)}))

DISPId = {'Unknown': -1, 'PropertyPut': -3, 'NewEnum': -4, 'Evaluate': -5, 'Constructor': -6, 'Destructor': -7, 'Collect': -8}
DISPID = _DISPIdMeta('DISPID', (_BCode, wintypes.LONG), {'_tab_nc': {**{n.lower(): c for n, c in DISPId.items()}, **{('@' + n.lower()): c for n, c in DISPId.items()}}, '_tab_cn': {c: n for n, c in DISPId.items()}, '_def': -1})
DISPPID = ctypes.POINTER(DISPID)

DISPFlags = {'Method': 1, 'PropertyGet': 2, 'PropertyPut': 4, 'PropertyPutRef': 8}
DISPFLAGS = type('DISPFLAGS', (_BCodeOr, wintypes.WORD), {'_tab_nc': {n.lower(): c for n, c in DISPFlags.items()}, '_tab_cn': {c: n for n, c in DISPFlags.items()}, '_def': 1})

class DISPPARAMS(ctypes.Structure):
  _fields_ = [('rgvarg', wintypes.LPVOID), ('rgdispidNamedArgs', wintypes.LPVOID), ('cArgs', wintypes.UINT), ('cNamedArgs', wintypes.UINT)]
  @classmethod
  def from_params(cls, pargs=(), nargs=None):
    args = (VARIANT * (cargs := len(pargs) + (cnargs := 0)))(*reversed(pargs)) if nargs is None else (VARIANT * (cargs := len(pargs) + (cnargs := len(nargs))))(*reversed(nargs.values()), *reversed(pargs))
    names = None if nargs is None else (DISPID * cnargs)(*reversed(nargs))
    return DISPPARAMS(ctypes.cast(ctypes.pointer(args), wintypes.LPVOID), (None if nargs is None else ctypes.cast(ctypes.pointer(names), wintypes.LPVOID)), cargs, cnargs)
  def to_params(self):
    args = (VARIANT * self.cArgs).from_address(self.rgvarg)
    names = (DISPID * self.cNamedArgs).from_address(self.rgdispidNamedArgs) if self.cNamedArgs else ()
    p = self.cNamedArgs - self.cArgs - 1
    return tuple(args[:p:-1]), dict(zip(names[::-1], args[p::-1]))
  @classmethod
  def from_param(cls, obj):
    return cls.from_params(*obj)
  @property
  def value(self):
    return self.to_params()
DISPPPARAMS = type('DISPPPARAMS', (_BPStruct, ctypes.POINTER(DISPPARAMS)),  {'_type_': DISPPARAMS})

class IDispatch(IUnknown):
  IID = GUID('00020400-0000-0000-C000-000000000046')
  _protos['GetIDsOfNames'] = 5, (wintypes.PGUID, wintypes.PLPOLESTR, wintypes.UINT, wintypes.LCID, DISPPID), (), wintypes.ULONG
  _protos['Invoke'] = 6, (DISPID, wintypes.PGUID, wintypes.LCID, DISPFLAGS, DISPPPARAMS, PVARIANT, wintypes.LPVOID, wintypes.LPVOID), ()
  def GetIDsOfNames(self, member_name, param_names=None, lcid=0):
    mn = member_name.lower()
    if (_cache := getattr(self, '_cache', None)) is None:
      self._cache = _cache = {}
    elif (cids := _cache.get(member_name.lower())) is not None:
      if param_names:
        if cids[1] is not None:
          pids = tuple(map(cids[1].get, map(str.lower, param_names)))
          if all(pid is not None for pid in pids):
            return (cids[0], pids)
      else:
        return cids[0]
    names = wintypes.LPOLESTR(member_name) if (count := 1 if not param_names else 1 + len(param_names)) == 1 else (wintypes.LPOLESTR * count)(member_name, *param_names)
    ids = (DISPID * count)()
    if ISetLastError(self.__class__._protos['GetIDsOfNames'](self.pI, wintypes.GUID(), names, count, lcid, ids)) not in (0, -2147352570):
      return None
    else:
      iids = iter(ids)
      if next(iids).code >= 0:
        if (cids := _cache.get(mn)) is None:
          _cache[mn] = cids = [ids[0], None]
        if count > 1:
          if (pids := cids[1]) is None:
            cids[1] = pids = {}
          for pn, pid in zip(map(str.lower, param_names), iids):
            if pid.code >= 0:
              pids[pn] = pid
      return ids.value
  def Invoke(self, member=0, context_flags=1, pargs=(), nargs=None, res=None, lcid=0):
    if isinstance(member, str) and not member.startswith('@'):
      if nargs:
        member, dids = self.GetIDsOfNames(member, list(map(str, nargs)), lcid)
        nargs = dict(zip((dids[i] if isinstance(name, str) and not name.startswith('@') else name for i, name in enumerate(nargs)), nargs.values()))
      else:
        member = self.GetIDsOfNames(member, None, lcid)
    return None if (r := self.__class__._protos['Invoke'](self.pI, member, wintypes.GUID(), lcid, context_flags, (pargs, nargs), (vr := None if res is False or (res is None and context_flags >= 4) else VARIANT()), None, None)) is None else (True if vr is None else vr.__ctypes_from_outparam__().value)
  def InvokeMethod(self, method, pargs=(), nargs=None, res=None, lcid=0):
    return self.Invoke(method, 1, pargs, nargs, res, lcid)
  def InvokeGet(self, property, pargs=(), nargs=None, res=True, lcid=0):
    return self.Invoke(property, 2, pargs, nargs, res, lcid)
  def InvokeSet(self, property, value, pargs=(), nargs=None, res=False, lcid=0):
    return self.Invoke(property, 4, pargs, ({-3: value} if nargs is None else {-3: value, **nargs}), res, lcid)
  InvokePut = InvokeSet
  def InvokeSetRef(self, property, value, pargs=(), nargs=None, res=False, lcid=0):
    return self.Invoke(property, 8, pargs, ({-3: value} if nargs is None else {-3: value, **nargs}), res, lcid)
  InvokePutRef = InvokeSetRef

class _WMPMAttribute:
  def __set_name__(self, owner, name):
    self.attribute_name = owner.__class__._attributes[owner.ItemType][name]
  def __get__(self, obj, cls=None):
    return self.attribute_name if obj is None else obj.GetItemInfoByName(self.attribute_name)

class _WMPMSCAttribute:
  def __set_name__(self, owner, name):
    self.attribute_name = owner.__class__._scattributes[owner.ItemType][name]
  def __get__(self, obj, cls=None):
    return self.attribute_name if obj is None else obj.GetItemInfoByType(self.attribute_name)

class _WMPMMCAttribute:
  def __set_name__(self, owner, name):
    self.attribute_name = owner.__class__._mcattributes[owner.ItemType][name]
  def __get__(self, obj, cls=None):
    return self.attribute_name if obj is None else obj.GetItemInfosByType(self.attribute_name)

class _IWMPPMeta(_IMeta):
  _attributes = {
    '': {
      'MediaType': 'MediaType',
      'FileSize': 'FileSize',
      'FileType': 'FileType',
      'SourceURL': 'SourceURL',
      'FilePath': 'SourceURL',
      'Title': 'Title'
    },
    'photo': {
      'CameraManufacturer': 'CameraManufacturer',
      'CameraModel': 'CameraModel',
      'CanonicalFileType': 'CanonicalFileType',
      'RecordingTime': 'RecordingTime',
      'RecordingTimeDay': 'RecordingTimeDay',
      'RecordingTimeMonth': 'RecordingTimeMonth',
      'RecordingTimeYear': 'RecordingTimeYear',
      'RecordingTimeDate': 'RecordingTimeYearMonthDay',
      'Height': 'WM/VideoHeight',
      'Width': 'WM/VideoWidth'
    }
  }
  _scattributes = {
    'photo': {
      'RecordingTimestamp': 'RecordingTime'
    }
  }
  _mcattributes = {
  }
  _alias = {'': {}}
  _alias.update({itype: {an.lower(): an for ityp in {'', itype} for a in aa if ityp in a for an in a[ityp]} for aa in ((_attributes, _scattributes, _mcattributes),) for itype in {ityp for a in aa for ityp in a}})
  def _resolve_attribute(cls, alias):
    italias = cls.__class__._alias[cls.ItemType]
    return alias if (an := italias.get(alias.lower())) is None else getattr(italias[_IWMPMMeta], an)
  @classmethod
  def _playlist_class(mcls, media_type=''):
    return mcls._alias.get(media_type.lower(), mcls._alias[''])[_IWMPPMeta]
  def __new__(mcls, name, bases, namespace, **kwds):
    cls = super().__new__(mcls, name, bases, namespace, **kwds)
    mcls._alias.setdefault(namespace.get('ItemType', ''), {})[_IWMPPMeta] = cls
    return cls

class _IWMPMMeta(_IWMPPMeta):
  @classmethod
  def _media_class(mcls, media_type=''):
    return mcls._alias.get(media_type.lower(), mcls._alias[''])[_IWMPMMeta]
  def __new__(mcls, name, bases, namespace, **kwds):
    itype = namespace.get('ItemType', '')
    italias = mcls._alias.setdefault(itype, {})
    namespace.update({an: d() for a, d in zip((mcls._mcattributes, mcls._scattributes, mcls._attributes), (_WMPMMCAttribute, _WMPMSCAttribute, _WMPMAttribute)) if itype in a for an in a[itype]})
    cls = super().__new__(mcls, name, bases, namespace, **kwds)
    italias[_IWMPMMeta] = cls
    return cls

class IWMPMedia(IDispatch, metaclass=_IWMPMMeta):
  IID = GUID(0xf118efc7, 0xf03a, 0x4fb4, 0x99, 0xc9, 0x1c, 0x02, 0xa5, 0xc1, 0x06, 0x5b)
  _protos['get_sourceURL'] = 8, (), (PBSTRING,)
  _protos['get_name'] = 9, (), (PBSTRING,)
  _protos['get_attributeCount'] = 18, (), (wintypes.PLONG,)
  _protos['getAttributeName'] = 19, (wintypes.LONG,), (PBSTRING,)
  _protos['getItemInfo'] = 20, (BSTRING,), (PBSTRING,)
  _protos['getItemInfoByAtom'] = 22, (wintypes.LONG,), (PBSTRING,)
  _protos['getAttributeCountByType'] = 26, (BSTRING, BSTRING), (wintypes.PLONG,)
  _protos['getItemInfoByType'] = 27, (BSTRING, BSTRING, wintypes.LONG), (PVARIANT,)
  ItemType = ''
  def GetSourceURL(self):
    return self.__class__._protos['get_sourceURL'](self.pI)
  def GetName(self):
    return self.__class__._protos['get_name'](self.pI)
  def GetAttributeCount(self):
    return self.__class__._protos['get_attributeCount'](self.pI)
  def GetAttributeName(self, index):
    return self.__class__._protos['getAttributeName'](self.pI, index)
  def GetItemInfo(self, attribute_name):
    return self.__class__._protos['getItemInfo'](self.pI, self.__class__._resolve_attribute(attribute_name))
  def GetItemInfoByAtom(self, attribute_atom):
    return self.__class__._protos['getItemInfoByAtom'](self.pI, attribute_atom)
  def GetItemInfoByName(self, attribute_name):
    return None if (a := self.factory.GetAttributeAtom(self.__class__._resolve_attribute(attribute_name))) is None else self.GetItemInfoByAtom(a)
  def GetAttributeCountByType(self, attribute_type, language=''):
    return self.__class__._protos['getAttributeCountByType'](self.pI, self.__class__._resolve_attribute(attribute_type), language)
  def GetItemInfoByType(self, attribute_type, language='', attribute_index=0):
    if (v := self.__class__._protos['getItemInfoByType'](self.pI, self.__class__._resolve_attribute(attribute_type), language, attribute_index)) is None:
      return None
    return v.value
  def GetItemInfoWithTypeByType(self, attribute_type, language='', attribute_index=0):
    if (v := self.__class__._protos['getItemInfoByType'](self.pI, self.__class__._resolve_attribute(attribute_type), language, attribute_index)) is None:
      return None
    return v.vt, v.value
  def GetItemInfosByType(self, attribute_type, language=''):
    return None if (c := self.GetAttributeCountByType(attribute_type)) is None else tuple(self.GetItemInfoByType(attribute_type, '', ind) for ind in range(c))
  def __getattr__(self, name):
    return self.__getattribute__(name) if (an := self.__class__.__class__._alias[self.__class__.ItemType].get(name.lower())) is None else getattr(self, an)
IWMPMedia3 = IWMPMedia

class IWMPPhoto(IWMPMedia):
  ItemType = 'photo'

class IWMPPlaylist(IDispatch, metaclass=_IWMPPMeta):
  IID = GUID(0xd5f0f4f1, 0x130c, 0x11d3, 0xb1, 0x4e, 0x00, 0xc0, 0x4f, 0x79, 0xfa, 0xa6)
  _protos['get_count'] = 7, (), (wintypes.PLONG,)
  _protos['get_name'] = 8, (), (PBSTRING,)
  _protos['get_attributeCount'] = 10, (), (wintypes.PLONG,)
  _protos['getAttributeName'] = 11, (wintypes.LONG,), (PBSTRING,)
  _protos['get_item'] = 12, (wintypes.LONG,), (wintypes.PLPVOID,)
  _protos['getItemInfo'] = 13, (BSTRING,), (PBSTRING,)
  ItemType = ''
  def GetName(self):
    return self.__class__._protos['get_name'](self.pI)
  def GetAttributeCount(self):
    return self.__class__._protos['get_attributeCount'](self.pI)
  def GetAttributeName(self, index):
    return self.__class__._protos['getAttributeName'](self.pI, index)
  def GetItemInfo(self, attribute_name):
    return self.__class__._protos['getItemInfo'](self.pI, self.__class__._resolve_attribute(attribute_name))
  def GetCount(self):
    return self.__class__._protos['get_count'](self.pI)
  def GetItem(self, index):
    return _IUtil.QueryInterface(IUnknown(self.__class__._protos['get_item'](self.pI, index)), _IWMPMMeta._media_class(self.__class__.ItemType), self.factory)
  def GetItems(self):
    if (c := self.GetCount()) is None:
      return None
    return (self.GetItem(ind) for ind in range(c))
  def GetInfos(self, *attributes):
    return None if (ms := self.GetItems()) is None else (tuple(m.GetItemInfoByName(a) for a in attributes) for m in ms)

class IWMPPPlaylist(IWMPPlaylist):
  ItemType = 'photo'

class IWMPQuery(IDispatch):
  IID = GUID(0xa00918f3, 0xa6b0, 0x4bfb, 0x91, 0x89, 0xfd, 0x83, 0x4c, 0x7b, 0xc5, 0xa5)
  _protos['addCondition'] = 7, (BSTRING, BSTRING, BSTRING), ()
  _protos['beginNextGroup'] = 8, (), ()
  def AddCondition(self, attribute_name, operator, value):
    return self.__class__._protos['addCondition'](self.pI, attribute_name, operator, value)
  def BeginNextGroup(self):
    return self.__class__._protos['beginNextGroup'](self.pI)

class IWMPMediaCollection(IDispatch):
  IID = GUID(0x8ba957f5, 0xfd8c, 0x4791, 0xb8, 0x2d, 0xf8, 0x40, 0x40, 0x1e, 0xe4, 0x74)
  _protos['getAll'] = 8, (), (wintypes.PLPVOID,)
  _protos['getByName'] = 9, (BSTRING,), (wintypes.PLPVOID,)
  _protos['getByAttribute'] = 13, (BSTRING, BSTRING), (wintypes.PLPVOID,)
  _protos['getMediaAtom'] = 16, (BSTRING,), (wintypes.PLONG,)
  _protos['createQuery'] = 19, (), (wintypes.PLPVOID,)
  _protos['getPlaylistByQuery'] = 20, (wintypes.LPVOID, BSTRING, BSTRING, wintypes.VARIANT_BOOL), (wintypes.PLPVOID,)
  _protos['getByAttributeAndMediaType'] = 22, (BSTRING, BSTRING, BSTRING), (wintypes.PLPVOID,)
  def __new__(cls, *args, **kwargs):
    self = IUnknown.__new__(cls, *args, **kwargs)
    self._attribute_atom = {}
    return self
  def GetAll(self):
    return IWMPPlaylist(self.__class__._protos['getAll'](self.pI), self)
  def GetByName(self, name):
    return IWMPPlaylist(self.__class__._protos['getByName'](self.pI, name), self)
  def GetByAttribute(self, attribute_name, value):
    return IWMPPlaylist(self.__class__._protos['getByAttribute'](self.pI, IWMPPlaylist._resolve_attribute(attribute_name), value), self)
  def GetByMediaType(self, media_type):
    return _IWMPPMeta._playlist_class(media_type)(self.__class__._protos['getByAttribute'](self.pI, 'MediaType', media_type), self)
  def GetByAttributeAndMediaType(self, attribute_name, value, media_type):
    icls = _IWMPPMeta._playlist_class(media_type)
    return icls(self.__class__._protos['getByAttributeAndMediaType'](self.pI, icls._resolve_attribute(attribute_name), value, media_type), self)
  def GetMediaAtom(self, attribute_name):
    return self.__class__._protos['getMediaAtom'](self.pI, attribute_name)
  def GetAttributeAtom(self, attribute_name):
    if attribute_name in self._attribute_atom:
      return self._attribute_atom[attribute_name]
    else:
      if (a := self.GetMediaAtom(attribute_name)) is not None and a >= 0:
        self._attribute_atom[attribute_name] = a
      return a
  def CreateQuery(self, *conditions_groups, media_type=''):
    if (IQuery := IWMPQuery(self.__class__._protos['createQuery'](self.pI), self)) is None:
      return None
    n = False
    icls = _IWMPPMeta._playlist_class(media_type)
    for cs in conditions_groups:
      if n:
        if IQuery.BeginNextGroup() is None:
          return None
      else:
        n = True
      for c in (cs if isinstance(cs[0], (list, tuple)) else (cs,)):
        if IQuery.AddCondition(icls._resolve_attribute(c[0]), c[1], c[2]) is None:
          return None
    return IQuery
  def GetByQuery(self, query, media_type, sort_attribute='', sort_ascending=True):
    icls = _IWMPPMeta._playlist_class(media_type)
    return icls(self.__class__._protos['getPlaylistByQuery'](self.pI, query, media_type, icls._resolve_attribute(sort_attribute), sort_ascending), self)
  def GetByFolder(self, folder_name, media_type, sort_attribute='', sort_ascending=True):
    return None if (q := self.CreateQuery(('SourceURL', 'BeginsWith', folder_name.rstrip('\\') + '\\'), media_type=media_type)) is None else self.GetByQuery(q, media_type, sort_attribute, sort_ascending)
  def GetPhotos(self):
    return self.GetByMediaType('photo')
  def GetPhotosByAttribute(self, attribute_name, value):
    return self.GetByAttributeAndMediaType(attribute_name, value, 'photo')
  def CreatePhotoQuery(self, *conditions_groups):
    return self.CreateQuery(*conditions_groups, media_type='photo')
  def GetPhotosByQuery(self, query, sort_attribute='', sort_ascending=True):
    return self.GetByQuery(query, 'photo', sort_attribute, sort_ascending)
  def GetPhotosByFolder(self, folder_name, sort_attribute='', sort_ascending=True):
    return self.GetByFolder(folder_name, 'photo', sort_attribute, sort_ascending)
IWMPMediaCollection2 = IWMPMediaCollection

class IWMPCore(IDispatch):
  CLSID = 'WMPlayer.ocx'
  IID = GUID(0x7587C667, 0x628f, 0x499f, 0x88, 0xe7, 0x6a, 0x6f, 0x4e, 0x88, 0x84, 0x64)
  _protos['get_mediaCollection'] = 16, (), (wintypes.PLPVOID,)
  def GetMediaCollection(self):
    return _IUtil.QueryInterface(IUnknown(self.__class__._protos['get_mediaCollection'](self.pI), self), IWMPMediaCollection)
  def GetMedia(self):
    return None if (pl := self.GetMediaCollection()) is None else pl.GetAll()
  def GetPhotos(self):
    return None if (pl := self.GetMediaCollection()) is None else pl.GetPhotos()
  def GetPhotosByQuery(self, conditions_groups, sort_attribute='', sort_ascending=True):
    return None if (pl := self.GetMediaCollection()) is None else (None if (q := pl.CreatePhotoQuery(*conditions_groups)) is None else pl.GetPhotosByQuery(q, sort_attribute, sort_ascending))
  def GetPhotosByFolder(self, folder_name, sort_attribute='', sort_ascending=True):
    return None if (pl := self.GetMediaCollection()) is None else pl.GetPhotosByFolder(folder_name, sort_attribute, sort_ascending)
IWMPCore3 = IWMPCore


class _WShUtil:
  @staticmethod
  def _wrap(n, *r_a, p=sh32):
    r, *a = r_a if r_a and r_a[0][1] == 0 else (None, *r_a)
    if r is None:
      f = ctypes.WINFUNCTYPE(wintypes.ULONG, *(t[0] for t in a))(*((p, n) if isinstance(p, int) else ((n, p),)), tuple((t[1],) for t in a))
      f.errcheck = _IUtil._errcheck_o if 2 in (t[1] for t in a) else _IUtil._errcheck_no
    else:
      f = ctypes.WINFUNCTYPE(*(t[0] for t in r_a), use_last_error=True)(*((p, n) if isinstance(p, int) else ((n, p),)), tuple((t[1],) for t in a))
      if 2 not in (t[1] for t in a):
        f.errcheck = _IUtil._errcheck_r
    return f
  @staticmethod
  def _bind_pidls(pidl, pidl0):
    if pidl is not None:
      pidl._needsfree = False
      pidl._base_pidl = pidl0
    return pidl
  @staticmethod
  def _subst_pidls(pidl, pidl0):
    if pidl is not None:
      setattr(wintypes.LPVOID.from_buffer(pidl0), 'value', None)
    return pidl
  @staticmethod
  def _set_factory(i, factory=None):
    if i is not None:
      if factory is False:
        i.factory = None
      elif factory is not None:
        i.factory = factory
    return i
  @staticmethod
  def _get_str(pwstr):
    if not pwstr:
      return None
    pwstr = ctypes.cast(pwstr, wintypes.LPWSTR)
    s = pwstr.value
    ole32.CoTaskMemFree(pwstr)
    return s

WSBindFlags = {'MayBotherUser': 1, 'JustTestExistence': 2}
WSBINDFLAGS = type('WSBINDFLAGS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSBindFlags.items()}, '_tab_cn': {c: n for n, c in WSBindFlags.items()}, '_def': 0})

WSStgm = (
  {'Read': 0x0, 'Write': 0x1, 'ReadWrite': 0x2},
  {'DenyNone': 0x40, 'DenyRead': 0x30, 'DenyWrite': 0x20, 'Exclusive': 0x10, 'Priority': 0x40000},
  {'Create': 0x1000, 'Convert': 0x20000, 'FailIfThere': 0x0},
  {'Direct': 0x0, 'Transacted': 0x10000},
  {'NoScratch': 0x100000, 'NoSnapshot': 0x200000},
  {'Simple': 0x8000000, 'DirectSWMR': 0x400000},
  {'DeleteOnRelease': 0x4000000}
)
_WSSTGMs = tuple(type(('WSSTGM%d' % g), (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in group.items()}, '_tab_cn': {c: n for n, c in group.items()}, '_def': 0}) for g, group in enumerate(WSStgm))
class WSSTGM(_BCode, wintypes.DWORD):
  @classmethod
  def name_code(cls, n):
    if not isinstance(n, str):
      return n
    c = 0
    for n_ in filter(None, n.lower().replace(' ', '|').replace('+', '|').split('|')):
      for _WSSTGM in _WSSTGMs:
        c |= _WSSTGM.name_code(n_)
    return c
  @classmethod
  def code_name(cls, c):
    n = []
    for _WSSTGM in _WSSTGMs:
      o = 0
      for c_ in _WSSTGM._tab_nc.values():
        o |= c_
      if not (n_ := _WSSTGM.code_name(c & o)).isdecimal():
        n.append(n_)
    return ' | '.join(n)


WSFileAttributes = {'ReadOnly': 1, 'Hidden': 2, 'System': 4, 'Directory': 16, 'Archive': 32, 'Device': 64, 'Normal': 128, 'Temporary': 256, 'SparseFile': 512, 'ReparsePoint': 1024, 'Compressed': 2048, 'Offline': 4096, 'NotContentIndexed': 8192, 'Encrypted': 16384, 'IntegrityStream': 32768, 'Virtual': 65536, 'NoScrubData': 131072, 'EA': 262144, 'Pinned': 524288, 'Unpinned': 1048576, 'RecallOnOpen': 262144, 'RecallOnDataAccess': 4194304}
WSFILEATTRIBUTES = type('WSFILEATTRIBUTES', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSFileAttributes.items()}, '_tab_cn': {c: n for n, c in WSFileAttributes.items()}, '_def': 128})

class WSFINDDATA(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('dwFileAttributes', WSFILEATTRIBUTES), ('ftCreationTime', FILETIME), ('ftLastAccessTime', FILETIME), ('ftLastWriteTime', FILETIME), ('nFileSizeHigh', wintypes.DWORD), ('nFileSizeLow', wintypes.DWORD), ('dwReserved0', wintypes.DWORD), ('dwReserved1', wintypes.DWORD), ('cFileName', wintypes.WCHAR * 260), ('cAlternateFileName', wintypes.WCHAR * 14)]
  @classmethod
  def from_param(cls, obj):
    if isinstance(obj, dict):
      if (fs := obj.get('nFileSize')) is not None:
        obj['nFileSizeHigh'] = fs >> 32
        obj['nFileSizeLow'] = fs & 0xffffffff
      obj.setdefault('cFileName', '')
      obj.setdefault('cAlternateFileName', '')
    return super().from_param(obj)
  def to_dict(self):
    d = super().to_dict()
    d['nFileSize'] = (d['nFileSizeHigh'] << 32) + d['nFileSizeLow']
    return d
  def to_tuple(self):
    return tuple(getattr(self, n) for n, t in self.__class__._fields_)
WSPFINDDATA = type('WSPFINDDATA', (_BPStruct, ctypes.POINTER(WSFINDDATA)), {'_type_': WSFINDDATA})

class _BDSStruct(_BDStruct):
  def __init__(self, *args, **kwargs):
    super().__init__(ctypes.sizeof(self.__class__), *args, **kwargs)
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, dict):
      next((f := iter(cls._fields_)), None)
      return cls(*(obj.get(k[0], 0) for k in f))
    else:
      return cls(*(obj[i] for i in range(min(len(cls._fields_) - 1, len(obj)))))
  def to_dict(self):
    next((f := iter(self.__class__._fields_)), None)
    return {k[0]: getattr(self, k[0]) for k in f}

class WSBINDOPTS(_BDSStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cbStruct', wintypes.DWORD), ('grfFlags', WSBINDFLAGS), ('grfMode', WSSTGM), ('dwTickCountDeadline', wintypes.DWORD), ('dwTrackFlags', wintypes.DWORD), ('dwClassContext', wintypes.DWORD), ('locale', wintypes.LCID), ('pServerInfo', wintypes.LPVOID), ('hwnd', wintypes.HWND)]
WSPBINDOPTS = type('WSPBINDOPTS', (_BPStruct, ctypes.POINTER(WSBINDOPTS)),  {'_type_': WSBINDOPTS})

WSWindowShow = {'Hidden': 0, 'Normal': 1, 'ShowNormal': 1, 'ShowMinimized': 2, 'Maximize': 3, 'ShowMaximized': 3, 'ShowNoActivate': 4, 'Show': 5, 'Minimize': 6, 'ShowMinNoactive': 7, 'ShowNA': 8, 'Restore': 9, 'ShowDefault': 10, 'ForceMinimize': 11}
WSWINDOWSHOW = type('WSWINDOWSHOW', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in WSWindowShow.items()}, '_tab_cn': {c: n for n, c in WSWindowShow.items()}, '_def': 1})

class WSCMINVOKECOMMANDINFO(_BDSStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cbSize', wintypes.DWORD), ('fMask', wintypes.DWORD), ('hwnd', wintypes.HWND), ('lpVerb', wintypes.LPCSTR), ('lpParameters', wintypes.LPCSTR), ('lpDirectory', wintypes.LPCSTR), ('nShow', WSWINDOWSHOW), ('dwHotKey', wintypes.DWORD), ('hIcon', wintypes.HANDLE)]
WSPCMINVOKECOMMANDINFO = type('WSPCMINVOKECOMMANDINFO', (_BPStruct, ctypes.POINTER(WSCMINVOKECOMMANDINFO)), {'_type_': WSCMINVOKECOMMANDINFO})

WSSfgao = {'CanCopy': 0x1, 'CanMove': 0x2, 'CanLink': 0x4, 'Storage': 0x8, 'CanRename': 0x10, 'CanDelete': 0x20, 'HasPropSheet': 0x40, 'DropTarget': 0x100, 'System': 0x1000, 'Encrypted': 0x2000, 'IsSlow': 0x4000, 'Ghosted': 0x8000, 'Link': 0x10000, 'Share': 0x20000, 'ReadOnly': 0x40000, 'Hidden': 0x80000, 'NonEnumerated': 0x100000, 'NewContent': 0x200000, 'Stream': 0x400000, 'StorageAncestor': 0x800000, 'Validate': 0x1000000, 'Removable': 0x2000000, 'Compressed': 0x4000000, 'Browsable': 0x8000000, 'FileSysAncestor': 0x10000000, 'Folder': 0x20000000, 'FileSystem': 0x40000000, 'HasSubFolder': 0x80000000}
WSSFGAO = type('WSSFGAO', (_BCodeOr, wintypes.ULONG), {'_tab_nc': {n.lower(): c for n, c in WSSfgao.items()}, '_tab_cn': {c: n for n, c in WSSfgao.items()}, '_def': 0})
WSPSFGAO = ctypes.POINTER(WSSFGAO)

WSShcids = {'AllFields': 0x80000000, 'CanonicalOnly': 0x10000000}
WSSHCIDS = type('WSSHCIDS', (_BCodeOr, wintypes.LPARAM), {'_tab_nc': {n.lower(): c for n, c in WSShcids.items()}, '_tab_cn': {c: n for n, c in WSShcids.items()}, '_def': 0})

WSShgdnf = {'Normal': 0, 'InFolder': 0x1, 'ForEditing': 0x1000, 'ForAddressBar': 0x4000, 'ForParsing': 0x8000}
WSSHGDNF = type('WSSHGDNF', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSShgdnf.items()}, '_tab_cn': {c: n for n, c in WSShgdnf.items()}, '_def': 0})

WSShcontf = {'CheckingForChildren': 0x10, 'Folders': 0x20, 'NonFolders': 0x40, 'IncludeHidden': 0x80, 'NetPrinterSrch': 0x200, 'Shareable': 0x400, 'Storage': 0x800, 'NavigationEnum': 0x1000, 'FastItems': 0x2000, 'FlatList': 0x4000, 'EnableAsync': 0x8000, 'IncludeSuperHidden': 0x10000}
WSSHCONTF = type('WSSHCONTF', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSShcontf.items()}, '_tab_cn': {c: n for n, c in WSShcontf.items()}, '_def': 0})

WSSigdn = {'Normal': 0, 'NormalDisplay': 0, 'ParentRelativeParsing': 0x80018001, 'DesktopAbsoluteParsing': 0x80028000, 'ParentRelativeEditing': 0x80031001, 'DesktopAbsoluteEditing': 0x8004c000, 'FileSyspath': 0x80058000, 'Url': 0x80068000, 'ParentRelativeForAddressBar': 0x8007c001, 'ParentRelative': 0x80080001, 'ParentRelativeForUI': 0x80094001}
WSSIGDN = type('WSSIGDN', (_BCode, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WSSigdn.items()}, '_tab_cn': {c: n for n, c in WSSigdn.items()}, '_def': 0})

WSSichintf = {'Display': 0, 'AllFields': 0x80000000, 'Canonical': 0x10000000, 'TestFileSyspathIfNotEqual': 0x20000000}
WSSICHINTF = type('WSSICHINTF', (_BCode, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSSichintf.items()}, '_tab_cn': {c: n for n, c in WSSichintf.items()}, '_def': 0})

class WSDVTARGETDEVICE(_BDSStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('tdSize', wintypes.DWORD), ('tdDriverNameOffset', wintypes.WORD), ('tdDeviceNameOffset', wintypes.WORD), ('tdPortNameOffset', wintypes.WORD), ('tdExtDevmodeOffset', wintypes.WORD), ('tdData', wintypes.BYTE * 0)]
WSPDVTARGETDEVICE = type('WSPDVTARGETDEVICE', (_BPStruct, ctypes.POINTER(WSDVTARGETDEVICE)),  {'_type_': WSDVTARGETDEVICE})

WSTymed = {'Null': 0, 'HGlobal': 1, 'File': 2, 'IStream': 4, 'IStorage': 8, 'GDI': 16, 'MFPict': 32, 'EnhMF': 64}
WSTYMED = type('WSTYMED', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSTymed.items()}, '_tab_cn': {c: n for n, c in WSTymed.items()}, '_def': 0})

WSCfFormat = {'Bitmap': 2, 'Dib': 8, 'EnhMetaFile': 14, 'HDrop': 15, 'MetaFilePict': 3, 'Text': 1, 'Tiff': 6, 'UnicodeText': 13}
WSCfFormatEq = {'shidlistarray': 'Shell IDList Array', 'preferreddropeffect': 'Preferred DropEffect', 'performeddropeffect': 'Performed DropEffect', 'pastesucceeded': 'Paste Succeeded'}
class WSCFFORMAT(_BCode, wintypes.WORD):
  _tab_nc = {n.lower(): c for n, c in WSCfFormat.items()}
  _tab_cn = {c: n for n, c in WSCfFormat.items()}
  _def = 1
  user32.RegisterClipboardFormatW.restype = wintypes.UINT
  user32.GetClipboardFormatNameW.restype = wintypes.INT
  @staticmethod
  def wname_code(n):
    return user32.RegisterClipboardFormatW(wintypes.LPCWSTR(WSCfFormatEq.get(n.lower(), n))) or None
  @staticmethod
  def code_wname(c):
    b = ctypes.create_unicode_buffer(1024)
    return b.value if user32.GetClipboardFormatNameW(wintypes.UINT(c), ctypes.byref(b), 1024) else None
  @classmethod
  def name_code(cls, n):
    return cls._tab_nc.get(n.lower(), (cls.wname_code(n) or cls._def)) if isinstance(n, str) else n
  @classmethod
  def code_name(cls, c):
    return cls._tab_cn.get(c, ((cls.code_wname(c) or str(c)) if isinstance(c, int) and c >= 0xc000 and c <= 0xffff else str(c)))

WSDvAspect = {'Content': 1, 'Thumbnail': 2, 'Icon': 4, 'DocPrint': 8}
WSDVASPECT = type('WSDVASPECT', (_BCode, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WSDvAspect.items()}, '_tab_cn': {c: n for n, c in WSDvAspect.items()}, '_def': 1})

class WSFORMATETC(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cfFormat', WSCFFORMAT), ('ptd', WSPDVTARGETDEVICE), ('dwAspect', WSDVASPECT), ('lindex', wintypes.LONG), ('tymed', WSTYMED)]
WSPFORMATETC = type('WSPFORMATETC', (_BPStruct, ctypes.POINTER(WSFORMATETC)),  {'_type_': WSFORMATETC})

class WSSTGMEDIUM(ctypes.Structure, metaclass=_WSMeta):
  _anonymous_ = ('un',)
  _fields_ = [('tymed', WSTYMED), ('un', ctypes.Union.__class__('WSSTGMEDIUM_UN', (ctypes.Union,), {'_fields_': [('hBitmap', wintypes.HBITMAP), ('hMetaFilePict', wintypes.HANDLE), ('hEnhMetaFile', wintypes.HANDLE), ('hGlobal', wintypes.HGLOBAL), ('lpszFileName', wintypes.LPOLESTR), ('pstm', PCOMSTREAM), ('pstg', PCOM)]})), ('pUnkForRelease', PCOM)]
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._needsclear = bool(self._pUnkForRelease)
  @classmethod
  def from_param(cls, obj):
    if obj is None or isinstance(obj, cls):
      return obj
    if isinstance(obj, dict):
      return cls(*(((t.from_param(obj[n]) if n in obj else t()) if issubclass(t, ctypes.Structure) else ((ctypes.cast(obj.get('data'), wintypes.LPVOID),) if issubclass(t, ctypes.Union) else obj.get(n, 0))) for n, t in cls._fields_))
    else:
      return cls(*((t.from_param(o) if issubclass(t, ctypes.Structure) else ((ctypes.cast(o, wintypes.LPVOID),) if issubclass(t, ctypes.Union) else o)) for (n, t), o in zip(cls._fields_, obj)))
  def to_dict(self):
    if isinstance((d := getattr(self, {1: 'hGlobal', 2: 'lpszFileName', 4: 'pstm', 8: 'pstg', 16: 'hBitmap', 32: 'hMetaFilePict', 64: 'hEnhMetaFile'}.get(self.tymed.code, ''), None)), int):
      d = wintypes.LPVOID(d)
      d._stgm = self
    else:
      d = getattr(d, 'content', d)
    return {'tymed': self.tymed, 'data': d, 'pUnkForRelease': self.pUnkForRelease}
  def __del__(self):
    if getattr(self, '_needsclear', False):
      ole32.ReleaseStgMedium(ctypes.byref(self))
    getattr(self.__class__.__bases__[0], '__del__', id)(self)
  @property
  def value(self):
    return self.to_dict()
  def __ctypes_from_outparam__(self):
    self._needsclear = not bool(self._pUnkForRelease)
    return self.value
  @classmethod
  def _get_data(cls, stg_medium, tymed):
    if isinstance(stg_medium, ctypes.Structure):
      stg_medium = cls.to_dict(stg_medium)
    elif not isinstance(stg_medium, dict):
      if stg_medium is None or len(stg_medium) < 2:
        return None
      stg_medium = {'tymed': stg_medium[0], 'data': stg_medium[1]}
    return stg_medium.get('data') if stg_medium.get('tymed') == tymed else None
WSPSTGMEDIUM = type('WSPSTGMEDIUM', (_BPStruct, ctypes.POINTER(WSSTGMEDIUM)),  {'_type_': WSSTGMEDIUM})

WSDataDir = {'Get': 1, 'Set': 2}
WSDATADIR = type('WSDATADIR', (_BCode, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WSDataDir.items()}, '_tab_cn': {c: n for n, c in WSDataDir.items()}, '_def': 1})

SIZE = _WSMeta('SIZE', (_BTStruct, wintypes.SIZE), {})

WSFDFlags = {'None': 0, 'Clsid': 0x1, 'SizePoint': 0x2, 'Attributes': 0x4, 'CreateTime': 0x8, 'AccessTime': 0x10, 'WritesTime': 0x20, 'FileSize': 0x40, 'ProgressUI': 0x4000, 'LinkUI': 0x8000, 'Unicode': 0x80000000}
WSFDFLAGS = type('WSFDFLAGS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSFDFlags.items()}, '_tab_cn': {c: n for n, c in WSFDFlags.items()}, '_def': 0})

class WSFILEDESCRIPTOR(_BDStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('dwFlags', WSFDFLAGS), ('clsid', wintypes.GUID), ('sizel', SIZE), ('pointl', POINT), ('dwFileAttributes', WSFILEATTRIBUTES), ('ftCreationTime', FILETIME), ('ftLastAccessTime', FILETIME), ('ftLastWriteTime', FILETIME), ('nFileSizeHigh', wintypes.DWORD), ('nFileSizeLow', wintypes.DWORD), ('cFileName', wintypes.WCHAR * 260)]
  @classmethod
  def from_param(cls, obj):
    if isinstance(obj, dict):
      if (fs := obj.get('nFileSize')) is not None:
        obj['nFileSizeHigh'] = fs >> 32
        obj['nFileSizeLow'] = fs & 0xffffffff
      obj.setdefault('cFileName', '')
    return super().from_param(obj)
  def to_dict(self):
    d = super().to_dict()
    d['nFileSize'] = (d['nFileSizeHigh'] << 32) + d['nFileSizeLow']
    return d
WSPFILEDESCRIPTOR = type('WSPFILEDESCRIPTOR', (_BPStruct, ctypes.POINTER(WSFILEDESCRIPTOR)), {'_type_': WSFILEDESCRIPTOR})

class WSFILEGROUPDESCRIPTOR(ctypes.Structure):
  _fields_ = [('cItems', wintypes.UINT), ('fgd', WSFILEDESCRIPTOR * 0)]
  def to_tuple(self):
    return tuple(fd.value for fd in (WSFILEDESCRIPTOR * self.cItems).from_address(ctypes.addressof(self.fgd)))
  @property
  def value(self):
    return self.to_tuple()
WSPFILEGROUPDESCRIPTOR = type('WSPFILEGROUPDESCRIPTOR', (_BPStruct, ctypes.POINTER(WSFILEGROUPDESCRIPTOR)),  {'_type_': WSFILEGROUPDESCRIPTOR})

class WSCIDA(_BTStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cidl', wintypes.UINT), ('aoffset', wintypes.UINT * 0)]
  def to_tuple(self):
    a = ctypes.addressof(self)
    ofs =  iter((wintypes.UINT * (self.cidl + 1)).from_address(a + self.__class__.aoffset.offset))
    return (ctypes.cast(a + next(ofs), WSPITEMIDLIST).Clone(), tuple(ctypes.cast(a + o, WSPITEMIDLIST).Clone() for o in ofs))
  @property
  def value(self):
    return self.to_tuple()
WSPCIDA = type('WSPCIDA', (_BPStruct, ctypes.POINTER(WSCIDA)),  {'_type_': WSCIDA})

WSKeyState = {'LButton': 0x1, 'RButton': 0x2, 'MButton': 0x10, 'Shift': 0x4, 'Ctrl': 0x8, 'Control': 0x8, 'Alt': 0x20}
WSKEYSTATE = type('WSKEYSTATE', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSKeyState.items()}, '_tab_cn': {c: n for n, c in WSKeyState.items()}, '_def': 0})

POINT = _WSMeta('POINT', (_BTStruct, wintypes.POINT), {})

WSDropEffect = {'None': 0, 'Copy': 0x1, 'Move': 0x2, 'Link': 0x4, 'Scroll': 0x80000000}
WSDROPEFFECT = type('WSDROPEFFECT', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSDropEffect.items()}, '_tab_cn': {c: n for n, c in WSDropEffect.items()}, '_def': 0})
WSPDROPEFFECT = ctypes.POINTER(WSDROPEFFECT)

WSBhid = {
  'SFObject': GUID(0x3981e224, 0xf559, 0x11d3, 0x8e, 0x3a, 0x00, 0xc0, 0x4f, 0x68, 0x37, 0xd5),
  'SFUIObject': GUID(0x3981e225, 0xf559, 0x11d3, 0x8e, 0x3a, 0x00, 0xc0, 0x4f, 0x68, 0x37, 0xd5),
  'Stream': GUID(0x1cebb3ab, 0x7c10, 0x499a, 0xa4, 0x17, 0x92, 0xca, 0x16, 0xc4, 0xcb, 0x83),
  'LinkTargetItem': GUID(0x3981e228, 0xf559, 0x11d3, 0x8e, 0x3a, 0x00, 0xc0, 0x4f, 0x68, 0x37, 0xd5),
  'StorageEnum': GUID(0x4621a4e3, 0xf0d6, 0x4773, 0x8a, 0x9c, 0x46, 0xe7, 0x7b, 0x17, 0x48, 0x40),
  'EnumItems': GUID(0x94f60519, 0x2850, 0x4924, 0xaa, 0x5a, 0xd1, 0x5e, 0x84, 0x86, 0x80, 0x39),
  'DataObject': GUID(0xb8c0bd9f, 0xed24, 0x455c, 0x83, 0xe6, 0xd5, 0x39, 0x0c, 0x4f, 0xe8, 0xc4)
}
WSBHID = _GMeta('WSBHID', (_BGUID, wintypes.GUID), {'_type_': ctypes.c_char, '_length_': 16, '_tab_ng': {n.lower(): g for n, g in WSBhid.items()}, '_tab_gn': {g: n for n, g in WSBhid.items()}, '_def': None})
WSPBHID = type('WSPBHID', (_BPGUID, ctypes.POINTER(WSBHID)), {'_type_': WSBHID})

WSSiattribflags = {'And': 0x1, 'Or': 0x2, 'AppCompat': 0x3, 'AllItems': 0x4000}
WSSIATTRIBFLAGS = type('WSSIATTRIBFLAGS', (_BCodeOr, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WSSiattribflags.items()}, '_tab_cn': {c: n for n, c in WSSiattribflags.items()}, '_def': 0})

WSSiigbf = {'ResizeToFit': 0, 'BiggerSizeOK': 0x1, 'MemoryOnly': 0x2, 'IconOnly': 0x4, 'ThumbnailOnly': 0x8, 'InCacheOnly': 0x10, 'CropToSquare': 0x20, 'WideThumbnails': 0x40, 'IconBackground': 0x80, 'ScaleUp': 0x100}
WSSIIGBF = type('WSSIIGBF', (_BCodeOr, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WSSiigbf.items()}, '_tab_cn': {c: n for n, c in WSSiigbf.items()}, '_def': 0})

WSOperationFlags = {'AllowUndo': 0x40, 'FilesOnly': 0x80, 'NoConfirmation': 0x10, 'NoConfirmMkDir': 0x200, 'NoConnectedElements': 0x2000, 'NoCopySecurityAttribs': 0x800, 'NoErrorUI': 0x400, 'NoRecursion': 0x1000, 'RenameOnCollision': 0x8, 'Silent': 0x4, 'WantNukeWarning': 0x4000, 'AddUndoRecord': 0x20000000, 'NoSkipJunctions': 0x10000, 'PreferHardLink': 0x20000, 'ShowElevationPrompt': 0x40000, 'EarlyFailure': 0x100000, 'PreserveFileExtensions': 0x200000, 'KeepNewerFile': 0x400000, 'NoCopyHooks': 0x800000, 'NoMinimizeBox': 0x1000000, 'MoveACLSAcrossVolumes': 0x2000000, 'DontDisplaySourcePath': 0x4000000, 'RecycleOnDelete': 0x80000, 'RequireElevation': 0x10000000, 'CopyAsDownload': 0x40000000, 'DontDisplayLocations': 0x80000000}
WSOPERATIONFLAGS = type('WSOPERATIONFLAGS', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WSOperationFlags.items()}, '_tab_cn': {c: n for n, c in WSOperationFlags.items()}, '_def': 0x240})

class _COM_IFileSystemBindData(_COM_IUnknown):
  _iids.add(GUID(0x3acf075f, 0x71db, 0x4afa, 0x81, 0xf0, 0x3f, 0xc4, 0xfd, 0xf2, 0xa5, 0xb8))
  _iids.add(GUID(0x01e18d10, 0x4d8b, 0x11d2, 0x85, 0x5d, 0x00, 0x60, 0x08, 0x05, 0x93, 0x67))
  _vtbl['SetFindData'] = (wintypes.ULONG, wintypes.LPVOID, WSPFINDDATA)
  _vtbl['GetFindData'] = (wintypes.ULONG, wintypes.LPVOID, WSPFINDDATA)
  _vtbl['SetFileID'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.LARGE_INTEGER)
  _vtbl['GetFileID'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PLARGE_INTEGER)
  _vtbl['SetJunctionCLSID'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PBYTES16)
  _vtbl['GetJunctionCLSID'] = (wintypes.ULONG, wintypes.LPVOID, wintypes.PBYTES16)
  _vars['fd'] = WSFINDDATA
  _vars['fid'] = wintypes.LARGE_INTEGER
  _vars['jclsid'] = wintypes.BYTES16
  @classmethod
  def _SetFindData(cls, pI, pfd):
    with cls[pI] as self:
      if not self or not pfd:
        return 0x80004003
      self.fd.__init__(*pfd.contents.to_tuple())
      return 0
  @classmethod
  def _GetFindData(cls, pI, pfd):
    with cls[pI] as self:
      if not self or not pfd:
        return 0x80004003
      pfd.contents.__init__(*self.fd.to_tuple())
      return 0
  @classmethod
  def _SetFileID(cls, pI, fid):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      self.fid = fid
      return 0
  @classmethod
  def _GetFileID(cls, pI, pfid):
    with cls[pI] as self:
      if not self or not pfid:
        return 0x80004003
      pfid.contents.value = self.fid
      return 0
  @classmethod
  def _SetJunctionCLSID(cls, pI, pjclsid):
    with cls[pI] as self:
      if not self or not pjclsid:
        return 0x80004003
      self.jclsid[:] = pjclsid.contents
      return 0
  @classmethod
  def _GetJunctionCLSID(cls, pI, pjclsid):
    with cls[pI] as self:
      if not self or not pjclsid:
        return 0x80004003
      pjclsid.contents[:] = self.jclsid
      return 0

class _COM_IFileSystemBindData_impl(metaclass=_COMMeta, interfaces=(_COM_IFileSystemBindData,)):
  CLSID = True
_COM_IFileSystemBindData._impl = _COM_IFileSystemBindData_impl

class IFileSystemBindData(IUnknown):
  IID = GUID(0x3acf075f, 0x71db, 0x4afa, 0x81, 0xf0, 0x3f, 0xc4, 0xfd, 0xf2, 0xa5, 0xb8)
  _protos['SetFindData'] = 3, (WSPFINDDATA,), ()
  _protos['GetFindData'] = 4, (), (WSPFINDDATA,)
  _protos['SetFileID'] = 5, (wintypes.LARGE_INTEGER,), ()
  _protos['GetFileID'] = 6, (), (wintypes.PLARGE_INTEGER,)
  _protos['SetJunctionCLSID'] = 7, (PUUID,), ()
  _protos['GetJunctionCLSID'] = 8, (), (PUUID,)
  def __new__(cls, clsid_component=False, factory=None, find_data=None, file_id=None, junction_clsid=None):
    if (self := IUnknown.__new__(cls, clsid_component, factory)) is None:
      return None
    if find_data is not None:
      self.SetFindData(find_data)
    if file_id is not None:
      self.SetFileID(file_id)
    if junction_clsid is not None:
      self.SetJunctionCLSID(junction_clsid)
    return self
  def SetFindData(self, find_data):
    return self.__class__._protos['SetFindData'](self.pI, find_data)
  def GetFindData(self):
    return self.__class__._protos['GetFindData'](self.pI)
  def SetFileID(self, file_id):
    return self.__class__._protos['SetFileID'](self.pI, file_id)
  def GetFileID(self):
    return self.__class__._protos['GetFileID'](self.pI)
  def SetJunctionCLSID(self, junction_clsid):
    return self.__class__._protos['SetJunctionCLSID'](self.pI, junction_clsid)
  def GetJunctionCLSID(self):
    return self.__class__._protos['GetJunctionCLSID'](self.pI)
IFileSystemBindData2 = IFileSystemBindData

class _COM_IFileSystemBindData_Proxy(_COM_IRpcProxy):
  _iids.update(_COM_IFileSystemBindData._iids)
  _vtbl.update(_COM_IFileSystemBindData._vtbl)
  @classmethod
  def _SetFindData(cls, pI, pfd):
    with cls[pI] as self:
      if not self or not pfd:
        return 0x80004003
      return cls._call(self, 3, (pfd.contents,), ())
  @classmethod
  def _GetFindData(cls, pI, pfd):
    with cls[pI] as self:
      if not self or not pfd:
        return 0x80004003
      return cls._call(self, 4, (), (pfd.contents,))
  @classmethod
  def _SetFileID(cls, pI, fid):
    with cls[pI] as self:
      if not self:
        return 0x80004003
      return cls._call(self, 5, (wintypes.LARGE_INTEGER(fid),), ())
  @classmethod
  def _GetFileID(cls, pI, pfid):
    with cls[pI] as self:
      if not self or not pfid:
        return 0x80004003
      return cls._call(self, 6, (), (pfid.contents,))
  @classmethod
  def _SetJunctionCLSID(cls, pI, pjclsid):
    with cls[pI] as self:
      if not self or not pjclsid:
        return 0x80004003
      return cls._call(self, 7, (pjclsid.contents,), ())
  @classmethod
  def _GetJunctionCLSID(cls, pI, pjclsid):
    with cls[pI] as self:
      if not self or not pjclsid:
        return 0x80004003
      return cls._call(self, 8, (), (pjclsid.contents,))

class _COM_IFileSystemBindData_Stub(_COM_IRpcStubBuffer):
  @classmethod
  def _invoke(cls, self, pI, channel, message):
    if (method := message.iMethod) == 3:
      iargs, oargs = cls._gen_args(self, channel, message, (WSFINDDATA,), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, WSPFINDDATA)(3, 'SetFindData')(pI, iargs[0]))
    elif method == 4:
      iargs, oargs = cls._gen_args(self, channel, message, (), (WSFINDDATA,))
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, WSPFINDDATA)(4, 'GetFindData')(pI, oargs[0]))
    elif method == 5:
      iargs, oargs = cls._gen_args(self, channel, message, (wintypes.LARGE_INTEGER,), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.LARGE_INTEGER)(5, 'SetFileID')(pI, iargs[0]))
    elif method == 6:
      iargs, oargs = cls._gen_args(self, channel, message, (), (wintypes.LARGE_INTEGER,))
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PLARGE_INTEGER)(6, 'GetFileID')(pI, oargs[0]))
    elif method == 7:
      iargs, oargs = cls._gen_args(self, channel, message, (wintypes.BYTES16,), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PBYTES16)(7, 'SetJunctionCLSID')(pI, iargs[0]))
    elif method == 8:
      iargs, oargs = cls._gen_args(self, channel, message, (), (wintypes.BYTES16,))
      return oargs if iargs is None else cls._fin_message(message, oargs, ctypes.WINFUNCTYPE(wintypes.ULONG, wintypes.PBYTES16)(8, 'GetJunctionCLSID')(pI, oargs[0]))
    else:
      iargs, oargs = cls._gen_args(self, channel, message, (), ())
      return oargs if iargs is None else cls._fin_message(message, oargs, 0x80004001)

class _PS_IFileSystemBindData_impl(metaclass=_PSImplMeta, ps_interfaces=((_COM_IFileSystemBindData_Proxy, _COM_IFileSystemBindData_Stub),)):
  CLSID = True

class _IBCMeta(_IMeta):
  @property
  def AllowNonExistingFile(cls):
    if (ibc := getattr(cls, '_AllowNonExistingFile', None)) is None:
      if (ibc := cls()) is not None:
        ibc.SetAllowNonExistingFile()
        cls._AllowNonExistingFile = ibc
    return ibc
  @property
  def AllowNonExistingFolder(cls):
    if (ibc := getattr(cls, '_AllowNonExistingFolder', None)) is None:
      if (ibc := cls()) is not None:
        ibc.SetAllowNonExistingFolder()
        cls._AllowNonExistingFolder = ibc
    return ibc

class IBindCtx(IUnknown, metaclass=_IBCMeta):
  IID = GUID(0x0000000e, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['SetBindOptions'] = 6, (WSPBINDOPTS,), ()
  _protos['GetBindOptions'] = 7, (), (WSPBINDOPTS,)
  _protos['RegisterObjectParam'] = 9, (wintypes.LPOLESTR, wintypes.LPVOID), ()
  _protos['GetObjectParam'] = 10, (wintypes.LPOLESTR,), (wintypes.PLPVOID,)
  _protos['EnumObjectParam'] = 11, (), (wintypes.PLPVOID,)
  _protos['RevokeObjectParam'] = 12, (wintypes.LPOLESTR,), ()
  def __new__(cls, clsid_component=False, factory=None):
    if clsid_component is False:
      return _WShUtil._set_factory(cls.CreateBindCtx(), factory)
    return IUnknown.__new__(cls, clsid_component, factory)
  def SetBindOptions(self, bind_options=(0, 2)):
    return self.__class__._protos['SetBindOptions'](self.pI, bind_options)
  def GetBindOptions(self):
    return self.__class__._protos['GetBindOptions'](self.pI)
  def RegisterObjectParam(self, bind_key, obj):
    return self.__class__._protos['RegisterObjectParam'](self.pI, bind_key, obj)
  def GetObjectParam(self, bind_key):
    return IUnknown(self.__class__._protos['GetObjectParam'](self.pI, bind_key), self.factory)
  def EnumObjectParam(self):
    return IEnumString(self.__class__._protos['EnumObjectParam'](self.pI), self.factory)
  def RevokeObjectParam(self, bind_key):
    return self.__class__._protos['RevokeObjectParam'](self.pI, bind_key)
  def SetAllowNonExistingFile(self):
    self.RegisterObjectParam('File System Bind Data', IFileSystemBindData())
  def SetAllowNonExistingFolder(self):
    self.RegisterObjectParam('File System Bind Data', IFileSystemBindData(find_data=('Directory',)))
  CreateBindCtx = classmethod(lambda cls, _cbc=_WShUtil._wrap('CreateBindCtx', (wintypes.DWORD, 1), (wintypes.PLPVOID, 2), p=ole32): cls(_cbc(0)))

class WSSHITEMID(ctypes.Structure):
  _fields_ = [('cb', wintypes.USHORT), ('abID', wintypes.BYTE * 0)]
  def to_bytes(self):
    return (wintypes.CHAR * max(self.cb - WSSHITEMID.cb.size, 0)).from_address(ctypes.addressof(self.abID)).raw
  @property
  def value(self):
    return self.to_bytes()
  def __bool__(self):
    return bool(self.cb)
WSPSHITEMID = ctypes.POINTER(WSSHITEMID)

class WSITEMIDLIST(ctypes.Structure):
  _fields_ = [('mkid', WSSHITEMID)]
  @property
  def value(self):
    o = 0
    c = []
    while True:
      i = WSSHITEMID.from_address(ctypes.addressof(self.mkid) + o)
      if not i.cb:
        return c
      c.append(i.value)
      o += i.cb
  def __len__(self):
    o = 0
    l = 0
    while True:
      i = WSSHITEMID.from_address(ctypes.addressof(self.mkid) + o)
      if not i.cb:
        return l
      l += 1
      o += i.cb

class _WSPIIDLUtil:
  @staticmethod
  def _ainit(arr, *args, needsfree=False, **kwargs):
    arr.__class__.__bases__[0].__init__(arr, *args, **kwargs)
    arr._needsfree = needsfree
  @staticmethod
  def _adel(arr):
    if getattr(arr, '_needsfree', False):
      for s in arr:
        if bool(s):
          ole32.CoTaskMemFree(s)
    getattr(arr.__class__.__bases__[0], '__del__', id)(arr)

class _WSPIIDLMeta(ctypes.POINTER(WSITEMIDLIST).__class__):
  _mul_cache = {}
  def __mul__(bcls, size):
    if bcls == PIDL:
      bcls = PIDL.__bases__[0]
    return bcls.__class__._mul_cache.get((bcls, size)) or bcls.__class__._mul_cache.setdefault((bcls, size), type('%s_Array_%d' % (bcls.__name__, size), (ctypes.POINTER(WSITEMIDLIST).__class__.__mul__(bcls, size),), {'__init__': _WSPIIDLUtil._ainit, '__del__': _WSPIIDLUtil._adel}))

class WSPITEMIDLIST(ctypes.POINTER(WSITEMIDLIST), metaclass=_WSPIIDLMeta):
  _type_ = WSITEMIDLIST
  def __new__(cls, *args, _needsfree=False):
    if len(args) == 1:
      a = args[0]
      if isinstance(a, WSPITEMIDLIST):
        return a.Clone()
      if isinstance(a, str):
        return WSPITEMIDLIST.SHParseDisplayName(a.rstrip('\\'), bind_context=getattr(IBindCtx, 'AllowNonExistingFolder' if a.endswith('\\') else 'AllowNonExistingFile'))
      if isinstance(a, (IShellFolder, IShellItem)):
        return WSPITEMIDLIST.SHGetIDListFromObject(a)
    return cls.__bases__[0].__new__(cls, *args, _needsfree=False)
  def __init__(self, *args, _needsfree=False):
    if not getattr(self, '_needsfree', False):
      super().__init__(*args)
      self._needsfree = _needsfree
  def __ctypes_from_outparam__(self):
    self._needsfree = True
    return self
  def  __del__(self):
    if self and getattr(self, '_needsfree', False):
      ole32.CoTaskMemFree(self)
    getattr(self.__class__.__bases__[0], '__del__', id)(self)
  @staticmethod
  def Expand(path):
    return WSPITEMIDLIST.ExpandEnvironmentStrings(path)
  @staticmethod
  def FromName(name='', bind_context=None):
    return WSPITEMIDLIST.SHParseDisplayName(name.rstrip('\\'), bind_context=bind_context)
  @staticmethod
  def FromPath(path=''):
    return WSPITEMIDLIST.ILCreateFromPath(path.rstrip('\\'))
  @property
  def content(self):
    return None if self is None else self.contents.value
  def GetName(self, name_form=0):
    return WSPITEMIDLIST.SHGetNameFromIDList(self, name_form)
  @property
  def Name(self):
    return self.GetName('NormalDisplay')
  @property
  def AbsoluteParsingName(self):
    return self.GetName('DesktopAbsoluteParsing')
  @property
  def RelativeParsingName(self):
    return self.GetName('ParentRelativeParsing')
  @property
  def AbsoluteName(self):
    return self.GetName('DesktopAbsoluteEditing')
  @property
  def RelativeName(self):
    return self.GetName('ParentRelativeEditing')
  def AppendID(self, pmkid):
    return WSPITEMIDLIST.ILAppendID((self if self._needsfree else self.Clone()), ctypes.cast(pmkid, WSPSHITEMID), True)
  def PrependID(self, pmkid):
    return WSPITEMIDLIST.ILAppendID((self if self._needsfree else self.Clone()), ctypes.cast(pmkid, WSPSHITEMID), False)
  def Clone(self):
    return WSPITEMIDLIST.ILClone(self)
  def CloneFirst(self):
    return WSPITEMIDLIST.ILCloneFirst(self)
  def CombineWith(self, pidl):
    return WSPITEMIDLIST.ILCombine(self, pidl)
  def FindChild(self, pidl):
    return WSPITEMIDLIST.ILFindChild(self, pidl)
  def FindLastID(self):
    return WSPITEMIDLIST.ILFindLastID(self)
  @property
  def LastID(self):
    return self.FindLastID()
  def CloneLast(self):
    return self.LastID.Clone()
  def GetNext(self):
    return WSPITEMIDLIST.ILGetNext(self)
  @property
  def Next(self):
    return self.GetNext()
  def GetSize(self):
    return WSPITEMIDLIST.ILGetSize(self)
  @property
  def Size(self):
    return self.GetSize()
  def GetIsEmpty(self):
    return WSPITEMIDLIST.ILIsEmpty(self)
  @property
  def IsEmpty(self):
    return self.GetIsEmpty()
  def GetIsChild(self):
    return WSPITEMIDLIST.ILIsChild(self)
  @property
  def IsChild(self):
    return self.GetIsChild()
  def IsEqualTo(self, pidl):
    return WSPITEMIDLIST.ILIsEqual(self, pidl)
  def IsParentOf(self, pidl):
    return WSPITEMIDLIST.ILIsParent(self, pidl)
  def RemoveLastID(self):
    return WSPITEMIDLIST.ILRemoveLastID(self)
  def GetPath(self):
    return WSPITEMIDLIST.SHGetPathFromIDList(self)
  @property
  def Path(self):
    return self.GetPath()
  def GetData(self):
    return None if (pr := self.GetParentAndRelativeIDList(IShellFolder)) is None else WSPITEMIDLIST.SHGetDataFromIDList(*pr)
  @property
  def Data(self):
    return self.GetData()
  def GetParentAndRelativeIDList(self, interface=None):
    return IShellFolder.SHBindToParent(self, interface)
  @property
  def ParentAndRelative(self):
    return self.GetParentAndRelativeIDList()
  def GetDropTarget(self, hwnd=None):
    return None if (f := IShellFolder(self)) is None else f.GetDropTarget(hwnd)
  @property
  def AsDropTarget(self):
    return self.GetDropTarget()
  def GetDataObject(self, bind_context=None):
    return None if (i := IShellItem(self)) is None else i.GetDataObject(bind_context)
  @property
  def AsDataObject(self):
    return self.GetDataObject()
WSPPITEMIDLIST = ctypes.POINTER(WSPITEMIDLIST)
WSPITEMIDLIST.ILAppendID = staticmethod(lambda pidl, pmkid, append=True, _ilaid=_WShUtil._wrap('ILAppendID', (WSPITEMIDLIST, 0), (WSPITEMIDLIST, 1), (WSPSHITEMID, 1), (wintypes.BOOL, 1)): _WShUtil._subst_pidls((_ilaid(pidl, pmkid, append) or None), pidl))
WSPITEMIDLIST.ILClone = staticmethod(lambda pidl, _ilc=_WShUtil._wrap('ILClone', (WSPITEMIDLIST, 0), (WSPITEMIDLIST, 1)): _ilc(pidl) or None)
WSPITEMIDLIST.ILCloneFirst = staticmethod(lambda pidl, _ilcf=_WShUtil._wrap('ILCloneFirst', (WSPITEMIDLIST, 0), (WSPITEMIDLIST, 1)): _ilcf(pidl) or None)
WSPITEMIDLIST.ILCombine = staticmethod(lambda pidl1, pidl2, _ilc=_WShUtil._wrap('ILCombine', (WSPITEMIDLIST, 0), (WSPITEMIDLIST, 1), (WSPITEMIDLIST, 1)): _ilc(pidl1, pidl2) or None)
WSPITEMIDLIST.ILCreateFromPath = staticmethod(lambda path, _ilcfp=_WShUtil._wrap('ILCreateFromPathW', (WSPITEMIDLIST, 0), (wintypes.LPCWSTR, 1)): _ilcfp(path) or None)
WSPITEMIDLIST.ILFindChild = staticmethod(lambda pidl_parent, pidl_child, _ilfc=_WShUtil._wrap('ILFindChild', (WSPITEMIDLIST, 0), (WSPITEMIDLIST, 1), (WSPITEMIDLIST, 1)): _WShUtil._bind_pidls((_ilfc(pidl_parent, pidl_child) or None), pidl_child))
WSPITEMIDLIST.ILFindLastID = staticmethod(lambda pidl, _ilflid=_WShUtil._wrap('ILFindLastID', (WSPITEMIDLIST, 0), (WSPITEMIDLIST, 1)): _WShUtil._bind_pidls(_ilflid(pidl), pidl))
WSPITEMIDLIST.ILGetNext = staticmethod(lambda pidl, _ilgn=_WShUtil._wrap('ILGetNext', (WSPITEMIDLIST, 0), (WSPITEMIDLIST, 1)): _WShUtil._bind_pidls((_ilgn(pidl) or None), pidl))
WSPITEMIDLIST.ILGetSize = staticmethod(lambda pidl, _ilgs=_WShUtil._wrap('ILGetSize', (wintypes.UINT, 0), (WSPITEMIDLIST, 1)): _ilgs(pidl))
WSPITEMIDLIST.ILIsEmpty = staticmethod(lambda pidl: not pidl or not pidl.contents.mkid)
WSPITEMIDLIST.ILIsChild = staticmethod(lambda pidl: not pidl or not pidl.contents.mkid or WSPITEMIDLIST.ILIsEmpty(WSPITEMIDLIST.ILGetNext(pidl)))
WSPITEMIDLIST.ILIsEqual = staticmethod(lambda pidl1, pidl2, _ilie=_WShUtil._wrap('ILIsEqual', (wintypes.BOOLE, 0), (WSPITEMIDLIST, 1), (WSPITEMIDLIST, 1)): _ilie(pidl1, pidl2))
WSPITEMIDLIST.ILIsParent = staticmethod(lambda pidl_parent, pidl_child, immediate=False, _ilip=_WShUtil._wrap('ILIsParent', (wintypes.BOOLE, 0), (WSPITEMIDLIST, 1), (WSPITEMIDLIST, 1), (wintypes.BOOL, 1)): _ilip(pidl_parent, pidl_child, immediate))
WSPITEMIDLIST.ILRemoveLastID = staticmethod(lambda pidl, _ilrlid=_WShUtil._wrap('ILRemoveLastID', (wintypes.BOOLE, 0), (WSPITEMIDLIST, 1)): _ilrlid(pidl))
WSPITEMIDLIST.SHGetIDListFromObject = staticmethod(lambda obj, _shgidlfo=_WShUtil._wrap('SHGetIDListFromObject', (wintypes.LPVOID, 1), (WSPPITEMIDLIST, 2)): _shgidlfo(obj) or None)
WSPITEMIDLIST.SHGetNameFromIDList = staticmethod(lambda pidl, name_form=0, _shgnfidl=_WShUtil._wrap('SHGetNameFromIDList', (WSPITEMIDLIST, 1), (WSSIGDN, 1), (wintypes.PLPVOID, 2)): _WShUtil._get_str(_shgnfidl(pidl, name_form)))
WSPITEMIDLIST.SHGetPathFromIDList = staticmethod(lambda pidl, _shgpfidl=_WShUtil._wrap('SHGetPathFromIDListW', (wintypes.BOOL, 0), (WSPITEMIDLIST, 1), (wintypes.LPWSTR, 1)): p.value if (p := ctypes.create_unicode_buffer(261)) and _shgpfidl(pidl, p) is not None else None)
WSPITEMIDLIST.SHParseDisplayName = staticmethod(lambda name, query_attributes=0, bind_context=None, _shpdn=_WShUtil._wrap('SHParseDisplayName', (wintypes.LPCWSTR, 1), (wintypes.LPVOID, 1), (WSPPITEMIDLIST, 2), (WSSFGAO, 1), (WSPSFGAO, 2)): None if (p_a := _shpdn(name, bind_context, query_attributes)) is None else (p_a if query_attributes else p_a[0]))
WSPITEMIDLIST.SHGetDataFromIDList = staticmethod(lambda parent, pidl, _shgdfidl=_WShUtil._wrap('SHGetDataFromIDListW', (wintypes.LPVOID, 1), (WSPITEMIDLIST, 1), (wintypes.INT, 1), (WSPFINDDATA, 2), (wintypes.INT, 1)): _shgdfidl(parent, pidl, 1, ctypes.sizeof(WSFINDDATA)))
WSPITEMIDLIST.ExpandEnvironmentStrings = staticmethod(lambda path, _ees=_WShUtil._wrap('ExpandEnvironmentStringsW', (wintypes.DWORD, 0), (wintypes.LPCWSTR, 1), (wintypes.LPWSTR, 1), (wintypes.DWORD, 1), p=kernel32): (p.value if (p := ctypes.create_unicode_buffer(l)) and _ees(path, p, l) is not None else None) if (l := _ees(path, None, 0)) else None)
class PIDL(WSPITEMIDLIST):
  _type_ = WSITEMIDLIST
  def __new__(cls, a=False):
    return WSPITEMIDLIST(IShellFolder() if a is False else a)

class WSSTRRET(ctypes.Structure):
  _anonymous_ = ('un',)
  _fields_ = [('uType', wintypes.UINT), ('un', ctypes.Union.__class__('WSSTRRET_UN', (ctypes.Union,), {'_fields_': [('pOleStr', wintypes.LPWSTR), ('uOffset', wintypes.UINT), ('cStr', wintypes.CHAR * 260)]}))]
  def to_str(self, pidl=None):
    if not getattr(self, '_needsclear', False):
      return None
    self._needsclear = False
    return self.StrRetToBSTR(self, pidl)
  def __ctypes_from_outparam__(self):
    self._needsclear = True
    return self
  def  __del__(self):
    if getattr(self, '_needsclear', False):
      self.to_str()
    getattr(self.__class__.__bases__[0], '__del__', id)(self)
WSPSTRRET = ctypes.POINTER(WSSTRRET)
WSSTRRET.StrRetToBSTR = staticmethod(_WShUtil._wrap('StrRetToBSTR', (ctypes.POINTER(WSSTRRET), 1), (WSPPITEMIDLIST, 1), (PBSTRING, 2), p=shl))

class IEnumIDList(IUnknown):
  IID = GUID(0x000214f2, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['Next'] = 3, (wintypes.ULONG, WSPPITEMIDLIST, wintypes.PULONG), ()
  _protos['Skip'] = 4, (wintypes.ULONG,), ()
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    a = (WSPITEMIDLIST * number)(needsfree=True)
    return None if self.__class__._protos['Next'](self.pI, number, a, r) is None else tuple(a[p] for p in range(r.value))
  def Skip(self, number):
    try:
      return self.__class__._protos['Skip'](self.pI, number)
    except:
      ISetLastError(0x80070057)
      return None
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    if not (n := self.Next(1)):
      raise StopIteration
    return n[0]

class IEnumFORMATETC(IUnknown):
  IID = GUID(0x00000103, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['Next'] = 3, (wintypes.ULONG, WSPFORMATETC, wintypes.PULONG), ()
  _protos['Skip'] = 4, (wintypes.ULONG,), ()
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    a = (WSFORMATETC * number)()
    return None if self.__class__._protos['Next'](self.pI, number, a, r) is None else tuple(a[p].value for p in range(r.value))
  def Skip(self, number):
    try:
      return self.__class__._protos['Skip'](self.pI, number)
    except:
      ISetLastError(0x80070057)
      return None
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    if not (n := self.Next(1)):
      raise StopIteration
    return n[0]

class IDataObject(IUnknown):
  IID = GUID(0x0000010e, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['GetData'] = 3, (WSPFORMATETC,), (WSPSTGMEDIUM,)
  _protos['QueryGetData'] = 5, (WSPFORMATETC,), ()
  _protos['SetData'] = 7, (WSPFORMATETC, WSPSTGMEDIUM, wintypes.BOOLE), ()
  _protos['EnumFormatEtc'] = 8, (WSDATADIR,), (wintypes.PLPVOID,)
  def EnumFormatEtc(self, direction=1):
    return IEnumFORMATETC(self._protos['EnumFormatEtc'](self.pI, direction), self.factory)
  def GetData(self, format_etc):
    return self._protos['GetData'](self.pI, format_etc)
  def QueryGetData(self, format_etc):
    return self._protos['QueryGetData'](self.pI, format_etc) is not None
  def SetData(self, format_etc, stg_medium, release):
    return self._protos['SetData'](self.pI, format_etc, stg_medium, release)
  @property
  def SupportedGetFormatEtc(self):
    return None if (ief := self.EnumFormatEtc(1)) is None else tuple(ief)
  @property
  def SupportedSetFormatEtc(self):
    return None if (ief := self.EnumFormatEtc(2)) is None else tuple(ief)
  kernel32.GlobalLock.restype = wintypes.LPVOID
  kernel32.GlobalUnlock.restype = wintypes.BOOLE
  sh32.DragQueryFileW.restype = wintypes.UINT
  @staticmethod
  def RetrieveFileNames(stg_medium):
    if (g := WSSTGMEDIUM._get_data(stg_medium, 1)) is None:
      return None
    fa = []
    for i in range(sh32.DragQueryFileW(g, 0xffffffff, None, 0)):
      fl = sh32.DragQueryFileW(g, wintypes.UINT(i), None, wintypes.UINT(0)) + 1
      f = ctypes.create_unicode_buffer(fl)
      sh32.DragQueryFileW(g, wintypes.UINT(i), ctypes.byref(f), wintypes.UINT(fl))
      fa.append(f)
    return tuple(f.value for f in fa)
  def GetFileNames(self):
    return self.RetrieveFileNames(self.GetData((15, None, 1, -1, 1)))
  @staticmethod
  def RetrieveFileDescriptors(stg_medium):
    if (g := WSSTGMEDIUM._get_data(stg_medium, 1)) is None or not (h := kernel32.GlobalLock(g)):
      return None
    fds = ctypes.cast(h, WSPFILEGROUPDESCRIPTOR).contents.value
    kernel32.GlobalUnlock(g)
    return fds
  def GetFileDescriptors(self):
    return self.RetrieveFileDescriptors(self.GetData(('FileGroupDescriptorW', None, 1, -1, 1)))
  @staticmethod
  def RetrieveFileContent(stg_medium):
    return WSSTGMEDIUM._get_data(stg_medium, 4)
  def GetFileContent(self, index=0):
    return None if (fds := self.GetFileDescriptors()) is None or index >= len(fds) else self.RetrieveFileContent(self.GetData(('FileContents', None, 1, index, 4)))
  @staticmethod
  def RetrieveShIDLists(stg_medium):
    if (g := WSSTGMEDIUM._get_data(stg_medium, 1)) is None or not (h := kernel32.GlobalLock(g)):
      return None
    idls = ctypes.cast(h, WSPCIDA).contents.value
    kernel32.GlobalUnlock(g)
    return idls
  def GetShIDLists(self):
    return self.RetrieveShIDLists(self.GetData(('ShIDListArray', None, 1, -1, 1)))
  GetPIDLs = GetShIDLists
  @staticmethod
  def RetrieveURL(stg_medium):
    if (g := WSSTGMEDIUM._get_data(stg_medium, 1)) is None or not (h := kernel32.GlobalLock(g)):
      return None
    url = ctypes.cast(h, wintypes.LPSTR).value
    kernel32.GlobalUnlock(g)
    return url.decode()
  def GetURL(self):
    return self.RetrieveURL(self.GetData(('UniformResourceLocator', None, 1, -1, 1)))

class IDataObjectAsyncCapability(IUnknown):
  IID = GUID(0x3d8b0590, 0xf691, 0x11d2, 0x8e, 0xa9, 0x00, 0x60, 0x97, 0xdf, 0x5b, 0xd4)
  _protos['SetAsyncMode'] = 3, (wintypes.BOOL,), ()
  _protos['GetAsyncMode'] = 4, (), (wintypes.PBOOLE,)
  _protos['InOperation'] = 6, (), (wintypes.PBOOLE,)
  def GetAsyncMode(self):
    return self._protos['GetAsyncMode'](self.pI)
  def SetAsyncMode(self, async_op=False):
    return self._protos['SetAsyncMode'](self.pI, (0xffff if async_op else 0))
  def InOperation(self):
    return self._protos['InOperation'](self.pI)

class IDropTarget(IUnknown):
  IID = GUID(0x00000122, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['DragEnter'] = 3, (wintypes.LPVOID, WSKEYSTATE, POINT, WSPDROPEFFECT), ()
  _protos['Drop'] = 6, (wintypes.LPVOID, WSKEYSTATE, POINT, WSPDROPEFFECT), ()
  def DragEnter(self, obj, effect, key_state=1, cursor_coordinates=(0,0)):
    e = WSDROPEFFECT(effect)
    return None if self._protos['DragEnter'](self.pI, obj, key_state, cursor_coordinates, e) is None else e
  def Drop(self, obj, effect, key_state=1, cursor_coordinates=(0,0)):
    e = WSDROPEFFECT(effect)
    return None if self._protos['Drop'](self.pI, obj, key_state, cursor_coordinates, e) is None else e
  def DropCopy(self, obj):
    if not isinstance(obj, IDataObject) and (obj := obj.GetDataObject()) is None:
      return None
    return self.DragEnter(obj, 'Copy') != 0 and self.Drop(obj, 'Copy') is not None
  def DropMove(self, obj):
    if not isinstance(obj, IDataObject) and (obj := obj.GetDataObject()) is None:
      return None
    return self.DragEnter(obj, 'Move') != 0 and self.Drop(obj, 'Move') is not None
  def DropShortcut(self, obj):
    if not isinstance(obj, IDataObject) and (obj := obj.GetDataObject()) is None:
      return None
    return self.DragEnter(obj, 'Link') != 0 and self.Drop(obj, 'Link') is not None

class IContextMenu(IUnknown):
  IID = GUID(0x000214e4, 0x0000, 0x0000, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46)
  _protos['QueryContextMenu'] = 3, (wintypes.HMENU, wintypes.UINT, wintypes.UINT, wintypes.UINT, wintypes.UINT), (), wintypes.ULONG
  _protos['InvokeCommand'] = 4, (WSPCMINVOKECOMMANDINFO,), ()
  _protos['GetCommandString'] = 5, (wintypes.WPARAM, wintypes.UINT, wintypes.PUINT, wintypes.LPWSTR, wintypes.UINT), ()
  def __new__(cls, clsid_component=False, factory=None):
    if (self := super().__new__(cls, clsid_component, factory)) is not None:
      self.QueryContextMenu()
    return self
  def QueryContextMenu(self):
    return None if ISetLastError(n := self._protos['QueryContextMenu'](self.pI, None, 0, 0, -1, 0)) else n
  def GetCommandString(self, identifier, information_flags=0):
    s = ctypes.create_unicode_buffer(256)
    return None if self._protos['GetCommandString'](self.pI, identifier, information_flags | 0x4, None, s, 255) is None else s.value
  def InvokeCommand(self, command_verb, confirmation=True, shift_down=False, control_down=False, show_window=1, hwnd=None):
    return self._protos['InvokeCommand'](self.pI, WSCMINVOKECOMMANDINFO.from_param({'lpVerb': command_verb.encode(), 'fMask': ((0 if confirmation else 0x400) | (0x10000000 if shift_down else 0) | (0x40000000 if control_down else 0)), 'nShow': show_window, 'hwnd': hwnd}))

class IShellFolder(IUnknown):
  IID = GUID(0x93f2f68c, 0x1d1b, 0x11d3, 0xa3, 0x0e, 0x00, 0xc0, 0x4f, 0x79, 0xab, 0xd1)
  _protos['ParseDisplayName'] = _WShUtil._wrap('ParseDisplayName', (wintypes.HWND, 1), (wintypes.LPVOID, 1), (wintypes.LPCWSTR, 1), (wintypes.PULONG, 1), (WSPPITEMIDLIST, 2), (WSPSFGAO, 1), p=3)
  _protos['EnumObjects'] = 4, (wintypes.HWND, WSSHCONTF), (wintypes.PLPVOID,)
  _protos['BindToObject'] = 5, (WSPITEMIDLIST, wintypes.LPVOID, PUUID), (wintypes.PLPVOID,)
  _protos['BindToStorage'] = 6, (WSPITEMIDLIST, wintypes.LPVOID, PUUID), (wintypes.PLPVOID,)
  _protos['CompareIDs'] = 7, (wintypes.LPARAM, WSPITEMIDLIST, WSPITEMIDLIST), (), wintypes.ULONG
  _protos['CreateViewObject'] = 8, (wintypes.HWND, PUUID), (wintypes.PLPVOID,)
  _protos['GetAttributesOf'] = 9, (wintypes.UINT, WSPPITEMIDLIST, WSPSFGAO), ()
  _protos['GetUIObjectOf'] = 10, (wintypes.HWND, wintypes.UINT, WSPPITEMIDLIST, PUUID, wintypes.PUINT), (wintypes.PLPVOID,)
  _protos['GetDisplayNameOf'] = 11, (WSPITEMIDLIST, WSSHGDNF), (WSPSTRRET,)
  _protos['SetNameOf'] = 12, (wintypes.HWND, WSPITEMIDLIST, wintypes.LPCWSTR, WSSHGDNF), (WSPPITEMIDLIST,)
  def __new__(cls, clsid_component=False, factory=None):
    if clsid_component is False:
      return _WShUtil._set_factory(cls.SHGetDesktopFolder(), factory)
    if isinstance(clsid_component, str):
      clsid_component = WSPITEMIDLIST(clsid_component.rstrip('\\') + '\\')
    if isinstance(clsid_component, (IShellFolder, IShellItem)):
      if factory is False:
        factory = None
      elif factory is None:
        factory = clsid_component.factory
      clsid_component = WSPITEMIDLIST.SHGetIDListFromObject(clsid_component)
    if isinstance(clsid_component, WSPITEMIDLIST):
      return _WShUtil._set_factory(cls.SHBindToObject(None, clsid_component), factory)
    return IUnknown.__new__(cls, clsid_component, factory)
  def ParseDisplayName(self, display_name='', query_attributes=0, bind_context=None, hwnd=None):
    a = WSSFGAO(query_attributes)
    return None if (pidl := self._protos['ParseDisplayName'](self.pI, hwnd, bind_context, display_name, None, a)) is None else ((pidl, a) if query_attributes else pidl)
  def GetDisplayNameOf(self, pidl, name_flags=0):
    return None if (n := self._protos['GetDisplayNameOf'](self.pI, pidl, name_flags)) is None else n.to_str(pidl)
  def GetAttributesOf(self, pidls, query_attributes=0):
    a = WSSFGAO(query_attributes)
    return a if self._protos['GetAttributesOf'](self.pI, (1 if (pidls is None or isinstance(pidls, WSPITEMIDLIST)) else len(pidls)), (pidls if pidls is None or isinstance(pidls, WSPITEMIDLIST) or (isinstance(pidls, ctypes.Array) and issubclass(pidls._type_, WSPITEMIDLIST)) else (WSPITEMIDLIST * len(pidls))(*pidls)), ctypes.byref(a)) else None
  def SetNameOf(self, pidl, name, name_flags=0, hwnd=None):
    return self._protos['SetNameOf'](self.pI, hwnd, pidl, name, name_flags)
  def EnumObjects(self, include_flags=0x60, hwnd=None):
    return IEnumIDList(self._protos['EnumObjects'](self.pI, hwnd, include_flags), self.factory)
  def BindToObject(self, pidl, interface=None, bind_context=None):
    return (interface or self.__class__)(self._protos['BindToObject'](self.pI, pidl, bind_context, (interface or self.__class__).IID), self.factory)
  def BindToStorage(self, pidl, interface=None, bind_context=None):
    return (interface or IStream)(self._protos['BindToStorage'](self.pI, pidl, bind_context, (interface or IStream).IID), self.factory)
  def CreateViewObject(self, interface, hwnd=None):
    return interface(self._protos['CreateViewObject'](self.pI, hwnd, interface.IID), self.factory)
  def CompareIDs(self, pidl1, pidl2, comparison_flags=0, comparison_rule=0):
    return None if ISetLastError(c := self._protos['CompareIDs'](self.pI, WSSHCIDS.name_code(comparison_flags) | comparison_rule, pidl1, pidl2)) else ((c & 0xffff) ^ 0x8000) - 0x8000
  def GetUIObjectOf(self, pidls, interface, hwnd=None):
    return interface(self._protos['GetUIObjectOf'](self.pI, hwnd, (1 if (pidls is None or isinstance(pidls, WSPITEMIDLIST)) else len(pidls)), (pidls if pidls is None or isinstance(pidls, WSPITEMIDLIST) or (isinstance(pidls, ctypes.Array) and issubclass(pidls._type_, WSPITEMIDLIST)) else (WSPITEMIDLIST * len(pidls))(*pidls)), interface.IID, None), self.factory)
  @classmethod
  def FromName(cls, name='', bind_context=None, factory=None):
    return None if (pidl := WSPITEMIDLIST.FromName(name, bind_context)) is None else _WShUtil._set_factory(cls.SHBindToObject(None, pidl), factory)
  @classmethod
  def FromPath(cls, path='', factory=None):
    return None if (pidl := WSPITEMIDLIST.FromPath(path)) is None else _WShUtil._set_factory(cls.SHBindToObject(None, pidl), factory)
  def GetDisplayName(self, name_form=0):
    return None if (pidl := WSPITEMIDLIST(self)) is None else pidl.GetName(name_form)
  @property
  def Name(self):
    return self.GetDisplayName('NormalDisplay')
  @property
  def AbsoluteParsingName(self):
    return self.GetDisplayName('DesktopAbsoluteParsing')
  @property
  def RelativeParsingName(self):
    return self.GetDisplayName('ParentRelativeParsing')
  @property
  def AbsoluteName(self):
    return self.GetDisplayName('DesktopAbsoluteEditing')
  @property
  def RelativeName(self):
    return self.GetDisplayName('ParentRelativeEditing')
  @property
  def SubFolders(self):
    return None if (e := self.EnumObjects(0x20)) is None else {(self.GetDisplayNameOf(pidl, 0x1) or tuple(pidl.content)): self.BindToObject(pidl) for pidl in e}
  @property
  def Children(self):
    return None if None in (es := (self.EnumObjects(0x20), self.EnumObjects(0x40))) else tuple({(self.GetDisplayNameOf(pidl, 0x1) or tuple(pidl.content)): self.GetItemOf(pidl) for pidl in e} for e in es)
  def GetSubFolderFromParsingName(self, name):
    return None if (pidl := self.ParseDisplayName(name)) is None else self.BindToObject(pidl)
  def GetSubFolderFromName(self, name):
    name = name.lower() or None
    return None if (e := self.EnumObjects(0x20)) is None else next((self.BindToObject(pidl) for pidl in e if (self.GetDisplayNameOf(pidl, 0x1) or '').lower() == name), None)
  def GetChildFromParsingName(self, name):
    return None if (pidl := self.ParseDisplayName(name)) is None else self.GetItemOf(pidl)
  def GetChildFromName(self, name):
    name = name.lower() or None
    return None if (e := self.EnumObjects(0x60)) is None else next((self.GetItemOf(pidl) for pidl in e if (self.GetDisplayNameOf(pidl, 0x1) or '').lower() == name), None)
  def GetPath(self):
    return None if (pidl := WSPITEMIDLIST(self)) is None else pidl.GetPath()
  @property
  def Path(self):
    return self.GetPath()
  def GetData(self):
    return None if (pidl := PIDL(self)) is None else pidl.Data
  @property
  def Data(self):
    return self.GetData()
  def GetDataOf(self, pidl):
    return WSPITEMIDLIST.SHGetDataFromIDList(self, pidl)
  def GetItemOf(self, pidl, interface=None):
    return IShellItem.SHCreateItemWithParent(self, pidl, interface)
  def GetDropTarget(self, hwnd=None):
    return self.CreateViewObject(IDropTarget, hwnd)
  @property
  def AsDropTarget(self):
    return self.GetDropTarget()
  def GetDataObject(self):
    return None if (i := IShellItem(self)) is None else i.GetDataObject()
  @property
  def AsDataObject(self):
    return self.GetDataObject()
  def GetContextMenu(self, hwnd=None):
    return self.CreateViewObject(IContextMenu, hwnd)
  @property
  def ContextMenu(self):
    return self.GetContextMenu()
  def GetDropTargetOf(self, pidl, hwnd=None):
    return self.GetUIObjectOf(pidl, IDropTarget, hwnd)
  def GetContextMenuOf(self, pidl, hwnd=None):
    return self.GetUIObjectOf(pidl, IContextMenu, hwnd)
  def ContextMenuNewFolder(self, name, hwnd=None):
    if ((e1 := self.EnumObjects(0x20, hwnd)) and (e1 := tuple(e1))) is None or (c := self.GetContextMenu(hwnd)) is None or c.InvokeCommand('NewFolder', hwnd=hwnd) is None or ((e2 := self.EnumObjects(0x20, hwnd)) and (e2 := tuple(e2))) is None or len(n := tuple(p for p in e2 if not any(map(p.IsEqualTo, e1)))) != 1 or (pidl := self.SetNameOf(n[0], name, hwnd=hwnd)) is None:
      return None
    return self.BindToObject(pidl)
  def __iter__(self):
    return iter(()) if (e := self.EnumObjects()) is None else e
  SHBindToFolderIDListParentEx = classmethod(lambda cls, root, pidl, interface=None, bind_context=None, _shbtfidlp=_WShUtil._wrap('SHBindToFolderIDListParentEx', (wintypes.LPVOID, 1), (WSPITEMIDLIST, 1), (wintypes.PLPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2), (WSPPITEMIDLIST, 2)): None if (p_p := _shbtfidlp(root, pidl, bind_context, (interface or cls).IID)) is None else ((interface or cls)(p_p[0], getattr(root, 'factory', None)), _WShUtil._bind_pidls(p_p[1], pidl)))
  SHBindToObject = classmethod(lambda cls, folder, pidl, interface=None, bind_context=None, _shbto=_WShUtil._wrap('SHBindToObject', (wintypes.LPVOID, 1), (WSPITEMIDLIST, 1), (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2)): (interface or cls)(_shbto(folder, pidl, bind_context, (interface or cls).IID), getattr(folder, 'factory', None)))
  SHBindToParent = classmethod(lambda cls, pidl, interface=None, _shbtp=_WShUtil._wrap('SHBindToParent', (WSPITEMIDLIST, 1), (PUUID, 1), (wintypes.PLPVOID, 2), (WSPPITEMIDLIST, 2)): None if (p_p := _shbtp(pidl, (interface or cls).IID)) is None else ((interface or cls)(p_p[0]), _WShUtil._bind_pidls(p_p[1], pidl)))
  SHGetDesktopFolder = classmethod(lambda cls, _shgdf=_WShUtil._wrap('SHGetDesktopFolder', (wintypes.PLPVOID, 2)): cls(_shgdf()))
IShellFolder2 = IShellFolder

class IShellItem(IUnknown):
  IID = GUID(0x7e9fb0d3, 0x919f, 0x4307, 0xab, 0x2e, 0x9b, 0x18, 0x60, 0x31, 0x0c, 0x93)
  _protos['BindToHandler'] = 3, (wintypes.LPVOID, WSPBHID, PUUID), (wintypes.PLPVOID,)
  _protos['GetParent'] = 4, (), (wintypes.PLPVOID,)
  _protos['GetDisplayName'] = 5, (WSSIGDN,), (wintypes.PLPVOID,)
  _protos['GetAttributes'] = 6, (WSSFGAO,), (WSPSFGAO,)
  _protos['Compare'] = 7, (wintypes.LPVOID, WSSICHINTF), (wintypes.PINT,)
  def __new__(cls, clsid_component=False, factory=None):
    if clsid_component is False:
      clsid_component = IShellFolder()
    if isinstance(clsid_component, str):
      return _WShUtil._set_factory(cls.SHCreateItemFromParsingName(clsid_component.rstrip('\\'), cls, bind_context=getattr(IBindCtx, 'AllowNonExistingFolder' if clsid_component.endswith('\\') else 'AllowNonExistingFile')), factory)
    if isinstance(clsid_component, WSPITEMIDLIST):
      return _WShUtil._set_factory(cls.SHCreateItemFromIDList(clsid_component, cls), factory)
    if isinstance(clsid_component, (IShellFolder, IShellItem)):
      return _WShUtil._set_factory(cls.SHGetItemFromObject(clsid_component, cls), factory)
    return IUnknown.__new__(cls, clsid_component, factory)
  def GetDisplayName(self, name_form=0):
    return _WShUtil._get_str(self._protos['GetDisplayName'](self.pI, name_form))
  def GetParent(self):
    return self.__class__(self._protos['GetParent'](self.pI), self.factory)
  def GetAttributes(self, query_attributes):
    return self._protos['GetAttributes'](self.pI, query_attributes)
  def Compare(self, item, compare_mode=0):
    return self._protos['Compare'](self.pI, item, compare_mode)
  def BindToHandler(self, handler_guid, interface, bind_context=None):
    return interface(self._protos['BindToHandler'](self.pI, bind_context, handler_guid, interface.IID), self.factory)
  @classmethod
  def FromName(cls, name='', bind_context=None, factory=None):
    return _WShUtil._set_factory(cls.SHCreateItemFromParsingName(name.rstrip('\\'), cls, bind_context), factory)
  @classmethod
  def FromPath(cls, path='', factory=None):
    return None if (pidl := WSPITEMIDLIST.FromPath(path)) is None else _WShUtil._set_factory(cls.SHCreateItemFromIDList(pidl, cls), factory)
  @property
  def Name(self):
    return self.GetDisplayName('NormalDisplay')
  @property
  def AbsoluteParsingName(self):
    return self.GetDisplayName('DesktopAbsoluteParsing')
  @property
  def RelativeParsingName(self):
    return self.GetDisplayName('ParentRelativeParsing')
  @property
  def AbsoluteName(self):
    return self.GetDisplayName('DesktopAbsoluteEditing')
  @property
  def RelativeName(self):
    return self.GetDisplayName('ParentRelativeEditing')
  @property
  def Parent(self):
    return self.GetParent()
  def CreateItemFromRelativeName(self, name, interface=None, bind_context=None):
    return self.SHCreateItemFromRelativeName(self, name, interface, bind_context)
  def GetPath(self):
    return None if (pidl := WSPITEMIDLIST(self)) is None else pidl.GetPath()
  @property
  def Path(self):
    return self.GetPath()
  def GetData(self):
    return None if (pidl := PIDL(self)) is None else pidl.Data
  @property
  def Data(self):
    return self.GetData()
  def GetFolder(self, bind_context=None):
    return self.BindToHandler('SFObject', IShellFolder, bind_context)
  @property
  def AsFolder(self):
    return self.GetFolder()
  def GetStream(self, bind_context=None):
    return self.BindToHandler('Stream', IStream, bind_context)
  def GetLinkTarget(self, bind_context=None):
    return self.BindToHandler('LinkTargetItem', IShellItem, bind_context)
  def GetContent(self, bind_context=None):
    return self.BindToHandler('EnumItems', IEnumShellItems, bind_context)
  @property
  def Content(self):
    return self.GetContent()
  def GetStorageContent(self, bind_context=None):
    return self.BindToHandler('StorageEnum', IEnumShellItems, bind_context)
  @property
  def StorageContent(self):
    return self.GetStorageContent()
  def GetDropTarget(self, hwnd=None):
    return None if (f := IShellFolder(self)) is None else f.GetDropTarget(hwnd)
  @property
  def AsDropTarget(self):
    return self.GetDropTarget()
  def GetDataObject(self, bind_context=None):
    return self.BindToHandler('DataObject', IDataObject, bind_context)
  @property
  def AsDataObject(self):
    return self.GetDataObject()
  def GetContextMenu(self, bind_context=None):
    return self.BindToHandler('SFUIObject', IContextMenu, bind_context)
  @property
  def ContextMenu(self):
    return self.GetContextMenu()
  def GetImageFactory(self):
    return self.QueryInterface(IShellItemImageFactory, self.factory)
  def GetImage(self, size, flags=0):
    return None if (f := self.GetImageFactory()) is None else f.GetImage(size, flags)
  def CopyTo(self, destination, name=None, confirmation=True, hwnd=None):
    if (f := IFileOperation.Create(confirmation, hwnd)) is None or (d := (destination if isinstance(destination, IShellItem) else IShellItem(destination))) is None or f.CopyItem(self, d, name) is None:
      return None
    return f.PerformOperations() is not None and not f.GetAnyOperationsAborted()
  def MoveTo(self, destination, name=None, confirmation=True, hwnd=None):
    if (f := IFileOperation.Create(confirmation, hwnd)) is None or (d := (destination if isinstance(destination, IShellItem) else IShellItem(destination))) is None or f.MoveItem(self, d, name) is None:
      return None
    return f.PerformOperations() is not None and not f.GetAnyOperationsAborted()
  def Delete(self, confirmation=True, hwnd=None):
    if (f := IFileOperation.Create(confirmation, hwnd)) is None or f.DeleteItem(self) is None:
      return None
    return f.PerformOperations() is not None and not f.GetAnyOperationsAborted()
  def DropCopyTo(self, destination, hwnd=None):
    if (s := self.GetDataObject()) is None or (d := (destination if isinstance(destination, IDropTarget) else destination.GetDropTarget(hwnd))) is None:
      return None
    return d.DropCopy(s)
  def DropMoveTo(self, destination, hwnd=None):
    if (s := self.GetDataObject()) is None or (d := (destination if isinstance(destination, IDropTarget) else destination.GetDropTarget(hwnd))) is None:
      return None
    return d.DropMove(s)
  def DropShortcutTo(self, destination, hwnd=None):
    if (s := self.GetDataObject()) is None or (d := (destination if isinstance(destination, IDropTarget) else destination.GetDropTarget(hwnd))) is None:
      return None
    return d.DropShortcut(s)
  def ContextMenuCopyTo(self, destination, hwnd=None):
    if (cs := self.GetContextMenu()) is None or cs.InvokeCommand('Copy', hwnd=hwnd) is None or (cd := destination.GetContextMenu()) is None:
      return None
    return cd.InvokeCommand('Paste', hwnd=hwnd)
  def ContextMenuMoveTo(self, destination, hwnd=None):
    if (cs := self.GetContextMenu()) is None or cs.InvokeCommand('Cut', hwnd=hwnd) is None or (cd := destination.GetContextMenu()) is None:
      return None
    return cd.InvokeCommand('Paste', hwnd=hwnd)
  def ContextMenuShortcutTo(self, destination, hwnd=None):
    if (cs := self.GetContextMenu()) is None or cs.InvokeCommand('Copy', hwnd=hwnd) is None or (cd := destination.GetContextMenu()) is None:
      return None
    return cd.InvokeCommand('PasteLink', hwnd=hwnd)
  def ContextMenuDelete(self, confirmation=True, permanent=False, hwnd=None):
    if (c := self.GetContextMenu()) is None:
      return None
    return c.InvokeCommand('Delete', confirmation=confirmation, shift_down=permanent, hwnd=hwnd)
  SHCreateItemFromIDList = classmethod(lambda cls, pidl, interface=None, _shcifidl=_WShUtil._wrap('SHCreateItemFromIDList', (WSPITEMIDLIST, 1), (PUUID, 1), (wintypes.PLPVOID, 2)): (interface or cls)(_shcifidl(pidl, (interface or cls).IID)))
  SHCreateItemFromParsingName = classmethod(lambda cls, name, interface=None, bind_context=None, _shcifpn=_WShUtil._wrap('SHCreateItemFromParsingName', (wintypes.LPCWSTR, 1), (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2)): (interface or cls)(_shcifpn(name, bind_context, (interface or cls).IID)))
  SHCreateItemFromRelativeName = classmethod(lambda cls, parent, name, interface=None, bind_context=None, _shcifrn=_WShUtil._wrap('SHCreateItemFromRelativeName', (wintypes.LPVOID, 1), (wintypes.LPCWSTR, 1), (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2)): _WShUtil._set_factory((interface or cls)(_shcifrn(parent, name, bind_context, (interface or cls).IID)), getattr(parent, 'factory', None)))
  SHCreateItemWithParent = classmethod(lambda cls, parent, pidl, interface=None, _shciwp=_WShUtil._wrap('SHCreateItemWithParent', (WSPITEMIDLIST, 1), (wintypes.LPVOID, 1), (WSPITEMIDLIST, 1), (PUUID, 1), (wintypes.PLPVOID, 2)): _WShUtil._set_factory((interface or cls)(_shciwp(*((None, parent) if isinstance(parent, (IShellFolder, wintypes.LPVOID)) else (parent, None)), pidl, (interface or cls).IID)), getattr(parent, 'factory', None)))
  SHGetItemFromObject = classmethod(lambda cls, obj, interface=None, _shgifo=_WShUtil._wrap('SHGetItemFromObject', (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2)): _WShUtil._set_factory((interface or cls)(_shgifo(obj, (interface or cls).IID)), getattr(obj, 'factory', None)))
IshellItem2 = IShellItem

class IEnumShellItems(IUnknown):
  IID = GUID(0x70629033, 0xe363, 0x4a28, 0xa5, 0x67, 0x0d, 0xb7, 0x80, 0x06, 0xe6, 0xd7)
  _protos['Next'] = 3, (wintypes.ULONG, wintypes.PLPVOID, wintypes.PULONG), ()
  _protos['Skip'] = 4, (wintypes.ULONG,), ()
  _protos['Reset'] = 5, (), ()
  _protos['Clone'] = 6, (), (wintypes.PLPVOID,)
  def __new__(cls, clsid_component=False, factory=None):
    if isinstance(clsid_component, IShellItemArray):
      return _WShUtil._set_factory(clsid_component.EnumItems(), factory)
    if clsid_component is False or isinstance(clsid_component, (WSPITEMIDLIST, IShellFolder)):
      clsid_component = IShellItem(clsid_component)
    if isinstance(clsid_component, str):
      clsid_component = IShellItem.SHCreateItemFromParsingName(clsid_component, IShellItem)
    if isinstance(clsid_component, IShellItem):
      return _WShUtil._set_factory(clsid_component.GetContent(), factory)
    return IUnknown.__new__(cls, clsid_component, factory)
  def Reset(self):
    return self.__class__._protos['Reset'](self.pI)
  def Next(self, number):
    r = wintypes.ULONG()
    a = (wintypes.LPVOID * number)()
    return None if self.__class__._protos['Next'](self.pI, number, a, r) is None else tuple(IShellItem(a[i], self.factory) for i in range(r.value))
  def Skip(self, number):
    try:
      return self.__class__._protos['Skip'](self.pI, number)
    except:
      ISetLastError(0x80070057)
      return None
  def Clone(self):
    return self.__class__(self.__class__._protos['Clone'](self.pI), self.factory)
  def __iter__(self):
    return self
  def __next__(self):
    if not (n := self.Next(1)):
      raise StopIteration
    return n[0]

class IShellItemArray(IUnknown):
  IID = GUID(0xb63ea76d, 0x1f85, 0x456f, 0xa1, 0x9c, 0x48, 0x15, 0x9e, 0xfa, 0x85, 0x8b)
  _protos['BindToHandler'] = 3, (wintypes.LPVOID, WSPBHID, PUUID), (wintypes.PLPVOID,)
  _protos['GetAttributes'] = 6, (WSSIATTRIBFLAGS, WSSFGAO), (WSPSFGAO,)
  _protos['GetCount'] = 7, (), (wintypes.PDWORD,)
  _protos['GetItemAt'] = 8, (wintypes.DWORD,), (wintypes.PLPVOID,)
  _protos['EnumItems'] = 9, (), (wintypes.PLPVOID,)
  def __new__(cls, clsid_component=False, factory=None):
    if clsid_component is False:
      clsid_component = IShellFolder()
    if isinstance(clsid_component, IShellItem):
      return _WShUtil._set_factory(cls.SHCreateShellItemArrayFromShellItem(clsid_component, cls), factory)
    if isinstance(clsid_component, str):
      if (clsid_component := IShellItem.SHCreateItemFromParsingName(clsid_component, IShellItem)) is not None:
        clsid_component = clsid_component.AsFolder()
    if isinstance(clsid_component, WSPITEMIDLIST):
      clsid_component = IShellFolder(clsid_component)
    if isinstance(clsid_component, IShellFolder):
      return _WShUtil._set_factory(None if (e := clsid_component.EnumObjects(0x60)) is None else cls.SHCreateShellItemArray(clsid_component, tuple(e)), factory)
    if isinstance(clsid_component, ctypes.Array) and issubclass(clsid_component._type_, WSPITEMIDLIST):
      return _WShUtil._set_factory(cls.SHCreateShellItemArrayFromIDLists(clsid_component), factory)
    if isinstance(clsid_component, IEnumShellItems):
      if factory is False:
        factory = None
      elif factory is None:
        factory = clsid_component.factory
      clsid_component = tuple(map(PIDL, clsid_component))
    if isinstance(clsid_component, (tuple, list, ctypes.Array)):
      return _WShUtil._set_factory(cls.SHCreateShellItemArrayFromIDLists(tuple(p if p is None or isinstance(p, WSPITEMIDLIST) else WSPITEMIDLIST(p) for p in clsid_component)), factory)
    return IUnknown.__new__(cls, clsid_component, factory)
  def GetAttributes(self, combine_flags, query_attributes):
    return self._protos['GetAttributes'](self.pI, combine_flags, query_attributes)
  def GetCount(self):
    return self.__class__._protos['GetCount'](self.pI)
  def GetItemAt(self, index):
    return IShellItem(self.__class__._protos['GetItemAt'](self.pI, index), self.factory)
  def EnumItems(self):
    return IEnumShellItems(self.__class__._protos['EnumItems'](self.pI), self.factory)
  def BindToHandler(self, handler_guid, interface, bind_context=None):
    return interface(self._protos['BindToHandler'](self.pI, bind_context, handler_guid, interface.IID), self.factory)
  @classmethod
  def FromNames(cls, names, bind_context=None, factory=None):
    return cls(tuple(WSPITEMIDLIST.FromName(name, bind_context) for name in names), factory)
  @classmethod
  def FromPathes(cls, pathes, factory=None):
    return cls(tuple(map(WSPITEMIDLIST.FromPath, pathes)), factory)
  def GetDataObject(self, bind_context=None):
    return self.BindToHandler('DataObject', IDataObject, bind_context)
  @property
  def AsDataObject(self):
    return self.GetDataObject()
  def GetContextMenu(self, bind_context=None):
    return self.BindToHandler('SFUIObject', IContextMenu, bind_context)
  @property
  def ContextMenu(self):
    return self.GetContextMenu()
  def CopyTo(self, destination, confirmation=True, hwnd=None):
    if (f := IFileOperation.Create(confirmation, hwnd)) is None or (d := (destination if isinstance(destination, IShellItem) else IShellItem(destination))) is None or f.CopyItems(self, d) is None:
      return None
    return f.PerformOperations() is not None and not f.GetAnyOperationsAborted()
  def MoveTo(self, destination, confirmation=True, hwnd=None):
    if (f := IFileOperation.Create(confirmation, hwnd)) is None or (d := (destination if isinstance(destination, IShellItem) else IShellItem(destination))) is None or f.MoveItems(self, d) is None:
      return None
    return f.PerformOperations() is not None and not f.GetAnyOperationsAborted()
  def Delete(self, confirmation=True, hwnd=None):
    if (f := IFileOperation.Create(confirmation, hwnd)) is None or f.DeleteItems(self) is None:
      return None
    return f.PerformOperations() is not None and not f.GetAnyOperationsAborted()
  def DropCopyTo(self, destination, hwnd=None):
    if (s := self.GetDataObject()) is None or (d := (destination if isinstance(destination, IDropTarget) else destination.GetDropTarget(hwnd))) is None:
      return None
    return d.DropCopy(s) or None
  def DropMoveTo(self, destination, hwnd=None):
    if (s := self.GetDataObject()) is None or (d := (destination if isinstance(destination, IDropTarget) else destination.GetDropTarget(hwnd))) is None:
      return None
    return d.DropMove(s) or None
  def DropShortcutTo(self, destination, hwnd=None):
    if (s := self.GetDataObject()) is None or (d := (destination if isinstance(destination, IDropTarget) else destination.GetDropTarget(hwnd))) is None:
      return None
    return d.DropShortcut(s) or None
  def ContextMenuCopyTo(self, destination, hwnd=None):
    if (cs := self.GetContextMenu()) is None or cs.InvokeCommand('Copy', hwnd=hwnd) is None or (cd := destination.GetContextMenu()) is None:
      return None
    return cd.InvokeCommand('Paste', hwnd=hwnd)
  def ContextMenuMoveTo(self, destination, hwnd=None):
    if (cs := self.GetContextMenu()) is None or cs.InvokeCommand('Cut', hwnd=hwnd) is None or (cd := destination.GetContextMenu()) is None:
      return None
    return cd.InvokeCommand('Paste', hwnd=hwnd)
  def ContextMenuShortcutTo(self, destination, hwnd=None):
    if (cs := self.GetContextMenu()) is None or cs.InvokeCommand('Copy', hwnd=hwnd) is None or (cd := destination.GetContextMenu()) is None:
      return None
    return cd.InvokeCommand('PasteLink', hwnd=hwnd)
  def ContextMenuDelete(self, confirmation=True, permanent=False, hwnd=None):
    if (c := self.GetContextMenu()) is None:
      return None
    return c.InvokeCommand('Delete', confirmation=confirmation, shift_down=permanent, hwnd=hwnd)
  def __len__(self):
    if (l := getattr(self, '_len', False)) is False:
      l = self.GetCount()
      self._len = l
    return l
  def __getitem__(self, key):
    return self.GetItemAt(k) if isinstance((k := range(len(self))[key]), int) else tuple(map(self.GetItemAt, k))
  SHCreateShellItemArray = classmethod(lambda cls, parent, pidls, _shcsia=_WShUtil._wrap('SHCreateShellItemArray', (WSPITEMIDLIST, 1), (wintypes.LPVOID, 1), (wintypes.UINT, 1), (WSPPITEMIDLIST, 1), (wintypes.PLPVOID, 2)): _WShUtil._set_factory(cls(_shcsia(*((None, parent) if isinstance(parent, (IShellFolder, wintypes.LPVOID)) else (parent, None)), (0 if pidls is None else len(pidls)), (pidls if pidls is None or isinstance(pidls, ctypes.Array) else (WSPITEMIDLIST * len(pidls))(*pidls)))), getattr(parent, 'factory', None)))
  SHCreateShellItemArrayFromIDLists = classmethod(lambda cls, pidls, _shcsiafidl=_WShUtil._wrap('SHCreateShellItemArrayFromIDLists', (wintypes.UINT, 1), (WSPPITEMIDLIST, 1), (wintypes.PLPVOID, 2)): cls(_shcsiafidl((0 if pidls is None else len(pidls)), (pidls if pidls is None or isinstance(pidls, ctypes.Array) else (WSPITEMIDLIST * len(pidls))(*pidls)))))
  SHCreateShellItemArrayFromShellItem = classmethod(lambda cls, item, interface=None, _shcsiafsi=_WShUtil._wrap('SHCreateShellItemArrayFromShellItem', (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2)): _WShUtil._set_factory((interface or cls)(_shcsiafsi(item, (interface or cls).IID)), getattr(item, 'factory', None)))

class HBITMAP(wintypes.HBITMAP):
  def __del__(self):
    gdi32.DeleteObject(self)
  def SaveTo(self, path, format=None, imaging_factory=None):
    if (fact := (imaging_factory or IWICImagingFactory())) is None or (bm := fact.CreateBitmapFromHBITMAP(self)) is None or (enc := fact.CreateEncoder(format or (p[2] if (p := path.rpartition('.'))[1] == '.' else 'png'))) is None or (istr := IStream.CreateOnFile(path, 'write')) is None or not enc.Initialize(istr) or (nf := enc.CreateNewFrame()) is None or not (fenc := nf[0]).Initialize() or not fenc.WriteSource(bm) or not fenc.Commit() or not enc.Commit():
      return False
    return True
PHBITMAP = ctypes.POINTER(HBITMAP)

class IShellItemImageFactory(IUnknown):
  IID = GUID(0xbcc18b79, 0xba16, 0x442f, 0x80, 0xc4, 0x8a, 0x59, 0xc3, 0x0c, 0x46, 0x3b)
  _protos['GetImage'] = 3, (SIZE, WSSIIGBF), (PHBITMAP,)
  def __new__(cls, clsid_component=False, factory=None):
    if clsid_component is False:
      clsid_component = IShellFolder()
    if isinstance(clsid_component, str):
      clsid_component = WSPITEMIDLIST(clsid_component)
    if isinstance(clsid_component, WSPITEMIDLIST):
      return _WShUtil._set_factory(IShellItem.SHCreateItemFromIDList(clsid_component, cls), factory)
    if isinstance(clsid_component, IShellItem):
      return _WShUtil._set_factory(clsid_component.GetImageFactory(), factory)
    if isinstance(clsid_component, IShellFolder):
      return _WShUtil._set_factory(IShellItem.SHGetItemFromObject(clsid_component, cls), factory)
    return IUnknown.__new__(cls, clsid_component, factory)
  def GetImage(self, size, flags=0):
    return self.__class__._protos['GetImage'](self.pI, size, flags)
  @classmethod
  def FromName(cls, name='', bind_context=None, factory=None):
    return _WShUtil._set_factory(IShellItem.SHCreateItemFromParsingName(name, cls, bind_context), factory)
  @classmethod
  def FromPath(cls, path='', factory=None):
    return None if (pidl := WSPITEMIDLIST.FromPath(path)) is None else _WShUtil._set_factory(IShellItem.SHCreateItemFromIDList(pidl, cls), factory)

class IFileOperation(IUnknown):
  CLSID = GUID(0x3ad05575, 0x8857, 0x4850, 0x92, 0x77, 0x11, 0xb8, 0x5b, 0xdb, 0x8e, 0x09)
  IID = GUID(0x947aab5f, 0x0a5c, 0x4c13, 0xb4, 0xd6, 0x4b, 0xf7, 0x83, 0x6f, 0xc9, 0xf8)
  _protos['SetOperationFlags'] = 5, (WSOPERATIONFLAGS,), ()
  _protos['SetOwnerWindow'] = 9, (wintypes.HWND,), ()
  _protos['RenameItem'] = 12, (wintypes.LPVOID, wintypes.LPCWSTR, wintypes.LPVOID), ()
  _protos['RenameItems'] = 13, (wintypes.LPVOID, wintypes.LPCWSTR), ()
  _protos['MoveItem'] = 14, (wintypes.LPVOID, wintypes.LPVOID, wintypes.LPCWSTR, wintypes.LPVOID), ()
  _protos['MoveItems'] = 15, (wintypes.LPVOID, wintypes.LPVOID), ()
  _protos['CopyItem'] = 16, (wintypes.LPVOID, wintypes.LPVOID, wintypes.LPCWSTR, wintypes.LPVOID), ()
  _protos['CopyItems'] = 17, (wintypes.LPVOID, wintypes.LPVOID), ()
  _protos['DeleteItem'] = 18, (wintypes.LPVOID, wintypes.LPVOID), ()
  _protos['DeleteItems'] = 19, (wintypes.LPVOID,), ()
  _protos['NewItem'] = 20, (wintypes.LPVOID, WSFILEATTRIBUTES, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID), ()
  _protos['PerformOperations'] = 21, (), ()
  _protos['GetAnyOperationsAborted'] = 22, (), (wintypes.PBOOLE,)
  def SetOperationFlags(self, operation_flags=0x240):
    return self._protos['SetOperationFlags'](self.pI, operation_flags)
  def SetOwnerWindow(self, hwnd=None):
    return self._protos['SetOwnerWindow'](self.pI, hwnd)
  def RenameItem(self, item, name):
    return self._protos['RenameItem'](self.pI, item, name, None)
  def RenameItems(self, items, name):
    return self._protos['RenameItems'](self.pI, items, name)
  def MoveItem(self, item, destination, name=None):
    return self._protos['MoveItem'](self.pI, item, destination, name, None)
  def MoveItems(self, items, destination):
    return self._protos['MoveItems'](self.pI, items, destination)
  def CopyItem(self, item, destination, name=None):
    return self._protos['CopyItem'](self.pI, item, destination, name, None)
  def CopyItems(self, items, destination):
    return self._protos['CopyItems'](self.pI, items, destination)
  def DeleteItem(self, item):
    return self._protos['DeleteItem'](self.pI, item, None)
  def DeleteItems(self, items):
    return self._protos['DeleteItems'](self.pI, items)
  def NewItem(self, destination, name, attributes=128, template=None):
    return self._protos['NewItem'](self.pI, destination, attributes, name, template, None)
  def PerformOperations(self):
    return self._protos['PerformOperations'](self.pI)
  def GetAnyOperationsAborted(self):
    return self._protos['GetAnyOperationsAborted'](self.pI)
  @classmethod
  def Create(cls, confirmation=True, hwnd=None):
    return None if (f := cls()) is None or (not confirmation and f.SetOperationFlags(0x250) is None) or (hwnd is not None and f.SetOwnerWindow(hwnd) is None) else f

class IWshShortcut(IDispatch):
  IID = GUID(0xf935dc23, 0x1cf0, 0x11d0, 0xad, 0xb9, 0x00, 0xc0, 0x4f, 0xd5, 0x8a, 0x0b)
  def Save(self):
    return self.InvokeMethod('Save', res=False)
  @property
  def FullName(self):
    return self.InvokeGet('FullName')
  @property
  def Description(self):
    return self.InvokeGet('Description')
  @Description.setter
  def Description(self, value):
    return self.InvokeSet('Description', ('VT_BSTR', value))
  @property
  def Hotkey(self):
    return self.InvokeGet('Hotkey')
  @Hotkey.setter
  def Hotkey(self, value):
    return self.InvokeSet('Hotkey', ('VT_BSTR', value))
  @property
  def TargetPath(self):
    return self.InvokeGet('TargetPath')
  @TargetPath.setter
  def TargetPath(self, value):
    return self.InvokeSet('TargetPath', ('VT_BSTR', value))
  @property
  def Arguments(self):
    return self.InvokeGet('Arguments')
  @Arguments.setter
  def Arguments(self, value):
    return self.InvokeSet('Arguments', ('VT_BSTR', value))
  @property
  def WorkingDirectory(self):
    return self.InvokeGet('WorkingDirectory')
  @WorkingDirectory.setter
  def WorkingDirectory(self, value):
    return self.InvokeSet('WorkingDirectory', ('VT_BSTR', value))
  @property
  def WindowStyle(self):
    return {1: 'default', 3: 'maximized', 7: 'minimized'}.get((r := self.InvokeGet('WindowStyle')), r)
  @WindowStyle.setter
  def WindowStyle(self, value):
    return self.InvokeSet('WindowStyle', ('VT_INT', ({'default': 1, 'maximized': 3, 'minimized': 7}.get(value.lower(), 1) if isinstance(value, str) else value)))
  @property
  def IconLocation(self):
    return self.InvokeGet('IconLocation')
  @IconLocation.setter
  def IconLocation(self, value):
    return self.InvokeSet('IconLocation', ('VT_BSTR', value))

class IWshCollection(IDispatch):
  IID = GUID(0xf935dc27, 0x1cf0, 0x11d0, 0xad, 0xb9, 0x00, 0xc0, 0x4f, 0xd5, 0x8a, 0x0b)
  def __len__(self):
    return self.InvokeGet('length') or 0
  def Item(self, index):
    return self.InvokeMethod('Item', pargs=((('VT_BSTR' if isinstance(index, str) else 'VT_UINT'), index),)) or None
  def __getitem__(self, index):
    return self.Item(index) if isinstance(index, str) or isinstance((k := range(len(self))[index]), int) else tuple(map(self.Item, k))

class IWshEnvironment(IDispatch):
  IID = GUID(0xf935dc29, 0x1cf0, 0x11d0, 0xad, 0xb9, 0x00, 0xc0, 0x4f, 0xd5, 0x8a, 0x0b)
  def __len__(self):
    return self.InvokeGet('length') or 0
  def __getitem__(self, name):
    if isinstance(name, str):
      return self.InvokeGet('Item', pargs=(('VT_BSTR', name),)) or None
    raise TypeError('range indices must be str')
  def __setitem__(self, name, value):
    if isinstance(name, str):
      self.InvokeSet('Item', ('VT_BSTR', value), pargs=(('VT_BSTR', name),)) or None
    else:
      raise TypeError('range indices must be str')
  def __delitem__(self, name):
    if isinstance(name, str):
      self.InvokeMethod('Remove', pargs=(('VT_BSTR', name),), res=False)
    else:
      raise TypeError('range indices must be str')

class IWshShell(IDispatch):
  CLSID = 'Wscript.Shell'
  IID = GUID(0x24be5a30, 0xedfe, 0x11d2, 0xb9, 0x33, 0x00, 0x10, 0x4b, 0x36, 0x5c, 0x9f)
  def CreateShortcut(self, link_path):
    return _IUtil.QueryInterface(self.InvokeMethod('CreateShortCut', pargs=(('VT_BSTR', link_path),)), IWshShortcut, self.factory)
  def Popup(self, text, title=None, icon=None, buttons=None, secs=None):
    nargs = {}
    if title is not None:
      nargs['Title'] = VARIANT('VT_BSTR', title)
    if icon is not None or buttons is not None:
      if isinstance(icon, str):
        icon = {'critical': 16, 'question': 32, 'exclamation': 48, 'information': 64}.get(icon.lower(), 64)
      if isinstance(buttons, str):
        buttons = {'ok': 0, 'ok,cancel': 1, 'abort,ignore,retry': 2, 'yes,no,cancel': 3, 'yes,no': 4, 'retry,cancel': 5}.get(buttons.lower().replace(' ', ''), 0)
      nargs['Type'] = VARIANT('VT_UINT', (icon or 0) | (buttons or 0))
    if secs is not None:
      nargs['SecondsToWait'] = VARIANT('VT_UINT', secs)
    return None if (ob := self.InvokeMethod('Popup', pargs=(('VT_BSTR', text),), nargs=nargs)) is None else (ob, {1: 'OK', 2: 'Cancel', 3: 'Abort', 4: 'Retry', 5: 'Ignore', 6: 'Yes', 7: 'No', -1: 'None'}.get(ob, ''))
  @property
  def SpecialFolders(self):
    return _IUtil.QueryInterface(self.InvokeGet('SpecialFolders'), IWshCollection, self.factory)
  def Environment(self, etype=None):
    return _IUtil.QueryInterface(self.InvokeGet('Environment', nargs=(None if etype is None else {'type': ('VT_BSTR', etype)})), IWshEnvironment, self.factory)
  def SendKeys(self, keys):
    return self.InvokeMethod('SendKeys', pargs=(('VT_BSTR', keys),), res=False)
  def AppActivate(self, app):
    return self.InvokeMethod('AppActivate', pargs=((('VT_BSTR' if isinstance(app, str) else 'VT_UINT'), app),))
IWshShell2 = IWshShell


class _WndUtil:
  @staticmethod
  def _errcheck(r, f, a):
    return getattr(r, 'value', r) if (c := getattr(r, '__ctypes_from_outparam__', None)) is None else c()
  @staticmethod
  def _wrap(n, *r_a, p=user32):
    r, *a = r_a
    f = ctypes.WINFUNCTYPE(*r_a, use_last_error=True)((n, p), ((1,),) * len(a))
    f.errcheck = _WndUtil._errcheck
    return f

WNDPROC = ctypes.WINFUNCTYPE(wintypes.LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM, use_last_error=True)

WNDClassStyle = {'ByteAlignClient': 0x1000, 'ByteAlignWindow': 0x2000, 'ClassDC': 0x40, 'DblClks': 0x8, 'DropShadow': 0x20000, 'GlobalClass': 0x4000, 'HRedraw': 0x2, 'NoClose': 0x200, 'OwnDC': 0x20, 'ParentDC': 0x80, 'SaveBits': 0x800, 'VRedraw': 0x1}
WNDCLASSSTYLE = type('WNDCLASSSTYLE', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in WNDClassStyle.items()}, '_tab_cn': {c: n for n, c in WNDClassStyle.items()}, '_def': 0})

class WNDCLASS(_BDSStruct, ctypes.Structure, metaclass=_WSMeta):
  _fields_ = [('cbSize', wintypes.UINT), ('style', WNDCLASSSTYLE), ('lpfnWndProc', WNDPROC), ('cbClsExtra', wintypes.INT),  ('cbWndExtra', wintypes.INT), ('hInstance', wintypes.HINSTANCE),  ('hIcon', wintypes.HICON), ('hCursor', wintypes.HCURSOR), ('hBrush', wintypes.HBRUSH), ('lpszMenuName', wintypes.LPCWSTR), ('lpszClassName', wintypes.LPCWSTR), ('hIconSm', wintypes.HICON)]
WNDPCLASS = type('WNDPCLASS', (_BPStruct, ctypes.POINTER(WNDCLASS)),  {'_type_': WNDCLASS})

WNDWindowStyle = {'Border': 0x800000, 'Caption': 0xC00000, 'Child': 0x40000000, 'ClipChildren': 0x2000000, 'ClipSiblings': 0x4000000, 'Disabled': 0x8000000, 'DlgFrame': 0x400000, 'Group': 0x20000, 'HScroll': 0x100000, 'Maximize': 0x1000000, 'MaximizeBox': 0x10000, 'Minimize': 0x20000000, 'MinimizeBox': 0x20000, 'Overlapped': 0, 'Popup': 0x80000000, 'SizeBox': 0x40000, 'SysMenu': 0x80000, 'Visible': 0x10000000, 'VScroll': 0x200000}
WNDWINDOWSTYLE = type('WNDWINDOWSTYLE', (_BCodeOr, wintypes.DWORD), {'_tab_nc': {n.lower(): c for n, c in WNDWindowStyle.items()}, '_tab_cn': {c: n for n, c in WNDWindowStyle.items()}, '_def': 0})

WNDCmdRelationship = {'Child': 5, 'EnabledPopup': 6, 'First': 0, 'Last': 1, 'Next': 2, 'Prev': 3, 'Owner': 4}
WNDCMDRELATIONSHIP = type('WNDCMDRELATIONSHIP', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in WNDCmdRelationship.items()}, '_tab_cn': {c: n for n, c in WNDCmdRelationship.items()}, '_def': 5})

WNDAncestorFlag = {'Parent': 1, 'Root': 2, 'RootOwner': 3}
WNDANCESTORFLAG = type('WNDANCESTORFLAG', (_BCode, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in WNDAncestorFlag.items()}, '_tab_cn': {c: n for n, c in WNDAncestorFlag.items()}, '_def': 1})

WNDCmdShow = {'Hide': 0, 'ShowNormal': 1, 'ShowMinimized': 2, 'ShowMaximized': 3, 'ShowNoActivate': 4, 'Show': 5, 'Minimize': 6, 'ShowMinNoActive': 7, 'ShowNA': 8, 'Restore': 9, 'ShowDefault': 10, 'ForceMinimize': 11}
WNDCMDSHOW = type('WNDCMDSHOW', (_BCode, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WNDCmdShow.items()}, '_tab_cn': {c: n for n, c in WNDCmdShow.items()}, '_def': 5})

WNDPosHwnd = {'Bottom': 1, 'NoTopMost': -2, 'Top': 0, 'TopMost': -1}
WNDPOSHWND = type('WNDPOSHWND', (_BCode, wintypes.LPARAM), {'_tab_nc': {n.lower(): c for n, c in WNDPosHwnd.items()}, '_tab_cn': {c: n for n, c in WNDPosHwnd.items()}, '_def': 0})

WNDPosFlags = {'AsyncWindowPos': 0x4000, 'DeferErase': 0x2000, 'DrawFrame': 0x20, 'FrameChanged': 0x20, 'HideWindow': 0x80, 'NoActivate': 0x10, 'NoCopyBits': 0x100, 'NoMove': 0x2, 'NoOwnerZOrder': 0x200, 'NoReposition': 0x200, 'NoSendChanging': 0x400, 'NoSize': 0x1, 'NoZOrder': 0x4, 'ShowWindow': 0x40}
WNDPOSFLAGS = type('WNDPOSFLAGS', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in WNDPosFlags.items()}, '_tab_cn': {c: n for n, c in WNDPosFlags.items()}, '_def': 0})

WNDIndex = {'ExStyle': -20, 'HInstance': -6, 'HwndParent': -8, 'ID': -12, 'Style': -16, 'UserData': -21, 'WndProc': -4}
WNDINDEX = type('WNDINDEX', (_BCode, wintypes.INT), {'_tab_nc': {n.lower(): c for n, c in WNDIndex.items()}, '_tab_cn': {c: n for n, c in WNDIndex.items()}, '_def': -16})

WNDRemoveMsg = {'NoRemove': 0, 'Remove': 1, 'NoYield': 2, 'Input': 0x1c070000, 'PostMessage': 0x980000, 'Paint': 0x200000, 'SendMessage': 0x400000}
WNDREMOVEMSG = type('WNDREMOVEMSG', (_BCodeOr, wintypes.UINT), {'_tab_nc': {n.lower(): c for n, c in WNDRemoveMsg.items()}, '_tab_cn': {c: n for n, c in WNDRemoveMsg.items()}, '_def': 0})

class HWND(wintypes.HWND):
  def __new__(cls, hwnd, ml=None):
    return None if hwnd is None else wintypes.HWND.__new__(cls, hwnd)
  def __init__(self, hwnd, ml=None):
    wintypes.HWND.__init__(self, hwnd)
    self._ml = ml
  @property
  def hwnd(self):
    return self.value
  def __eq__(self, other):
    return self.value == getattr(other, 'value', other)
  @property
  def IsExisting(self):
    return Window.IsWindow(self)
  def Shut(self):
    return Window.ShutWindow(self)
  def WaitShutdown(self, timeout=None):
    if self._ml:
      self._ml.join(timeout)
  def GetWindow(self, cmd=5):
    return HWND(Window.GetWindow(self, cmd))
  def FindChildWindow(self, previous_hwnd=None, class_name=None, window_name=None):
    return HWND(Window.FindWindowEx(self, previous_hwnd, class_name, window_name))
  def GetAncestor(self, flag=1):
    return HWND(Window.GetAncestor(self, flag))
  @property
  def Parent(self):
    return HWND(Window.GetAncestor(self, 1))
  @property
  def Owner(self):
    return HWND(Window.GetWindow(self, 4))
  @property
  def ParentOrOwner(self):
    return HWND(Window.GetParent(self))
  @Parent.setter
  def Parent(self, value):
    Window.SetParent(self, value)
  def IsChildOf(self, hwnd):
    return Window.IsChild(hwnd, self)
  def HasForChild(self, hwnd):
    return Window.IsChild(self, hwnd)
  @property
  def IsVisible(self):
    return Window.IsWindowVisible(self)
  @property
  def IsZoomed(self):
    return Window.IsZoomed(self)
  def Show(self, cmd=5):
    return Window.ShowWindow(self, cmd)
  def ShowOwnedPopups(self, show=True):
    return Window.ShowOwnedPopups(self, show)
  def Close(self):
    return Window.CloseWindow(self)
  def Destroy(self):
    return Window.DestroyWindow(self)
  @property
  def TopWindow(self):
    return HWND(Window.GetTopWindow(self))
  def BringToTop(self):
    return Window.BringWindowToTop(self)
  @property
  def Rect(self):
    r = RECT()
    return r if Window.GetWindowRect(self, r) else None
  @property
  def ClientRect(self):
    r = RECT()
    return r if Window.GetClientRect(self, r) else None
  def Move(self, ltwh, repaint=True):
    return Window.MoveWindow(self, *ltwh, repaint)
  def SetPos(self, insert_after, ltwh, flags=0):
    return Window.SetWindowPos(self, getattr(insert_after, 'value', insert_after) or 0, *ltwh, flags)
  @property
  def ClassName(self):
    cn = ctypes.create_unicode_buffer(257)
    ctypes.set_last_error(0)
    return None if not Window.GetClassName(self, cn, 257) and ctypes.get_last_error() else cn.value
  @property
  def Name(self):
    return Window.GetWindowName(self)
  @Name.setter
  def Name(self, value):
    Window.SetWindowName(self, value)
  @property
  def ThreadProcessId(self):
    pid = wintypes.DWORD()
    ctypes.set_last_error(0)
    return None if not (tid := Window.GetWindowThreadProcessId(self, pid)) and ctypes.get_last_error() else (tid, pid.value)
  @property
  def ExStyle(self):
    ctypes.set_last_error(0)
    return None if not (r := Window.GetWindowLongPtr(self, 'ExStyle')) and ctypes.get_last_error() else r
  @ExStyle.setter
  def ExStyle(self, value):
    Window.SetWindowLongPtr(self, 'ExStyle', value)
  @property
  def HInstance(self):
    ctypes.set_last_error(0)
    return None if not (r := Window.GetWindowLongPtr(self, 'HInstance')) and ctypes.get_last_error() else r
  @HInstance.setter
  def HInstance(self, value):
    Window.SetWindowLongPtr(self, 'HInstance', getattr(value, 'value', value) or 0)
  @property
  def HwndParent(self):
    ctypes.set_last_error(0)
    return None if not (r := Window.GetWindowLongPtr(self, 'HwndParent')) and ctypes.get_last_error() else r
  @HwndParent.setter
  def HwndParent(self, value):
    Window.SetWindowLongPtr(self, 'HwndParent', getattr(value, 'value', value) or 0)
  @property
  def ID(self):
    ctypes.set_last_error(0)
    return None if not (r := Window.GetWindowLongPtr(self, 'ID')) and ctypes.get_last_error() else r
  @property
  def Style(self):
    ctypes.set_last_error(0)
    return None if not (r := Window.GetWindowLongPtr(self, 'Style')) and ctypes.get_last_error() else WNDWINDOWSTYLE(r)
  @Style.setter
  def Style(self, value):
    Window.SetWindowLongPtr(self, 'Style', WNDWINDOWSTYLE.from_param(value))
  @property
  def WndProc(self):
    ctypes.set_last_error(0)
    return None if not (r := Window.GetWindowLongPtr(self, 'WndProc')) and ctypes.get_last_error() else r
  @WndProc.setter
  def WndProc(self, value):
    Window.SetWindowLongPtr(self, 'WndProc', getattr(value, 'value', value) or 0)
  def PeekMessage(self, filter=(0, 0), flag=0, lpMsg=None):
    if lpMsg is None:
      lpMsg = ctypes.pointer(wintypes.MSG())
    return lpMsg.contents if Window.PeekMessage(lpMsg, self, *filter, flag) else None
  def GetMessage(self, filter=(0, 0), lpMsg=None):
    if lpMsg is None:
      lpMsg = ctypes.pointer(wintypes.MSG())
    return None if Window.GetMessage(lpMsg, self, *filter) < 0 else lpMsg.contents
  def PostMessage(self, Msg, wParam, lParam):
    return Window.PostMessage(self, Msg, wParam, lParam)
  def SendMessage(self, Msg, wParam, lParam):
    ctypes.set_last_error(0)
    return None if not (r := Window.SendMessage(self, Msg, wParam, lParam)) and ctypes.get_last_error() else r
  def SendNotifyMessage(self, Msg, wParam, lParam):
    return Window.SendNotifyMessage(self, Msg, wParam, lParam)

class _WndMeta(type):
  @property
  def ModuleHandle(cls):
    return cls.GetModuleHandle(None)
  @property
  def DesktopWindow(cls):
    return HWND(cls.GetDesktopWindow())
  @property
  def ForegroundWindow(cls):
    return HWND(cls.GetForegroundWindow())
  @ForegroundWindow.setter
  def ForegroundWindow(cls, value):
    cls.SetForegroundWindow(value)
  def DefMessageLoop(cls, hwnd):
    lpMsg = ctypes.byref(wintypes.MSG())
    while cls.GetMessage(lpMsg, hwnd, 0, 0) > 0:
      cls.TranslateMessage(lpMsg)
      cls.DispatchMessage(lpMsg)
  def DefMessageLoopQuit(cls, hwnd):
    lpMsg = ctypes.byref(wintypes.MSG())
    while cls.GetMessage(lpMsg, None, 0, 0) > 0:
      cls.TranslateMessage(lpMsg)
      cls.DispatchMessage(lpMsg)

class Window(metaclass=_WndMeta):
  WindowProc = WNDPROC
  @classmethod
  def RegisterWindowClass(cls, class_name, window_proc=None, class_style=0):
    return cls.RegisterClassEx((class_style, window_proc or cls.DefWindowProc, 0,  0, cls.GetModuleHandle(None), 0, 0, 0, 0, class_name, 0))
  @classmethod
  def UnregisterWindowClass(cls, class_name):
    return cls.UnregisterClass((wintypes.LPCWSTR(class_name) if isinstance(class_name, (int, wintypes.ATOM)) else class_name), cls.GetModuleHandle(None))
  def __new__(cls, class_name, window_name='', window_style=0, window_ex_style=0, window_position=(0, 0), window_size=(0, 0), window_parent=None, window_menu=None, message_loop=None):
    hwnd = None
    b = threading.Barrier(2)
    def _new():
      nonlocal message_loop, hwnd
      try:
        hwnd = cls.CreateWindowEx(window_ex_style, (wintypes.LPCWSTR(class_name) if isinstance(class_name, (int, wintypes.ATOM)) else class_name), window_name, window_style, *window_position, *window_size, window_parent, window_menu, cls.GetModuleHandle(None), None)
      except:
        pass
      b.wait()
      if hwnd:
        (message_loop or cls.DefMessageLoop)(hwnd)
    th = threading.Thread(target=_new, daemon=True)
    th.start()
    b.wait()
    return HWND(hwnd, th)
  @classmethod
  def ShutWindow(cls, hwnd):
    return cls.PostMessage(hwnd, 0x10, 0, 0)
  @classmethod
  def GetWindowName(cls, hwnd):
    ctypes.set_last_error(0)
    if not (l := cls.GetWindowTextLength(hwnd)) and ctypes.get_last_error():
      return None
    n = ctypes.create_unicode_buffer(l + 1)
    ctypes.set_last_error(0)
    return None if not cls.GetWindowText(hwnd, n, l + 1) and ctypes.get_last_error() else n.value
  @classmethod
  def SetWindowName(cls, hwnd, name=''):
    return cls.SetWindowText(hwnd, name)
  GetModuleHandle = _WndUtil._wrap('GetModuleHandleW', wintypes.HMODULE, wintypes.LPCWSTR, p=kernel32)
  RegisterClassEx = _WndUtil._wrap('RegisterClassExW', wintypes.ATOM, WNDPCLASS)
  UnregisterClass = _WndUtil._wrap('UnregisterClassW', wintypes.BOOLE, wintypes.LPCWSTR, wintypes.HINSTANCE)
  CreateWindowEx = _WndUtil._wrap('CreateWindowExW', wintypes.HWND, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, WNDWINDOWSTYLE, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID)
  IsWindow = _WndUtil._wrap('IsWindow', wintypes.BOOLE, wintypes.HWND)
  GetWindow = _WndUtil._wrap('GetWindow', wintypes.HWND, wintypes.HWND, WNDCMDRELATIONSHIP)
  FindWindowEx = _WndUtil._wrap('FindWindowExW', wintypes.HWND, wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR)
  GetAncestor = _WndUtil._wrap('GetAncestor', wintypes.HWND, wintypes.HWND, WNDANCESTORFLAG)
  GetParent = _WndUtil._wrap('GetParent', wintypes.HWND, wintypes.HWND)
  SetParent = _WndUtil._wrap('SetParent', wintypes.HWND, wintypes.HWND, wintypes.HWND)
  IsChild = _WndUtil._wrap('IsChild', wintypes.BOOLE, wintypes.HWND, wintypes.HWND)
  IsWindowVisible = _WndUtil._wrap('IsWindowVisible', wintypes.BOOLE, wintypes.HWND)
  IsZoomed = _WndUtil._wrap('IsZoomed', wintypes.BOOLE, wintypes.HWND)
  ShowWindow = _WndUtil._wrap('ShowWindow', wintypes.BOOLE, wintypes.HWND, WNDCMDSHOW)
  ShowOwnedPopups = _WndUtil._wrap('ShowOwnedPopups', wintypes.BOOLE, wintypes.HWND, wintypes.BOOL)
  CloseWindow = _WndUtil._wrap('CloseWindow', wintypes.BOOLE, wintypes.HWND)
  DestroyWindow = _WndUtil._wrap('DestroyWindow', wintypes.BOOLE, wintypes.HWND)
  GetDesktopWindow = _WndUtil._wrap('GetDesktopWindow', wintypes.HWND)
  GetForegroundWindow = _WndUtil._wrap('GetForegroundWindow', wintypes.HWND)
  SetForegroundWindow = _WndUtil._wrap('SetForegroundWindow', wintypes.BOOLE, wintypes.HWND)
  GetTopWindow = _WndUtil._wrap('GetTopWindow', wintypes.HWND, wintypes.HWND)
  BringWindowToTop = _WndUtil._wrap('BringWindowToTop', wintypes.BOOLE, wintypes.HWND)
  GetWindowRect = _WndUtil._wrap('GetWindowRect', wintypes.BOOLE, wintypes.HWND, wintypes.LPRECT)
  GetClientRect = _WndUtil._wrap('GetClientRect', wintypes.BOOLE, wintypes.HWND, wintypes.LPRECT)
  AdjustWindowRectEx = _WndUtil._wrap('AdjustWindowRectEx', wintypes.BOOLE, wintypes.LPRECT, WNDWINDOWSTYLE, wintypes.BOOL, wintypes.DWORD)
  MoveWindow = _WndUtil._wrap('MoveWindow', wintypes.BOOLE, wintypes.HWND, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.BOOL)
  SetWindowPos = _WndUtil._wrap('SetWindowPos', wintypes.BOOLE, wintypes.HWND, WNDPOSHWND, wintypes.INT, wintypes.INT, wintypes.INT, wintypes.INT, WNDPOSFLAGS)
  GetClassName = _WndUtil._wrap('GetClassNameW', wintypes.INT, wintypes.HWND, wintypes.LPWSTR, wintypes.INT)
  GetWindowTextLength = _WndUtil._wrap('GetWindowTextLengthW', wintypes.INT, wintypes.HWND)
  GetWindowText = _WndUtil._wrap('GetWindowTextW', wintypes.INT, wintypes.HWND, wintypes.LPWSTR, wintypes.INT)
  SetWindowText = _WndUtil._wrap('SetWindowTextW', wintypes.BOOLE, wintypes.HWND, wintypes.LPCWSTR)
  GetWindowThreadProcessId = _WndUtil._wrap('GetWindowThreadProcessId', wintypes.DWORD, wintypes.HWND, wintypes.PDWORD)
  GetWindowLongPtr = _WndUtil._wrap('GetWindowLongPtrW', wintypes.LPARAM, wintypes.HWND, WNDINDEX)
  SetWindowLongPtr = _WndUtil._wrap('SetWindowLongPtrW', wintypes.LPARAM, wintypes.HWND, WNDINDEX, wintypes.LPARAM)
  PeekMessage = _WndUtil._wrap('PeekMessageW', wintypes.BOOLE, wintypes.LPMSG, wintypes.HWND, wintypes.UINT, wintypes.UINT, WNDREMOVEMSG)
  GetMessage = _WndUtil._wrap('GetMessageW', wintypes.LONG, wintypes.LPMSG, wintypes.HWND, wintypes.UINT, wintypes.UINT)
  TranslateMessage = _WndUtil._wrap('TranslateMessage', wintypes.BOOLE, wintypes.LPMSG)
  DispatchMessage = _WndUtil._wrap('DispatchMessageW', wintypes.LRESULT, wintypes.LPMSG)
  PostMessage = _WndUtil._wrap('PostMessageW', wintypes.BOOLE, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
  SendMessage = _WndUtil._wrap('SendMessageW', wintypes.LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
  SendNotifyMessage = _WndUtil._wrap('SendNotifyMessageW', wintypes.BOOLE, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
  PostQuitMessage = _WndUtil._wrap('PostQuitMessage', None, wintypes.INT)
  DefWindowProc = _WndUtil._wrap('DefWindowProcW', wintypes.LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
  @WindowProc
  def DefWindowProcQuit(hWnd, Msg, wParam, lParam):
    if Msg == 0x2:
      Window.PostQuitMessage(0)
    return Window.DefWindowProc(hWnd, Msg, wParam, lParam)
  CallWindowProc = _WndUtil._wrap('CallWindowProcW', wintypes.LRESULT, WNDPROC, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


def Initialize(mode=6, ole=False):
  if ISetLastError(ole32.OleInitialize(None) if ole else ole32.CoInitializeEx(None, wintypes.DWORD((mode := (4 if mode.lower() in ('mt', 'mta') else 6)) if isinstance(mode, str) else mode))):
    return None
  if not hasattr(_IUtil._local, 'initialized'):
    _IUtil._local.initialized = [0, 0]
    _IUtil._local.multithreaded = not (ole or bool(mode & 2))
  _IUtil._local.initialized[1 if ole else 0] += 1
  return True
def Uninitialize():
  if hasattr(_IUtil._local, 'initialized'):
    while _IUtil._local.initialized[1] > 0:
      ISetLastError(ole32.OleUninitialize())
      _IUtil._local.initialized[1] -= 1
    while _IUtil._local.initialized[0] > 0:
      ISetLastError(ole32.CoUninitialize())
      _IUtil._local.initialized[0] -= 1
    del _IUtil._local.initialized
    if hasattr(_IUtil._local, 'multithreaded'):
      del _IUtil._local.multithreaded
    return True
  return None

def DllGetClassObject(rclsid, riid, ppv):
  if not ppv:
    return ISetLastError(0x80004003)
  if not rclsid or not riid:
    arg = None
    ISetLastError(0x80004003)
  elif (arg := _COMMeta._COMImplMeta._clsids.get(GUID(UUID.from_address(rclsid)))) is None:
    ISetLastError(0x80040154)
  wintypes.LPVOID.from_address(ppv).value = arg and (_COM_IPSFactoryBuffer_impl(iid, ps_impl=arg) if (iid := UUID.from_address(riid)) == _COMMeta._iid_ipsfactorybuffer else _COM_IClassFactory_impl(iid, impl=arg))
  return ctypes.get_last_error()
def DllCanUnloadNow():
  ISetLastError(0)
  return 1 if _COMMeta._refs else 0

class COMRegistration:
  @classmethod
  def _RegisterFactory(cls, clsid, pUnk):
    if clsid is None or pUnk is None:
      return None
    token = cls.CoRegisterClassObject(clsid, pUnk, 1, 1)
    pUnk.Release()
    return token
  @classmethod
  def RegisterCOMFactory(cls, icls_impl):
    if not isinstance((impl := globals().get('_COM_%s_impl' % icls_impl.__name__) if isinstance(icls_impl, _IMeta) else icls_impl), _COMMeta._COMImplMeta):
      return None
    return cls._RegisterFactory(getattr(impl, 'CLSID', None), PCOM(_COM_IClassFactory_impl(_COMMeta._iid_iunknown, impl=impl)))
  @classmethod
  def RegisterPSFactory(cls, icls_ps_impl):
    if not isinstance((ps_impl := globals().get('_PS_%s_impl' % icls_ps_impl.__name__) if isinstance(icls_ps_impl, _IMeta) else icls_ps_impl), _PSImplMeta):
      return None
    return cls._RegisterFactory(getattr(ps_impl, 'CLSID', None), PCOM(_COM_IPSFactoryBuffer_impl(_COMMeta._iid_iunknown, ps_impl=ps_impl)))
  @classmethod
  def RevokeFactory(cls, token):
    return cls.CoRevokeClassObject(token)
  @classmethod
  def RegisterProxyStub(cls, icls_ps_impl, iid=None):
    if not isinstance((ps_impl := globals().get('_PS_%s_impl' % icls_ps_impl.__name__) if isinstance(icls_ps_impl, _IMeta) else icls_ps_impl), _PSImplMeta) or (clsid := getattr(ps_impl, 'CLSID', None)) is None:
      return None
    return {iid: cls.CoRegisterPSClsid(iid, clsid) for iid in ps_impl.stub_impl._siids[0]} if iid is None else cls.CoRegisterPSClsid(iid, clsid)
  @staticmethod
  def _RegistryAddFactory(clsid, name, user, server):
    if clsid is None:
      return False
    clsid = ('{%s}' % GUID(clsid)).upper()
    name = 'WICPy.' + name
    try:
      key = winreg.CreateKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\CLSID\%s' % clsid)
      winreg.SetValue(key, '', winreg.REG_SZ, name)
      skey = winreg.CreateKey(key, 'InprocServer32')
      winreg.SetValue(skey, '', winreg.REG_SZ, (server or os.path.join(os.path.dirname(os.path.abspath(globals().get('__file__', ' '))), "comserver.dll")))
      winreg.SetValueEx(skey, 'ThreadingModel', 0, winreg.REG_SZ, 'Both')
      winreg.CloseKey(skey)
      winreg.SetValue(key, 'ProgID', winreg.REG_SZ, name)
      winreg.CloseKey(key)
      key = winreg.CreateKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\%s' % name)
      winreg.SetValue(key, '', winreg.REG_SZ, name)
      winreg.SetValue(key, 'CLSID', winreg.REG_SZ, clsid)
      winreg.CloseKey(key)
      return True
    except:
      return False
  @classmethod
  def RegistryAddCOMFactory(cls, icls_impl, name=None, *, user=True, server=None):
    if not isinstance((impl := globals().get('_COM_%s_impl' % icls_impl.__name__) if isinstance(icls_impl, _IMeta) else icls_impl), _COMMeta._COMImplMeta):
      return False
    return cls._RegistryAddFactory(getattr(impl, 'CLSID', None), (impl.__name__[slice((5 if impl.__name__.upper().startswith('_COM_') else 0), (-5 if impl.__name__.lower().endswith('_impl') else None))] if name is None else name), user, server)
  @classmethod
  def RegistryAddPSFactory(cls, icls_ps_impl, name=None, *, user=True, server=None):
    if not isinstance((ps_impl := globals().get('_PS_%s_impl' % icls_ps_impl.__name__) if isinstance(icls_ps_impl, _IMeta) else icls_ps_impl), _PSImplMeta):
      return False
    return cls._RegistryAddFactory(getattr(ps_impl, 'CLSID', None), ((ps_impl.__name__[slice((4 if ps_impl.__name__.upper().startswith('_PS_') else 0), (-5 if ps_impl.__name__.lower().endswith('_impl') else None))] + 'ProxyStub') if name is None else name), user, server)
  @staticmethod
  def _RegistryRemoveFactory(clsid, user):
    if clsid is None:
      return False
    clsid = ('{%s}' % GUID(clsid)).upper()
    try:
      key = winreg.OpenKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\CLSID\%s' % clsid)
      if not (name := winreg.QueryValue(key, '')):
        raise
      winreg.DeleteKey(key, 'InprocServer32')
      winreg.DeleteKey(key, 'ProgID')
      winreg.CloseKey(key)
      winreg.DeleteKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\CLSID\%s' % clsid)
      winreg.DeleteKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\%s\CLSID' % name)
      winreg.DeleteKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\%s' % name)
      return True
    except:
      return False
  @classmethod
  def RegistryRemoveCOMFactory(cls, icls_impl, *, user=True):
    if not isinstance((impl := globals().get('_COM_%s_impl' % icls_impl.__name__) if isinstance(icls_impl, _IMeta) else icls_impl), _COMMeta._COMImplMeta):
      return False
    return cls._RegistryRemoveFactory(getattr(impl, 'CLSID', None), user)
  @classmethod
  def RegistryRemovePSFactory(cls, icls_ps_impl, *, user=True):
    if not isinstance((ps_impl := globals().get('_PS_%s_impl' % icls_ps_impl.__name__) if isinstance(icls_ps_impl, _IMeta) else icls_ps_impl), _PSImplMeta):
      return False
    return cls._RegistryRemoveFactory(getattr(ps_impl, 'CLSID', None), user)
  @classmethod
  def RegistryAddProxyStub(cls, iid_icls, name=None, ps_impl=None, *, user=True):
    if ps_impl is None:
      if name is not None:
        ps_impl = globals().get('_PS_%s_impl' % name)
      elif isinstance(iid_icls, _IMeta):
        ps_impl = globals().get('_PS_%s_impl' % iid_icls.__name__)
    if ps_impl is None or not isinstance(ps_impl, _PSImplMeta) or (clsid := getattr(ps_impl, 'CLSID', None)) is None:
      return False
    if name is None:
      name = iid_icls.__name__ if isinstance(iid_icls, _COMMeta) else ps_impl.__name__[slice((4 if ps_impl.__name__.upper().startswith('_PS_') else 0), (-5 if ps_impl.__name__.lower().endswith('_impl') else None))]
    clsid = ('{%s}' % GUID(clsid)).upper()
    iid = ('{%s}' % GUID(getattr(iid_icls, 'IID', iid_icls))).upper()
    name = 'WICPy.' + name
    try:
      key = winreg.CreateKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\Interface\%s' % iid)
      winreg.SetValue(key, '', winreg.REG_SZ, name)
      winreg.SetValue(key, 'ProxyStubClsid32', winreg.REG_SZ, clsid)
      winreg.CloseKey(key)
      return True
    except:
      return False
  @classmethod
  def RegistryRemoveProxyStub(cls, iid_name, *, user=True):
    iid = ('{%s}' % GUID(getattr(iid_name, 'IID', iid_name))).upper()
    try:
      winreg.DeleteKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\Interface\%s\ProxyStubClsid32' % iid)
      winreg.DeleteKey((winreg.HKEY_CURRENT_USER if user else winreg.HKEY_LOCAL_MACHINE), r'SOFTWARE\Classes\Interface\%s' % iid)
      return True
    except:
      return False
  CoRegisterClassObject = _WShUtil._wrap('CoRegisterClassObject', (PUUID, 1), (wintypes.LPVOID, 1), (wintypes.DWORD, 1), (wintypes.DWORD, 1), (wintypes.PDWORD, 2), p=ole32)
  CoRevokeClassObject = _WShUtil._wrap('CoRevokeClassObject', (wintypes.DWORD, 1), p=ole32)
  CoRegisterPSClsid = _WShUtil._wrap('CoRegisterPSClsid', (PUUID, 1), (PUUID, 1), p=ole32)

class COMSharing:
  def __init__(self, ole=False):
    self._ole = ole
    self._request = None
    self._response = [threading.Event(), None, None]
    self._lock = threading.Lock()
    self._thread = None
  @classmethod
  def Marshal(cls, iinstance):
    if iinstance:
      if (istream := IStream(cls.CoMarshalInterThreadInterfaceInStream(iinstance.IID, iinstance), factory=iinstance)) is not None:
        istream._pI = iinstance.pI
      return istream
    else:
      return None
  @classmethod
  def Unmarshal(cls, istream):
    if istream:
      istream.AddRef(False)
      if (iinstance := ((f := istream.factory).__class__)(cls.CoGetInterfaceAndReleaseStream(istream, f.__class__.IID), factory=f.factory)) is not None:
        iinstance._pI = istream._pI
      e = IGetLastError()
      istream.Release()
      ISetLastError(e)
      return iinstance
    else:
      return None
  @staticmethod
  def Source(iinstance):
    if (iinstance := iinstance.__class__(getattr(iinstance, '_pI', iinstance.pI), factory=iinstance.factory) if iinstance else None):
      iinstance.AddRef(False)
    return iinstance
  def _message_loop(self):
    Initialize(ole=self._ole)
    lpMsg = ctypes.byref((msg := wintypes.MSG()))
    Window.PeekMessage(lpMsg, None, 0x8000, 0x8000, 0)
    (r := self._response)[0].set()
    while Window.GetMessage(lpMsg, None, 0, 0) > 0:
      if not msg.hWnd and msg.message == 0x8000:
        if self._request:
          if (l := len(self._request)) == 3:
            interface_iinstance, args, kwargs = self._request
            self._request = None
            iinstance = interface_iinstance(*args, **kwargs) if callable(interface_iinstance) else (self.__class__.Source(interface_iinstance) if isinstance(interface_iinstance, IUnknown) and not (args or kwargs) else None)
            interface_iinstance = args = kwargs = None
            r[1] = self.__class__.Marshal(iinstance), (tuple((k, v) for k, v in vars(iinstance).items() if k not in {'pI', 'refs', 'factory', '_lightweight'}) if iinstance else ())
            r[2] = IGetLastError()
            if iinstance:
              iinstance.Release()
            iinstance = None
            r[0].set()
          elif l == 2:
            r[1] = (COMRegistration.RegisterCOMFactory if self._request[1][1] else COMRegistration.RegisterPSFactory)(self._request[1][0]) if self._request[0] else COMRegistration.RevokeFactory(self._request[1])
            self._request = None
            r[2] = IGetLastError()
            r[0].set()
        continue
      Window.TranslateMessage(lpMsg)
      Window.DispatchMessage(lpMsg)
    Uninitialize()
  def Start(self):
    with self._lock:
      if self._thread:
        return False
      self._thread = threading.Thread(target=self._message_loop, daemon=True)
      self._thread.start()
      self._response[0].wait()
      self._response[0].clear()
    return True
  def Stop(self):
    with self._lock:
      if not self._thread or (nid := self._thread.native_id) is None:
        return False
      self.__class__.PostThreadMessage(nid, 0x12, 0, 0)
      self._thread.join()
      self._thread = None
    return True
  def _RegisterFactory(self, icls_impl, ps):
    with self._lock:
      if not self._thread or (nid := self._thread.native_id) is None:
        return None
      self._request = (True, (icls_impl, ps))
      self.__class__.PostThreadMessage(nid, 0x8000, 0, 0)
      (r := self._response)[0].wait()
      r[0].clear()
      ISetLastError(r[2])
      c = r[1]
      r[1] = r[2] = None
    return c
  def RegisterCOMFactory(self, icls_impl):
    return self._RegisterFactory(icls_impl, True)
  def RegisterPSFactory(self, icls_ps_impl):
    return self._RegisterFactory(icls_ps_impl, False)
  def RevokeFactory(self, token):
    with self._lock:
      if not self._thread or (nid := self._thread.native_id) is None:
        return None
      self._request = (False, token)
      self.__class__.PostThreadMessage(nid, 0x8000, 0, 0)
      (r := self._response)[0].wait()
      r[0].clear()
      ISetLastError(r[2])
      c = r[1]
      r[1] = r[2] = None
    return c
  def Get(self, interface_iinstance, *args, **kwargs):
    with self._lock:
      if not self._thread or (nid := self._thread.native_id) is None:
        return None
      self._request = (interface_iinstance, args, kwargs)
      self.__class__.PostThreadMessage(nid, 0x8000, 0, 0)
      (r := self._response)[0].wait()
      r[0].clear()
      ISetLastError(r[2])
      if (iinstance := self.__class__.Unmarshal(r[1][0])):
        for k, v in r[1][1]:
          setattr(iinstance, k, v)
      r[1] = r[2] = None
    return iinstance
  __call__ = Get
  CoMarshalInterThreadInterfaceInStream = _WShUtil._wrap('CoMarshalInterThreadInterfaceInStream', (PUUID, 1), (wintypes.LPVOID, 1), (wintypes.PLPVOID, 2), p=ole32)
  CoMarshalInterThreadInterfaceIntoStream = _WShUtil._wrap('CoMarshalInterThreadInterfaceInStream', (PUUID, 1), (wintypes.LPVOID, 1), (wintypes.PLPVOID, 1), p=ole32)
  CoGetInterfaceAndReleaseStream = _WShUtil._wrap('CoGetInterfaceAndReleaseStream', (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2), p=ole32)
  CoGetInterfaceIntoAndReleaseStream = _WShUtil._wrap('CoGetInterfaceAndReleaseStream', (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 1), p=ole32)
  CoMarshalInterface = _WShUtil._wrap('CoMarshalInterface', (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.LPVOID, 1), (wintypes.LPVOID, 1), (wintypes.DWORD, 1), p=ole32)
  CoUnmarshalInterface = _WShUtil._wrap('CoUnmarshalInterface', (wintypes.LPVOID, 1), (PUUID, 1), (wintypes.PLPVOID, 2), p=ole32)
  CoReleaseMarshalData = _WShUtil._wrap('CoReleaseMarshalData', (wintypes.LPVOID, 1), p=ole32)
  PostThreadMessage = _WndUtil._wrap('PostThreadMessageW', wintypes.BOOLE, wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)