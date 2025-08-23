"""
Module for reading RBR data from legacy MATLAB .mat files.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr
import scipy.io
from datetime import datetime
from ctd_tools.readers.base import AbstractReader


class RbrMatlabLegacyReader(AbstractReader):
    """Reader which converts RBR data stored in MATLAB .mat files into an xarray Dataset."""

    def __init__(self, input_file, mapping=None, time_dim: str = "time"):
        self.time_dim = time_dim
        # side-info captured during parse
        self.serial_number = None
        self.start_date = None
        self.end_date = None
        self.comment = ""
        self.latitude = None
        self.longitude = None
        self.coefficients = []
        # Channel information for multi-parameter support
        self.channel_names = []
        self.channel_units = []
        super().__init__(input_file, mapping)
        self.__read()

    # ---------- internals ----------
    def __parse_data(self, mat_file_path) -> pd.DataFrame:
        """
        Parse MATLAB file into a pandas.DataFrame with a datetime index and
        multiple parameter columns based on available channels. Also returns 
        side info via instance attributes.
        """
        # Load the .mat with MATLAB-like structs squeezed into simple objects
        mat = scipy.io.loadmat(mat_file_path, squeeze_me=True, struct_as_record=False)

        # Raise error if mat file is empty
        if mat is None:
            raise ValueError("Could not read .mat file.")            

        # Raise error ift RBR entry not in mat file
        if "RBR" not in mat:
            raise ValueError("Expected 'RBR' struct not found in .mat file.")
        
        # Get top-level struct named 'RBR'
        RBR = mat["RBR"]

        # Extract channel names and units if available
        channel_names = self._extract_channel_names(RBR)
        channel_units = self._extract_channel_units(RBR)

        # --- Serial number from the end of the 'name' field ---
        try:
            name_str = str(getattr(RBR, "name", "")).strip()
            self.serial_number = name_str.split()[-1] if name_str else None
        except Exception:
            self.serial_number = None

        # Start / end times as numpy datetime64
        def _parse_start_end(s: str) -> np.datetime64:
            # e.g., "12/08/2018 12:00:00 PM"
            return np.datetime64(datetime.strptime(s, "%d/%m/%Y %I:%M:%S %p"))

        self.start_date = _parse_start_end(RBR.starttime)
        self.end_date   = _parse_start_end(RBR.endtime)

        # Events → comment (string)
        events_arr = np.atleast_1d(getattr(RBR, "events", []))
        self.comment = "; ".join(map(str, events_arr)) if events_arr.size else ""

        # Lat/Lon from nested parameters struct (optional)
        params = getattr(RBR, "parameters", None)
        self.latitude = getattr(params, "latitude", None) if params is not None else None
        self.longitude = getattr(params, "longitude", None) if params is not None else None

        # Coefficients (store on the temperature variable later)
        coeff = np.atleast_1d(getattr(RBR, "coefficients", []))
        self.coefficients = coeff.astype(float).tolist() if coeff.size else []

        # ---- sample times (cell array of strings) → datetime64 ----
        # Examples like: '12/08/2018 12:00:00.000 PM' or without milliseconds
        raw_times = np.atleast_1d(RBR.sampletimes)

        def _parse_time_any(s: str) -> pd.Timestamp:
            # try with milliseconds, then without
            for fmt in ("%d/%m/%Y %I:%M:%S.%f %p", "%d/%m/%Y %I:%M:%S %p"):
                try:
                    return pd.to_datetime(s, format=fmt, dayfirst=True)
                except Exception:
                    continue
            # robust fallback
            result = pd.to_datetime(s, dayfirst=True, errors="coerce")
            if pd.isna(result):
                raise ValueError(f"Could not parse time string: {s}")
            return result

        times = pd.to_datetime([_parse_time_any(str(s)) for s in raw_times])
        if times.isna().any():
            n_bad = int(times.isna().sum())
            raise ValueError(f"Failed to parse {n_bad} sample time strings from 'sampletimes'.")

        # ---- data (NxM array for M channels) → DataFrame ----
        data = np.asarray(getattr(RBR, "data", []), dtype=float)
        
        # Handle different data shapes
        if data.ndim == 1:
            # Single parameter (original case)
            data = data.reshape(-1, 1)
            if not channel_names:
                channel_names = ["temperature"]  # Default fallback
        elif data.ndim == 2:
            # Multiple parameters
            if not channel_names or len(channel_names) < data.shape[1]:
                # Generate default names if not enough channel names available
                default_names = [f"parameter_{i+1}" for i in range(data.shape[1])]
                if channel_names:
                    # Use available names, fill rest with defaults
                    channel_names.extend(default_names[len(channel_names):])
                else:
                    channel_names = default_names
        else:
            raise ValueError(f"Unexpected data shape {data.shape}; expected 1D or 2D array.")

        # Ensure we have the right number of channel names
        if data.shape[1] != len(channel_names):
            channel_names = channel_names[:data.shape[1]]  # Truncate if too many
            while len(channel_names) < data.shape[1]:
                channel_names.append(f"parameter_{len(channel_names)+1}")

        if data.shape[0] != times.size:
            raise ValueError(f"Data length ({data.shape[0]}) != time length ({times.size}).")

        # Build DataFrame with multiple columns
        df_data = {}
        for i, channel_name in enumerate(channel_names):
            # Clean channel name for DataFrame column
            clean_name = self._clean_channel_name(channel_name)
            df_data[clean_name] = data[:, i]
        
        df = pd.DataFrame(df_data, index=times)
        df.index.name = self.time_dim
        
        # Store channel information for later use
        self.channel_names = channel_names
        self.channel_units = channel_units
        
        return df

    def _extract_channel_names(self, RBR) -> list:
        """Extract channel names from RBR structure."""
        try:
            channel_names = getattr(RBR, "channelnames", [])
            if hasattr(channel_names, '__iter__') and not isinstance(channel_names, str):
                # Handle array of strings
                return [str(name) for name in np.atleast_1d(channel_names)]
            elif isinstance(channel_names, str):
                return [channel_names]
            else:
                return []
        except:
            return []

    def _extract_channel_units(self, RBR) -> list:
        """Extract channel units from RBR structure."""
        try:
            channel_units = getattr(RBR, "channelunits", [])
            if hasattr(channel_units, '__iter__') and not isinstance(channel_units, str):
                # Handle array of strings
                return [str(unit) for unit in np.atleast_1d(channel_units)]
            elif isinstance(channel_units, str):
                return [channel_units]
            else:
                return []
        except:
            return []

    def _clean_channel_name(self, channel_name: str) -> str:
        """Clean channel name for use as DataFrame column name."""
        # Remove spaces, special characters, make lowercase
        import re
        clean_name = re.sub(r'[^\w]', '_', str(channel_name).strip())
        clean_name = re.sub(r'_+', '_', clean_name)  # Multiple underscores to single
        clean_name = clean_name.strip('_')  # Remove leading/trailing underscores
        return clean_name.lower() if clean_name else "unknown_parameter"

    def __create_xarray_dataset(self, df: pd.DataFrame) -> xr.Dataset:
        """Create an xarray Dataset and attach metadata for all parameters."""
        # Create data variables for each column in the DataFrame
        data_vars = {}
        coords = {self.time_dim: df.index.values.astype("datetime64[ns]")}
        
        for i, col in enumerate(df.columns):
            # Get original channel name and units
            original_name = self.channel_names[i] if i < len(self.channel_names) else col
            units = (self.channel_units[i] if i < len(self.channel_units) else '')
            
            # Create DataArray for this parameter
            data_vars[col] = xr.DataArray(
                df[col].to_numpy(),
                dims=[self.time_dim],
                attrs={
                    "units": units,
                    "long_name": original_name,
                    "original_name": original_name
                }
            )
            
            # Add coefficients to first parameter (legacy behavior)
            if i == 0 and self.coefficients:
                data_vars[col].attrs["coefficients"] = self.coefficients

        # Create Dataset
        ds = xr.Dataset(
            data_vars=data_vars,
            coords=coords,
            attrs={
                "Conventions": "CF-1.8",
                "title": "RBR oceanographic data",
                "source": "RBR instrument (legacy MATLAB export)",
                "rbr_serial_number": self.serial_number,
                "rbr_start_date": self.start_date,
                "rbr_end_date": self.end_date,
            },
        )

        # Optional global attrs
        if self.comment:
            ds.attrs["comment"] = self.comment
        if self.latitude is not None:
            ds.attrs["latitude"] = float(self.latitude)
        if self.longitude is not None:
            ds.attrs["longitude"] = float(self.longitude)

        # Let base class attach any mapped metadata
        for key in list(ds.data_vars.keys()) + list(ds.coords.keys()):
            super()._assign_metadata_for_key_to_xarray_dataset(ds, key)
        
        # Perform default post-processing
        ds = self._perform_default_postprocessing(ds)
        
        return ds

    def __read(self):
        df = self.__parse_data(self.input_file)
        self.data = self.__create_xarray_dataset(df)

    # ------------ public API ------------
    def get_data(self) -> xr.Dataset:
        return self.data

    @staticmethod
    def format_key() -> str:
        return "rbr-matlab-legacy"

    @staticmethod
    def format_name() -> str:
        return "RBR Matlab Legacy"

    @staticmethod
    def file_extension() -> str | None:
        return None
    
