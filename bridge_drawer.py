import ezdxf
import numpy as np
from math import tan, radians
from io import BytesIO
import tempfile
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedBridgeDrawer:
    """Enhanced bridge drawing class with improved error handling and deployment compatibility"""
    
    def __init__(self, params):
        """Initialize the bridge drawer with parameters"""
        self.params = params
        self.doc = None
        self.msp = None
        self._initialize_drawing()
    
    def _initialize_drawing(self):
        """Initialize the DXF document and model space"""
        try:
            self.doc = ezdxf.new(dxfversion="R2010", setup=True)
            self.msp = self.doc.modelspace()
            self.setup_layers()
            self.setup_styles()
            self.setup_dimension_style()
            logger.info("Drawing initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize drawing: {e}")
            raise
    
    def setup_layers(self):
        """Set up drawing layers with colors and descriptions"""
        layers = [
            ("STRUCTURE", 1, "Main structural elements"),
            ("DIMENSIONS", 6, "Dimension lines and text"),
            ("ANNOTATIONS", 3, "Text and labels"),
            ("CENTERLINES", 4, "Center lines"),
            ("HATCHING", 9, "Section hatching"),
            ("DETAILS", 2, "Detail elements"),
            ("GRID", 8, "Grid lines and axes")
        ]
        
        for name, color, description in layers:
            try:
                layer = self.doc.layers.new(name=name)
                layer.dxf.color = color
                layer.description = description
            except Exception as e:
                logger.warning(f"Could not create layer {name}: {e}")
    
    def setup_styles(self):
        """Set up text styles"""
        try:
            self.doc.styles.new("MAIN_TEXT", dxfattribs={
                'font': 'arial.ttf',
                'height': 2.5,
                'width': 0.8
            })
            
            self.doc.styles.new("TITLE_TEXT", dxfattribs={
                'font': 'arial.ttf',
                'height': 5.0,
                'width': 1.0
            })
        except Exception as e:
            logger.warning(f"Could not create text styles: {e}")
    
    def setup_dimension_style(self):
        """Set up dimension style"""
        try:
            dimstyle = self.doc.dimstyles.new('PROFESSIONAL')
            dimstyle.dxf.dimasz = 2.0  # Arrow size
            dimstyle.dxf.dimtxt = 2.5  # Text height
            dimstyle.dxf.dimexe = 1.0  # Extension line extension
            dimstyle.dxf.dimexo = 0.6  # Extension line offset
            dimstyle.dxf.dimgap = 0.6  # Gap between dimension line and text
            dimstyle.dxf.dimtxsty = "MAIN_TEXT"
        except Exception as e:
            logger.warning(f"Could not create dimension style: {e}")
    
    def draw_title_block(self, project_name, drawing_title, scale, date):
        """Draw title block with project information"""
        try:
            title_x, title_y = 200, 20
            title_w, title_h = 180, 60
            
            # Title block border
            self.msp.add_lwpolyline([
                (title_x, title_y),
                (title_x + title_w, title_y),
                (title_x + title_w, title_y + title_h),
                (title_x, title_y + title_h),
                (title_x, title_y)
            ], dxfattribs={'layer': 'STRUCTURE'})
            
            # Drawing title
            self.msp.add_text(
                drawing_title,
                dxfattribs={
                    'insert': (title_x + 5, title_y + title_h - 15),
                    'height': 4,
                    'style': 'TITLE_TEXT',
                    'layer': 'ANNOTATIONS'
                }
            )
            
            # Project information
            info_lines = [
                f"Project: {project_name}",
                f"Scale: {scale}",
                f"Date: {date}",
                f"Drawn by: BridgeGAD Pro"
            ]
            
            for i, line in enumerate(info_lines):
                self.msp.add_text(
                    line,
                    dxfattribs={
                        'insert': (title_x + 5, title_y + 30 - i * 8),
                        'height': 2.5,
                        'style': 'MAIN_TEXT',
                        'layer': 'ANNOTATIONS'
                    }
                )
        except Exception as e:
            logger.error(f"Error drawing title block: {e}")
    
    def draw_grid(self, left, right, datum, top, x_incr, y_incr, scale):
        """Draw grid lines for reference"""
        try:
            # Horizontal grid lines (levels)
            current_level = datum
            while current_level <= top:
                y_pos = self.vpos(current_level, datum, scale)
                self.msp.add_line(
                    (left, y_pos),
                    (right, y_pos),
                    dxfattribs={'layer': 'GRID', 'linetype': 'DASHED'}
                )
                
                # Level annotation
                self.msp.add_text(
                    f"RL {current_level:.2f}",
                    dxfattribs={
                        'insert': (left - 30, y_pos - 2),
                        'height': 2.0,
                        'style': 'MAIN_TEXT',
                        'layer': 'ANNOTATIONS'
                    }
                )
                current_level += y_incr
            
            # Vertical grid lines (chainage)
            current_ch = left
            while current_ch <= right:
                x_pos = self.hpos(current_ch, left, scale)
                self.msp.add_line(
                    (x_pos, datum),
                    (x_pos, self.vpos(top, datum, scale)),
                    dxfattribs={'layer': 'GRID', 'linetype': 'DASHED'}
                )
                
                # Chainage annotation
                self.msp.add_text(
                    f"Ch {current_ch:.0f}",
                    dxfattribs={
                        'insert': (x_pos - 5, datum - 15),
                        'height': 2.0,
                        'style': 'MAIN_TEXT',
                        'layer': 'ANNOTATIONS',
                        'rotation': 90
                    }
                )
                current_ch += x_incr
        except Exception as e:
            logger.error(f"Error drawing grid: {e}")
    
    def draw_elevation(self):
        """Draw bridge elevation view"""
        try:
            # Get parameters with defaults
            abtl = float(self.params.get('ABTL', 0))
            span1 = float(self.params.get('SPAN1', 30))
            nspan = int(self.params.get('NSPAN', 3))
            rtl = float(self.params.get('RTL', 105))
            deck_thickness = float(self.params.get('DECKT', 1.2))
            scale = float(self.params.get('SCALE1', 100)) / float(self.params.get('SCALE2', 50))
            datum = float(self.params.get('DATUM', 100))
            
            # Draw deck for each span
            for i in range(nspan):
                x1 = self.hpos(abtl + i * span1, abtl, scale)
                x2 = self.hpos(abtl + (i + 1) * span1, abtl, scale)
                y1 = self.vpos(rtl, datum, scale)
                y2 = self.vpos(rtl - deck_thickness, datum, scale)
                
                # Deck outline
                deck_points = [
                    (x1, y1),
                    (x2, y1),
                    (x2, y2),
                    (x1, y2)
                ]
                
                self.msp.add_lwpolyline(
                    deck_points,
                    close=True,
                    dxfattribs={'layer': 'STRUCTURE', 'color': 1}
                )
                
                # Add hatching to deck
                try:
                    hatch = self.msp.add_hatch(color=8, dxfattribs={'layer': 'HATCHING'})
                    hatch.paths.add_polyline_path(deck_points, is_closed=True)
                    hatch.set_pattern_fill("ANSI31", scale=0.5)
                except Exception as e:
                    logger.warning(f"Could not add hatching to deck: {e}")
            
            # Draw other bridge components
            self.draw_piers()
            self.draw_abutments()
            self.draw_approach_slabs()
            
        except Exception as e:
            logger.error(f"Error drawing elevation: {e}")
            raise
    
    def draw_piers(self):
        """Draw bridge piers"""
        try:
            nspan = int(self.params.get('NSPAN', 3))
            if nspan <= 1:
                return  # No piers needed for single span
            
            # Get pier parameters
            abtl = float(self.params.get('ABTL', 0))
            span1 = float(self.params.get('SPAN1', 30))
            capt = float(self.params.get('CAPT', 104))
            capb = float(self.params.get('CAPB', 102))
            capw = float(self.params.get('CAPW', 1.2))
            piertw = float(self.params.get('PIERTW', 0.8))
            battr = float(self.params.get('BATTR', 6))
            futrl = float(self.params.get('FUTRL', 98))
            futd = float(self.params.get('FUTD', 1))
            futw = float(self.params.get('FUTW', 2.5))
            scale = float(self.params.get('SCALE1', 100)) / float(self.params.get('SCALE2', 50))
            datum = float(self.params.get('DATUM', 100))
            
            # Draw piers at span joints
            for i in range(1, nspan):
                pier_ch = abtl + i * span1
                x_center = self.hpos(pier_ch, abtl, scale)
                
                # Pier cap
                cap_x1 = x_center - capw * scale / 2
                cap_x2 = x_center + capw * scale / 2
                cap_y1 = self.vpos(capt, datum, scale)
                cap_y2 = self.vpos(capb, datum, scale)
                
                self.msp.add_lwpolyline([
                    (cap_x1, cap_y1),
                    (cap_x2, cap_y1),
                    (cap_x2, cap_y2),
                    (cap_x1, cap_y2),
                    (cap_x1, cap_y1)
                ], dxfattribs={'layer': 'STRUCTURE'})
                
                # Pier shaft (tapered)
                pier_top_half = piertw * scale / 2
                pier_height = capb - futrl - futd
                pier_bottom_half = pier_top_half + pier_height / battr
                
                pier_y1 = cap_y2
                pier_y2 = self.vpos(futrl + futd, datum, scale)
                
                # Left side of pier
                self.msp.add_line(
                    (x_center - pier_top_half, pier_y1),
                    (x_center - pier_bottom_half, pier_y2),
                    dxfattribs={'layer': 'STRUCTURE'}
                )
                
                # Right side of pier
                self.msp.add_line(
                    (x_center + pier_top_half, pier_y1),
                    (x_center + pier_bottom_half, pier_y2),
                    dxfattribs={'layer': 'STRUCTURE'}
                )
                
                # Pier footing
                foot_x1 = x_center - futw * scale / 2
                foot_x2 = x_center + futw * scale / 2
                foot_y1 = pier_y2
                foot_y2 = self.vpos(futrl, datum, scale)
                
                self.msp.add_lwpolyline([
                    (foot_x1, foot_y1),
                    (foot_x2, foot_y1),
                    (foot_x2, foot_y2),
                    (foot_x1, foot_y2),
                    (foot_x1, foot_y1)
                ], dxfattribs={'layer': 'STRUCTURE'})
                
        except Exception as e:
            logger.error(f"Error drawing piers: {e}")
    
    def draw_abutments(self):
        """Draw bridge abutments"""
        try:
            # Get abutment parameters
            abtl = float(self.params.get('ABTL', 0))
            nspan = int(self.params.get('NSPAN', 3))
            span1 = float(self.params.get('SPAN1', 30))
            rtl = float(self.params.get('RTL', 105))
            abut_height = float(self.params.get('ABUT_HEIGHT', 6))
            abut_width = float(self.params.get('ABUT_WIDTH', 1.5))
            foot_length = float(self.params.get('FOOT_LENGTH', 8))
            foot_thick = float(self.params.get('FOOT_THICK', 1.2))
            scale = float(self.params.get('SCALE1', 100)) / float(self.params.get('SCALE2', 50))
            datum = float(self.params.get('DATUM', 100))
            
            # Left abutment stem
            stem_x1 = self.hpos(abtl - abut_width, abtl, scale)
            stem_x2 = self.hpos(abtl, abtl, scale)
            stem_y1 = self.vpos(rtl, datum, scale)
            stem_y2 = self.vpos(rtl - abut_height, datum, scale)
            
            self.msp.add_lwpolyline([
                (stem_x1, stem_y1),
                (stem_x2, stem_y1),
                (stem_x2, stem_y2),
                (stem_x1, stem_y2),
                (stem_x1, stem_y1)
            ], dxfattribs={'layer': 'STRUCTURE'})
            
            # Left abutment footing
            foot_x1 = self.hpos(abtl - abut_width/2 - foot_length/2, abtl, scale)
            foot_x2 = self.hpos(abtl - abut_width/2 + foot_length/2, abtl, scale)
            foot_y1 = self.vpos(rtl - abut_height - foot_thick, datum, scale)
            foot_y2 = self.vpos(rtl - abut_height, datum, scale)
            
            self.msp.add_lwpolyline([
                (foot_x1, foot_y1),
                (foot_x2, foot_y1),
                (foot_x2, foot_y2),
                (foot_x1, foot_y2),
                (foot_x1, foot_y1)
            ], dxfattribs={'layer': 'STRUCTURE'})
            
            # Right abutment
            bridge_length = abtl + nspan * span1
            
            # Right abutment stem
            stem_x1 = self.hpos(bridge_length, abtl, scale)
            stem_x2 = self.hpos(bridge_length + abut_width, abtl, scale)
            
            self.msp.add_lwpolyline([
                (stem_x1, stem_y1),
                (stem_x2, stem_y1),
                (stem_x2, stem_y2),
                (stem_x1, stem_y2),
                (stem_x1, stem_y1)
            ], dxfattribs={'layer': 'STRUCTURE'})
            
            # Right abutment footing
            foot_x1 = self.hpos(bridge_length + abut_width/2 - foot_length/2, abtl, scale)
            foot_x2 = self.hpos(bridge_length + abut_width/2 + foot_length/2, abtl, scale)
            
            self.msp.add_lwpolyline([
                (foot_x1, foot_y1),
                (foot_x2, foot_y1),
                (foot_x2, foot_y2),
                (foot_x1, foot_y2),
                (foot_x1, foot_y1)
            ], dxfattribs={'layer': 'STRUCTURE'})
            
        except Exception as e:
            logger.error(f"Error drawing abutments: {e}")
    
    def draw_approach_slabs(self):
        """Draw approach slabs"""
        try:
            # Get approach slab parameters
            abtl = float(self.params.get('ABTL', 0))
            nspan = int(self.params.get('NSPAN', 3))
            span1 = float(self.params.get('SPAN1', 30))
            rtl = float(self.params.get('RTL', 105))
            laslab = float(self.params.get('APPR_LENGTH', 8))
            apthk = float(self.params.get('APPR_THICK', 0.3))
            scale = float(self.params.get('SCALE1', 100)) / float(self.params.get('SCALE2', 50))
            datum = float(self.params.get('DATUM', 100))
            
            bridge_length = abtl + nspan * span1
            
            # Define approach slab coordinates
            left_start = self.hpos(abtl - laslab, abtl, scale)
            left_end = self.hpos(abtl, abtl, scale)
            right_start = self.hpos(bridge_length, abtl, scale)
            right_end = self.hpos(bridge_length + laslab, abtl, scale)
            
            slab_top = self.vpos(rtl, datum, scale)
            slab_bottom = self.vpos(rtl - apthk, datum, scale)
            
            # Draw left and right approach slabs
            for start_x, end_x in [(left_start, left_end), (right_start, right_end)]:
                self.msp.add_lwpolyline([
                    (start_x, slab_top),
                    (end_x, slab_top),
                    (end_x, slab_bottom),
                    (start_x, slab_bottom),
                    (start_x, slab_top)
                ], dxfattribs={'layer': 'STRUCTURE'})
                
        except Exception as e:
            logger.error(f"Error drawing approach slabs: {e}")
    
    def draw_plan(self):
        """Draw bridge plan view"""
        try:
            # Get plan parameters
            bridge_length = float(self.params.get('LBRIDGE', 100))
            bridge_width = float(self.params.get('BRIDGEW', 12))
            nspan = int(self.params.get('NSPAN', 3))
            span1 = float(self.params.get('SPAN1', 30))
            skew_angle = float(self.params.get('SKEW', 0))
            scale = float(self.params.get('SCALE1', 100)) / float(self.params.get('SCALE2', 50))
            abtl = float(self.params.get('ABTL', 0))
            
            # Offset plan view vertically to avoid overlap with elevation
            PLAN_OFFSET_Y = -100
            
            # Draw bridge deck outline
            if skew_angle != 0:
                # Skewed bridge
                skew_offset = bridge_width * tan(radians(skew_angle))
                deck_corners = [
                    (self.hpos(0, abtl, scale), -bridge_width/2 * scale + PLAN_OFFSET_Y),
                    (self.hpos(bridge_length, abtl, scale), (-bridge_width/2 + skew_offset) * scale + PLAN_OFFSET_Y),
                    (self.hpos(bridge_length, abtl, scale), (bridge_width/2 + skew_offset) * scale + PLAN_OFFSET_Y),
                    (self.hpos(0, abtl, scale), bridge_width/2 * scale + PLAN_OFFSET_Y)
                ]
                
                self.msp.add_lwpolyline(
                    deck_corners,
                    close=True,
                    dxfattribs={'layer': 'STRUCTURE', 'color': 1}
                )
            else:
                # Square bridge
                x1 = self.hpos(0, abtl, scale)
                y1 = -bridge_width/2 * scale + PLAN_OFFSET_Y
                
                self.msp.add_lwpolyline([
                    (x1, y1),
                    (x1 + bridge_length * scale, y1),
                    (x1 + bridge_length * scale, y1 + bridge_width * scale),
                    (x1, y1 + bridge_width * scale),
                    (x1, y1)
                ], dxfattribs={'layer': 'STRUCTURE', 'color': 1})
            
            # Draw centerline
            self.msp.add_line(
                (self.hpos(0, abtl, scale), PLAN_OFFSET_Y),
                (self.hpos(bridge_length, abtl, scale), PLAN_OFFSET_Y),
                dxfattribs={'layer': 'CENTERLINES', 'linetype': 'CENTER', 'color': 4}
            )
            
            # Draw piers in plan view
            if nspan > 1:
                pier_locations = [abtl + i * span1 for i in range(1, nspan)]
                pier_width = float(self.params.get('PIER_WIDTH', 2.0))
                pier_length = bridge_width + 1
                
                for i, pier_x in enumerate(pier_locations):
                    x_center = self.hpos(pier_x, abtl, scale)
                    
                    self.msp.add_lwpolyline([
                        (x_center - pier_width/2 * scale, -pier_length/2 * scale + PLAN_OFFSET_Y),
                        (x_center + pier_width/2 * scale, -pier_length/2 * scale + PLAN_OFFSET_Y),
                        (x_center + pier_width/2 * scale, pier_length/2 * scale + PLAN_OFFSET_Y),
                        (x_center - pier_width/2 * scale, pier_length/2 * scale + PLAN_OFFSET_Y),
                        (x_center - pier_width/2 * scale, -pier_length/2 * scale + PLAN_OFFSET_Y)
                    ], dxfattribs={'layer': 'STRUCTURE'})
                    
                    # Pier label
                    self.msp.add_text(
                        f'P{i+1}',
                        dxfattribs={
                            'insert': (x_center, PLAN_OFFSET_Y),
                            'height': 2.5,
                            'style': 'MAIN_TEXT',
                            'layer': 'ANNOTATIONS'
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error drawing plan: {e}")
    
    def add_dimensions(self):
        """Add dimensions to the drawing"""
        try:
            # Get dimension parameters
            nspan = int(self.params.get('NSPAN', 3))
            abtl = float(self.params.get('ABTL', 0))
            span1 = float(self.params.get('SPAN1', 30))
            bridge_length = float(self.params.get('LBRIDGE', 100))
            rtl = float(self.params.get('RTL', 105))
            deck_thickness = float(self.params.get('DECKT', 1.2))
            abut_height = float(self.params.get('ABUT_HEIGHT', 6))
            scale = float(self.params.get('SCALE1', 100)) / float(self.params.get('SCALE2', 50))
            datum = float(self.params.get('DATUM', 100))
            
            # Span dimensions
            dim_y = self.vpos(datum - 10, datum, scale)
            
            for i in range(nspan):
                x1 = self.hpos(abtl + i * span1, abtl, scale)
                x2 = self.hpos(abtl + (i + 1) * span1, abtl, scale)
                
                try:
                    dim = self.msp.add_linear_dim(
                        base=(x1, dim_y),
                        p1=(x1, dim_y + 5),
                        p2=(x2, dim_y + 5),
                        dimstyle="PROFESSIONAL",
                        dxfattribs={'layer': 'DIMENSIONS'}
                    )
                    dim.render()
                except Exception as e:
                    logger.warning(f"Could not add span dimension {i}: {e}")
            
            # Vertical dimensions
            dim_x = self.hpos(bridge_length + 15, abtl, scale)
            
            # Deck thickness dimension
            try:
                self.msp.add_linear_dim(
                    base=(dim_x, self.vpos(rtl - deck_thickness, datum, scale)),
                    p1=(dim_x, self.vpos(rtl - deck_thickness, datum, scale)),
                    p2=(dim_x, self.vpos(rtl, datum, scale)),
                    dimstyle="PROFESSIONAL",
                    dxfattribs={'layer': 'DIMENSIONS'}
                ).render()
            except Exception as e:
                logger.warning(f"Could not add deck thickness dimension: {e}")
            
            # Abutment height dimension
            try:
                self.msp.add_linear_dim(
                    base=(dim_x + 2, self.vpos(rtl - abut_height, datum, scale)),
                    p1=(dim_x + 2, self.vpos(rtl - abut_height, datum, scale)),
                    p2=(dim_x + 2, self.vpos(rtl, datum, scale)),
                    dimstyle="PROFESSIONAL",
                    dxfattribs={'layer': 'DIMENSIONS'}
                ).render()
            except Exception as e:
                logger.warning(f"Could not add abutment height dimension: {e}")
                
        except Exception as e:
            logger.error(f"Error adding dimensions: {e}")
    
    def hpos(self, chainage, left, scale):
        """Convert chainage to horizontal position"""
        return chainage * scale
    
    def vpos(self, level, datum, scale):
        """Convert level to vertical position"""
        return (level - datum) * scale
    
    def save_drawing(self, output_path=None):
        """Save the drawing to file or BytesIO"""
        try:
            if output_path is None:
                # Save to BytesIO for web deployment
                buffer = BytesIO()
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                try:
                    # Save DXF to temporary file
                    self.doc.saveas(temp_path)
                    
                    # Read temp file into buffer
                    with open(temp_path, 'rb') as f:
                        buffer.write(f.read())
                    
                    buffer.seek(0)
                    return buffer.getvalue()
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"Could not delete temporary file {temp_path}: {e}")
            else:
                # Save directly to file
                self.doc.saveas(output_path)
                logger.info(f"Drawing saved to {output_path}")
                
        except Exception as e:
            logger.error(f"Error saving drawing: {e}")
            raise
