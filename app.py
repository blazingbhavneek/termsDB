"""
Streamlit Term Manager UI
View and edit term statuses with filtering
"""

import streamlit as st
import pandas as pd
from manager import TermManager

# Initialize manager
@st.cache_resource
def get_manager():
    return TermManager()

manager = get_manager()

# Page config
st.set_page_config(page_title="Term Manager", layout="wide")
st.title("📚 Term Status Manager")

# Sidebar - Filters
st.sidebar.header("Filters")
status_filter = st.sidebar.multiselect(
    "Status",
    options=["pending", "approved", "disapproved"],
    default=["pending", "approved", "disapproved"]
)

search_term = st.sidebar.text_input("Search term", "")

# Stats
col1, col2, col3, col4 = st.columns(4)

def get_stats():
    all_terms = list(manager.collection.find())
    df = pd.DataFrame(all_terms)
    if df.empty:
        return 0, 0, 0, 0
    
    total = len(df)
    pending = len(df[df['status'] == 'pending'])
    approved = len(df[df['status'] == 'approved'])
    disapproved = len(df[df['status'] == 'disapproved'])
    return total, pending, approved, disapproved

total, pending, approved, disapproved = get_stats()

col1.metric("Total Terms", total)
col2.metric("Pending", pending)
col3.metric("Approved", approved)
col4.metric("Disapproved", disapproved)

st.divider()

# Fetch and display terms
query = {}
if status_filter:
    query["status"] = {"$in": status_filter}
if search_term:
    query["term"] = {"$regex": search_term, "$options": "i"}

terms = list(manager.collection.find(query).sort("createdAt", -1).limit(100))

if not terms:
    st.info("No terms found")
else:
    st.subheader(f"Terms ({len(terms)} shown)")
    
    # Bulk actions
    with st.expander("Bulk Actions"):
        bulk_col1, bulk_col2 = st.columns(2)
        
        with bulk_col1:
            if st.button("✅ Approve All Pending"):
                result = manager.collection.update_many(
                    {"status": "pending"},
                    {"$set": {"status": "approved"}}
                )
                st.success(f"Approved {result.modified_count} terms")
                st.rerun()
        
        with bulk_col2:
            if st.button("❌ Disapprove All Pending"):
                result = manager.collection.update_many(
                    {"status": "pending"},
                    {"$set": {"status": "disapproved"}}
                )
                st.success(f"Disapproved {result.modified_count} terms")
                st.rerun()
    
    # Display terms in table format
    for i, term in enumerate(terms):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 4, 1, 1, 1])
            
            # Status badge color
            status_colors = {
                "pending": "🟡",
                "approved": "🟢",
                "disapproved": "🔴"
            }
            
            with col1:
                st.write(f"**{term['term']}**")
            
            with col2:
                st.write(term['meaning'])
            
            with col3:
                st.write(f"{status_colors[term['status']]} {term['status']}")
            
            with col4:
                if term['status'] != 'approved':
                    if st.button("✅", key=f"approve_{i}"):
                        manager.update_status(term['term'], 'approved')
                        st.rerun()
            
            with col5:
                if term['status'] != 'disapproved':
                    if st.button("❌", key=f"disapprove_{i}"):
                        manager.update_status(term['term'], 'disapproved')
                        st.rerun()
            
            st.divider()

# Footer actions
st.sidebar.divider()
st.sidebar.header("Actions")

if st.sidebar.button("🔄 Refresh"):
    st.rerun()

if st.sidebar.button("🗑️ Clear All Terms", type="secondary"):
    if st.sidebar.checkbox("Confirm deletion"):
        manager.clear_all()
        st.sidebar.success("All terms deleted")
        st.rerun()
