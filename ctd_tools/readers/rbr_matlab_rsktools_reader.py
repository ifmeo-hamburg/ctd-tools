"""
Module for reading RBR RSK data from MATLAB files.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import xarray as xr
import scipy.io
from ctd_tools.readers.base import AbstractReader
import ctd_tools.parameters as params


class RbrMatlabRsktoolsReader(AbstractReader):
    """
    Reader for Matlab files created with RBR RSKtools.

    This class converts RSK structures (created with RSK2MAT.m from RBR RSKtools) 
    into xarray Datasets with separate variables for each sensor channel.
    """

    def __init__(self, input_file, mapping=None, time_dim: str = params.TIME):
        self.time_dim = time_dim
        # Instrument information
        self.instrument_info = {}
        self.channels_info = {}
        self.epochs_info = {}
        super().__init__(input_file, mapping)
        self.__read()

    def __parse_rsk_data(self, mat_file_path : str) -> xr.Dataset:
        """
        Parse RSK MATLAB file into xarray Dataset.
        
        Parameters
        ----------
        mat_file_path : str
            Path to the .mat file containing RSK structure.

        Returns
        -------
        xr.Dataset
            Converted Dataset.
        """
        # Load MATLAB file
        try:
            mat = scipy.io.loadmat(
                mat_file_path, 
                squeeze_me=True, 
                struct_as_record=False
            )
        except Exception as e:
            raise ValueError(f"Could not read .mat file: {e}")

        # RSK structure extraction
        if "rsk" not in mat:
            raise ValueError("Expected 'rsk' struct not found in .mat file.")
        
        rsk = mat["rsk"]

        # Metadata extraction
        self._extract_metadata(rsk)

        # Timestamp extraction
        timestamps = self._extract_timestamps(rsk)

        # Channel data extraction
        data_vars, coords = self._extract_channels_data(rsk, timestamps)

        # Dataset creation
        ds = xr.Dataset(
            data_vars=data_vars,
            coords=coords,
            attrs=self._create_global_attributes()
        )
        
        # Perform default post-processing
        ds = self._perform_default_postprocessing(ds)

        return ds
    
    def _extract_metadata(self, rsk):
        """Extract metadata from RSK structure."""

        # Instrument information
        instruments = getattr(rsk, 'instruments', None)
        if instruments is not None:
            self.instrument_info = {
                'model': self._safe_getattr(instruments, 'model', 'Unknown'),
                'serial_id': self._safe_getattr(instruments, 'serialID', 'Unknown'),
                'firmware_version': self._safe_getattr(instruments, 'firmwareVersion', 'Unknown'),
                'firmware_type': self._safe_getattr(instruments, 'firmwareType', 'Unknown'),
            }

        # Channel information
        channels = getattr(rsk, 'channels', [])
        if hasattr(channels, '__len__') and len(channels) > 0:
            for i, channel in enumerate(np.atleast_1d(channels)):
                try:
                    channel_name = self._safe_getattr(channel, 'longName', f'Channel_{i}')
                    self.channels_info[channel_name] = {
                        'index': i,
                        'longName': channel_name,
                        'shortName': self._safe_getattr(channel, 'shortName', channel_name),
                        'units': self._safe_getattr(channel, 'units', ''),
                        'channelID': self._safe_getattr(channel, 'channelID', i+1)
                    }
                except Exception:
                    continue

        # Epoch information
        epochs = getattr(rsk, 'epochs', None)
        if epochs is not None:
            self.epochs_info = {
                'startTime': self._safe_getattr(epochs, 'startTime', None),
                'endTime': self._safe_getattr(epochs, 'endTime', None),
                'deploymentID': self._safe_getattr(epochs, 'deploymentID', None)
            }
    
    def _extract_timestamps(self, rsk):
        """Extract and convert timestamps."""
        data_struct = getattr(rsk, 'data', None)
        if data_struct is None:
            raise ValueError("'data' structure not found in RSK")
        
        tstamp = getattr(data_struct, 'tstamp', None)
        if tstamp is None:
            raise ValueError("'tstamp' array not found in data structure")
        
        tstamp = np.asarray(tstamp)

        # Convert MATLAB datenum to datetime64
        try:
            timestamps = pd.to_datetime(tstamp, unit='D', origin='0000-01-01').values
        except:
            # Fallback: manual conversion
            unix_timestamps = (tstamp - 719529) * 86400
            timestamps = pd.to_datetime(unix_timestamps, unit='s').values
        
        return timestamps
    
    def _extract_channels_data(self, rsk, timestamps):
        """Extract data for all channels."""
        data_struct = getattr(rsk, 'data', None)
        if data_struct is None:
            raise ValueError("'data' structure not found")
        
        values = getattr(data_struct, 'values', None)
        if values is None:
            raise ValueError("'values' array not found")
        
        values = np.asarray(values)

        # Coordinates
        coords = {self.time_dim: timestamps}

        # Data variables for each channel
        data_vars = {}
        
        for channel_name, channel_info in self.channels_info.items():
            channel_index = channel_info['index']
            
            if channel_index < values.shape[1]:
                channel_data = values[:, channel_index]
                
                data_vars[channel_name] = xr.DataArray(
                    channel_data,
                    dims=[self.time_dim],
                    attrs={
                        'long_name': channel_info['longName'],
                        'units': channel_info['units'],
                        'short_name': channel_info['shortName'],
                        'rbr_channel_id': channel_info['channelID'],
                        'rbr_original_units': channel_info['units'],
                        'rbr_original_name': channel_name,
                    }
                )
        
        return data_vars, coords
    
    def _safe_getattr(self, obj, attr, default=None):
        """Safely access MATLAB structure attributes."""
        try:
            value = getattr(obj, attr, default)
            if isinstance(value, np.ndarray) and value.size == 1:
                return value.item()
            elif isinstance(value, np.ndarray) and value.dtype.kind in ['U', 'S']:
                return str(value)
            return value
        except:
            return default
    
    def _create_global_attributes(self) -> dict:
        """Extract global dataset attributes."""
        attrs = {
            'Conventions': 'CF-1.8',
            'source': f"RBR {self.instrument_info.get('model', 'Unknown')}",
        }

        # Instrument information
        for key, value in self.instrument_info.items():
            attrs[f'rbr_instrument_{key}'] = value

        # Epoch information
        if self.epochs_info.get('startTime') is not None:
            try:
                start_dt = pd.to_datetime(
                    self.epochs_info['startTime'], 
                    unit='D', 
                    origin='0000-01-01'
                )
                attrs['rbr_time_coverage_start'] = start_dt.isoformat()
            except:
                pass
        
        if self.epochs_info.get('endTime') is not None:
            try:
                end_dt = pd.to_datetime(
                    self.epochs_info['endTime'], 
                    unit='D', 
                    origin='0000-01-01'
                )
                attrs['rbr_time_coverage_end'] = end_dt.isoformat()
            except:
                pass
        
        return attrs

    def __read(self):
        """Main reading method."""
        self.data = self.__parse_rsk_data(self.input_file)

    def get_data(self) -> xr.Dataset:
        """Return the converted dataset."""
        return self.data

    @staticmethod
    def format_key() -> str:
        return "rbr-matlab-rsktools"

    @staticmethod
    def format_name() -> str:
        return "RBR Matlab RSKtools"

    @staticmethod
    def file_extension() -> str | None:
        return None
