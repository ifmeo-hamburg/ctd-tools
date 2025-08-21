
TEMPERATURE = 'temperature'
OXYGEN = 'oxygen'
PRESSURE = 'pressure'
SALINITY = 'salinity'
TURBIDITY = 'turbidity'
CONDUCTIVITY = 'conductivity'
DEPTH = 'depth'
DATE = 'date'
TIME = 'time'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
DENSITY = 'density'
POTENTIAL_TEMPERATURE = 'potential_temperature'
SPEED_OF_SOUND = 'speed_of_sound'
TIME_J = 'julian_days_offset'
TIME_Q = 'seconds_since_jan_1_2000'
TIME_N = 'timeN'
TIME_S = 'timeS'
POWER_SUPPLY_INPUT_VOLTAGE = 'power_supply_input'
EAST_VELOCITY = 'east_velocity'
NORTH_VELOCITY = 'north_velocity'
UP_VELOCITY = 'up_velocity'
EAST_AMPLITUDE = 'east_amplitude'
NORTH_AMPLITUDE = 'north_amplitude'
UP_AMPLITUDE = 'up_amplitude'
SOUNDSPEED = 'speed_of_sound'
CHLOROPHYLL = 'chlorophyll'
FLUORESCENCE = 'fluorescence'
ECHO_INTENSITY = 'echo_intensity'
CORRELATION = 'correlation'
DIRECTION = 'direction'
MAGNITUDE = 'magnitude'
PITCH = 'pitch'
ROLL = 'roll'
HEADING = 'heading'
BATTERY_VOLTAGE = 'battery_voltage'
ALTIMETER = 'altimeter'

