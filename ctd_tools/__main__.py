import argparse
import os
import ctd_tools.ctd_parameters as ctdparams
import re
import pandas as pd

from .modules.reader import NetCdfReader, CsvReader, CnvReader, TobReader, RbrAsciiReader, NortekAsciiReader, RCM_matlab_Reader_14
from .modules.writer import NetCdfWriter, CsvWriter, ExcelWriter
from .modules.plotter import CtdPlotter
from .modules.calculator import CtdCalculator, CtdResampler
from .modules.subsetter import CtdSubsetter
from datetime import datetime

INPUTFORMAT_KEY_SBE_CNV = 'sbe-cnv'
INPUTFORMAT_KEY_SEASUN_TOB = 'seasun-tob'
INPUTFORMAT_KEY_CSV = 'csv'
INPUTFORMAT_KEY_NETCDF = 'netcdf'
INPUTFORMAT_KEY_RBR_ASCII = 'rbr-ascii'
INPUTFORMAT_KEY_NORTEK_ASCII = 'nortek-ascii'
INPUTFORMAT_KEY_RCM_MAT = 'rcm-mat'

# Input formats for the CLI commands
input_formats = [
    INPUTFORMAT_KEY_SBE_CNV,      # Seabird CNV
    INPUTFORMAT_KEY_SEASUN_TOB,   # Sea & Sun TOB
    INPUTFORMAT_KEY_CSV,          # Comma separated file
    INPUTFORMAT_KEY_NETCDF,       # netCDF
    INPUTFORMAT_KEY_RBR_ASCII,    # RBR ASCII
    INPUTFORMAT_KEY_NORTEK_ASCII, # Nortek ASCII
    INPUTFORMAT_KEY_RCM_MAT       # RCM Matlab
]

# Output formats for the CLI commands
output_formats = [
    'netcdf',       # netCDF
    'csv',          # Comma separated file
    'excel'         # Excel
]

