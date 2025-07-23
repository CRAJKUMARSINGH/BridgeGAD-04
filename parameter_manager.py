import pandas as pd
import numpy as np
from io import BytesIO
import logging


# your Streamlit logic here

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParameterManager:
    """Manages bridge design parameters with validation and Excel I/O"""
    
    def __init__(self):
        """Initialize parameter manager with default definitions"""
        self.parameter_definitions = {
            # Bridge geometry
            'NSPAN': {'description': 'Number of spans', 'type': 'int', 'min': 1, 'max': 51, 'default': 3},
            'SPAN1': {'description': 'Span length (m)', 'type': 'float', 'min': 3, 'max': 100, 'default': 30.0},
            'LBRIDGE': {'description': 'Total bridge length (m)', 'type': 'float', 'min': 3, 'max': 1000, 'default': 90.0},
            'BRIDGEW': {'description': 'Bridge width (m)', 'type': 'float', 'min': 6, 'max': 30, 'default': 12.0},
            'SKEW': {'description': 'Skew angle (degrees)', 'type': 'float', 'min': 0, 'max': 45, 'default': 0.0},
            
            # Levels and elevations
            'RTL': {'description': 'Riding surface level (m)', 'type': 'float', 'min': 90, 'max': 200, 'default': 105.0},
            'DATUM': {'description': 'Drawing datum level (m)', 'type': 'float', 'min': 80, 'max': 150, 'default': 100.0},
            'ABTL': {'description': 'Left abutment chainage (m)', 'type': 'float', 'min': 0, 'max': 100, 'default': 0.0},
            
            # Deck parameters
            'DECKT': {'description': 'Deck thickness (m)', 'type': 'float', 'min': 0.8, 'max': 3.0, 'default': 1.2},
            
            # Pier parameters
            'CAPT': {'description': 'Pier cap top level (m)', 'type': 'float', 'min': 90, 'max': 200, 'default': 104.0},
            'CAPB': {'description': 'Pier cap bottom level (m)', 'type': 'float', 'min': 85, 'max': 195, 'default': 102.0},
            'CAPW': {'description': 'Pier cap width (m)', 'type': 'float', 'min': 0.8, 'max': 3.0, 'default': 1.2},
            'PIERTW': {'description': 'Pier top width (m)', 'type': 'float', 'min': 0.5, 'max': 2.0, 'default': 0.8},
            'BATTR': {'description': 'Pier batter ratio', 'type': 'float', 'min': 3, 'max': 20, 'default': 6.0},
            'PIER_WIDTH': {'description': 'Pier width in plan (m)', 'type': 'float', 'min': 1.0, 'max': 5.0, 'default': 2.0},
            
            # Foundation parameters
            'FUTRL': {'description': 'Foundation top level (m)', 'type': 'float', 'min': 80, 'max': 150, 'default': 98.0},
            'FUTD': {'description': 'Foundation depth (m)', 'type': 'float', 'min': 0.5, 'max': 3.0, 'default': 1.0},
            'FUTW': {'description': 'Foundation width (m)', 'type': 'float', 'min': 1.5, 'max': 5.0, 'default': 2.5},
            
            # Abutment parameters
            'ABUT_HEIGHT': {'description': 'Abutment height (m)', 'type': 'float', 'min': 3, 'max': 15, 'default': 6.0},
            'ABUT_WIDTH': {'description': 'Abutment width (m)', 'type': 'float', 'min': 1.0, 'max': 3.0, 'default': 1.5},
            'FOOT_LENGTH': {'description': 'Abutment footing length (m)', 'type': 'float', 'min': 4, 'max': 15, 'default': 8.0},
            'FOOT_THICK': {'description': 'Abutment footing thickness (m)', 'type': 'float', 'min': 0.8, 'max': 2.5, 'default': 1.2},
            
            # Approach slab parameters
            'APPR_LENGTH': {'description': 'Approach slab length (m)', 'type': 'float', 'min': 5, 'max': 15, 'default': 8.0},
            'APPR_THICK': {'description': 'Approach slab thickness (m)', 'type': 'float', 'min': 0.2, 'max': 0.6, 'default': 0.3},
            
            # Drawing scale
            'SCALE1': {'description': 'Drawing scale numerator', 'type': 'float', 'min': 50, 'max': 1000, 'default': 100.0},
            'SCALE2': {'description': 'Drawing scale denominator', 'type': 'float', 'min': 25, 'max': 200, 'default': 50.0},
        }
    
    def generate_template(self):
        """Generate Excel template with default parameters"""
        try:
            data = []
            for param, config in self.parameter_definitions.items():
                data.append({
                    'Parameter': param,
                    'Value': config['default'],
                    'Description': config['description'],
                    'Type': config['type'],
                    'Min': config.get('min', ''),
                    'Max': config.get('max', ''),
                    'Units': self._get_units(config['description'])
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Generated template with {len(data)} parameters")
            return df
            
        except Exception as e:
            logger.error(f"Error generating template: {e}")
            raise
    
    def _get_units(self, description):
        """Extract units from parameter description"""
        if '(m)' in description:
            return 'm'
        elif '(degrees)' in description:
            return 'degrees'
        elif 'ratio' in description.lower():
            return 'ratio'
        else:
            return ''
    
    def load_parameters(self, file):
        """Load parameters from uploaded Excel file"""
        try:
            # Read Excel file
            if hasattr(file, 'read'):
                # BytesIO object
                df = pd.read_excel(file, sheet_name=0)
            else:
                # File path
                df = pd.read_excel(file, sheet_name=0)
            
            # Extract parameters
            params = {}
            
            # Try different column name variations
            param_col = None
            value_col = None
            
            for col in df.columns:
                if col.lower() in ['parameter', 'param', 'variable', 'name']:
                    param_col = col
                elif col.lower() in ['value', 'val', 'amount']:
                    value_col = col
            
            if param_col is None or value_col is None:
                # Fallback: assume first two columns
                if len(df.columns) >= 2:
                    param_col = df.columns[0]
                    value_col = df.columns[1]
                else:
                    raise ValueError("Excel file must have at least 2 columns (Parameter, Value)")
            
            # Extract parameter-value pairs
            for _, row in df.iterrows():
                param_name = str(row[param_col]).strip()
                param_value = row[value_col]
                
                # Skip empty rows
                if pd.isna(param_name) or str(param_name).strip() == '' or pd.isna(param_value):
                    continue
                
                # Convert value to appropriate type
                try:
                    if param_name in self.parameter_definitions:
                        param_type = self.parameter_definitions[param_name]['type']
                        if param_type == 'int':
                            params[param_name] = int(float(param_value))
                        elif param_type == 'float':
                            params[param_name] = float(param_value)
                        else:
                            params[param_name] = param_value
                    else:
                        # Unknown parameter, try to convert to float
                        params[param_name] = float(param_value)
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not convert parameter {param_name} value {param_value}: {e}")
                    params[param_name] = param_value
            
            # Add missing parameters with defaults
            for param, config in self.parameter_definitions.items():
                if param not in params:
                    params[param] = config['default']
                    logger.info(f"Added default value for missing parameter {param}: {config['default']}")
            
            logger.info(f"Loaded {len(params)} parameters from Excel file")
            return params
            
        except Exception as e:
            logger.error(f"Error loading parameters from Excel: {e}")
            raise
    
    def validate_parameters(self, params):
        """Validate bridge parameters"""
        errors = []
        warnings = []
        
        try:
            # Check required parameters
            required_params = ['NSPAN', 'SPAN1', 'LBRIDGE', 'BRIDGEW', 'RTL', 'DATUM']
            for param in required_params:
                if param not in params:
                    errors.append(f"Missing required parameter: {param}")
                elif pd.isna(params[param]):
                    errors.append(f"Parameter {param} cannot be empty")
            
            # Validate individual parameters
            for param, value in params.items():
                if param in self.parameter_definitions:
                    config = self.parameter_definitions[param]
                    
                    # Type validation
                    try:
                        if config['type'] == 'int':
                            value = int(float(value))
                        elif config['type'] == 'float':
                            value = float(value)
                        params[param] = value  # Update with converted value
                    except (ValueError, TypeError):
                        errors.append(f"Parameter {param} must be a {config['type']}")
                        continue
                    
                    # Range validation
                    if 'min' in config and value < config['min']:
                        errors.append(f"Parameter {param} ({value}) is below minimum ({config['min']})")
                    if 'max' in config and value > config['max']:
                        errors.append(f"Parameter {param} ({value}) is above maximum ({config['max']})")
            
            # Logical validations
            try:
                nspan = int(params.get('NSPAN', 1))
                span1 = float(params.get('SPAN1', 30))
                lbridge = float(params.get('LBRIDGE', 90))
                
                # Check if bridge length matches span configuration
                calculated_length = nspan * span1
                if abs(calculated_length - lbridge) > 0.1:
                    warnings.append(f"Bridge length ({lbridge}m) doesn't match spans ({nspan} × {span1}m = {calculated_length}m)")
                
                # Check deck levels
                rtl = float(params.get('RTL', 105))
                datum = float(params.get('DATUM', 100))
                if rtl <= datum:
                    errors.append("Riding surface level (RTL) must be above datum level")
                
                # Check pier levels
                if nspan > 1:
                    capt = float(params.get('CAPT', 104))
                    capb = float(params.get('CAPB', 102))
                    futrl = float(params.get('FUTRL', 98))
                    
                    if capt <= capb:
                        errors.append("Pier cap top level must be above bottom level")
                    if capb <= futrl:
                        errors.append("Pier cap bottom level must be above foundation level")
                    if capt >= rtl:
                        warnings.append("Pier cap top level is above or equal to riding surface level")
                
            except (ValueError, TypeError, KeyError) as e:
                errors.append(f"Error in logical validation: {e}")
            
            result = {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
            if warnings:
                logger.warning(f"Parameter validation warnings: {warnings}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating parameters: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def export_parameters(self, params, filename=None):
        """Export parameters to Excel file"""
        try:
            data = []
            for param, value in params.items():
                config = self.parameter_definitions.get(param, {})
                data.append({
                    'Parameter': param,
                    'Value': value,
                    'Description': config.get('description', ''),
                    'Type': config.get('type', ''),
                    'Min': config.get('min', ''),
                    'Max': config.get('max', ''),
                    'Units': self._get_units(config.get('description', ''))
                })
            
            df = pd.DataFrame(data)
            
            if filename:
                df.to_excel(filename, index=False)
                logger.info(f"Parameters exported to {filename}")
            else:
                # Return BytesIO buffer
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Bridge_Parameters')
                return buffer.getvalue()
                
        except Exception as e:
            logger.error(f"Error exporting parameters: {e}")
            raise
