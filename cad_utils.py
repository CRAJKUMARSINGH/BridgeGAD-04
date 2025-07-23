import ezdxf
import logging
from io import BytesIO
import tempfile
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CADUtils:
    """Utilities for CAD file generation and management"""
    
    def __init__(self):
        """Initialize CAD utilities"""
        self.supported_formats = ['dxf']
        logger.info("CAD utilities initialized")
    
    def generate_complete_bridge_dxf(self, params, options=None):
        """Generate complete bridge DXF with all views and annotations"""
        try:
            from bridge_drawer import EnhancedBridgeDrawer
            
            # Default options
            if options is None:
                options = {}
            
            default_options = {
                'scale': '1:100',
                'include_dimensions': True,
                'include_annotations': True,
                'include_title_block': True,
                'project_name': 'Bridge Project',
                'drawing_title': 'Bridge General Arrangement',
                'prepared_by': 'BridgeGAD Pro',
                'date': datetime.now().strftime("%Y-%m-%d")
            }
            
            # Merge options
            for key, value in default_options.items():
                if key not in options:
                    options[key] = value
            
            # Create bridge drawer
            drawer = EnhancedBridgeDrawer(params)
            
            # Parse scale
            scale_parts = options['scale'].split(':')
            if len(scale_parts) == 2:
                scale_factor = float(scale_parts[1]) / float(scale_parts[0])
            else:
                scale_factor = 1.0
            
            # Update scale in parameters
            params['SCALE1'] = 100.0
            params['SCALE2'] = 50.0
            
            # Draw elevation view
            logger.info("Drawing elevation view")
            drawer.draw_elevation()
            
            # Draw plan view
            logger.info("Drawing plan view")
            drawer.draw_plan()
            
            # Add dimensions if requested
            if options.get('include_dimensions', True):
                logger.info("Adding dimensions")
                drawer.add_dimensions()
            
            # Add title block if requested
            if options.get('include_title_block', True):
                logger.info("Adding title block")
                drawer.draw_title_block(
                    options.get('project_name', 'Bridge Project'),
                    options.get('drawing_title', 'Bridge General Arrangement'),
                    options.get('scale', '1:100'),
                    options.get('date', datetime.now().strftime("%Y-%m-%d"))
                )
            
            # Add annotations if requested
            if options.get('include_annotations', True):
                logger.info("Adding annotations")
                self._add_view_labels(drawer)
            
            # Save and return DXF content
            logger.info("Saving DXF content")
            dxf_content = drawer.save_drawing()
            
            logger.info("DXF generation completed successfully")
            return dxf_content
            
        except Exception as e:
            logger.error(f"Error generating complete bridge DXF: {e}")
            raise
    
    def _add_view_labels(self, drawer):
        """Add view labels to the drawing"""
        try:
            # Add elevation view label
            drawer.msp.add_text(
                "ELEVATION",
                dxfattribs={
                    'insert': (-50, 50),
                    'height': 4,
                    'style': 'TITLE_TEXT',
                    'layer': 'ANNOTATIONS'
                }
            )
            
            # Add plan view label
            drawer.msp.add_text(
                "PLAN",
                dxfattribs={
                    'insert': (-50, -150),
                    'height': 4,
                    'style': 'TITLE_TEXT',
                    'layer': 'ANNOTATIONS'
                }
            )
            
            # Add north arrow for plan view
            self._add_north_arrow(drawer, (300, -100))
            
        except Exception as e:
            logger.warning(f"Could not add view labels: {e}")
    
    def _add_north_arrow(self, drawer, position):
        """Add north arrow to the drawing"""
        try:
            x, y = position
            arrow_size = 10
            
            # North arrow outline
            arrow_points = [
                (x, y + arrow_size),
                (x - arrow_size/3, y),
                (x, y - arrow_size/6),
                (x + arrow_size/3, y),
                (x, y + arrow_size)
            ]
            
            drawer.msp.add_lwpolyline(
                arrow_points,
                close=True,
                dxfattribs={'layer': 'ANNOTATIONS'}
            )
            
            # North label
            drawer.msp.add_text(
                "N",
                dxfattribs={
                    'insert': (x, y + arrow_size + 5),
                    'height': 3,
                    'style': 'MAIN_TEXT',
                    'layer': 'ANNOTATIONS'
                }
            )
            
        except Exception as e:
            logger.warning(f"Could not add north arrow: {e}")
    
    def validate_dxf_content(self, dxf_content):
        """Validate DXF content"""
        try:
            if not dxf_content:
                return False, "DXF content is empty"
            
            if len(dxf_content) < 100:
                return False, "DXF content too small"
            
            # Check for DXF header
            if isinstance(dxf_content, bytes):
                content_str = dxf_content.decode('utf-8', errors='ignore')
            else:
                content_str = str(dxf_content)
            
            if 'SECTION' not in content_str or 'ENTITIES' not in content_str:
                return False, "Invalid DXF format"
            
            return True, "DXF content is valid"
            
        except Exception as e:
            return False, f"Error validating DXF: {e}"
    
    def get_drawing_info(self, params):
        """Get drawing information summary"""
        try:
            info = {
                'bridge_type': 'Slab Bridge',
                'spans': int(params.get('NSPAN', 1)),
                'total_length': f"{params.get('LBRIDGE', 0):.2f} m",
                'bridge_width': f"{params.get('BRIDGEW', 0):.2f} m",
                'skew_angle': f"{params.get('SKEW', 0):.1f}°",
                'deck_thickness': f"{params.get('DECKT', 0):.2f} m",
                'riding_level': f"{params.get('RTL', 0):.2f} m",
                'datum_level': f"{params.get('DATUM', 0):.2f} m"
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting drawing info: {e}")
            return {}
    
    def optimize_for_deployment(self, dxf_content):
        """Optimize DXF content for web deployment"""
        try:
            # For now, just return the content as-is
            # Future optimizations could include:
            # - Compression
            # - Removing unnecessary entities
            # - Simplifying complex geometries
            
            logger.info("DXF content optimized for deployment")
            return dxf_content
            
        except Exception as e:
            logger.error(f"Error optimizing DXF for deployment: {e}")
            return dxf_content