class CommandController:
    """ Controller logic for CLI commands """

    def __init__(self, argsparser, args):
        self.argsparser = argsparser
        self.args = args

    def execute(self):
        """ Manages the routing according to the given command in the args. """

        if self.args.command == 'convert':
            self.handle_convert_command()
        elif self.args.command == 'plot-ts':
            self.handle_plot_ts_command()
        elif self.args.command == 'plot-profile':
            self.handle_plot_profile_command()
        elif self.args.command == 'plot-series':
            self.handle_plot_series_command()
        elif self.args.command == 'show':
            self.handle_show_command()
        elif self.args.command == 'calc':
            self.handle_calc_command()
        elif self.args.command == 'subset':
            self.handle_subset_command()
        else:
            self.argsparser.print_help()

    def __read_data(self, input_file, header_input_file=None):
        """ Helper for reading data from input file of different types.
        Returns the data. """

        format=self.args.input_format

        if input_file.lower().endswith('.nc') or format == INPUTFORMAT_KEY_NETCDF:
            reader = NetCdfReader(input_file)
        elif input_file.lower().endswith('.csv') or format == INPUTFORMAT_KEY_CSV:
            reader = CsvReader(input_file)
        elif input_file.lower().endswith('.cnv') or format == INPUTFORMAT_KEY_SBE_CNV:
            reader = CnvReader(input_file)
        elif input_file.lower().endswith('.tob') or format == INPUTFORMAT_KEY_SEASUN_TOB:
            reader = TobReader(input_file)
        elif format == INPUTFORMAT_KEY_RBR_ASCII:
            reader = RbrAsciiReader(input_file)
        elif format == INPUTFORMAT_KEY_NORTEK_ASCII:
            if not header_input_file:
                raise argparse.ArgumentTypeError("Header input file is required for Nortek ASCII files.")
            reader = NortekAsciiReader(input_file, header_input_file)
        else:
            raise argparse.ArgumentTypeError("Input file must be a netCDF (.nc) " \
                    "CSV (.csv), CNV (.cnv), or TOB (.tob), or RBR ASCII file.")
        return reader.get_data()
    
    def __handle_output_directory(self, output_file):
        if output_file:
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

    def handle_plot_series_command(self):
        """ Handles the CLI 'plot-series' command. """

        # Read data from input file
        data = self.__read_data(self.args.input, self.args.header_input)
        
        # Create output directory if it doesn't exist
        self.__handle_output_directory(self.args.output)

        # Create plotter
        plotter = CtdPlotter(data)
        plotter.plot_time_series(parameter_name=self.args.parameter, output_file=self.args.output)

    def handle_plot_profile_command(self):
        """ Handles the CLI 'plot-profile' command. """

        # Read data from input file
        data = self.__read_data(self.args.input, self.args.header_input)
        
        # Create output directory if it doesn't exist
        self.__handle_output_directory(self.args.output)

        # Create plotter
        plotter = CtdPlotter(data)
        plotter.plot_profile(
            output_file=self.args.output, 
            title=self.args.title,
            dot_size=self.args.dot_size,
            show_lines_between_dots=(not self.args.no_lines_between_dots),
            show_grid=(not self.args.no_grid)
        )

    def handle_plot_ts_command(self):
        """ Handles the CLI 'plot-ts' command. """

        if self.args.dot_size:
            if self.args.dot_size < 1 or self.args.dot_size > 200:
                raise argparse.ArgumentTypeError("--dot-size must be between 1 and 200")

        # Read data from input file
        data = self.__read_data(self.args.input, self.args.header_input)

        # Create output directory if it doesn't exist
        self.__handle_output_directory(self.args.output)

        # Create plotter
        plotter = CtdPlotter(data)
        plotter.plot_ts_diagram(
            output_file=self.args.output, 
            title=self.args.title, 
            dot_size=self.args.dot_size, 
            use_colormap=(not self.args.no_colormap), 
            show_density_isolines=(not self.args.no_isolines),
            colormap=self.args.colormap, 
            show_lines_between_dots=(not self.args.no_lines_between_dots),
            show_grid=(not self.args.no_grid)
        )

    def handle_convert_command(self):
        """ Handles the CLI 'convert' command. """

        # Determine output format
        format = None
        if self.args.output_format:
            format = self.args.output_format
        else:
            if self.args.output.lower().endswith('.nc'):
                format = 'netcdf'
            elif self.args.output.lower().endswith('.csv'):
                format = 'csv'
            elif self.args.output.lower().endswith('.xlsx'):
                format = 'excel'
            else:
                raise argparse.ArgumentTypeError(
                    "Output file must be a netCDF (.nc), " \
                    "CSV (.csv), or Excel (.xlsx) file.")

        # Map column names to standard parameter names
        parameter_mapping = {}
        allowed_parameters = ctdparams.allowed_parameters()
        if self.args.mapping:
            for mapping in self.args.mapping:
                key, value = mapping.split('=')
                if key in allowed_parameters:
                    parameter_mapping[key] = value
                else:
                    raise ValueError(f"Unallowed parameter name: {key}. " \
                            "Allowed parameters are: {', '.join(allowed_parameters)}")

        # Create output directory if it doesn't exist
        self.__handle_output_directory(self.args.output)

        # Read data from CNV file
        data = self.__read_data(self.args.input)

        # Write data to netCDF or CSV
        if format == 'netcdf':
            writer = NetCdfWriter(data)
            writer.write(self.args.output)
        elif format == 'csv':
            writer = CsvWriter(data)
            writer.write(self.args.output)
        elif format == 'excel':
            writer = ExcelWriter(data)
            writer.write(self.args.output)
        else:
            raise argparse.ArgumentTypeError('Unknown output format')

    def handle_show_command(self):
        """ Handles the CLI 'show' command. """

        # Read data from input file
        data = self.__read_data(self.args.input, self.args.header_input)

        if data:
            schema = self.args.schema
            if schema == 'summary':
                print(data)
            elif schema == 'info':
                data.info()
            elif schema == 'example':
                df = data.to_dataframe()
                print(df.head())
        else:
            raise ValueError('No data found in file.')
        
    def handle_subset_command(self):
        """ Handles the CLI 'subset' command. """

        # Read data from input file
        data = self.__read_data(self.args.input, self.args.header_input)

        if data:
            subsetter = CtdSubsetter(data)
            if self.args.sample_min:
                subsetter.set_sample_min(self.args.sample_min)
            if self.args.sample_max:
                subsetter.set_sample_max(self.args.sample_max)
            if self.args.time_min:
                subsetter.set_time_min(self.args.time_min)
            if self.args.time_max:
                subsetter.set_time_max(self.args.time_max)
            if self.args.parameter:
                subsetter.set_parameter_name(self.args.parameter)
            if self.args.value_min:
                subsetter.set_parameter_value_min(self.args.value_min)
            if self.args.value_max:
                subsetter.set_parameter_value_max(self.args.value_max)
            subset = subsetter.get_subset()
            print(subset)
        else:
            raise ValueError('No data found in file.')

    def __run_calculation(self, data):
        calc = CtdCalculator(data, self.args.parameter)
        if self.args.method == 'max':
            return calc.max()
        elif self.args.method == 'min':
            return calc.min()
        elif self.args.method == 'mean':
            return calc.mean()
        elif self.args.method == 'median':
            return calc.median()
        elif self.args.method == 'std' or self.args.method == 'standard_deviation':
            return calc.std()
        elif self.args.method == 'var' or self.args.method == 'variance':
            return calc.var()
        else:
            raise ValueError(f"Unknown calculation method: {self.args.method}")
        
    def handle_calc_command(self):
        """ Handles the CLI 'calc' command. """

        # Read data from input file
        data = self.__read_data(self.args.input, self.args.header_input)

        if data:
            if self.args.resample:
                resampler = CtdResampler(data)
                data = resampler.resample(self.args.time_interval)

                datetime_format_pattern = "%Y-%m-%d %H:%M:%S"
                if re.match(r"^[0-9\.]*M$", self.args.time_interval):
                    datetime_format_pattern = '%Y-%m'
                elif re.match(r"^[0-9\.]*Y$", self.args.time_interval):
                    datetime_format_pattern = '%Y'
                elif re.match(r"^[0-9\.]*D$", self.args.time_interval):
                    datetime_format_pattern = '%Y-%m-%d'
                elif re.match(r"^[0-9\.]*H$", self.args.time_interval):
                    datetime_format_pattern = '%Y-%m-%d %H:%M'
                elif re.match(r"^[0-9\.]*min$", self.args.time_interval):
                    datetime_format_pattern = '%Y-%m-%d %H:%M'
                print(datetime_format_pattern)
                for time_period, group in data:
                    result = self.__run_calculation(group)
                    dt_datetime = pd.to_datetime(time_period)
                    datetime_string = dt_datetime.strftime(datetime_format_pattern)
                    print(f"{datetime_string}: {result}")
            else:
                print(self.__run_calculation(data))

        else:
            raise ValueError('No data found in file.')

