# server.py
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import ASCENDING, MongoClient

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allows all origins. In production, specify your React app's URL(s) e.g., ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


# --- TermManager Class ---
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
            {"term": {"$in": term_names}}, {"term": 1, "status": 1, "_id": 0}
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
                new_terms.append(
                    {
                        "term": term,
                        "meaning": term_data["meaning"],
                        "status": "pending",
                        "createdAt": datetime.utcnow(),
                    }
                )
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
        result = self.collection.update_one(
            {"term": term}, {"$set": {"status": status}}
        )
        if result.matched_count == 0:
            raise ValueError(f"Term '{term}' not found in database.")

    def update_meaning(self, term: str, meaning: str):
        """Update term meaning"""
        result = self.collection.update_one(
            {"term": term}, {"$set": {"meaning": meaning}}
        )
        if result.matched_count == 0:
            raise ValueError(f"Term '{term}' not found in database.")

    def get_all_pending(self) -> List[Dict]:
        """Get all pending terms for review"""
        terms = list(self.collection.find({"status": "pending"}, {"_id": 0}))
        for term in terms:
            if isinstance(term.get("createdAt"), datetime):
                term["createdAt"] = term["createdAt"].isoformat()
        return terms

    def get_all_terms(self, statuses: Optional[List[str]] = None) -> List[Dict]:
        """Get all terms, optionally filtered by status"""
        query = {}
        if statuses:
            query["status"] = {"$in": statuses}
        terms = list(self.collection.find(query, {"_id": 0}))
        for term in terms:
            if isinstance(term.get("createdAt"), datetime):
                term["createdAt"] = term["createdAt"].isoformat()
        return terms

    def delete_term(self, term: str):
        """Delete a term by name"""
        result = self.collection.delete_one({"term": term})
        if result.deleted_count == 0:
            raise ValueError(f"Term '{term}' not found in database.")

    def clear_all(self):
        """Clear all terms (for testing)"""
        self.collection.delete_many({})

    def get_stats(self) -> Dict[str, int]:
        """Get statistics on term counts by status"""
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        results = list(self.collection.aggregate(pipeline))
        stats = {doc["_id"]: doc["count"] for doc in results}
        # Ensure all statuses are present in the output
        for status in ["pending", "approved", "disapproved"]:
            if status not in stats:
                stats[status] = 0
        total = sum(stats.values())
        stats["total"] = total
        return stats


# Initialize the TermManager instance
term_manager = TermManager()


# --- Pydantic Models for Request/Response Bodies ---
class Term(BaseModel):
    term: str
    meaning: str
    status: str
    createdAt: Optional[str] = None  # ISO string format


class UpdateStatusRequest(BaseModel):
    status: str


class UpdateMeaningRequest(BaseModel):
    meaning: str


class BatchUpdateRequest(BaseModel):
    changes: List[Dict]  # Structure depends on your frontend history format


# --- API Routes ---
@app.get("/")
def read_root():
    return {"message": "Term Management API"}


@app.get("/terms")
async def get_terms(
    statuses: str = Query(
        None,
        description="Comma-separated list of statuses to filter by (e.g., 'pending,approved')",
    )
):
    try:
        status_list = None
        if statuses:
            status_list = [s.strip() for s in statuses.split(",")]
        terms = term_manager.get_all_terms(statuses=status_list)
        return terms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching terms: {str(e)}")


@app.get("/terms/stats")
async def get_term_stats():
    try:
        stats = term_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.put("/terms/{term_name}/status")
async def update_term_status(term_name: str, request: UpdateStatusRequest):
    try:
        term_manager.update_status(term_name, request.status)
        return {"message": f"Status updated for term '{term_name}'"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@app.put("/terms/{term_name}/meaning")
async def update_term_meaning(term_name: str, request: UpdateMeaningRequest):
    try:
        term_manager.update_meaning(term_name, request.meaning)
        return {"message": f"Meaning updated for term '{term_name}'"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating meaning: {str(e)}")


@app.delete("/terms/{term_name}")
async def delete_term(term_name: str):
    try:
        term_manager.delete_term(term_name)
        return {"message": f"Term '{term_name}' deleted successfully"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting term: {str(e)}")


@app.post("/terms/batch-update")
async def batch_update(request: BatchUpdateRequest):
    """
    Process a batch of changes from the frontend history.
    Expects a list of change objects like:
    [
      { "type": "status", "term": "React", "old": "pending", "new": "approved", ... },
      { "type": "meaning", "term": "Component", "old": "Old meaning", "new": "New meaning", ... },
      { "type": "delete", "term": "OldTerm", ... }
    ]
    """
    try:
        changes = request.changes
        results = []
        for change in changes:
            term_name = change.get("term")
            change_type = change.get("type")
            new_value = change.get("new")

            if not term_name or not change_type:
                results.append({"error": f"Invalid change object: {change}"})
                continue

            try:
                if change_type == "status":
                    term_manager.update_status(term_name, new_value)
                    results.append({"success": f"Status updated for '{term_name}'"})
                elif change_type == "meaning":
                    term_manager.update_meaning(term_name, new_value)
                    results.append({"success": f"Meaning updated for '{term_name}'"})
                elif change_type == "delete":
                    term_manager.delete_term(term_name)
                    results.append({"success": f"Term '{term_name}' deleted"})
                else:
                    results.append(
                        {
                            "error": f"Unknown change type '{change_type}' for term '{term_name}'"
                        }
                    )
            except ValueError as ve:
                results.append({"error": f"Term '{term_name}' not found: {str(ve)}"})
            except Exception as e:
                results.append(
                    {"error": f"Failed to apply change for '{term_name}': {str(e)}"}
                )

        return {"results": results, "processed_count": len(changes)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing batch update: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
