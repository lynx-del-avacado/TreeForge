# Family Tree Visualization Application

## Overview

This is a Streamlit-based family tree visualization application that allows users to upload CSV data containing family information and generate interactive tree visualizations. The application provides multiple layout options (hierarchical, circular, spring), filtering capabilities, and detailed member information display. Users can explore family relationships through both graphical tree views and tabular list views.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Streamlit Framework**: Single-page web application built with Streamlit for rapid prototyping and deployment
- **Interactive Visualizations**: Plotly integration for creating dynamic, zoomable family tree diagrams
- **Real-time Filtering**: Client-side filtering system for generation ranges, birth years, and family branches
- **Responsive Design**: Streamlit's built-in responsive components for cross-device compatibility

### Backend Architecture
- **Object-Oriented Design**: Core family tree logic encapsulated in `FamilyMember` and `FamilyTree` classes
- **Graph-based Data Structure**: NetworkX integration for efficient relationship traversal and layout algorithms
- **Modular Components**: Separated concerns across distinct modules:
  - `family_tree.py`: Core data models and relationship logic
  - `data_processor.py`: CSV validation and data transformation
  - `visualization.py`: Plotly-based rendering and layout algorithms
  - `app.py`: Streamlit UI orchestration and state management

### Data Processing Pipeline
- **CSV Import System**: Pandas-based data ingestion with comprehensive validation
- **Flexible Schema Support**: Optional columns for extended genealogical information (birth/death dates, places, occupations, military service, etc.)
- **Data Validation**: Multi-layer validation including required fields, date format checking, and duplicate detection
- **Error Handling**: Graceful degradation with warning messages for data quality issues

### Visualization Engine
- **Multiple Layout Algorithms**: 
  - Hierarchical layout for traditional family tree representation
  - Circular layout for compact relationship visualization
  - Spring layout for organic network-style display
- **Interactive Features**: Search highlighting, hover tooltips, zoom/pan capabilities
- **Customizable Display Options**: Toggle date display, gender-based coloring, and relationship highlighting

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the user interface
- **Pandas**: Data manipulation and CSV processing
- **Plotly**: Interactive visualization and graphing
- **NetworkX**: Graph algorithms and layout computation

### Data Storage
- **File-based Input**: CSV file upload system (no persistent database required)
- **In-memory Processing**: Session-based data storage using Streamlit's state management

### Deployment Environment
- **Python Runtime**: Compatible with standard Python 3.x environments
- **Web Browser**: Client-side rendering through modern web browsers
- **No External APIs**: Self-contained application with no third-party service dependencies