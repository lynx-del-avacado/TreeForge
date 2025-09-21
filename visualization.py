import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import pandas as pd
from typing import Dict, List, Optional, Any
import math
from family_tree import FamilyTree, FamilyMember

def create_tree_visualization(
    family_tree: FamilyTree,
    layout_type: str = "hierarchical",
    show_dates: bool = True,
    color_by_gender: bool = True,
    search_term: Optional[str] = None,
    highlight_search: bool = True
) -> go.Figure:
    """Create an interactive tree visualization using Plotly."""
    
    if not family_tree.members:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No family data to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Get positions based on layout type
    if layout_type == "hierarchical":
        pos = _get_hierarchical_layout(family_tree)
    elif layout_type == "circular":
        pos = _get_circular_layout(family_tree)
    else:  # spring layout
        pos = _get_spring_layout(family_tree)
    
    # Prepare node and edge data
    node_trace, edge_trace = _prepare_graph_traces(
        family_tree, pos, show_dates, color_by_gender, search_term, highlight_search
    )
    
    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    
    # Update layout
    fig.update_layout(
        title=f"Family Tree ({len(family_tree.members)} members)",
        font_size=16,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        annotations=[ dict(
            text="Drag to pan, scroll to zoom",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002,
            xanchor='left', yanchor='bottom',
            font=dict(color="gray", size=12)
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    return fig

def _get_hierarchical_layout(family_tree: FamilyTree) -> Dict[str, tuple]:
    """Create hierarchical layout positions."""
    pos = {}
    generations = family_tree.get_members_by_generation()
    
    max_gen = max(generations.keys()) if generations else 0
    
    for gen, members in generations.items():
        y = max_gen - gen  # Higher generations at top
        
        # Distribute members horizontally within generation
        if len(members) == 1:
            x_positions = [0]
        else:
            x_positions = [i * 2 - (len(members) - 1) for i in range(len(members))]
        
        for i, member in enumerate(members):
            pos[member.name] = (x_positions[i], y)
    
    return pos

def _get_circular_layout(family_tree: FamilyTree) -> Dict[str, tuple]:
    """Create circular layout positions."""
    graph = family_tree.graph
    pos = nx.circular_layout(graph, scale=2)
    return {node: (pos[node][0], pos[node][1]) for node in pos}

def _get_spring_layout(family_tree: FamilyTree) -> Dict[str, tuple]:
    """Create spring layout positions."""
    graph = family_tree.graph
    pos = nx.spring_layout(graph, k=3, iterations=50, scale=2)
    return {node: (pos[node][0], pos[node][1]) for node in pos}

def _prepare_graph_traces(
    family_tree: FamilyTree,
    pos: Dict[str, tuple],
    show_dates: bool,
    color_by_gender: bool,
    search_term: Optional[str],
    highlight_search: bool
):
    """Prepare node and edge traces for the graph."""
    
    # Edge trace
    edge_x = []
    edge_y = []
    
    for edge in family_tree.graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='lightgray'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Node trace
    node_x = []
    node_y = []
    node_text = []
    node_info = []
    node_colors = []
    node_sizes = []
    
    # Search results for highlighting
    search_matches = set()
    if search_term and highlight_search:
        search_results = family_tree.search_members(search_term)
        search_matches = {member.name for member in search_results}
    
    for name, member in family_tree.members.items():
        x, y = pos[name]
        node_x.append(x)
        node_y.append(y)
        
        # Create node label
        label = member.name
        if show_dates and member.birth_date:
            label += f"<br>({member.birth_date})"
        
        node_text.append(label)
        
        # Create hover info
        info_parts = [f"<b>{member.name}</b>"]
        if member.birth_date:
            info_parts.append(f"Born: {member.birth_date}")
        if member.death_date:
            info_parts.append(f"Died: {member.death_date}")
        age = member.get_age()
        if age:
            info_parts.append(f"Age: {age}")
        if member.occupation:
            info_parts.append(f"Occupation: {member.occupation}")
        if member.spouse:
            info_parts.append(f"Spouse: {member.spouse}")
        info_parts.append(f"Generation: {member.generation}")
        info_parts.append(f"Children: {len(member.children)}")
        
        node_info.append("<br>".join(info_parts))
        
        # Node color
        if name in search_matches:
            node_colors.append('red')
        elif color_by_gender and member.gender:
            if member.gender.upper() == 'M':
                node_colors.append('lightblue')
            elif member.gender.upper() == 'F':
                node_colors.append('pink')
            else:
                node_colors.append('lightgreen')
        else:
            node_colors.append('lightgray')
        
        # Node size (larger for search matches or based on children count)
        if name in search_matches:
            node_sizes.append(20)
        else:
            size = min(15 + len(member.children) * 2, 25)
            node_sizes.append(size)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        hovertext=node_info,
        textposition="middle center",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color='white')
        )
    )
    
    return node_trace, edge_trace

def create_list_view(
    family_tree: FamilyTree,
    original_df: pd.DataFrame,
    search_term: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "ascending"
) -> pd.DataFrame:
    """Create a structured list view of family members."""
    
    # Convert family tree to DataFrame
    df = family_tree.to_dataframe()
    
    # Apply search filter
    if search_term:
        search_term = search_term.lower()
        mask = (
            df['name'].str.lower().str.contains(search_term, na=False) |
            df['occupation'].str.lower().str.contains(search_term, na=False) |
            df['notes'].str.lower().str.contains(search_term, na=False)
        )
        df = df[mask]
    
    # Sort the DataFrame
    ascending = sort_order == "ascending"
    
    if sort_by == "birth_date":
        # Handle date sorting
        df['birth_date_sort'] = pd.to_datetime(df['birth_date'], errors='coerce')
        df = df.sort_values(by='birth_date_sort', ascending=ascending)
        df = df.drop('birth_date_sort', axis=1)
    else:
        df = df.sort_values(by=sort_by, ascending=ascending)
    
    # Reorder and select columns for display
    display_columns = [
        'name', 'parent', 'birth_date', 'death_date', 'age', 'gender',
        'spouse', 'occupation', 'generation', 'children_count', 'living', 'notes'
    ]
    
    # Only include columns that exist in the DataFrame
    available_columns = [col for col in display_columns if col in df.columns]
    df = df[available_columns]
    
    # Rename columns for better display
    column_renames = {
        'children_count': 'Children',
        'birth_date': 'Birth Date',
        'death_date': 'Death Date',
        'living': 'Living'
    }
    
    df = df.rename(columns={k: v for k, v in column_renames.items() if k in df.columns})
    
    # Format the DataFrame for better display
    if 'Living' in df.columns:
        df['Living'] = df['Living'].apply(lambda x: '✅ Yes' if x else '❌ No')
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df
