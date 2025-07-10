"""
Reader Registry - Single Source of Truth for All Reader Information

This module contains all metadata about available readers in one place.
When adding a new reader, only this file and the reader implementation need to be updated.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class ReaderMetadata:
    """Metadata for a file reader.
    
    Attributes:
    -----------
    class_name: str
        The name of the reader class (e.g., "SbeCnvReader").
    module_name: str
        The module where the reader class is defined (e.g., ".sbe_cnv_reader").
    format_name: str
        The human-readable name of the format (e.g., "SeaBird CNV").
    format_key: str
        A unique key for the format used in detection (e.g., "sbe-cnv").
    file_extension: Optional[str]
        The unique file extension associated with the format (e.g., ".cnv").
    """

    # Class information
    class_name: str                       # e.g., "SbeCnvReader"
    module_name: str                      # e.g., ".sbe_cnv_reader"

    # Format information
    format_name: str                      # e.g., "SeaBird CNV"
    format_key: str                       # e.g., "sbe-cnv"
    file_extension: Optional[str] = None  # e.g., ".cnv"


# Single source of truth for all readers
READER_REGISTRY: List[ReaderMetadata] = [
    ReaderMetadata(
        class_name="NetCdfReader",
        module_name=".netcdf_reader",
        format_name="netCDF",
        format_key="netcdf",
        file_extension=".nc"
    ),
    ReaderMetadata(
        class_name="CsvReader",
        module_name=".csv_reader",
        format_name="CSV",
        format_key="csv",
        file_extension=".csv"
    ),
    ReaderMetadata(
        class_name="SbeCnvReader",
        module_name=".sbe_cnv_reader",
        format_name="SeaBird CNV",
        format_key="sbe-cnv",
        file_extension=".cnv"
    ),
    ReaderMetadata(
        class_name="SeasunTobReader",
        module_name=".seasun_tob_reader",
        format_name="Sea & Sun TOB",
        format_key="seasun-tob",
        file_extension=".tob"
    ),
    ReaderMetadata(
        class_name="RbrRskReader",
        module_name=".rbr_rsk_reader",
        format_name="RBR RSK Default",
        format_key="rbr-rsk-default",
        file_extension=None
    ),
    ReaderMetadata(
        class_name="RbrRskLegacyReader",
        module_name=".rbr_rsk_legacy_reader",
        format_name="RBR RSK Legacy",
        format_key="rbr-rsk-legacy",
        file_extension=None
    ),
    ReaderMetadata(
        class_name="RbrRskAutoReader",
        module_name=".rbr_rsk_auto_reader",
        format_name="RBR RSK",
        format_key="rbr-rsk",
        file_extension='.rsk'
    ),
    ReaderMetadata(
        class_name="RbrAsciiReader",
        module_name=".rbr_ascii_reader",
        format_name="RBR ASCII",
        format_key="rbr-ascii",
        file_extension=None
    ),
    ReaderMetadata(
        class_name="NortekAsciiReader",
        module_name=".nortek_ascii_reader",
        format_name="Nortek ASCII",
        format_key="nortek-ascii",
        file_extension=None
    ),
    ReaderMetadata(
        class_name="AdcpMatlabReader",
        module_name=".adcp_matlab_reader",
        format_name="ADCP Matlab",
        format_key="adcp-matlab",
        file_extension= None
    ),
]


# Utility functions to extract information from registry
def get_reader_modules() -> Dict[str, str]:
    """Get mapping of class names to module names for lazy loading."""
    return {reader.class_name: reader.module_name for reader in READER_REGISTRY}


def get_format_registry() -> List[Dict[str, str]]:
    """Get format information for the format registry."""
    formats = []
    for reader in READER_REGISTRY:
        format_info = {
            'format': reader.format_name,
            'key': reader.format_key,
        }
        if reader.file_extension:
            format_info['extension'] = reader.file_extension
        formats.append(format_info)
    return formats


def get_extension_map() -> Dict[str, str]:
    """Get mapping of file extensions to format keys."""
    return {
        reader.file_extension: reader.format_key 
        for reader in READER_REGISTRY 
        if reader.file_extension
    }


def get_input_formats() -> Dict[str, str]:
    """Get mapping of format keys to format names."""
    return {reader.format_key: reader.format_name for reader in READER_REGISTRY}


def get_all_reader_classes() -> List[str]:
    """Get list of all reader class names."""
    return [reader.class_name for reader in READER_REGISTRY]


def get_reader_by_format_key(format_key: str) -> Optional[ReaderMetadata]:
    """Get reader metadata by format key."""
    for reader in READER_REGISTRY:
        if reader.format_key == format_key:
            return reader
    return None


def get_readers_by_extension(extension: str) -> List[ReaderMetadata]:
    """Get readers that can handle a specific file extension."""
    return [
        reader for reader in READER_REGISTRY 
        if reader.file_extension == extension
    ]
