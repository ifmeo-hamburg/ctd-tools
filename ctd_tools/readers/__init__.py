"""
CTD Tools Readers Module

This module provides various reader classes for importing CTD sensor data
from different file formats into xarray Datasets. It includes a registry
of available readers, allowing for lazy loading of specific reader classes
based on the file format.

Available Readers:
-----------------
- NetCdfReader: Read NetCDF files
- CsvReader: Read CSV files
- RbrAsciiReader: Read RBR ASCII files
- NortekAsciiReader: Read Nortek ASCII files
- RbrRskLegacyReader: Read legacy RSK files
- RbrRskReader: Read RSK files
- RbrRskAutoReader: Auto-detect RSK format
- SbeCnvReader: Read SeaBird CNV files
- SeasunTobReader: Read Sea & Sun TOB files

Example Usage:
--------------
from ctd_tools.readers import SbeCnvReader, NetCdfReader

# Read a CNV file
reader = SbeCnvReader("data.cnv")
data = reader.get_data()

# Read a NetCDF file  
nc_reader = NetCdfReader("data.nc")
nc_data = nc_reader.get_data()
"""

# Import the base class (lightweight)
from .base import AbstractReader

# Import reader registry (single source of truth)
from .registry import get_reader_modules, get_all_reader_classes

# Get reader class mapping from registry for lazy loading
_READER_MODULES = get_reader_modules()

# Cache for loaded reader classes
_loaded_readers = {}

def __getattr__(name):
    """Lazy loading of reader classes."""
    if name in _READER_MODULES:
        if name not in _loaded_readers:
            # Import only the specific module and class
            # pylint: disable=C0415
            from importlib import import_module
            module = import_module(_READER_MODULES[name], package=__name__)
            _loaded_readers[name] = getattr(module, name)
        return _loaded_readers[name]

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Build __all__ from registry  
__all__ = [
    'AbstractReader',
    'AdcpMatlabReader',
    'CsvReader',
    'NetCdfReader', 
    'NortekAsciiReader',
    'RbrAsciiReader',
    'RbrRskAutoReader',
    'RbrRskLegacyReader',
    'RbrRskReader',
    'SbeCnvReader',
    'SeasunTobReader'
]
