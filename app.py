import streamlit as st
import pandas as pd
from family_tree import FamilyTree
from visualization import create_tree_visualization, create_list_view
from data_processor import process_csv_data, validate_csv_structure

def main():
    st.set_page_config(
        page_title="Family Tree Maker",
        page_icon="🌳",
        layout="wide"
    )
    
    st.title("🌳 Family Tree Maker")
    st.markdown("Upload a CSV file with family data to create interactive family trees and structured lists.")
    
    # Initialize session state
    if 'family_tree' not in st.session_state:
        st.session_state.family_tree = None
    if 'df' not in st.session_state:
        st.session_state.df = None
    
    # Sidebar for file upload and controls
    with st.sidebar:
        st.header("📁 Data Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type="csv",
            help="Upload a CSV file with columns: name, parent, birth_date, gender, etc."
        )
        
        if uploaded_file is not None:
            try:
                # Read and process CSV
                df = pd.read_csv(uploaded_file)
                
                # Validate CSV structure
                validation_result = validate_csv_structure(df)
                if not validation_result['valid']:
                    st.error(f"Invalid CSV structure: {validation_result['message']}")
                    st.stop()
                
                # Process the data
                processed_data = process_csv_data(df)
                
                # Create family tree
                family_tree = FamilyTree()
                family_tree.build_from_data(processed_data)
                
                # Store in session state
                st.session_state.family_tree = family_tree
                st.session_state.df = df
                
                st.success(f"✅ Loaded {len(df)} family members successfully!")
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.stop()
        
        # Display CSV format instructions
        st.header("📋 CSV Format")
        st.markdown("""
        **Required columns:**
        - `name`: Full name of the person
        - `parent`: Name of parent (empty for root ancestors)
        
        **Optional columns:**
        - `birth_date`: Birth date (YYYY-MM-DD)
        - `death_date`: Death date (YYYY-MM-DD)
        - `gender`: Gender (M/F/Other)
        - `spouse`: Name of spouse
        - `occupation`: Occupation
        - `notes`: Additional notes
        """)
        
        # Sample CSV download
        sample_data = pd.DataFrame({
            'name': ['John Smith', 'Mary Smith', 'Robert Smith', 'Lisa Johnson'],
            'parent': ['', '', 'John Smith', 'Mary Smith'],
            'birth_date': ['1950-01-15', '1952-03-20', '1975-07-10', '1978-11-05'],
            'gender': ['M', 'F', 'M', 'F'],
            'spouse': ['Mary Smith', 'John Smith', '', ''],
            'occupation': ['Engineer', 'Teacher', 'Doctor', 'Artist']
        })
        
        csv_sample = sample_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Sample CSV",
            data=csv_sample,
            file_name="family_tree_sample.csv",
            mime="text/csv"
        )
    
    # Main content area
    if st.session_state.family_tree is not None:
        # View selection tabs
        tab1, tab2 = st.tabs(["🌳 Tree View", "📋 List View"])
        
        with tab1:
            st.header("Interactive Family Tree")
            
            # Search functionality
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input(
                    "🔍 Search family members",
                    placeholder="Enter name to search..."
                )
            with col2:
                highlight_search = st.checkbox("Highlight in tree", value=True)
            
            # Tree visualization options
            with st.expander("🎨 Visualization Options"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    layout_type = st.selectbox(
                        "Layout Type",
                        ["hierarchical", "circular", "spring"],
                        index=0
                    )
                with col2:
                    show_dates = st.checkbox("Show birth dates", value=True)
                with col3:
                    color_by_gender = st.checkbox("Color by gender", value=True)
            
            # Create and display tree visualization
            try:
                fig = create_tree_visualization(
                    st.session_state.family_tree,
                    layout_type=layout_type,
                    show_dates=show_dates,
                    color_by_gender=color_by_gender,
                    search_term=search_term if search_term else None,
                    highlight_search=highlight_search
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating tree visualization: {str(e)}")
        
        with tab2:
            st.header("Family Members List")
            
            # List view options
            col1, col2, col3 = st.columns(3)
            with col1:
                search_list = st.text_input(
                    "🔍 Filter list",
                    placeholder="Search in list..."
                )
            with col2:
                sort_by = st.selectbox(
                    "Sort by",
                    ["name", "birth_date", "generation"],
                    index=0
                )
            with col3:
                sort_order = st.selectbox(
                    "Order",
                    ["ascending", "descending"],
                    index=0
                )
            
            # Create and display list view
            try:
                list_view = create_list_view(
                    st.session_state.family_tree,
                    st.session_state.df if st.session_state.df is not None else pd.DataFrame(),
                    search_term=search_list,
                    sort_by=sort_by,
                    sort_order=sort_order
                )
                st.dataframe(list_view, use_container_width=True)
                
                # Statistics
                st.subheader("📊 Family Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                total_members = len(st.session_state.df) if st.session_state.df is not None else 0
                generations = st.session_state.family_tree.get_generation_count()
                avg_age = st.session_state.family_tree.get_average_age()
                living_members = st.session_state.family_tree.get_living_count()
                
                col1.metric("Total Members", total_members)
                col2.metric("Generations", generations)
                col3.metric("Average Age", f"{avg_age:.1f}" if avg_age else "N/A")
                col4.metric("Living Members", living_members)
                
            except Exception as e:
                st.error(f"Error creating list view: {str(e)}")
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to Family Tree Maker! 👨‍👩‍👧‍👦
        
        This application helps you create and visualize family trees from CSV data.
        
        ### Getting Started:
        1. **Upload a CSV file** using the sidebar
        2. **View your family tree** in the interactive tree visualization
        3. **Browse family members** in the structured list view
        4. **Search and filter** to find specific family members
        
        ### Features:
        - 🌳 **Interactive Tree Visualization** - Explore family relationships visually
        - 📋 **Detailed List View** - See all family information in a table
        - 🔍 **Search Functionality** - Find family members quickly
        - 📊 **Family Statistics** - Get insights about your family data
        - 🎨 **Customizable Views** - Adjust layouts and display options
        
        **Start by uploading your family data CSV file in the sidebar!**
        """)

if __name__ == "__main__":
    main()