# Meta data should use standardized values from https://cfconventions.org/
metadata = {
    TEMPERATURE: {
        'long_name': "Temperature",
        'units': "ITS-90, deg C",
        'coverage_content_type': 'physicalMeasurement',
        'standard_name': 'sea_water_temperature',
        'short_name': "WT",
        'measurement_type': "Measured",
    },
    PRESSURE: {
        'long_name': "Pressure",
        'units': "dbar",
        'coverage_content_type': 'physicalMeasurement',
        'standard_name': 'sea_water_pressure',
        'short_name': "WP",
        'measurement_type': "Measured",
    },
    CONDUCTIVITY: {
        'long_name': "Conductivity",
        'coverage_content_type': 'physicalMeasurement',
        'units': "S m-1",
        'standard_name': 'sea_water_electrical_conductivity',
        'short_name': "COND",
        'measurement_type': "Measured",
    },
    SALINITY: {
        'long_name': "Salinity",
        'coverage_content_type': 'physicalMeasurement',
        'standard_name': 'sea_water_salinity',
        'short_name': 'SAL',
        'measurement_type': 'Derived', 
    },
    TURBIDITY: {
        'long_name': "Turbidity",
        'coverage_content_type': 'physicalMeasurement',
        'standard_name': 'sea_water_turbidity',
        'measurement_type': "Measured",
        'short_name': "Tur", 
    }, 
    OXYGEN: {
        'long_name': "Oxygen",
        'coverage_content_type': 'physicalMeasurement',
        'standard_name': 'volume_fraction_of_oxygen_in_sea_water'
    },
    DEPTH: {
        'long_name': 'Depth',
        'units': 'meters',
        'positive': 'up',
        'standard_name': 'depth',
        'coverage_content_type': 'coordinate',
        'short_name': "D",
    },
    DENSITY: {
        'long_name': 'Density',
        'units': 'kg m-3',
        'standard_name': 'sea_water_density',
        'measurement_type': 'Derived',
    },
    POTENTIAL_TEMPERATURE: {
        'long_name': 'Potential Temperature θ',
        'units': 'degC',
        'standard_name': 'sea_water_potential_temperature',
        'measurement_type': 'Derived',
    },
    SPEED_OF_SOUND: {
        'long_name': 'Speed of Sound',
        'units': 'm s-1',
        'standard_name': 'speed_of_sound_in_sea_water',
        'measurement_type': 'Derived',
    },
    LATITUDE: {
        'long_name': 'Latitude',
        'units': 'degrees_north',
        'standard_name': 'latitude',
        'coverage_content_type': 'coordinate',
        'short_name': "lat",
    },
    LONGITUDE: {
        'long_name': 'Longitude',
        'units': 'degrees_east',
        'standard_name': 'longitude',
        'coverage_content_type': 'coordinate',
        'short_name': "lon",
    },
    TIME: {
        'long_name': 'Time',
        'standard_name': 'time',
        'coverage_content_type': 'coordinate' 
    },
    POWER_SUPPLY_INPUT_VOLTAGE: {
        'long_name': 'Power supply input voltage',
        'units': 'V',
    },
    EAST_VELOCITY: {
        'units': 'm/s',
        'long_name': 'Eastward velocity',
        'standard_name': 'eastward_sea_water_velocity',
    },
    NORTH_VELOCITY: {
        'units': 'm/s',
        'long_name': 'Northward velocity',
        'standard_name': 'northward_sea_water_velocity',
    },
    UP_VELOCITY: {
        'units': 'm/s',
        'long_name': 'Upward velocity',
        'standard_name': 'upward_sea_water_velocity',
    },
    SPEED_OF_SOUND: {
        'units': 'm/s',
        'long_name': 'Speed of sound in sea water',
        'standard_name': 'speed_of_sound_in_sea_water',
    },
    ECHO_INTENSITY: {
        'units': 'dB',
        'long_name': 'Echo intensity',
        'standard_name': 'echo_intensity',
    },
    CORRELATION: {
        'units': 'unitless',
        'long_name': 'Correlation',
        'standard_name': 'correlation',
    },
    DIRECTION: {
        'units': 'degrees',
        'long_name': 'Current direction',
        'standard_name': 'direction',
    },
    MAGNITUDE: {
        'units': 'm/s',
        'long_name': 'Current magnitude',
        'standard_name': 'magnitude',
    },
    PITCH: {
        'units': 'degrees',
        'long_name': 'Pitch angle',
        'standard_name': 'platform_pitch_angle',
    },
    ROLL: {
        'units': 'degrees',
        'long_name': 'Roll angle',
        'standard_name': 'platform_roll_angle',
    },
    HEADING: {
        'units': 'degrees',
        'long_name': 'Heading angle',
        'standard_name': 'platform_heading_angle',
    },
    BATTERY_VOLTAGE: {
        'units': 'volts',
        'long_name': 'Battery voltage',
        'standard_name': 'battery_voltage',
    }
}