class CliInterface:
    """ Definition of the CLI interface """

    @staticmethod
    def parse(argparser: argparse.ArgumentParser):
        subparsers = argparser.add_subparsers(dest='command', help='Verfügbare Befehle')

        # Sub parser for "convert" command
        # -------------------------------------------------------------------------------
        mapping_help = 'Map CNV column names to standard parameter names in the ' \
            'format name=value. Allowed parameter names are: ' + \
            ', \n'.join(f"{k}" for k, v in ctdparams.allowed_parameters().items())
        format_help = 'Choose the output format. Allowed formats are: ' + \
            ', '.join(['netcdf','csv','excel'])
        convert_parser = subparsers.add_parser('convert', help='Convert a file to a specific format.')
        convert_parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file')
        convert_parser.add_argument('-f', '--input-format', type=str, default=None, choices=input_formats, help='Format of input file')
        convert_parser.add_argument('-H', '--header-input', type=str, default=None, help='Path of header input file (for Nortek ASCII files)')
        convert_parser.add_argument('-o', '--output', type=str, required=True, help='Path of output file')
        convert_parser.add_argument('-F', '--output-format', type=str, choices=output_formats, help=format_help)
        convert_parser.add_argument('-m', '--mapping', nargs='+', help=mapping_help)

        # Sub parser for "show" command
        # -------------------------------------------------------------------------------
        show_parser = subparsers.add_parser('show', help='Show contents of a file.')
        show_parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file')
        show_parser.add_argument('-f', '--input-format', type=str, default=None, choices=input_formats, help='Format of input file')
        show_parser.add_argument('-H', '--header-input', type=str, default=None, help='Path of header input file (for Nortek ASCII files)')
        show_parser.add_argument('-s', '--schema', type=str, choices=['summary', 'info', 'example'], default='summary', help='What to show.')

        # Sub parser for "plot-ts" command
        # -------------------------------------------------------------------------------
        plot_ts_parser = subparsers.add_parser('plot-ts', help='Plot a T-S diagram from a netCDF, CNV, CSV, or TOB file')
        plot_ts_parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file')
        plot_ts_parser.add_argument('-f', '--input-format', type=str, default=None, choices=input_formats, help='Format of input file')
        plot_ts_parser.add_argument('-H', '--header-input', type=str, default=None, help='Path of header input file (for Nortek ASCII files)')
        plot_ts_parser.add_argument('-o', '--output', type=str, help='Path of output file if plot shall be written')
        plot_ts_parser.add_argument('-t', '--title', default='T-S Diagram', type=str, help='Title of the plot.')
        plot_ts_parser.add_argument('--dot-size', default=70, type=int, help='Dot size for scatter plot (1-200)')
        plot_ts_parser.add_argument('--colormap', default='jet', type=str, help='Name of the colormap for the plot. Must be a valid Matplotlib colormap.')
        plot_ts_parser.add_argument('--no-lines-between-dots', default=False, action='store_true', help='Disable the connecting lines between dots.')
        plot_ts_parser.add_argument('--no-colormap', action='store_true', default=False, help='Disable the colormap in the plot')
        plot_ts_parser.add_argument('--no-isolines', default=False, action='store_true', help='Disable the density isolines in the plot')
        plot_ts_parser.add_argument('--no-grid', default=False, action='store_true', help='Disable the grid.')

        # Sub parser for "plot-profile" command
        # -------------------------------------------------------------------------------
        plot_profile_parser = subparsers.add_parser('plot-profile', help='Plot a vertical CTD profile from an input file')
        plot_profile_parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file')
        plot_profile_parser.add_argument('-f', '--input-format', type=str, default=None, choices=input_formats, help='Format of input file')
        plot_profile_parser.add_argument('-H', '--header-input', type=str, default=None, help='Path of header input file (for Nortek ASCII files)')
        plot_profile_parser.add_argument('-o', '--output', type=str, help='Path of output file if plot shall be written')
        plot_profile_parser.add_argument('-t', '--title', default='Salinity and Temperature Profiles', type=str, help='Title of the plot.')
        plot_profile_parser.add_argument('--dot-size', default=3, type=int, help='Dot size for scatter plot (1-200)')
        plot_profile_parser.add_argument('--no-lines-between-dots', default=False, action='store_true', help='Disable the connecting lines between dots.')
        plot_profile_parser.add_argument('--no-grid', default=False, action='store_true', help='Disable the grid.')

        # Sub parser for "plot-series" command
        # -------------------------------------------------------------------------------
        plot_series_parser = subparsers.add_parser('plot-series', help='Plot a time series for a single parameter from an input file')
        plot_series_parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file')
        plot_series_parser.add_argument('-f', '--input-format', type=str, default=None, choices=input_formats, help='Format of input file')
        plot_series_parser.add_argument('-H', '--header-input', type=str, default=None, help='Path of header input file (for Nortek ASCII files)')
        plot_series_parser.add_argument('-o', '--output', type=str, help='Path of output file if plot shall be written')
        plot_series_parser.add_argument('-p', '--parameter', type=str, required=True, help='Standard name of a parameter, e.g. "temperature" or "salinity".')

        # Sub parser for "subset" command
        # -------------------------------------------------------------------------------
        calc_parser = subparsers.add_parser('subset', help='Extract a subset of a file and save the result in another')
        calc_parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file')
        calc_parser.add_argument('-f', '--input-format', type=str, default=None, choices=input_formats, help='Format of input file')
        calc_parser.add_argument('-H', '--header-input', type=str, default=None, help='Path of header input file (for Nortek ASCII files)')
        calc_parser.add_argument('-F', '--output-format', type=str, choices=output_formats, help=format_help)
        calc_parser.add_argument('--time-min', type=str, help='Minimum datetime value. Formats are: YYYY-MM-DD HH:ii:mm.ss')
        calc_parser.add_argument('--time-max', type=str, help='Maximum datetime value. Formats are: YYYY-MM-DD HH:ii:mm.ss')
        calc_parser.add_argument('--sample-min', type=int, help='Minimum sample/index value (integer)')
        calc_parser.add_argument('--sample-max', type=int, help='Maximum sample/index value (integer)')
        calc_parser.add_argument('--parameter', type=str, help='Standard name of a parameter, e.g. "temperature" or "salinity".')
        calc_parser.add_argument('--value-min', type=float, help='Minimum value for the specified parameter (float, integer)')
        calc_parser.add_argument('--value-max', type=float, help='Maximum value for the specified parameter (float, integer)')

        # Sub parser for "calc" command
        # -------------------------------------------------------------------------------
        method_choices = ['min', 'max', 'mean', 'arithmetic_mean', 'median', 'std', 'standard_deviation', 'var', 'variance', 'sum']
        calc_parser = subparsers.add_parser('calc', help='Run an aggregate function on a parameter of the whole dataset')
        calc_parser.add_argument('-i', '--input', type=str, required=True, help='Path of input file')
        calc_parser.add_argument('-f', '--input-format', type=str, default=None, choices=input_formats, help='Format of input file')
        calc_parser.add_argument('-H', '--header-input', type=str, default=None, help='Path of header input file (for Nortek ASCII files)')
        calc_parser.add_argument('-o', '--output', type=str, help='Path of output file')
        calc_parser.add_argument('-F', '--output-format', type=str, choices=output_formats, help=format_help)
        calc_parser.add_argument('-M', '--method', type=str, choices=method_choices, help='Mathematical method operated on the values.')
        calc_parser.add_argument('-p', '--parameter', type=str, required=True, help='Standard name of a parameter, e.g. "temperature" or "salinity".')
        calc_parser.add_argument('-r', '--resample', default=False, action='store_true', help='Resample the time series.')
        calc_parser.add_argument('-T', '--time-interval', type=str, help='Time interval for resampling. Examples: 1M (one month)')

        return argparser.parse_args()

def main():
    argparser = argparse.ArgumentParser(description='CTD Tools', formatter_class=argparse.RawTextHelpFormatter)
    args = CliInterface.parse(argparser)
    controller = CommandController(argparser, args)
    controller.execute()

if __name__ == "__main__":
    main()
