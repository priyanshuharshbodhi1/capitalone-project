"""
Government Schemes Knowledge Base

Structured knowledge base for Indian government agricultural schemes and policies.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Scheme:
    name: str
    description: str
    eligibility: List[str]
    benefits: List[str]
    subsidy_amount: Optional[str]
    application_process: List[str]
    required_documents: List[str]
    application_links: List[str]
    implementing_agency: str
    state: Optional[str]  # None for central schemes
    category: str  # 'irrigation', 'seeds', 'fertilizers', 'insurance', etc.
    status: str  # 'active', 'closed', 'upcoming'
    launch_date: Optional[datetime]
    end_date: Optional[datetime]
    budget_allocation: Optional[str]
    beneficiaries_target: Optional[str]
    contact_info: Dict[str, str]
    source_urls: List[str]
    last_updated: datetime

class GovtSchemesKB:
    """Knowledge base for government agricultural schemes"""
    
    def __init__(self, kb_path: str = "./schemes_kb"):
        self.logger = logging.getLogger(__name__)
        self.kb_path = Path(kb_path)
        self.kb_path.mkdir(exist_ok=True)
        
        # In-memory storage for fast access
        self.schemes_db: Dict[str, Scheme] = {}
        self.schemes_by_state: Dict[str, List[str]] = {}
        self.schemes_by_category: Dict[str, List[str]] = {}
        
        # Load existing knowledge base
        self._load_kb()
    
    def add_scheme(self, scheme: Scheme) -> bool:
        """Add a new scheme to the knowledge base"""
        try:
            scheme_id = self._generate_scheme_id(scheme)
            self.schemes_db[scheme_id] = scheme
            
            # Update indexes
            self._update_indexes(scheme_id, scheme)
            
            # Persist to disk
            self._save_scheme(scheme_id, scheme)
            
            self.logger.info(f"Added scheme: {scheme.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding scheme {scheme.name}: {e}")
            return False
    
    def update_scheme(self, scheme_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing scheme"""
        try:
            if scheme_id not in self.schemes_db:
                self.logger.warning(f"Scheme {scheme_id} not found for update")
                return False
            
            scheme = self.schemes_db[scheme_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(scheme, field):
                    setattr(scheme, field, value)
            
            scheme.last_updated = datetime.now()
            
            # Update indexes
            self._update_indexes(scheme_id, scheme)
            
            # Persist to disk
            self._save_scheme(scheme_id, scheme)
            
            self.logger.info(f"Updated scheme: {scheme.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating scheme {scheme_id}: {e}")
            return False
    
    def get_scheme(self, scheme_id: str) -> Optional[Scheme]:
        """Get a scheme by ID"""
        return self.schemes_db.get(scheme_id)
    
    def search_schemes(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Tuple[str, Scheme, float]]:
        """Search schemes by text query with optional filters"""
        results = []
        query_lower = query.lower()
        
        for scheme_id, scheme in self.schemes_db.items():
            # Apply filters first
            if filters and not self._match_filters(scheme, filters):
                continue
            
            # Calculate relevance score
            score = self._calculate_relevance(scheme, query_lower)
            
            if score > 0.1:  # Minimum relevance threshold
                results.append((scheme_id, scheme, score))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[2], reverse=True)
        return results
    
    def get_schemes_by_state(self, state: str) -> List[Tuple[str, Scheme]]:
        """Get all schemes for a specific state"""
        scheme_ids = self.schemes_by_state.get(state.lower(), [])
        return [(scheme_id, self.schemes_db[scheme_id]) for scheme_id in scheme_ids]
    
    def get_schemes_by_category(self, category: str) -> List[Tuple[str, Scheme]]:
        """Get all schemes in a specific category"""
        scheme_ids = self.schemes_by_category.get(category.lower(), [])
        return [(scheme_id, self.schemes_db[scheme_id]) for scheme_id in scheme_ids]
    
    def get_active_schemes(self) -> List[Tuple[str, Scheme]]:
        """Get all currently active schemes"""
        active_schemes = []
        
        for scheme_id, scheme in self.schemes_db.items():
            if scheme.status == 'active':
                active_schemes.append((scheme_id, scheme))
        
        return active_schemes
    
    def get_schemes_for_farmer_type(self, farmer_type: str) -> List[Tuple[str, Scheme]]:
        """Get schemes applicable to specific farmer type"""
        matching_schemes = []
        farmer_type_lower = farmer_type.lower()
        
        for scheme_id, scheme in self.schemes_db.items():
            # Check eligibility criteria
            for eligibility in scheme.eligibility:
                if farmer_type_lower in eligibility.lower():
                    matching_schemes.append((scheme_id, scheme))
                    break
        
        return matching_schemes
    
    def get_irrigation_schemes(self) -> List[Tuple[str, Scheme]]:
        """Get all irrigation-related schemes"""
        irrigation_categories = ['irrigation', 'water', 'drip irrigation', 'micro irrigation']
        irrigation_schemes = []
        
        for scheme_id, scheme in self.schemes_db.items():
            if (scheme.category.lower() in irrigation_categories or
                any(cat in scheme.name.lower() for cat in irrigation_categories) or
                any(cat in scheme.description.lower() for cat in irrigation_categories)):
                irrigation_schemes.append((scheme_id, scheme))
        
        return irrigation_schemes
    
    def get_subsidy_schemes(self, min_amount: Optional[float] = None) -> List[Tuple[str, Scheme]]:
        """Get schemes offering subsidies"""
        subsidy_schemes = []
        
        for scheme_id, scheme in self.schemes_db.items():
            if scheme.subsidy_amount:
                # Extract amount if needed for filtering
                if min_amount is None:
                    subsidy_schemes.append((scheme_id, scheme))
                else:
                    # Simple amount extraction (could be improved)
                    amount_str = scheme.subsidy_amount.lower()
                    if 'lakh' in amount_str or '₹' in amount_str:
                        subsidy_schemes.append((scheme_id, scheme))
        
        return subsidy_schemes
    
    def get_kb_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        total_schemes = len(self.schemes_db)
        active_schemes = len([s for s in self.schemes_db.values() if s.status == 'active'])
        
        state_distribution = {state: len(schemes) for state, schemes in self.schemes_by_state.items()}
        category_distribution = {cat: len(schemes) for cat, schemes in self.schemes_by_category.items()}
        
        return {
            'total_schemes': total_schemes,
            'active_schemes': active_schemes,
            'inactive_schemes': total_schemes - active_schemes,
            'states_covered': len(self.schemes_by_state),
            'categories': len(self.schemes_by_category),
            'state_distribution': state_distribution,
            'category_distribution': category_distribution,
            'last_updated': max([s.last_updated for s in self.schemes_db.values()]).isoformat() if self.schemes_db else None
        }
    
    def export_schemes(self, output_path: str, format: str = 'json') -> bool:
        """Export schemes to file"""
        try:
            output_file = Path(output_path)
            
            if format == 'json':
                schemes_data = {
                    scheme_id: asdict(scheme) for scheme_id, scheme in self.schemes_db.items()
                }
                
                # Convert datetime objects to strings for JSON serialization
                for scheme_data in schemes_data.values():
                    for key, value in scheme_data.items():
                        if isinstance(value, datetime):
                            scheme_data[key] = value.isoformat()
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(schemes_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported {len(self.schemes_db)} schemes to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting schemes: {e}")
            return False
    
    def _generate_scheme_id(self, scheme: Scheme) -> str:
        """Generate unique ID for a scheme"""
        import hashlib
        
        # Create ID based on scheme name and implementing agency
        id_string = f"{scheme.name}_{scheme.implementing_agency}_{scheme.state or 'central'}"
        scheme_hash = hashlib.md5(id_string.encode()).hexdigest()[:8]
        
        return f"scheme_{scheme_hash}"
    
    def _update_indexes(self, scheme_id: str, scheme: Scheme):
        """Update internal indexes"""
        # State index
        if scheme.state:
            state_key = scheme.state.lower()
            if state_key not in self.schemes_by_state:
                self.schemes_by_state[state_key] = []
            if scheme_id not in self.schemes_by_state[state_key]:
                self.schemes_by_state[state_key].append(scheme_id)
        
        # Category index
        category_key = scheme.category.lower()
        if category_key not in self.schemes_by_category:
            self.schemes_by_category[category_key] = []
        if scheme_id not in self.schemes_by_category[category_key]:
            self.schemes_by_category[category_key].append(scheme_id)
    
    def _match_filters(self, scheme: Scheme, filters: Dict[str, Any]) -> bool:
        """Check if scheme matches the given filters"""
        for key, value in filters.items():
            if not hasattr(scheme, key):
                continue
            
            scheme_value = getattr(scheme, key)
            
            if isinstance(value, list):
                if scheme_value not in value:
                    return False
            elif isinstance(value, str):
                if value.lower() not in str(scheme_value).lower():
                    return False
            else:
                if scheme_value != value:
                    return False
        
        return True
    
    def _calculate_relevance(self, scheme: Scheme, query: str) -> float:
        """Calculate relevance score for a scheme based on query"""
        score = 0.0
        
        # Exact matches get higher scores
        if query in scheme.name.lower():
            score += 1.0
        
        if query in scheme.description.lower():
            score += 0.8
        
        # Partial matches
        query_words = query.split()
        for word in query_words:
            if word in scheme.name.lower():
                score += 0.3
            if word in scheme.description.lower():
                score += 0.2
            if any(word in eligibility.lower() for eligibility in scheme.eligibility):
                score += 0.2
            if any(word in benefit.lower() for benefit in scheme.benefits):
                score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _load_kb(self):
        """Load knowledge base from disk"""
        schemes_file = self.kb_path / "schemes.json"
        
        if not schemes_file.exists():
            self.logger.info("No existing knowledge base found, starting fresh")
            return
        
        try:
            with open(schemes_file, 'r', encoding='utf-8') as f:
                schemes_data = json.load(f)
            
            for scheme_id, scheme_dict in schemes_data.items():
                # Convert datetime strings back to datetime objects
                if scheme_dict.get('launch_date'):
                    scheme_dict['launch_date'] = datetime.fromisoformat(scheme_dict['launch_date'])
                if scheme_dict.get('end_date'):
                    scheme_dict['end_date'] = datetime.fromisoformat(scheme_dict['end_date'])
                if scheme_dict.get('last_updated'):
                    scheme_dict['last_updated'] = datetime.fromisoformat(scheme_dict['last_updated'])
                
                scheme = Scheme(**scheme_dict)
                self.schemes_db[scheme_id] = scheme
                self._update_indexes(scheme_id, scheme)
            
            self.logger.info(f"Loaded {len(self.schemes_db)} schemes from knowledge base")
            
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {e}")
    
    def _save_scheme(self, scheme_id: str, scheme: Scheme):
        """Save single scheme to disk"""
        try:
            schemes_file = self.kb_path / "schemes.json"
            
            # Load existing data
            if schemes_file.exists():
                with open(schemes_file, 'r', encoding='utf-8') as f:
                    schemes_data = json.load(f)
            else:
                schemes_data = {}
            
            # Add/update scheme
            scheme_dict = asdict(scheme)
            
            # Convert datetime objects to strings
            for key, value in scheme_dict.items():
                if isinstance(value, datetime):
                    scheme_dict[key] = value.isoformat()
            
            schemes_data[scheme_id] = scheme_dict
            
            # Save back to disk
            with open(schemes_file, 'w', encoding='utf-8') as f:
                json.dump(schemes_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"Error saving scheme {scheme_id}: {e}")
