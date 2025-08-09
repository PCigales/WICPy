#include <stdio.h>
#include <windows.h>
#include <shlwapi.h>
#include <Python.h>

PyObject *py_mod;
INT py_ini;

HRESULT WINAPI DllGetClassObject(const REFCLSID rclsid, const REFIID riid, LPVOID *ppv) {
  PyGILState_STATE state = PyGILState_Ensure();
  PyObject *py_func = PyObject_GetAttrString(py_mod, "DllGetClassObject");
  if (! py_func) {
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

HRESULT WINAPI DllCanUnloadNow(void) {
  PyGILState_STATE state = PyGILState_Ensure();
  PyObject *py_func = PyObject_GetAttrString(py_mod, "DllCanUnloadNow");
  if (! py_func) {
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
      WCHAR *e = wcsrchr(dllpath, '\\');
      if (e) {*e = '\0';}
      py_ini = Py_IsInitialized();
      if (! py_ini) {Py_InitializeEx(0);}
      PyGILState_STATE state = PyGILState_Ensure();
      PyObject *py_path = PySys_GetObject("path");
      PyObject *py_mpath = PyUnicode_FromWideChar(dllpath, -1);
      if (! py_path || ! py_mpath) {
        PyGILState_Release(state);
        return FALSE;
      }
      PyList_Append(py_path, py_mpath);
      Py_XDECREF(py_mpath);
      free(dllpath);
      py_mod = PyImport_ImportModule("wic");
      if (! py_mod) {
        PyErr_Clear();
        PyGILState_Release(state);
        return FALSE;
      }
      PyGILState_Release(state);
    break;
    case DLL_PROCESS_DETACH:
      if (! lpvReserved) {
        PyGILState_STATE state = PyGILState_Ensure();
        Py_XDECREF(py_mod);
        PyGILState_Release(state);
        if (! py_ini) {Py_FinalizeEx();}
      }
    break;
  }
 return TRUE;
}