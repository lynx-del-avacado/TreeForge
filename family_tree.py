import networkx as nx
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

class FamilyMember:
    """Represents a single family member with all their information."""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.parent = kwargs.get('parent', None)
        self.birth_date = kwargs.get('birth_date', None)
        self.death_date = kwargs.get('death_date', None)
        self.gender = kwargs.get('gender', None)
        self.spouse = kwargs.get('spouse', None)
        self.occupation = kwargs.get('occupation', None)
        self.notes = kwargs.get('notes', None)
        self.children = []
        self.generation = 0
    
    def add_child(self, child: 'FamilyMember'):
        """Add a child to this family member."""
        if child not in self.children:
            self.children.append(child)
    
    def get_age(self) -> Optional[int]:
        """Calculate age (current age if living, age at death if deceased)."""
        if not self.birth_date:
            return None
        
        try:
            birth = datetime.strptime(str(self.birth_date), '%Y-%m-%d')
            end_date = datetime.now()
            
            if self.death_date:
                end_date = datetime.strptime(str(self.death_date), '%Y-%m-%d')
            
            age = end_date.year - birth.year
            if end_date.month < birth.month or (end_date.month == birth.month and end_date.day < birth.day):
                age -= 1
            
            return max(0, age)
        except (ValueError, TypeError):
            return None
    
    def is_living(self) -> bool:
        """Check if the person is still living."""
        return self.death_date is None or str(self.death_date).strip() == ''
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert family member to dictionary."""
        return {
            'name': self.name,
            'parent': self.parent,
            'birth_date': self.birth_date,
            'death_date': self.death_date,
            'gender': self.gender,
            'spouse': self.spouse,
            'occupation': self.occupation,
            'notes': self.notes,
            'age': self.get_age(),
            'living': self.is_living(),
            'generation': self.generation,
            'children_count': len(self.children)
        }

class FamilyTree:
    """Main family tree class that manages the tree structure and operations."""
    
    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph for parent-child relationships
        self.members: Dict[str, FamilyMember] = {}
        self.roots = []  # Root ancestors (no parents)
    
    def add_member(self, member: FamilyMember):
        """Add a family member to the tree."""
        self.members[member.name] = member
        self.graph.add_node(member.name, data=member)
        
        # Add edge from parent to child if parent exists
        if member.parent and member.parent in self.members:
            self.graph.add_edge(member.parent, member.name)
            self.members[member.parent].add_child(member)
        elif not member.parent:
            # This is a root ancestor
            if member not in self.roots:
                self.roots.append(member)
    
    def build_from_data(self, data: List[Dict[str, Any]]):
        """Build the family tree from processed data."""
        # First pass: create all family members
        for row in data:
            member = FamilyMember(**row)
            self.add_member(member)
        
        # Second pass: establish parent-child relationships and update any missing connections
        for row in data:
            member = self.members[row['name']]
            if member.parent and member.parent in self.members:
                parent = self.members[member.parent]
                if member not in parent.children:
                    parent.add_child(member)
                
                # Ensure graph edge exists
                if not self.graph.has_edge(member.parent, member.name):
                    self.graph.add_edge(member.parent, member.name)
        
        # Calculate generations
        self._calculate_generations()
    
    def _calculate_generations(self):
        """Calculate generation numbers for all family members."""
        # Start with root members (generation 0)
        for root in self.roots:
            root.generation = 0
            self._set_generation_recursive(root, 0)
    
    def _set_generation_recursive(self, member: FamilyMember, generation: int):
        """Recursively set generation numbers."""
        member.generation = generation
        for child in member.children:
            self._set_generation_recursive(child, generation + 1)
    
    def search_members(self, search_term: str) -> List[FamilyMember]:
        """Search for family members by name (case-insensitive)."""
        if not search_term:
            return list(self.members.values())
        
        search_term = search_term.lower()
        results = []
        
        for member in self.members.values():
            if (search_term in member.name.lower() or 
                (member.occupation and search_term in member.occupation.lower()) or
                (member.notes and search_term in member.notes.lower())):
                results.append(member)
        
        return results
    
    def get_descendants(self, member_name: str) -> List[FamilyMember]:
        """Get all descendants of a family member."""
        if member_name not in self.members:
            return []
        
        descendants = []
        member = self.members[member_name]
        
        def collect_descendants(current_member):
            for child in current_member.children:
                descendants.append(child)
                collect_descendants(child)
        
        collect_descendants(member)
        return descendants
    
    def get_ancestors(self, member_name: str) -> List[FamilyMember]:
        """Get all ancestors of a family member."""
        if member_name not in self.members:
            return []
        
        ancestors = []
        current = self.members[member_name]
        
        while current.parent and current.parent in self.members:
            parent = self.members[current.parent]
            ancestors.append(parent)
            current = parent
        
        return ancestors
    
    def get_siblings(self, member_name: str) -> List[FamilyMember]:
        """Get all siblings of a family member."""
        if member_name not in self.members:
            return []
        
        member = self.members[member_name]
        if not member.parent or member.parent not in self.members:
            return []
        
        parent = self.members[member.parent]
        siblings = [child for child in parent.children if child.name != member_name]
        return siblings
    
    def get_generation_count(self) -> int:
        """Get the total number of generations in the tree."""
        if not self.members:
            return 0
        return max(member.generation for member in self.members.values()) + 1
    
    def get_average_age(self) -> Optional[float]:
        """Calculate the average age of all family members."""
        ages = [member.get_age() for member in self.members.values() if member.get_age() is not None]
        return sum(ages) / len(ages) if ages else None
    
    def get_living_count(self) -> int:
        """Get the count of living family members."""
        return sum(1 for member in self.members.values() if member.is_living())
    
    def get_members_by_generation(self) -> Dict[int, List[FamilyMember]]:
        """Group family members by generation."""
        generations = {}
        for member in self.members.values():
            gen = member.generation
            if gen not in generations:
                generations[gen] = []
            generations[gen].append(member)
        return generations
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert the family tree to a pandas DataFrame."""
        data = [member.to_dict() for member in self.members.values()]
        return pd.DataFrame(data)
    
    def get_tree_structure(self) -> Dict[str, Any]:
        """Get the tree structure for visualization."""
        structure = {
            'nodes': [],
            'edges': []
        }
        
        # Add nodes
        for name, member in self.members.items():
            structure['nodes'].append({
                'id': name,
                'label': name,
                'data': member.to_dict()
            })
        
        # Add edges
        for edge in self.graph.edges():
            structure['edges'].append({
                'source': edge[0],
                'target': edge[1]
            })
        
        return structure
