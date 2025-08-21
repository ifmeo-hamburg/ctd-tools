"""
Module for abstract base class for reading sensor data from various file formats.

This module defines the `AbstractReader` class, which serves as a base class for
all reader implementations in the CTD Tools package. Concrete reader classes should
inherit from this class and implement the methods for reading and processing data
from specific file formats (e.g., CNV, TOB, NetCDF, CSV, RBR, Nortek).
"""

from __future__ import annotations
import platform
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
from collections import defaultdict
import re
import xarray as xr
import gsw
import ctd_tools.parameters as params

MODULE_NAME = 'ctd_tools'


class AbstractReader(ABC):
    """ Abstract super class for reading sensor data. 

    Must be subclassed to implement specific file format readers.
    
    Attributes
    ---------- 
    input_file : str
        The path to the input file containing sensor data.
    data : xr.Dataset | None
        The processed sensor data as a xarray Dataset, or None if not yet processed.
    mapping : dict, optional
        A dictionary mapping names used in the input file to standard names.
    perform_default_postprocessing : bool
        Whether to perform default post-processing on the data.
    rename_variables : bool
        Whether to rename xarray variables to standard names.
    assign_metadata : bool
        Whether to assign metadata to xarray variables.
    sort_variables : bool
        Whether to sort xarray variables by name.
    
    Methods
    -------
    __init__(input_file: str, mapping: dict | None = None, 
                    perform_default_postprocessing: bool = True,
                    rename_variables: bool = True, assign_metadata: bool = True, 
                    sort_variables: bool = True)
            Initializes the reader with the input file and optional mapping.
    _perform_default_postprocessing(ds: xr.Dataset) -> xr.Dataset
            Performs default post-processing on the xarray Dataset.
    get_data() -> xr.Dataset | None
            Returns the processed data as an xarray Dataset.
    """

    # Attribute which indicates whether to perform default post-processing
    perform_default_postprocessing = True

    # Attribute to indicate whether to rename xarray variables to standard names
    rename_variables = True

    # Attribute to indicate whether to assign CF metadata to xarray variables
    assign_metadata = True

    # Attribute to indicate whether to sort xarray variables by name
    sort_variables = True

    def __init__(self, input_file: str, mapping: dict | None = None,
                 input_header_file: str | None = None,
                 perform_default_postprocessing: bool = True, rename_variables: bool = True,
                 assign_metadata: bool = True, sort_variables: bool = True):
        """Initializes the AbstractReader with the input file and optional mapping.

        This constructor sets the input file, initializes the data attribute to None,
        and sets the mapping for variable names. It also allows for configuration of
        default post-processing, renaming of variables, assignment of metadata, and 
        sorting of variables.

        Parameters
        ---------- 
        input_file : str
            The path to the input file containing sensor data.
        mapping : dict, optional
            A dictionary mapping names used in the input file to standard names.
        perform_default_postprocessing : bool, optional
            Whether to perform default post-processing on the data. Default is True.
        rename_variables : bool, optional
            Whether to rename xarray variables to standard names. Default is True.
        assign_metadata : bool, optional
            Whether to assign CF metadata to xarray variables. Default is True.
        sort_variables : bool, optional
            Whether to sort xarray variables by name. Default is True.
        """

        self.input_file = input_file
        self.input_header_file = input_header_file
        self.data = None
        self.mapping = mapping if mapping is not None else {}
        self.perform_default_postprocessing = perform_default_postprocessing
        self.rename_variables = rename_variables
        self.assign_metadata = assign_metadata
        self.sort_variables = sort_variables

    def _julian_to_gregorian(self, julian_days, start_date):
        full_days = int(julian_days) - 1  # Julian days start at 1, not 0
        seconds = (julian_days - int(julian_days)) * 24 * 60 * 60
        return start_date + timedelta(days=full_days, seconds=seconds)

    def _elapsed_seconds_since_jan_1970_to_datetime(self, elapsed_seconds):
        base_date = datetime(1970, 1, 1)
        time_delta = timedelta(seconds=elapsed_seconds)
        return base_date + time_delta

    def _elapsed_seconds_since_jan_2000_to_datetime(self, elapsed_seconds):
        base_date = datetime(2000, 1, 1)
        time_delta = timedelta(seconds=elapsed_seconds)
        date_value = base_date + time_delta
        return date_value

    def _elapsed_seconds_since_offset_to_datetime(self, elapsed_seconds, offset_datetime):
        base_date = offset_datetime
        time_delta = timedelta(seconds=elapsed_seconds)
        return base_date + time_delta

    def _validate_necessary_parameters(self, data, longitude, latitude, entity: str):
        if not params.TIME and not params.TIME_J and not params.TIME_Q \
                and not params.TIME_N in data:
            raise ValueError(f"Parameter '{params.TIME}' is missing in {entity}.")
        if not params.PRESSURE in data and not params.DEPTH:
            raise ValueError(f"Parameter '{params.PRESSURE}' is missing in {entity}.")

    def _get_xarray_dataset_template(self, time_array, depth_array, 
                latitude, longitude, depth_name = params.DEPTH):
        coords = dict(
            time = time_array,
            latitude = latitude,
            longitude = longitude,
        )

        # Only add depth coordinate if depth_array is not None
        if depth_array is not None:
            coords[depth_name] = ([params.TIME], depth_array)

        return xr.Dataset(
            data_vars = dict(),
            coords = coords,
            attrs = dict(
                latitude = latitude,
                longitude = longitude,
                CreateTime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                DataType = 'TimeSeries',
            )
        )

    def _assign_data_for_key_to_xarray_dataset(self, ds: xr.Dataset, key:str, data):
        ds[key] = xr.DataArray(data, dims=params.TIME)
        ds[key].attrs = {}

    def _assign_metadata_for_key_to_xarray_dataset(self, ds: xr.Dataset, key: str, 
                    label = None, unit = None):
        if not ds[key].attrs:
            ds[key].attrs = {}
        # Check for numbered standard names (e.g., temperature_1, temperature_2)
        base_key = key
        m = re.match(r"^([a-zA-Z0-9_]+?)(?:_\d{1,2})?$", key)
        if m:
            base_key = m.group(1)
        # Use metadata for base_key if available
        if base_key in params.metadata:
            for attribute, value in params.metadata[base_key].items():
                if attribute not in ds[key].attrs:
                    ds[key].attrs[attribute] = value
        if unit:
            ds[key].attrs['units'] = unit
        if label:
            if unit:
                label = label.replace(f"[{unit}]", '').strip() # Remove unit from label
            ds[key].attrs['long_name'] = label

    def _derive_oceanographic_parameters(self, ds: xr.Dataset) -> xr.Dataset:
        """Derive oceanographic parameters from temperature, pressure, and salinity.
        
        This method calculates derived parameters like density and potential temperature
        using the Gibbs SeaWater (GSW) oceanographic toolbox when temperature, pressure,
        and salinity data are available in the xarray Dataset.
        
        For multiple sensors (e.g., temperature_1, temperature_2), it will use the first
        available sensor (temperature_1) or the base parameter name if only one exists.
        
        Parameters
        ----------
        ds : xr.Dataset
            The xarray Dataset containing the sensor data and to add derived parameters to.
            
        Returns
        -------
        xr.Dataset
            The xarray Dataset with derived parameters added.
        """
        
        # Find the appropriate temperature variable
        temperature_var = None
        if params.TEMPERATURE in ds.data_vars:
            temperature_var = params.TEMPERATURE
        elif f"{params.TEMPERATURE}_1" in ds.data_vars:
            temperature_var = f"{params.TEMPERATURE}_1"
        
        # Find the appropriate salinity variable
        salinity_var = None
        if params.SALINITY in ds.data_vars:
            salinity_var = params.SALINITY
        elif f"{params.SALINITY}_1" in ds.data_vars:
            salinity_var = f"{params.SALINITY}_1"
        
        # Pressure should typically be singular, but check both possibilities
        pressure_var = None
        if params.PRESSURE in ds.data_vars:
            pressure_var = params.PRESSURE
        elif f"{params.PRESSURE}_1" in ds.data_vars:
            pressure_var = f"{params.PRESSURE}_1"
        
        # Check if we have all required parameters for oceanographic calculations
        if temperature_var and salinity_var and pressure_var:
            
            # Derive density using GSW
            ds[params.DENSITY] = ([params.TIME], gsw.density.rho(
                ds[salinity_var].values, 
                ds[temperature_var].values, 
                ds[pressure_var].values))
            
            # Derive potential temperature using GSW
            ds[params.POTENTIAL_TEMPERATURE] = ([params.TIME], gsw.pt0_from_t(
                ds[salinity_var].values, 
                ds[temperature_var].values, 
                ds[pressure_var].values))
            
            if self.assign_metadata:
                # Assign metadata for derived parameters
                self._assign_metadata_for_key_to_xarray_dataset(ds, params.DENSITY)
                self._assign_metadata_for_key_to_xarray_dataset(ds, params.POTENTIAL_TEMPERATURE)
                
        return ds

    def _sort_xarray_variables(self, ds: xr.Dataset) -> xr.Dataset:
        """Sorts the variables in an xarray Dataset based on their standard names.

        The sorting is done in a way that ensures that variables with the same base name
        (e.g., temperature_1, temperature_2) are grouped together.

        Parameters
        ----------
        ds : xr.Dataset
            The xarray Dataset to be sorted.

        Returns
        -------
        xr.Dataset
            The xarray Dataset with variables sorted by their names.
        """
        # Sort all variables and coordinates by name
        all_names = sorted(list(ds.data_vars) + list(ds.coords))

        # Create a new Dataset with sorted variables and coordinates
        ds_sorted = ds[all_names]

        # Ensure that the attributes are preserved
        ds_sorted.attrs = ds.attrs.copy()

        return ds_sorted

    def _rename_xarray_parameters(self, ds: xr.Dataset) -> xr.Dataset:
        """
        Rename variables in an xarray.Dataset according to params.default_mappings.
        Handles aliases with or without trailing numbering and ensures unique standard 
        names with numbering. If a standard name only occurs once, it will not have a 
        numbering suffix.
        """

        ds_vars = list(ds.variables)
        rename_dict = {}

        # Build a reverse mapping: alias_lower -> standard_name
        alias_to_standard = {}
        for standard_name, aliases in params.default_mappings.items():
            for alias in aliases:
                alias_to_standard[alias.lower()] = standard_name

        # First, collect all matches: (standard_name, original_var, suffix)
        matches = []
        for var in ds_vars:
            if not isinstance(var, str):
                continue
            var_lower = var.lower()
            matched = False
            for alias_lower, standard_name in alias_to_standard.items():
                # Match alias with optional _<number> at the end
                m = re.match(rf"^{re.escape(alias_lower)}(_?\d{{1,2}})?$", var_lower)
                if m:
                    suffix = m.group(1) or ""
                    matches.append((standard_name, var, suffix))
                    matched = True
                    break
            if not matched:
                continue

        # Group by standard_name
        grouped = defaultdict(list)
        for standard_name, var, suffix in matches:
            grouped[standard_name].append((var, suffix))

        # Assign new names: only add numbering if there are multiple
        for standard_name, vars_with_suffixes in grouped.items():
            if len(vars_with_suffixes) == 1:
                # Only one variable: use plain standard name
                rename_dict[vars_with_suffixes[0][0]] = standard_name
            else:
                # Multiple variables: always add numbering (_1, _2, ...)
                for idx, (var, suffix) in enumerate(vars_with_suffixes, 1):
                    rename_dict[var] = f"{standard_name}_{idx}"

        return ds.rename(rename_dict)

    def _assign_default_global_attributes(self, ds: xr.Dataset) -> xr.Dataset:
        """Assigns default global attributes to the xarray Dataset.

        This method sets the global attributes for the xarray Dataset, including
        the title, institution, source, and other relevant metadata.

        Parameters
        ----------
        ds : xr.Dataset
            The xarray Dataset to which the global attributes will be assigned.
        """

        module_name = MODULE_NAME
        module_version = version(MODULE_NAME)
        module_reader_class = self.__class__.__name__
        python_version = platform.python_version()
        input_file = self.input_file
        input_file_type = self.format_name()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # assemble history entry
        history_entry = (
            f"{timestamp}: created from {input_file_type} file ({input_file}) "
            f"using {module_name} v{module_version} ({module_reader_class} class) "
            f"under Python {python_version}"
        )

        ds.attrs['history'] = history_entry
        ds.attrs['Conventions'] = 'CF-1.8'

        # Information about the processor of the xarray dataset
        ds.attrs['processor_name'] = module_name
        ds.attrs['processor_version'] = module_version
        ds.attrs['processor_reader_class'] = module_reader_class
        ds.attrs['processor_python_version'] = python_version
        ds.attrs['processor_input_filename'] = input_file
        ds.attrs['processor_input_file_type'] = input_file_type

        return ds

    def _perform_default_postprocessing(self, ds: xr.Dataset) -> xr.Dataset:
        """
        Perform default post-processing on the xarray Dataset.
        This includes renaming variables and assigning metadata.

        Parameters
        ----------
        ds : xr.Dataset
            The xarray Dataset to be processed.

        Returns
        -------
        xr.Dataset
            The processed xarray Dataset.
        """

        # Apply custom mapping of variable names if provided
        if self.mapping is not None:
            for key, value in self.mapping.items():
                if value in ds.variables:
                    ds = ds.rename({value: key})

        # Rename variables according to default mappings
        if self.rename_variables:
            ds = self._rename_xarray_parameters(ds)

        # Assign metadata for all attributes of the xarray Dataset
        if self.assign_metadata:
            for key in (list(ds.data_vars.keys()) + list(ds.coords.keys())):
                self._assign_metadata_for_key_to_xarray_dataset(ds, key)

        # Assign default global attributes
        ds = self._assign_default_global_attributes(ds)

        # Sort variables and coordinates by name
        if self.sort_variables:
            ds = self._sort_xarray_variables(ds)

        return ds   

    def get_data(self) -> xr.Dataset | None:
        """ Returns the processed data as an xarray Dataset. """
        return self.data

    @staticmethod
    @abstractmethod
    def format_name() -> str:
        """Get the format name for this reader.

        This property must be implemented by all subclasses.

        Returns:
        --------
        str
            The format (e.g., 'SeaBird CNV', 'Nortek ASCII', 'RBR RSK').

        Raises:
        -------
        NotImplementedError:
            If the subclass does not implement this property.
        """
        raise NotImplementedError("Reader classes must define a format name")

    @staticmethod
    @abstractmethod
    def format_key() -> str:
        """Get the format key for this reader.

        This property must be implemented by all subclasses.
        
        Returns:
        --------
        str
            The format key (e.g., 'sbe-cnv', 'nortek-ascii', 'rbr-rsk').

        Raises:
        -------
        NotImplementedError:
            If the subclass does not implement this property.
        """
        raise NotImplementedError("Writer classes must define a format key")

    @staticmethod
    @abstractmethod
    def file_extension() -> str | None:
        """Get the file extension for this reader.

        This property must be implemented by all subclasses.

        Returns:
        --------
        str
            The file extension (e.g., '.cnv', '.tob', '.rsk').

        Raises:
        -------
        NotImplementedError:
            If the subclass does not implement this property.
        """
        raise NotImplementedError("Reader classes must define a file extension")
