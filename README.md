# WICPy
A module in Python3, without any dependecy, providing a bridge with the Windows Imaging Component (WIC) framework

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

WICPy defines Python (>=v3.8) classes wrapping the COM interfaces, bringing access to their methods and coordinating the memory managed and unmanaged modes of the resources from either side.

The COM library must be initialized for each thread creating from scratch a new component by calling Initialize() and therefore uninitialized at the end by calling Uninitialize(), after having released all interfaces.

Bases of wrappers for Direct2D, Direct3D 11 and DXGI interfaces involved in interoperability with WIC are made available.
WICPy also gives access to the Windows Media Player photo library, as well as some Windows Shell Namespace resources.

Besides, the module facilitates the creation of custom COM interfaces, implementations and pxoxies/stubs using metaclasses. Factory classes registered in the registry can be invoked from their CLSID only if "Lib\site-packages\comtypes\server\inprocserver.py" is symlinked to "wic.py" as the module referred to by the hook in ctypes which is called by "DllGetClassObject" in _ctypes.pyd is hardcoded, with no possibility to define an alternative in the registry, such as through a dedicated subkey in the key associated with the CLSID (see https://github.com/python/cpython/issues/127369 and https://github.com/python/cpython/issues/127369#issuecomment-2544931573).

The script test.py illustrates how to use the module through various applications.
