# WICPy
A module in Python3 providing a bridge with the Windows Imaging Component (WIC) framework

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.

WICPy defines Python (>=v3.8) classes wrapping the COM interfaces, bringing access to their methods and coordinating the memory managed and unmanaged modes of the resources from either side.

The COM library must be initialized for each thread creating from scratch a new component by calling Initialize() and therefore uninitialized at the end by calling Uninitialize(), after having released all interfaces.

The script test.py illustrates how to use the module through various applications.
