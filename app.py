import streamlit as st
import pandas as pd
from family_tree import FamilyTree, FamilyMember
from visualization import create_tree_visualization, create_list_view
from data_processor import process_csv_data, validate_csv_structure
import copy

def apply_tree_filters(family_tree, generation_range=None, birth_year_range=None, selected_branch=None):
    """Apply filters to family tree and return filtered version."""
    
    # Create a copy of the family tree to avoid modifying the original
    filtered_tree = FamilyTree()
    
    # Get members to include based on filters
    members_to_include = set()
    
    # Precompute branch filter if needed
    branch_allowed_members = None
    if selected_branch is not None:
        ancestors = family_tree.get_ancestors(selected_branch)
        descendants = family_tree.get_descendants(selected_branch)
        ancestor_names = {a.name for a in ancestors}
        descendant_names = {d.name for d in descendants}
        branch_allowed_members = ancestor_names | descendant_names | {selected_branch}
    
    # Start with all members
    for member in family_tree.members.values():
        include_member = True
        
        # Apply generation filter
        if generation_range is not None:
            if not (generation_range[0] <= member.generation <= generation_range[1]):
                include_member = False
        
        # Apply birth year filter
        if include_member and birth_year_range is not None and member.birth_date:
            try:
                birth_year = pd.to_datetime(member.birth_date).year
                if not (birth_year_range[0] <= birth_year <= birth_year_range[1]):
                    include_member = False
            except:
                # If birth date parsing fails, exclude
                include_member = False
        
        # Apply branch filter (precomputed allowed members)
        if include_member and branch_allowed_members is not None:
            if member.name not in branch_allowed_members:
                include_member = False
        
        if include_member:
            members_to_include.add(member.name)
    
    # Build filtered tree with included members
    for member_name in members_to_include:
        original_member = family_tree.members[member_name]
        
        # Create a copy of the member with all extended fields including two-parent support
        filtered_member = FamilyMember(
            name=original_member.name,
            parent=original_member.parent if original_member.parent in members_to_include else None,
            mother=original_member.mother if original_member.mother in members_to_include else None,
            father=original_member.father if original_member.father in members_to_include else None,
            generation=original_member.generation,
            manual_generation=getattr(original_member, 'manual_generation', False),
            birth_date=original_member.birth_date,
            death_date=original_member.death_date,
            gender=original_member.gender,
            spouse=original_member.spouse,
            occupation=original_member.occupation,
            notes=original_member.notes,
            relationship_type=getattr(original_member, 'relationship_type', 'biological'),
            birth_place=getattr(original_member, 'birth_place', None),
            death_place=getattr(original_member, 'death_place', None),
            burial_place=getattr(original_member, 'burial_place', None),
            marriage_date=getattr(original_member, 'marriage_date', None),
            divorce_date=getattr(original_member, 'divorce_date', None),
            education=getattr(original_member, 'education', None),
            military_service=getattr(original_member, 'military_service', None),
            religion=getattr(original_member, 'religion', None)
        )
        
        filtered_tree.add_member(filtered_member)
    
    # Second pass: establish proper parent-child relationships and rebuild graph for two-parent support
    for member_name in members_to_include:
        member = filtered_tree.members[member_name]
        
        # Handle mother relationship
        if member.mother and member.mother in filtered_tree.members:
            mother = filtered_tree.members[member.mother]
            if member not in mother.children:
                mother.add_child(member)
            if not filtered_tree.graph.has_edge(member.mother, member.name):
                filtered_tree.graph.add_edge(member.mother, member.name)
        
        # Handle father relationship
        if member.father and member.father in filtered_tree.members:
            father = filtered_tree.members[member.father]
            if member not in father.children:
                father.add_child(member)
            if not filtered_tree.graph.has_edge(member.father, member.name):
                filtered_tree.graph.add_edge(member.father, member.name)
        
        # Handle legacy single parent relationship
        if member.parent and member.parent in filtered_tree.members:
            parent = filtered_tree.members[member.parent]
            if member not in parent.children:
                parent.add_child(member)
            if not filtered_tree.graph.has_edge(member.parent, member.name):
                filtered_tree.graph.add_edge(member.parent, member.name)
    
    # Recalculate generations for filtered tree
    filtered_tree._calculate_generations()
    
    return filtered_tree

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
    if 'modified_csv_data' not in st.session_state:
        st.session_state.modified_csv_data = None
    
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
                # Initialize the modified CSV data copy
                st.session_state.modified_csv_data = family_tree.to_dataframe()
                
                st.success(f"✅ Loaded {len(df)} family members successfully!")
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.stop()
        
        # Display CSV format instructions
        st.header("📋 CSV Format")
        st.markdown("""
        **Required columns:**
        - `name`: Full name of the person
        
        **Parent columns:**
        - `mother`: Name of mother (empty for root ancestors)
        - `father`: Name of father (empty for root ancestors)
        
        **Optional columns:**
        - `birth_date`: Birth date (YYYY-MM-DD)
        - `death_date`: Death date (YYYY-MM-DD)
        - `gender`: Gender (M/F/Other)
        - `spouse`: Name of spouse
        - `occupation`: Occupation
        - `generation`: Generation number (0, 1, 2, etc.)
        - `notes`: Additional notes
        """)
        
        # Sample CSV download with two-parent structure
        sample_data = pd.DataFrame({
            'name': ['John Smith', 'Mary Smith', 'Robert Smith', 'Lisa Johnson'],
            'mother': ['', '', 'Mary Smith', 'Mary Smith'],
            'father': ['', '', 'John Smith', 'John Smith'],
            'birth_date': ['1950-01-15', '1952-03-20', '1975-07-10', '1978-11-05'],
            'gender': ['M', 'F', 'M', 'F'],
            'spouse': ['Mary Smith', 'John Smith', '', ''],
            'occupation': ['Engineer', 'Teacher', 'Doctor', 'Artist'],
            'generation': [0, 0, 1, 1]
        })
        
        csv_sample = sample_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Sample CSV",
            data=csv_sample,
            file_name="family_tree_sample.csv",
            mime="text/csv"
        )
        
        # Export current family tree
        if st.session_state.family_tree is not None:
            st.header("📤 Export Data")
            
            # Export current family tree data
            current_df = st.session_state.family_tree.to_dataframe()
            
            # Prepare export data (include all available columns, remove only internal ones)
            columns_to_exclude = ['age', 'living', 'generation', 'children_count']
            export_columns = [col for col in current_df.columns if col not in columns_to_exclude]
            export_df = current_df[export_columns].copy()
            export_df = export_df.fillna('')  # Replace None with empty strings for CSV
            
            export_csv = export_df.to_csv(index=False)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📤 Export Family Tree CSV",
                    data=export_csv,
                    file_name=f"family_tree_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    help="Download the current family tree data as a CSV file"
                )
            
            with col2:
                # Export as JSON option
                export_json = export_df.to_json(orient='records', indent=2)
                st.download_button(
                    label="📤 Export Family Tree JSON",
                    data=export_json,
                    file_name=f"family_tree_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    help="Download the current family tree data as a JSON file"
                )
    
    # Main content area
    if st.session_state.family_tree is not None:
        # View selection tabs
        tab1, tab2, tab3 = st.tabs(["🌳 Tree View", "📋 List View", "✏️ Edit Members"])
        
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
            
            # Advanced filtering options
            with st.expander("🔍 Advanced Filters"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Generation filter
                    max_generations = st.session_state.family_tree.get_generation_count()
                    generation_range = st.slider(
                        "Show Generations", 
                        0, max_generations - 1, 
                        (0, max_generations - 1),
                        help="Filter family members by generation level"
                    )
                    
                with col2:
                    # Date range filter
                    all_birth_years = []
                    for member in st.session_state.family_tree.members.values():
                        if member.birth_date:
                            try:
                                year = pd.to_datetime(member.birth_date).year
                                all_birth_years.append(year)
                            except:
                                pass
                    
                    if all_birth_years:
                        min_year, max_year = min(all_birth_years), max(all_birth_years)
                        birth_year_range = st.slider(
                            "Birth Year Range",
                            min_year, max_year,
                            (min_year, max_year),
                            help="Filter by birth year range"
                        )
                    else:
                        birth_year_range = None
                
                with col3:
                    # Branch filter (descendants of specific person)
                    branch_options = ["Show All"] + list(st.session_state.family_tree.members.keys())
                    selected_branch = st.selectbox(
                        "Show Branch of:",
                        branch_options,
                        help="Show only descendants of selected person"
                    )
            
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
                # Apply filters
                filtered_family_tree = apply_tree_filters(
                    st.session_state.family_tree,
                    generation_range=generation_range,
                    birth_year_range=birth_year_range,
                    selected_branch=selected_branch if selected_branch != "Show All" else None
                )
                
                fig = create_tree_visualization(
                    filtered_family_tree,
                    layout_type=layout_type,
                    show_dates=show_dates,
                    color_by_gender=color_by_gender,
                    search_term=search_term if search_term else None,
                    highlight_search=highlight_search
                )
                st.plotly_chart(fig, width='stretch')
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
                st.dataframe(list_view, width='stretch')
                
                # Enhanced Statistics Dashboard
                st.subheader("📊 Family Statistics")
                
                # Basic metrics
                col1, col2, col3, col4 = st.columns(4)
                
                total_members = len(st.session_state.df) if st.session_state.df is not None else 0
                generations = st.session_state.family_tree.get_generation_count()
                avg_age = st.session_state.family_tree.get_average_age()
                living_members = st.session_state.family_tree.get_living_count()
                
                col1.metric("Total Members", total_members)
                col2.metric("Generations", generations)
                col3.metric("Average Age", f"{avg_age:.1f}" if avg_age else "N/A")
                col4.metric("Living Members", living_members)
                
                # Detailed statistics
                st.markdown("### Detailed Analysis")
                
                # Gender distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Gender Distribution")
                    gender_counts = {}
                    for member in st.session_state.family_tree.members.values():
                        gender = member.gender if member.gender else "Unknown"
                        gender_counts[gender] = gender_counts.get(gender, 0) + 1
                    
                    if gender_counts:
                        gender_df = pd.DataFrame(list(gender_counts.items()), columns=["Gender", "Count"])
                        st.bar_chart(gender_df.set_index("Gender"))
                
                with col2:
                    st.markdown("#### Age Distribution")
                    ages = [member.get_age() for member in st.session_state.family_tree.members.values() if member.get_age()]
                    
                    if ages:
                        age_ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "80+": 0}
                        for age in ages:
                            if age <= 20:
                                age_ranges["0-20"] += 1
                            elif age <= 40:
                                age_ranges["21-40"] += 1
                            elif age <= 60:
                                age_ranges["41-60"] += 1
                            elif age <= 80:
                                age_ranges["61-80"] += 1
                            else:
                                age_ranges["80+"] += 1
                        
                        age_df = pd.DataFrame(list(age_ranges.items()), columns=["Age Range", "Count"])
                        st.bar_chart(age_df.set_index("Age Range"))
                
                # Generation breakdown
                st.markdown("#### Members by Generation")
                generations_data = st.session_state.family_tree.get_members_by_generation()
                gen_counts = {f"Generation {gen}": len(members) for gen, members in generations_data.items()}
                
                if gen_counts:
                    gen_df = pd.DataFrame(list(gen_counts.items()), columns=["Generation", "Members"])
                    st.bar_chart(gen_df.set_index("Generation"))
                
                # Additional insights
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Count members with occupations
                    with_occupation = sum(1 for m in st.session_state.family_tree.members.values() if m.occupation)
                    st.metric("With Occupations", with_occupation, f"{with_occupation/total_members*100:.1f}%" if total_members > 0 else "0%")
                
                with col2:
                    # Count married members
                    with_spouse = sum(1 for m in st.session_state.family_tree.members.values() if m.spouse)
                    st.metric("With Spouses", with_spouse, f"{with_spouse/total_members*100:.1f}%" if total_members > 0 else "0%")
                
                with col3:
                    # Deceased members
                    deceased = total_members - living_members
                    st.metric("Deceased", deceased, f"{deceased/total_members*100:.1f}%" if total_members > 0 else "0%")
                
            except Exception as e:
                st.error(f"Error creating list view: {str(e)}")
        
        with tab3:
            st.header("✏️ Edit Family Members")
            
            # Select member to edit
            member_names = list(st.session_state.family_tree.members.keys())
            selected_member_name = st.selectbox(
                "Select member to edit:",
                member_names,
                help="Choose a family member to edit their information"
            )
            
            if selected_member_name:
                member = st.session_state.family_tree.members[selected_member_name]
                
                st.subheader(f"Editing: {selected_member_name}")
                
                # Create editing form
                with st.form(f"edit_form_{selected_member_name}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_name = st.text_input("Name", value=member.name)
                        new_birth_date = st.date_input(
                            "Birth Date",
                            value=pd.to_datetime(member.birth_date) if member.birth_date else None
                        )
                        new_gender = st.selectbox(
                            "Gender", 
                            ["", "M", "F", "Other"], 
                            index=["", "M", "F", "Other"].index(member.gender) if member.gender in ["", "M", "F", "Other"] else 0
                        )
                        new_occupation = st.text_input("Occupation", value=member.occupation or "")
                        
                        # Extended fields
                        new_birth_place = st.text_input("Birth Place", value=getattr(member, 'birth_place', '') or "")
                        new_education = st.text_input("Education", value=getattr(member, 'education', '') or "")
                        new_religion = st.text_input("Religion", value=getattr(member, 'religion', '') or "")
                    
                    with col2:
                        # Two parent selection
                        parent_options = [""] + [name for name in member_names if name != selected_member_name]
                        
                        # Mother selection
                        current_mother_index = 0
                        if member.mother and member.mother in parent_options:
                            current_mother_index = parent_options.index(member.mother)
                        elif member.parent and member.parent in parent_options and not member.mother and not member.father:
                            # Backward compatibility - if old single parent exists, put in mother for now
                            current_mother_index = parent_options.index(member.parent)
                        
                        new_mother = st.selectbox("Mother", parent_options, index=current_mother_index)
                        
                        # Father selection
                        current_father_index = 0
                        if member.father and member.father in parent_options:
                            current_father_index = parent_options.index(member.father)
                        
                        new_father = st.selectbox("Father", parent_options, index=current_father_index)
                        
                        # Manual generation setting
                        col2a, col2b = st.columns(2)
                        with col2a:
                            new_generation = st.number_input(
                                "Generation", 
                                min_value=0, 
                                max_value=20, 
                                value=member.generation,
                                help="Set generation level manually"
                            )
                        with col2b:
                            new_manual_generation = st.checkbox(
                                "Manual Generation", 
                                value=getattr(member, 'manual_generation', False),
                                help="Check to manually set generation instead of auto-calculating"
                            )
                        new_death_date = st.date_input(
                            "Death Date (leave empty if living)",
                            value=pd.to_datetime(member.death_date) if member.death_date else None
                        )
                        new_spouse = st.text_input("Spouse", value=member.spouse or "")
                        new_notes = st.text_area("Notes", value=member.notes or "")
                        
                        # Additional relationship fields
                        relationship_options = ["biological", "adopted", "step", "foster", "other"]
                        current_rel_type = getattr(member, 'relationship_type', 'biological')
                        rel_index = relationship_options.index(current_rel_type) if current_rel_type in relationship_options else 0
                        new_relationship_type = st.selectbox("Relationship Type", relationship_options, index=rel_index)
                        
                        new_marriage_date = st.date_input(
                            "Marriage Date",
                            value=pd.to_datetime(getattr(member, 'marriage_date', None)) if getattr(member, 'marriage_date', None) else None
                        )
                        new_death_place = st.text_input("Death Place", value=getattr(member, 'death_place', '') or "")
                    
                    submitted = st.form_submit_button("Save Changes")
                    
                    if submitted:
                        try:
                            # Update member data
                            old_name = member.name
                            
                            # Update member attributes
                            member.name = new_name
                            # Update two-parent structure
                            member.mother = new_mother if new_mother else None
                            member.father = new_father if new_father else None
                            member.parent = None  # Clear old single parent field
                            member.birth_date = str(new_birth_date) if new_birth_date else None
                            member.death_date = str(new_death_date) if new_death_date else None
                            member.gender = new_gender if new_gender else None
                            member.spouse = new_spouse if new_spouse else None
                            member.occupation = new_occupation if new_occupation else None
                            member.notes = new_notes if new_notes else None
                            
                            # Update generation settings
                            if new_manual_generation:
                                member.generation = int(new_generation)
                                member.manual_generation = True
                            else:
                                member.manual_generation = False
                            
                            # Update extended attributes
                            member.relationship_type = new_relationship_type
                            member.birth_place = new_birth_place if new_birth_place else None
                            member.education = new_education if new_education else None
                            member.religion = new_religion if new_religion else None
                            member.marriage_date = str(new_marriage_date) if new_marriage_date else None
                            member.death_place = new_death_place if new_death_place else None
                            
                            # If name changed, update references
                            if old_name != new_name:
                                # Update in family tree members dict
                                del st.session_state.family_tree.members[old_name]
                                st.session_state.family_tree.members[new_name] = member
                                
                                # Update graph node
                                st.session_state.family_tree.graph.remove_node(old_name)
                                st.session_state.family_tree.graph.add_node(new_name, data=member)
                                
                                # Update parent references for children
                                for child in member.children:
                                    child.parent = new_name
                                
                                # Update spouse references
                                for other_member in st.session_state.family_tree.members.values():
                                    if other_member.spouse == old_name:
                                        other_member.spouse = new_name
                            
                            # Update parent-child relationships in graph
                            # Remove old edges involving this member as child
                            edges_to_remove = [(u, v) for u, v in st.session_state.family_tree.graph.edges() 
                                             if v == member.name]
                            st.session_state.family_tree.graph.remove_edges_from(edges_to_remove)
                            
                            # Add new parent edges
                            if member.mother and member.mother in st.session_state.family_tree.members:
                                st.session_state.family_tree.graph.add_edge(member.mother, member.name)
                                # Add this member to mother's children
                                mother = st.session_state.family_tree.members[member.mother]
                                if member not in mother.children:
                                    mother.children.append(member)
                            
                            if member.father and member.father in st.session_state.family_tree.members:
                                st.session_state.family_tree.graph.add_edge(member.father, member.name)
                                # Add this member to father's children
                                father = st.session_state.family_tree.members[member.father]
                                if member not in father.children:
                                    father.children.append(member)
                            
                            # Rebuild child relationships and graph edges for this member as parent
                            member.children = []
                            for other_member in st.session_state.family_tree.members.values():
                                # Check if this member is mother or father of other member
                                if (other_member.mother == member.name or 
                                    other_member.father == member.name or 
                                    other_member.parent == member.name):
                                    member.children.append(other_member)
                                    if not st.session_state.family_tree.graph.has_edge(member.name, other_member.name):
                                        st.session_state.family_tree.graph.add_edge(member.name, other_member.name)
                            
                            # Recalculate generations
                            st.session_state.family_tree._calculate_generations()
                            
                            # Update the DataFrame in session state
                            st.session_state.df = st.session_state.family_tree.to_dataframe()
                            # Update the modified CSV data copy
                            st.session_state.modified_csv_data = st.session_state.family_tree.to_dataframe()
                            
                            st.success(f"✅ Successfully updated {member.name}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error updating member: {str(e)}")
            
            # Add new member section
            st.markdown("---")
            st.subheader("➕ Add New Family Member")
            
            with st.form("add_new_member"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_member_name = st.text_input("Name*", placeholder="Enter full name")
                    new_member_birth = st.date_input("Birth Date")
                    new_member_gender = st.selectbox("Gender", ["", "M", "F", "Other"])
                    new_member_occupation = st.text_input("Occupation")
                
                with col2:
                    parent_options = [""] + member_names
                    new_member_mother = st.selectbox("Mother", parent_options)
                    new_member_father = st.selectbox("Father", parent_options)
                    new_member_death = st.date_input("Death Date (leave if living)")
                    new_member_spouse = st.text_input("Spouse")
                    new_member_notes = st.text_area("Notes")
                    
                    # Generation setting for new member
                    new_member_generation = st.number_input(
                        "Generation", 
                        min_value=0, 
                        max_value=20, 
                        value=0,
                        help="Set generation level (0 for roots, auto-calculated if parents are selected)"
                    )
                    new_member_manual_generation = st.checkbox(
                        "Manual Generation",
                        value=False,
                        help="Check to manually set generation instead of auto-calculating"
                    )
                
                add_submitted = st.form_submit_button("Add New Member")
                
                if add_submitted:
                    if new_member_name and new_member_name not in st.session_state.family_tree.members:
                        try:
                            # Create new member
                            from family_tree import FamilyMember
                            
                            new_member = FamilyMember(
                                name=new_member_name,
                                mother=new_member_mother if new_member_mother else None,
                                father=new_member_father if new_member_father else None,
                                generation=new_member_generation,
                                manual_generation=new_member_manual_generation,
                                birth_date=str(new_member_birth) if new_member_birth else None,
                                death_date=str(new_member_death) if new_member_death else None,
                                gender=new_member_gender if new_member_gender else None,
                                spouse=new_member_spouse if new_member_spouse else None,
                                occupation=new_member_occupation if new_member_occupation else None,
                                notes=new_member_notes if new_member_notes else None
                            )
                            
                            # Add to family tree
                            st.session_state.family_tree.add_member(new_member)
                            
                            # Recalculate generations
                            st.session_state.family_tree._calculate_generations()
                            
                            # Update DataFrame
                            st.session_state.df = st.session_state.family_tree.to_dataframe()
                            # Update the modified CSV data copy
                            st.session_state.modified_csv_data = st.session_state.family_tree.to_dataframe()
                            
                            st.success(f"✅ Successfully added {new_member_name}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error adding new member: {str(e)}")
                    elif new_member_name in st.session_state.family_tree.members:
                        st.error("A family member with this name already exists!")
                    else:
                        st.error("Please enter a name for the new family member.")
            
            # Download Modified CSV Section
            st.markdown("---")
            st.subheader("📥 Download Updated Family Data")
            
            if st.session_state.modified_csv_data is not None and not st.session_state.modified_csv_data.empty:
                # Convert DataFrame to CSV string
                csv_string = st.session_state.modified_csv_data.to_csv(index=False)
                
                st.markdown("Download your family tree data with all the changes you've made:")
                
                st.download_button(
                    label="📄 Download Updated CSV",
                    data=csv_string,
                    file_name="updated_family_tree.csv",
                    mime="text/csv",
                    help="Download the family tree data including all your edits and additions"
                )
                
                st.info(f"💡 This file contains {len(st.session_state.modified_csv_data)} family members with all your recent changes.")
            else:
                st.info("Upload a family tree file and make some changes to download an updated version.")
    
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
