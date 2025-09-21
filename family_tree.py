import networkx as nx
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

class FamilyMember:
    """Represents a single family member with all their information."""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        # Support for two parents
        self.mother = kwargs.get('mother', None)
        self.father = kwargs.get('father', None)
        # Keep parent for backward compatibility, but prefer mother/father
        if 'parent' in kwargs and not self.mother and not self.father:
            self.parent = kwargs.get('parent', None)
        else:
            self.parent = None
        self.birth_date = kwargs.get('birth_date', None)
        self.death_date = kwargs.get('death_date', None)
        self.gender = kwargs.get('gender', None)
        self.spouse = kwargs.get('spouse', None)
        self.occupation = kwargs.get('occupation', None)
        self.notes = kwargs.get('notes', None)
        self.children = []
        self.generation = kwargs.get('generation', 0)  # Allow manual generation setting
        self.manual_generation = kwargs.get('manual_generation', False)  # Track if generation was manually set
        
        # Extended relationship types
        self.relationship_type = kwargs.get('relationship_type', 'biological')  # biological, adopted, step, foster
        self.birth_place = kwargs.get('birth_place', None)
        self.death_place = kwargs.get('death_place', None)
        self.burial_place = kwargs.get('burial_place', None)
        self.marriage_date = kwargs.get('marriage_date', None)
        self.divorce_date = kwargs.get('divorce_date', None)
        self.education = kwargs.get('education', None)
        self.military_service = kwargs.get('military_service', None)
        self.religion = kwargs.get('religion', None)
    
    def add_child(self, child: 'FamilyMember'):
        """Add a child to this family member."""
        if child not in self.children:
            self.children.append(child)
    
    def get_parents(self) -> List['FamilyMember']:
        """Get all parents (mother and father) as a list."""
        parents = []
        if self.mother:
            parents.append(self.mother)
        if self.father:
            parents.append(self.father)
        # For backward compatibility with single parent
        if self.parent and not parents:
            parents.append(self.parent)
        return parents
    
    def has_parents(self) -> bool:
        """Check if this member has any parents."""
        return bool(self.mother or self.father or self.parent)
    
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
            'parent': self.parent,  # Keep for backward compatibility
            'mother': self.mother,
            'father': self.father,
            'birth_date': self.birth_date,
            'death_date': self.death_date,
            'gender': self.gender,
            'spouse': self.spouse,
            'occupation': self.occupation,
            'notes': self.notes,
            'age': self.get_age(),
            'living': self.is_living(),
            'generation': self.generation,
            'manual_generation': self.manual_generation,
            'children_count': len(self.children),
            'relationship_type': self.relationship_type,
            'birth_place': self.birth_place,
            'death_place': self.death_place,
            'burial_place': self.burial_place,
            'marriage_date': self.marriage_date,
            'divorce_date': self.divorce_date,
            'education': self.education,
            'military_service': self.military_service,
            'religion': self.religion
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
        
        # Add edges from parents to child
        parents_added = False
        
        # Handle mother
        if member.mother and member.mother in self.members:
            self.graph.add_edge(member.mother, member.name)
            self.members[member.mother].add_child(member)
            parents_added = True
        
        # Handle father
        if member.father and member.father in self.members:
            self.graph.add_edge(member.father, member.name)
            self.members[member.father].add_child(member)
            parents_added = True
        
        # Handle backward compatibility with single parent
        if member.parent and member.parent in self.members and not parents_added:
            self.graph.add_edge(member.parent, member.name)
            self.members[member.parent].add_child(member)
            parents_added = True
        
        # This is a root ancestor if no parents
        if not parents_added and not member.has_parents():
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
            
            # Handle mother relationship
            if member.mother and member.mother in self.members:
                parent = self.members[member.mother]
                if member not in parent.children:
                    parent.add_child(member)
                # Ensure graph edge exists
                if not self.graph.has_edge(member.mother, member.name):
                    self.graph.add_edge(member.mother, member.name)
            
            # Handle father relationship
            if member.father and member.father in self.members:
                parent = self.members[member.father]
                if member not in parent.children:
                    parent.add_child(member)
                # Ensure graph edge exists
                if not self.graph.has_edge(member.father, member.name):
                    self.graph.add_edge(member.father, member.name)
            
            # Handle backward compatibility with single parent
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
        """Calculate generation numbers for all family members, respecting manual settings."""
        # First, set root members to generation 0 if not manually set
        for root in self.roots:
            if not root.manual_generation:
                root.generation = 0
            self._set_generation_recursive(root, root.generation)
    
    def _set_generation_recursive(self, member: FamilyMember, generation: int):
        """Recursively set generation numbers, respecting manual overrides."""
        # Only update generation if not manually set
        if not member.manual_generation:
            member.generation = generation
        
        for child in member.children:
            # Calculate next generation based on current member's generation
            next_generation = member.generation + 1
            self._set_generation_recursive(child, next_generation)
    
    def set_manual_generation(self, member_name: str, generation: int):
        """Manually set a member's generation and mark it as manual."""
        if member_name in self.members:
            member = self.members[member_name]
            member.generation = generation
            member.manual_generation = True
            # Recalculate generations for the whole tree
            self._calculate_generations()
    
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
        visited = set()
        
        def collect_ancestors(member: FamilyMember):
            if member.name in visited:
                return
            visited.add(member.name)
            
            # Handle mother
            if member.mother and member.mother in self.members:
                mother = self.members[member.mother]
                ancestors.append(mother)
                collect_ancestors(mother)
            
            # Handle father
            if member.father and member.father in self.members:
                father = self.members[member.father]
                ancestors.append(father)
                collect_ancestors(father)
            
            # Handle backward compatibility with single parent
            if member.parent and member.parent in self.members and not member.mother and not member.father:
                parent = self.members[member.parent]
                ancestors.append(parent)
                collect_ancestors(parent)
        
        current = self.members[member_name]
        collect_ancestors(current)
        
        return ancestors
    
    def get_siblings(self, member_name: str) -> List[FamilyMember]:
        """Get all siblings of a family member."""
        if member_name not in self.members:
            return []
        
        member = self.members[member_name]
        siblings = set()  # Use set to avoid duplicates
        
        # Find siblings through mother
        if member.mother and member.mother in self.members:
            mother = self.members[member.mother]
            for child in mother.children:
                if child.name != member_name:
                    siblings.add(child)
        
        # Find siblings through father
        if member.father and member.father in self.members:
            father = self.members[member.father]
            for child in father.children:
                if child.name != member_name:
                    siblings.add(child)
        
        # Handle backward compatibility with single parent
        if member.parent and member.parent in self.members and not member.mother and not member.father:
            parent = self.members[member.parent]
            for child in parent.children:
                if child.name != member_name:
                    siblings.add(child)
        
        return list(siblings)
    
    def get_generation_count(self) -> int:
        """Get the total number of generations in the tree."""
        if not self.members:
            return 0
        return max(member.generation for member in self.members.values()) + 1
    
    def get_average_age(self) -> Optional[float]:
        """Calculate the average age of all family members."""
        ages = [age for member in self.members.values() if (age := member.get_age()) is not None]
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