default_mappings = {
    TEMPERATURE: [
        't090C', 't068', 
        't190C', 't168',
        'tv290C', 'TEMP', 'temp', 'Temp', 
        'Temperature', 'temperature',
        'T1', 'T2',
        'temp90', 'temp68'
    ],
    POTENTIAL_TEMPERATURE: [
        'potemp090C', 'potemp190C'
    ],
    SALINITY: [
        'sal00', 'sal11', 'PSAL2', 'PSAL', 'SAL', 'Salinity'
    ],
    CONDUCTIVITY: [
        'c0mS/cm', 'cond0mS/cm', 'c0', 'c0S/m', 
        'c1mS/cm', 'cond1mS/cm', 'c1', 'c1S/m',
        'COND', 'Conductivity',
        'cond0', 'cond1'
    ],
    PRESSURE: [
        'prdM', 'prDM', 
        'pr', 'pr50M', 'pr200M', 'pr350M', 'pr600M', 'pr1000M',
        'PRES', 'Pressure', 'Sea Pressure', 'Sea pressure',
        'p'
    ],
    TURBIDITY: [
        'turbWETntu0', 'Turbidity', 'Backscatter'
    ],
    DEPTH: [
        'depSM', 'Depth'
    ],
    TIME_J: [
        'timeJ', 'timeJV2', 'timeSCP'
    ],
    TIME_Q: [
        'timeQ', 'timeK'
    ],
    TIME_N: [
        'timeN'
    ],
    TIME_S: [
        'timeS'
    ],
    OXYGEN: [
        'oxsatMm/Kg', 'oxsolMm/Kg', 
        'sbeox0V', 'sbeox0', 'sbeox0ML/L', 'sbeox0Mm/Kg', 'sbeox0Mm/L', 'sbeox0PS',
        'sbeox1V','sbeox1', 'sbeox1ML/L', 'sbeox1Mm/Kg', 'sbeox1Mm/L', 'sbeox1PS',
        'Oxygen', 'O2', 'OXY', 'Dissolved O2',
        'Dissolved Oxygen', 'Dissolved O2 Saturation',
        'dissolved_o2_saturation', 'Dissolved O₂', 'Dissolved O₂ saturation'
    ],
    LATITUDE: [
        'latitude', 'LATITUDE', 'lat', 'LAT', 'Latitude', 'Lat'
    ], 
    LONGITUDE: [
        'longitude', 'LONGITUDE', 'lon', 'LON', 'Longitude', 'Lon'
    ],
    POWER_SUPPLY_INPUT_VOLTAGE: [
        'Vbatt', 'Vcharge', 'Vmote'
    ],
    EAST_VELOCITY: [
        'east_velocity', 'eastward_velocity', 'eastward_sea_water_velocity',
        'Velocity (Beam1|X|East)', 'Eastward velocity'
    ],
    NORTH_VELOCITY: [
        'north_velocity', 'northward_velocity', 'northward_sea_water_velocity',
        'Velocity (Beam2|Y|North)', 'Northward velocity'
    ],
    UP_VELOCITY: [
        'up_velocity', 'upward_velocity', 'upward_sea_water_velocity',
        'Velocity (Beam3|Z|Up)', 'Upward velocity'
    ],
    EAST_AMPLITUDE: [
        'Amplitude (Beam1)', 'Eastward amplitude'
    ],
    NORTH_AMPLITUDE: [
        'Amplitude (Beam2)', 'Northward amplitude'
    ],
    UP_AMPLITUDE: [
        'Amplitude (Beam3)', 'Upward amplitude'
    ],
    SPEED_OF_SOUND: [
        'Soundspeed', 'Speed of Sound', 'speed_of_sound'
    ],
    CHLOROPHYLL: [
        'Chlorophyll'
    ],
    FLUORESCENCE: [
        'flECO-AFL', 'Fluorescence'
    ],
    ALTIMETER: [
        'altM', 'altimeter'
    ],
    DENSITY: [ 
        'sigma-t00', 'sigma-t11',
        'sigma-theta00', 'sigma-theta11',
        'dens00', 'dens11',
        'Density', 'density',
        'SIGMA', 'Sigma', 'sigma'
    ]
}

rename_list = {
    'Velocity (Beam1|X|East)': EAST_VELOCITY,
    'Velocity (Beam2|Y|North)': NORTH_VELOCITY,
    'Velocity (Beam3|Z|Up)': UP_VELOCITY,
    'Amplitude (Beam1)': EAST_AMPLITUDE,
    'Amplitude (Beam2)': NORTH_AMPLITUDE,
    'Amplitude (Beam3)': UP_AMPLITUDE,
    'Temperature': TEMPERATURE,
    'Pressure': PRESSURE,
    'Temp': TEMPERATURE,
    'datetime': TIME,
    'Soundspeed': SPEED_OF_SOUND
}

def allowed_parameters():
    """Returns a dictionary of allowed parameter names with their descriptions."""
    return {
        TEMPERATURE: 'Temperature in degrees Celsius',
        SALINITY: 'Salinity in PSU',
        CONDUCTIVITY: 'Conductivity in S/m',
        PRESSURE: 'Pressure in Dbar',
        OXYGEN: 'Oxygen in micromoles/kg',
        TURBIDITY: 'Turbidity in NTU',
        DEPTH: 'Depth in meters',
        DATE: 'Date of the measurement'
    }
