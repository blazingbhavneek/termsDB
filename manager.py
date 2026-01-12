"""
MongoDB Term Manager
Handles bulk term filtering with approved/pending/disapproved status
"""

from pymongo import MongoClient, ASCENDING
from datetime import datetime
from typing import List, Dict

class TermManager:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="terms_db"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db.terms
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Create unique index on term field"""
        self.collection.create_index([("term", ASCENDING)], unique=True)
    
    def process_terms(self, terms_data: List[Dict]) -> List[Dict]:
        """
        Main function: filters terms based on DB status
        
        Args:
            terms_data: [{"term": "word", "meaning": "definition"}, ...]
        
        Returns:
            Filtered list with approved/pending terms only
        """
        if not terms_data:
            return []
        
        # Extract term names
        term_names = [t["term"] for t in terms_data]
        
        # Bulk fetch from DB
        existing = self.collection.find(
            {"term": {"$in": term_names}},
            {"term": 1, "status": 1, "_id": 0}
        )
        
        # Build lookup map
        status_map = {doc["term"]: doc["status"] for doc in existing}
        
        # Filter and collect new terms
        result = []
        new_terms = []
        
        for term_data in terms_data:
            term = term_data["term"]
            status = status_map.get(term)
            
            if status is None:
                # New term - add as pending
                result.append(term_data)
                new_terms.append({
                    "term": term,
                    "meaning": term_data["meaning"],
                    "status": "pending",
                    "createdAt": datetime.utcnow()
                })
            elif status in ["approved", "pending"]:
                # Include in result
                result.append(term_data)
            # disapproved terms are skipped
        
        # Bulk insert new terms
        if new_terms:
            try:
                self.collection.insert_many(new_terms, ordered=False)
            except Exception as e:
                # Handle duplicate key errors (race conditions)
                print(f"Insert warning: {e}")
        
        return result
    
    def update_status(self, term: str, status: str):
        """Update term status (for human approval/disapproval)"""
        self.collection.update_one(
            {"term": term},
            {"$set": {"status": status}}
        )
    
    def get_all_pending(self) -> List[Dict]:
        """Get all pending terms for review"""
        return list(self.collection.find({"status": "pending"}))
    
    def clear_all(self):
        """Clear all terms (for testing)"""
        self.collection.delete_many({})
