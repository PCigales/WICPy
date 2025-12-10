#include <stdio.h>
#include <Windows.h>
#include <Objbase.h>
#include <Python.h>
#define DLLEXPORT __declspec(dllexport)

PyObject *py_wmod = NULL;
INT py_ini = 1;

HRESULT DLLEXPORT WINAPI DllGetClassObject(const REFCLSID rclsid, const REFIID riid, LPVOID *ppv) {
  LPOLESTR pclsid;
  if (! py_wmod || StringFromCLSID(rclsid, &pclsid) || wcslen(pclsid) != 38) {return E_FAIL;}
  WCHAR rpath[60] = L"CLSID\\                                      \\InprocServer32";
  wcsncpy(rpath + 6, pclsid, 38);
  CoTaskMemFree(pclsid);
  WCHAR *mpath = NULL;
  DWORD msize = 0;
  if (! RegGetValueW(HKEY_CLASSES_ROOT, rpath, L"PyModule", RRF_RT_REG_SZ, NULL, NULL, &msize) && msize) {
    if (mpath = (WCHAR*) malloc(msize)) {
      if (RegGetValueW(HKEY_CLASSES_ROOT, rpath, L"PyModule", RRF_RT_REG_SZ, NULL, mpath, &msize)) {
        free(mpath);
        return E_FAIL;
      }
    } else {return E_FAIL;}
  }
  PyGILState_STATE state = PyGILState_Ensure();
  PyObject *py_mod = NULL;
  if (mpath) {
    PyObject *py_mname = NULL;
    WCHAR *mname = wcsrchr(mpath, L'\\');
    if (mname) {
      *(mname++) = 0;
      PyObject *py_path = PySys_GetObject("path");
      PyObject *py_mpath = PyUnicode_FromWideChar(mpath, -1);
      if (! py_path || ! py_mpath) {
        free(mpath);
        Py_XDECREF(py_mpath);
        PyErr_Clear();
        PyGILState_Release(state);
        return E_FAIL;
      }
      if (! PySequence_Contains(py_path, py_mpath)) {
        PyList_Append(py_path, py_mpath);
      }
      Py_XDECREF(py_mpath);
    } else {
      mname = mpath;
    }
    WCHAR *mext = wcsrchr(mname, L'.');
    if (mext && ! _wcsicmp(mext, L".py")) {
      *mext = 0;
    }
    py_mname = PyUnicode_FromWideChar(mname, -1);
    free(mpath);
    if (! py_mname) {
      PyErr_Clear();
      PyGILState_Release(state);
      return E_FAIL;
    }
    if (! (py_mod = PyImport_GetModule(py_mname)) &&  ! PyErr_Occurred()) {
      py_mod = PyImport_Import(py_mname);
    }
    Py_XDECREF(py_mname);
    if (! py_mod) {
      PyErr_Clear();
      PyGILState_Release(state);
      return E_FAIL;
    }
  }
  PyObject *py_func = PyObject_GetAttrString(py_mod ? py_mod : py_wmod, "DllGetClassObject");
  Py_XDECREF(py_mod);
  if (! (py_func )) {
    PyErr_Clear();
    PyGILState_Release(state);
    return E_FAIL;
  }
  long res = E_FAIL;
  PyObject *py_rclsid = PyLong_FromVoidPtr((void*) rclsid);
  PyObject *py_riid = PyLong_FromVoidPtr((void*) riid);
  PyObject *py_ppv = PyLong_FromVoidPtr(ppv);
  if (py_rclsid && py_riid && py_ppv) {
    PyObject *py_res = PyObject_CallFunctionObjArgs(py_func, py_rclsid, py_riid, py_ppv, NULL);
    if (py_res) {
      res = PyLong_AsLong(py_res);
      if (PyErr_Occurred()) {
        PyErr_Clear();
        res = E_FAIL;
      }
      Py_DECREF(py_res);
    }
  } else {
    PyErr_Clear();
  }
  Py_DECREF(py_func);
  Py_XDECREF(py_rclsid);
  Py_XDECREF(py_riid);
  Py_XDECREF(py_ppv);
  PyGILState_Release(state);
  return res;
}

HRESULT DLLEXPORT WINAPI DllCanUnloadNow(void) {
  if (! py_wmod) {return E_FAIL;}
  PyGILState_STATE state = PyGILState_Ensure();
  PyObject *py_func = PyObject_GetAttrString(py_wmod, "DllCanUnloadNow");
  if (! py_func) {
    PyErr_Clear();
    PyGILState_Release(state);
    return E_FAIL;
  }
  long res = E_FAIL;
  PyObject *py_res = PyObject_CallNoArgs(py_func);
  if (py_res) {
    res = PyLong_AsLong(py_res);
    if (PyErr_Occurred()) {
      PyErr_Clear();
      res = E_FAIL;
    }
    Py_DECREF(py_res);
  }
  Py_DECREF(py_func);
  PyGILState_Release(state);
  return res;
}

BOOL WINAPI DllMain(const HINSTANCE hinstDLL, const DWORD fdwReason, const LPVOID lpvReserved ) {
  switch(fdwReason) {
    case DLL_PROCESS_ATTACH:
      py_ini = Py_IsInitialized();
      if (! py_ini) {
        Py_InitializeEx(0);
        if (PyErr_Occurred()) {
          PyErr_Clear();
          return FALSE;
        }
      }
      WCHAR *dllpath = NULL;
      DWORD alen = MAX_PATH;
      DWORD rlen;
      do {
        if (! (dllpath = (WCHAR*) malloc(sizeof(WCHAR) * alen))) {return FALSE;}
        if (! (rlen = GetModuleFileNameW(hinstDLL, dllpath, alen))) {
          free(dllpath);
          return FALSE;
        }
        if (rlen < alen) {break;}
        free(dllpath);
        dllpath = NULL;
        alen *= 2;
      } while (alen <= 66560);
      if (! dllpath) {return FALSE;}
      WCHAR *e = wcsrchr(dllpath, L'\\');
      if (e) {*e = 0;}
      PyGILState_STATE state = PyGILState_Ensure();
      PyObject *py_path = PySys_GetObject("path");
      PyObject *py_mpath = PyUnicode_FromWideChar(dllpath, -1);
      free(dllpath);
      if (! py_path || ! py_mpath) {
        Py_XDECREF(py_mpath);
        PyErr_Clear();
        PyGILState_Release(state);
        return FALSE;
      }
      PyList_Append(py_path, py_mpath);
      Py_XDECREF(py_mpath);
      if (! (py_wmod = PyImport_ImportModule("wic"))) {
        PyErr_Clear();
        PyGILState_Release(state);
        return FALSE;
      }
      PyGILState_Release(state);
    break;
    case DLL_PROCESS_DETACH:
      if (! lpvReserved) {
        PyGILState_STATE state = PyGILState_Ensure();
        Py_XDECREF(py_wmod);
        py_wmod = NULL;
        PyGILState_Release(state);
        if (! py_ini) {
          py_ini = 1;
          Py_FinalizeEx();
          if (PyErr_Occurred()) {
            PyErr_Clear();
          }
        }
      }
    break;
  }
 return TRUE;
}