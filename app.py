import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import traceback
import logging
from datetime import datetime
import tempfile
import os

# Import custom modules with error handling
try:
    from bridge_drawer import EnhancedBridgeDrawer
    from parameter_manager import ParameterManager
    from cad_utils import CADUtils
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="BridgeGAD Pro - Professional Bridge Design",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'parameters' not in st.session_state:
    st.session_state.parameters = {}
if 'drawing_generated' not in st.session_state:
    st.session_state.drawing_generated = False

# Custom CSS for professional styling
st.markdown("""
<style>
.main-header {
    font-size: 3.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: bold;
}
.section-header {
    font-size: 1.8rem;
    color: #ff7f0e;
    border-bottom: 3px solid #ff7f0e;
    padding-bottom: 0.8rem;
    margin: 1.5rem 0;
    text-align: center;
    font-weight: bold;
}
.parameter-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    font-size: 1.2rem;
    font-weight: bold;
}
.parameter-card h4 {
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
}
.parameter-card p {
    font-size: 1.6rem;
    margin: 0;
    font-weight: bold;
}
.info-box {
    background-color: #e8f4f8;
    border-left: 5px solid #1f77b4;
    padding: 1.5rem;
    margin: 1.5rem 0;
    text-align: center;
    font-size: 1.3rem;
    font-weight: 500;
}
.success-box {
    background-color: #d4edda;
    border-left: 5px solid #28a745;
    padding: 1.5rem;
    margin: 1.5rem 0;
    text-align: center;
    font-size: 1.3rem;
    font-weight: 500;
}
.error-box {
    background-color: #f8d7da;
    border-left: 5px solid #dc3545;
    padding: 1.5rem;
    margin: 1.5rem 0;
    text-align: center;
    font-size: 1.3rem;
    font-weight: 500;
}
.center-content {
    text-align: center;
}
.large-button {
    font-size: 1.3rem !important;
    padding: 0.8rem 2rem !important;
    font-weight: bold !important;
}
/* Center sidebar headers */
.sidebar .element-container {
    text-align: center;
}
/* Increase input label sizes */
.stTextInput > label {
    font-size: 1.2rem !important;
    font-weight: bold !important;
}
.stSelectbox > label {
    font-size: 1.2rem !important;
    font-weight: bold !important;
}
.stCheckbox > label {
    font-size: 1.1rem !important;
    font-weight: bold !important;
}
.stFileUploader > label {
    font-size: 1.3rem !important;
    font-weight: bold !important;
    text-align: center !important;
}
/* Center main content headers */
h3 {
    text-align: center !important;
    font-size: 1.6rem !important;
    font-weight: bold !important;
}
/* Center getting started content */
.getting-started {
    text-align: center;
    font-size: 1.2rem;
    line-height: 1.6;
}
.getting-started h3 {
    font-size: 1.8rem !important;
    color: #1f77b4;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Title and description
st.markdown('<h1 class="main-header">🏗️ BridgeGAD Pro</h1>', unsafe_allow_html=True)
st.markdown('<div class="info-box">Professional Bridge Design Generator with Industry-Standard CAD Output</div>', unsafe_allow_html=True)

# Sidebar for project settings
with st.sidebar:
    st.markdown('<div class="section-header">📊 Project Settings</div>', unsafe_allow_html=True)
    
    project_name = st.text_input("Project Name", "Slab Bridge Project", key="project_name_input")
    drawing_title = st.text_input("Drawing Title", "Bridge General Arrangement", key="drawing_title_input")
    
    st.markdown('<div class="section-header">⚙️ Drawing Options</div>', unsafe_allow_html=True)
    
    add_dimensions = st.checkbox("Add Dimensions", value=True, key="add_dimensions_checkbox")
    add_annotations = st.checkbox("Add Annotations", value=True, key="add_annotations_checkbox")
    add_title_block = st.checkbox("Add Title Block", value=True, key="add_title_block_checkbox")
    drawing_scale = st.selectbox("Drawing Scale", ["1:100", "1:200", "1:500", "1:1000"], index=0, key="drawing_scale_select")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-header">📁 Upload Bridge Parameters</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose Excel file with bridge parameters",
        type=["xlsx", "xls"],
        help="Upload an Excel file with bridge design parameters",
        key="file_uploader"
    )

with col2:
    st.markdown('<div class="section-header">📋 Sample Template</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="center-content">', unsafe_allow_html=True)
    if st.button("📥 Generate Template", key="generate_template_btn", help="Download Excel template with bridge parameters", use_container_width=True):
        try:
            param_manager = ParameterManager()
            template_df = param_manager.generate_template()
            
            # Create BytesIO buffer for Excel file
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                template_df.to_excel(writer, index=False, sheet_name='Bridge_Parameters')
            buffer.seek(0)
            
            st.download_button(
                label="📥 Download Excel Template",
                data=buffer.getvalue(),
                file_name="bridge_parameters_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_template_btn",
                use_container_width=True,
                help="Click to download the Excel template file"
            )
            st.markdown('<div class="success-box">✅ Template generated successfully!</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error generating template: {str(e)}")
            logger.error(f"Template generation error: {traceback.format_exc()}")

# Process uploaded file
if uploaded_file:
    try:
        param_manager = ParameterManager()
        params = param_manager.load_parameters(uploaded_file)
        
        # Store parameters in session state
        st.session_state.parameters = params
        
        # Validate parameters
        validation_result = param_manager.validate_parameters(params)
        if not validation_result['valid']:
            st.error(f"Parameter validation failed: {', '.join(validation_result['errors'])}")
            st.stop()
        
        # Display parameters in cards
        st.markdown('<div class="section-header">🔧 Bridge Parameters</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f'<div class="parameter-card"><h4>Spans</h4><p>{int(params.get("NSPAN", 0))}</p></div>',
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f'<div class="parameter-card"><h4>Span Length</h4><p>{params.get("SPAN1", 0):.1f} m</p></div>',
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f'<div class="parameter-card"><h4>Bridge Length</h4><p>{params.get("LBRIDGE", 0):.1f} m</p></div>',
                unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                f'<div class="parameter-card"><h4>Skew Angle</h4><p>{params.get("SKEW", 0):.1f}°</p></div>',
                unsafe_allow_html=True
            )
        
        # Editable parameters table
        st.markdown('<div class="section-header">📝 Edit Parameters</div>', unsafe_allow_html=True)
        
        # Create DataFrame for editing
        df = pd.DataFrame({
            'Variable': list(params.keys()),
            'Value': list(params.values()),
            'Description': [param_manager.parameter_definitions.get(k, {}).get('description', 'No description') for k in params.keys()]
        })
        
        edited_df = st.data_editor(
            df,
            column_config={
                "Value": st.column_config.NumberColumn("Value", format="%.3f"),
                "Variable": st.column_config.TextColumn("Variable", disabled=True),
                "Description": st.column_config.TextColumn("Description", disabled=True)
            },
            use_container_width=True,
            height=300,
            key="parameter_editor"
        )
        
        # Generate drawing button
        st.markdown('<div class="center-content">', unsafe_allow_html=True)
        if st.button("🚀 Generate Professional DXF Drawing", type="primary", use_container_width=True, key="generate_drawing_btn", help="Click to generate your bridge CAD drawing"):
            with st.spinner("Creating professional CAD drawing..."):
                try:
                    # Update parameters from edited data
                    updated_params = dict(zip(edited_df['Variable'], edited_df['Value']))
                    
                    # Validate updated parameters
                    validation_result = param_manager.validate_parameters(updated_params)
                    if not validation_result['valid']:
                        st.error(f"Parameter validation failed: {', '.join(validation_result['errors'])}")
                        st.stop()
                    
                    # Initialize CAD utilities and drawer
                    cad_utils = CADUtils()
                    drawer = EnhancedBridgeDrawer(updated_params)
                    
                    # Prepare CAD options
                    cad_options = {
                        'scale': drawing_scale,
                        'include_dimensions': add_dimensions,
                        'include_annotations': add_annotations,
                        'include_title_block': add_title_block,
                        'project_name': project_name,
                        'drawing_title': drawing_title,
                        'prepared_by': 'BridgeGAD Pro',
                        'date': datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Generate DXF content
                    dxf_content = cad_utils.generate_complete_bridge_dxf(updated_params, cad_options)
                    
                    # Mark drawing as generated
                    st.session_state.drawing_generated = True
                    
                    # Success message
                    st.markdown('<div class="success-box">🎉 DXF File Generated Successfully!</div>', unsafe_allow_html=True)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download DXF File",
                        data=dxf_content,
                        file_name=f"{project_name.replace(' ', '_')}_bridge_drawing.dxf",
                        mime="application/dxf",
                        key="download_dxf_btn",
                        use_container_width=True,
                        help="Download your generated bridge drawing in DXF format"
                    )
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Display drawing information
                    with st.expander("📊 Drawing Information"):
                        info_df = pd.DataFrame({
                            'Property': ['Project Name', 'Drawing Title', 'Scale', 'Date Generated', 'Number of Spans', 'Total Bridge Length'],
                            'Value': [
                                project_name,
                                drawing_title,
                                drawing_scale,
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                int(updated_params.get('NSPAN', 0)),
                                f"{updated_params.get('LBRIDGE', 0):.2f} m"
                            ]
                        })
                        st.dataframe(info_df, use_container_width=True)
                    
                except Exception as e:
                    st.markdown(f'<div class="error-box">❌ Failed to generate DXF file: {str(e)}</div>', unsafe_allow_html=True)
                    logger.error(f"DXF generation error: {traceback.format_exc()}")
                    
                    # Show detailed error in expander for debugging
                    with st.expander("🔍 Error Details (for debugging)"):
                        st.code(traceback.format_exc())

    except Exception as e:
        st.markdown(f'<div class="error-box">❌ Error processing file: {str(e)}</div>', unsafe_allow_html=True)
        logger.error(f"File processing error: {traceback.format_exc()}")
        
        # Show detailed error in expander for debugging
        with st.expander("🔍 Error Details (for debugging)"):
            st.code(traceback.format_exc())

else:
    # Show instructions when no file is uploaded
    st.markdown('<div class="section-header">📖 Getting Started</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="getting-started">', unsafe_allow_html=True)
    st.markdown("""
    ### How to use BridgeGAD Pro:
    
    **1. Download Template** - Click the "Generate Template" button to download an Excel template
    
    **2. Fill Parameters** - Open the template and fill in your bridge design parameters
    
    **3. Upload File** - Upload your completed Excel file using the file uploader
    
    **4. Review & Edit** - Review the loaded parameters and make any necessary adjustments
    
    **5. Configure Drawing** - Set your drawing options in the sidebar
    
    **6. Generate DXF** - Click "Generate Professional DXF Drawing" to create your CAD file
    
    ### Supported Parameters:
    - **Bridge geometry** (spans up to 51, length, width)
    - **Structural elements** (deck, piers, abutments)
    - **Levels and elevations**
    - **Foundation details**
    - **Drawing scale and annotations**
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown('<div class="center-content" style="font-size: 1.2rem; font-weight: bold; color: #1f77b4; margin-top: 2rem; margin-bottom: 1rem;">**BridgeGAD Pro** - Professional Bridge Design Application | Developed with Streamlit</div>', unsafe_allow_html=True)
