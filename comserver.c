#include <stdio.h>
#include <Windows.h>
#include <Objbase.h>
#include <Python.h>
#define DLLEXPORT __declspec(dllexport)

PyObject *py_wmod = NULL;
INT py_ini = 1;

HRESULT DLLEXPORT WINAPI DllGetClassObject(const REFCLSID rclsid, const REFIID riid, LPVOID *ppv) {
  LPOLESTR pclsid;
  if (! py_wmod || StringFromCLSID(rclsid, &pclsid)) {return E_FAIL;}
  WCHAR *rpath = (WCHAR *) malloc(sizeof(WCHAR) * (wcslen(pclsid) + 22));
  wcscpy(rpath, L"CLSID\\");
  wcscat(rpath, pclsid);
  CoTaskMemFree(pclsid);
  wcscat(rpath, L"\\InprocServer32");
  WCHAR *mpath = NULL;
  DWORD msize = 0;
  if (! RegGetValueW(HKEY_CLASSES_ROOT, rpath, L"PyModule", RRF_RT_REG_SZ, NULL, NULL, &msize) && msize) {
    if (! (mpath = (WCHAR*) malloc(msize)) || RegGetValueW(HKEY_CLASSES_ROOT, rpath, L"PyModule", RRF_RT_REG_SZ, NULL, mpath, &msize)) {return E_FAIL;}
  }
  free(rpath);
  PyGILState_STATE state = PyGILState_Ensure();
  PyObject *py_mod = py_wmod;
  if (mpath) {
    PyObject *py_mname = NULL;
    WCHAR *mname = wcsrchr(mpath, L'\\');
    if (mname) {
      *mname = 0;
      PyObject *py_path = PySys_GetObject("path");
      PyObject *py_mpath = PyUnicode_FromWideChar(mpath, -1);
      if (! py_path || ! py_mpath) {
        Py_XDECREF(py_mpath);
        PyGILState_Release(state);
        free(mpath);
        return E_FAIL;
      }
      PyList_Append(py_path, py_mpath);
      Py_XDECREF(py_mpath);
      WCHAR *mext = wcsrchr(++mname, L'.');
      if (mext && ! wcscmp(mext, L".py")) {
        *mext = 0;
      }
      py_mname = PyUnicode_FromWideChar(mname, -1);
    } else {
      py_mname = PyUnicode_FromWideChar(mpath, -1);
    }
    free(mpath);
    if (! py_mname) {
      PyGILState_Release(state);
      return E_FAIL;
    }
    if (! (py_mod = PyImport_GetModule(py_mname)) && (PyErr_Occurred() || ! (py_mod = PyImport_Import(py_mname)))) {
      PyErr_Clear();
      Py_XDECREF(py_mname);
      PyGILState_Release(state);
      return E_FAIL;
    }
    Py_XDECREF(py_mname);
  }
  PyObject *py_func;
  if (! (py_func = PyObject_GetAttrString(py_mod, "DllGetClassObject"))) {
    PyGILState_Release(state);
    return E_FAIL;
  }
  Py_XDECREF(py_mod);
  long res = E_FAIL;
  PyObject *py_rclsid = PyLong_FromVoidPtr((void*) rclsid);
  PyObject *py_riid = PyLong_FromVoidPtr((void*) riid);
  PyObject *py_ppv = PyLong_FromVoidPtr(ppv);
  if (py_rclsid && py_riid && py_ppv) {
    PyObject *py_res = PyObject_CallFunctionObjArgs(py_func, py_rclsid, py_riid, py_ppv, NULL);
    if (py_res) {
      res = PyLong_AsLong(py_res);
      if (PyErr_Occurred()) {
        res = E_FAIL;
      }
      Py_DECREF(py_res);
    }
  }
  Py_DECREF(py_func);
  Py_XDECREF(py_rclsid);
  Py_XDECREF(py_riid);
  Py_XDECREF(py_ppv);
  PyGILState_Release(state);
  return res;
}

HRESULT DLLEXPORT WINAPI DllCanUnloadNow(void) {
  PyGILState_STATE state = PyGILState_Ensure();
  PyObject *py_func;
  if (! py_wmod || ! (py_func = PyObject_GetAttrString(py_wmod, "DllCanUnloadNow"))) {
    PyGILState_Release(state);
    return E_FAIL;
  }
  long res = E_FAIL;
  PyObject *py_res = PyObject_CallNoArgs(py_func);
  if (py_res) {
    res = PyLong_AsLong(py_res);
    if (PyErr_Occurred()) {
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
      if (! py_ini) {Py_InitializeEx(0);}
      WCHAR *dllpath = NULL;
      DWORD alen = MAX_PATH;
      DWORD rlen;
      do {
        if (! (dllpath = (WCHAR*) malloc(sizeof(WCHAR) * alen)) || ! (rlen = GetModuleFileNameW(hinstDLL, dllpath, alen))) {return FALSE;}
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
      if (! py_path || ! py_mpath) {
        Py_XDECREF(py_mpath);
        PyGILState_Release(state);
        return FALSE;
      }
      PyList_Append(py_path, py_mpath);
      Py_XDECREF(py_mpath);
      free(dllpath);
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
        }
      }
    break;
  }
 return TRUE;
}