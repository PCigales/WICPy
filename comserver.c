#include <stdio.h>
#include <Windows.h>
#include <Objbase.h>
#include <Python.h>
#define DLLEXPORT __declspec(dllexport)

PyObject *py_wmod = NULL;
INT py_ini = 1;

#define FUNC1(name) \
  if (! py_wmod) {return E_FAIL;} \
  PyGILState_STATE state = PyGILState_Ensure(); \
  PyObject *py_func = PyObject_GetAttrString(py_wmod, name); \
  if (! (py_func )) { \
    PyErr_Clear(); \
    PyGILState_Release(state); \
    return E_FAIL; \
  } \
  long res = E_FAIL;

#define FUNC_ \
  if (py_res) { \
    res = PyLong_AsLong(py_res); \
    if (PyErr_Occurred()) { \
      PyErr_Clear(); \
      res = E_FAIL; \
    } \
    Py_DECREF(py_res); \
  }

#define FUNC2 \
    FUNC_ \
  } else { \
    PyErr_Clear(); \
  } \
  Py_DECREF(py_func); \

#define FUNC3 \
  PyGILState_Release(state); \
  return res;

#define FUNC4(name) \
  FUNC1(name) \
  PyObject *py_res = PyObject_CallNoArgs(py_func); \
  FUNC_ \
  Py_DECREF(py_func); \
  FUNC3

HRESULT DLLEXPORT WINAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID *ppv) {
  FUNC1("DllGetClassObject")
  PyObject *py_rclsid = PyLong_FromVoidPtr((void*) rclsid);
  PyObject *py_riid = PyLong_FromVoidPtr((void*) riid);
  PyObject *py_ppv = PyLong_FromVoidPtr(ppv);
  if (py_rclsid && py_riid && py_ppv) {
    PyObject *py_res = PyObject_CallFunctionObjArgs(py_func, py_rclsid, py_riid, py_ppv, NULL);
    FUNC2
  Py_XDECREF(py_rclsid);
  Py_XDECREF(py_riid);
  Py_XDECREF(py_ppv);
  FUNC3
}

HRESULT DLLEXPORT WINAPI DllCanUnloadNow(void) {
  FUNC4("DllCanUnloadNow")
}

HRESULT DLLEXPORT WINAPI DllRegisterServer() {
  FUNC4("DllRegisterServer")
}

HRESULT DLLEXPORT WINAPI DllUnregisterServer() {
  FUNC4("DllUnregisterServer")
}

HRESULT DLLEXPORT WINAPI DllInstall(BOOL bInstall, PCWSTR pszCmdLine) {
  FUNC1("DllInstall")
  PyObject *py_bInstall = PyLong_FromInt32(bInstall);
  PyObject *py_pszCmdLine = PyLong_FromVoidPtr((void*) pszCmdLine);
  if (py_bInstall && py_pszCmdLine) {
    PyObject *py_res = PyObject_CallFunctionObjArgs(py_func, py_bInstall, py_pszCmdLine, NULL);
    FUNC2
  Py_XDECREF(py_bInstall);
  Py_XDECREF(py_pszCmdLine);
  FUNC3
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
      if (! py_ini) {
        PyThreadState_Clear(PyThreadState_Get());
        PyThreadState_DeleteCurrent();
      }
    break;
    case DLL_PROCESS_DETACH:
      if (! lpvReserved) {
        PyGILState_STATE state = PyGILState_Ensure();
        Py_XDECREF(py_wmod);
        py_wmod = NULL;
        if (py_ini) {
          PyGILState_Release(state);
        } else  {
          py_ini = 1;
          Py_FinalizeEx();
        }
      }
    break;
  }
 return TRUE;
}