"""
Streamlit Term Manager UI with Japanese Support and Local State Management
Uses radio buttons for status selection and includes bulk operations
"""

import copy
from datetime import datetime

import pandas as pd
import streamlit as st

from manager import TermManager

# Translations
TRANSLATIONS = {
    "en": {
        "title": "📚 Term Status Manager",
        "filters": "Filters",
        "status": "Status",
        "search": "Search term",
        "all_statuses": "All Statuses",
        "pending": "Pending",
        "approved": "Approved",
        "disapproved": "Disapproved",
        "total": "Total Terms",
        "terms_shown": "Terms ({} shown)",
        "no_terms": "No terms found",
        "bulk_actions": "Bulk Actions",
        "approve_all": "✅ Approve All Filtered",
        "disapprove_all": "❌ Disapprove All Filtered",
        "delete_all_pending": "🗑️ Delete All Pending",
        "delete_all_filtered": "🗑️ Delete All Filtered",
        "approved_count": "Approved {} terms",
        "disapproved_count": "Disapproved {} terms",
        "deleted_count": "Deleted {} terms",
        "actions": "Actions",
        "refresh": "🔄 Refresh from DB",
        "update_db": "💾 Save Changes to DB",
        "undo": "↩️ Undo Last Change",
        "clear_all": "🗑️ Clear All Terms",
        "confirm_delete": "Confirm deletion",
        "all_deleted": "All terms deleted",
        "term": "Term",
        "meaning": "Meaning",
        "approve": "✅",
        "disapprove": "❌",
        "delete": "🗑️",
        "deleted": "Term deleted",
        "sort_by": "Sort by",
        "sort": "Sort",
        "changes_pending": "⚠️ {} unsaved changes",
        "no_changes": "✓ No pending changes",
        "saved": "Changes saved to database!",
        "undo_success": "Undone last change",
        "no_undo": "Nothing to undo",
        "edit_meaning": "Edit meaning",
        "save_meaning": "Save",
        "loaded_terms": "Loaded {} terms from database",
        "apply_changes": "Apply Changes",
        "editor_instructions": "Edit values directly in the table. Use the controls below to apply changes.",
        "loading": "Loading terms...",
        "status_radio_label": "Set Status",
    },
    "ja": {
        "title": "📚 用語ステータス管理",
        "filters": "フィルター",
        "status": "ステータス",
        "search": "用語を検索",
        "all_statuses": "全ステータス",
        "pending": "保留中",
        "approved": "承認済み",
        "disapproved": "却下済み",
        "total": "総用語数",
        "terms_shown": "用語 ({}件表示)",
        "no_terms": "用語が見つかりません",
        "bulk_actions": "一括操作",
        "approve_all": "✅ 絞込結果を全承認",
        "disapprove_all": "❌ 絞込結果を全却下",
        "delete_all_pending": "🗑️ 保留中を全削除",
        "delete_all_filtered": "🗑️ 絞込結果を全削除",
        "approved_count": "{}件の用語を承認しました",
        "disapproved_count": "{}件の用語を却下しました",
        "deleted_count": "{}件の用語を削除しました",
        "actions": "アクション",
        "refresh": "🔄 DBから更新",
        "update_db": "💾 変更を保存",
        "undo": "↩️ 元に戻す",
        "clear_all": "🗑️ 全削除",
        "confirm_delete": "削除を確認",
        "all_deleted": "全ての用語を削除しました",
        "term": "用語",
        "meaning": "意味",
        "approve": "✅",
        "disapprove": "❌",
        "delete": "🗑️",
        "deleted": "用語を削除しました",
        "sort_by": "並び替え",
        "sort": "並び替え",
        "changes_pending": "⚠️ {}件の未保存変更",
        "no_changes": "✓ 変更なし",
        "saved": "データベースに保存しました！",
        "undo_success": "変更を元に戻しました",
        "no_undo": "元に戻す操作がありません",
        "edit_meaning": "意味を編集",
        "save_meaning": "保存",
        "loaded_terms": "DBから{}件の用語を読み込みました",
        "apply_changes": "変更を適用",
        "editor_instructions": "表で直接値を編集してください。下のボタンで変更を適用します。",
        "loading": "用語を読み込み中...",
        "status_radio_label": "ステータス設定",
    },
}


# Initialize manager
@st.cache_resource
def get_manager():
    return TermManager()


manager = get_manager()

# Initialize session state
if "language" not in st.session_state:
    st.session_state.language = "en"
if "local_terms" not in st.session_state:
    st.session_state.local_terms = None
if "change_history" not in st.session_state:
    st.session_state.change_history = []
if "db_version" not in st.session_state:
    st.session_state.db_version = 0
if "current_edited_df" not in st.session_state:
    st.session_state.current_edited_df = None
if "original_df" not in st.session_state:
    st.session_state.original_df = None
if "message" not in st.session_state:
    st.session_state.message = None


# Get translations
def t(key):
    return TRANSLATIONS[st.session_state.language].get(key, key)


# Show message
def show_message(text, msg_type="info"):
    st.session_state.message = {"text": text, "type": msg_type}
    # Auto-clear message after 3 seconds
    st.rerun()


def clear_message():
    st.session_state.message = None


# Convert terms dict to DataFrame
def terms_to_dataframe(terms_dict):
    if not terms_dict:
        return pd.DataFrame(columns=["term", "meaning", "status"])

    df_data = []
    for term_data in terms_dict.values():
        df_data.append(
            {
                "term": term_data["term"],
                "meaning": term_data.get("meaning", ""),
                "status": term_data["status"],
            }
        )

    return pd.DataFrame(df_data)


# Convert DataFrame back to terms dict
def dataframe_to_terms(df):
    terms_dict = {}
    for _, row in df.iterrows():
        terms_dict[row["term"]] = {
            "term": row["term"],
            "meaning": row["meaning"],
            "status": row["status"],
        }
    return terms_dict


# Load ALL data from DB once
def load_from_db():
    """Load entire database into memory - ONE DB call"""
    terms = list(manager.collection.find())
    st.session_state.local_terms = {term["term"]: term for term in terms}
    st.session_state.change_history = []
    st.session_state.db_version += 1

    # Create original dataframe for comparison
    df = terms_to_dataframe(st.session_state.local_terms)
    st.session_state.original_df = df.copy()
    st.session_state.current_edited_df = df.copy()

    show_message(t("loaded_terms").format(len(terms)), "success")
    return len(terms)


# Initialize local terms if needed
if st.session_state.local_terms is None:
    with st.spinner(t("loading")):
        num_loaded = load_from_db()


# Track changes between original and edited dataframe
def detect_changes(original_df, edited_df):
    changes = []

    # Find modified rows
    merged = original_df.merge(edited_df, on="term", suffixes=("_orig", "_edited"))
    changed_rows = merged[
        (merged["meaning_orig"] != merged["meaning_edited"])
        | (merged["status_orig"] != merged["status_edited"])
    ]

    for _, row in changed_rows.iterrows():
        term_name = row["term"]
        if row["meaning_orig"] != row["meaning_edited"]:
            changes.append(
                {
                    "type": "meaning",
                    "term": term_name,
                    "old": row["meaning_orig"],
                    "new": row["meaning_edited"],
                }
            )

        if row["status_orig"] != row["status_edited"]:
            changes.append(
                {
                    "type": "status",
                    "term": term_name,
                    "old": row["status_orig"],
                    "new": row["status_edited"],
                }
            )

    # Find deleted rows (in original but not in edited)
    deleted_terms = set(original_df["term"]) - set(edited_df["term"])
    for term in deleted_terms:
        original_row = original_df[original_df["term"] == term].iloc[0]
        changes.append(
            {
                "type": "delete",
                "term": term,
                "old": {
                    "term": term,
                    "meaning": original_row["meaning"],
                    "status": original_row["status"],
                },
                "new": None,
            }
        )

    return changes


# Record a change for potential undo
def record_change(change_type, term_name, old_value, new_value):
    st.session_state.change_history.append(
        {
            "type": change_type,
            "term": term_name,
            "old": old_value,
            "new": new_value,
            "timestamp": datetime.now(),
        }
    )


# Undo last change
def undo_last_change():
    if not st.session_state.change_history:
        show_message(t("no_undo"), "info")
        return False

    last_change = st.session_state.change_history.pop()
    change_type = last_change["type"]
    term_name = last_change["term"]

    if change_type == "status":
        # Update status back to old value
        mask = st.session_state.current_edited_df["term"] == term_name
        st.session_state.current_edited_df.loc[mask, "status"] = last_change["old"]
    elif change_type == "meaning":
        # Update meaning back to old value
        mask = st.session_state.current_edited_df["term"] == term_name
        st.session_state.current_edited_df.loc[mask, "meaning"] = last_change["old"]
    elif change_type == "delete":
        # Restore the deleted term
        restored_term = last_change["old"]
        new_row = pd.DataFrame(
            [
                {
                    "term": restored_term["term"],
                    "meaning": restored_term["meaning"],
                    "status": restored_term["status"],
                }
            ]
        )
        st.session_state.current_edited_df = pd.concat(
            [st.session_state.current_edited_df, new_row], ignore_index=True
        )

    show_message(t("undo_success"), "success")
    return True


# Save all changes to DB - ONE batch operation
def save_to_db():
    """Process all changes in a single batch - minimal DB interaction"""
    if st.session_state.current_edited_df is None:
        return 0

    # Detect changes between original and current edited dataframe
    changes = detect_changes(
        st.session_state.original_df, st.session_state.current_edited_df
    )

    if not changes:
        return 0

    # Group changes by type for efficient batch processing
    status_updates = []
    meaning_updates = []
    deletions = []

    for change in changes:
        if change["type"] == "status":
            status_updates.append((change["term"], change["new"]))
        elif change["type"] == "meaning":
            meaning_updates.append((change["term"], change["new"]))
        elif change["type"] == "delete":
            deletions.append(change["term"])

    # Batch DB operations
    change_count = 0

    # Batch status updates
    for term, status in status_updates:
        manager.collection.update_one({"term": term}, {"$set": {"status": status}})
        change_count += 1

    # Batch meaning updates
    for term, meaning in meaning_updates:
        manager.collection.update_one({"term": term}, {"$set": {"meaning": meaning}})
        change_count += 1

    # Batch deletions
    if deletions:
        manager.collection.delete_many({"term": {"$in": deletions}})
        change_count += len(deletions)

    # Update local terms to reflect saved changes
    st.session_state.local_terms = dataframe_to_terms(
        st.session_state.current_edited_df
    )
    st.session_state.original_df = st.session_state.current_edited_df.copy()
    st.session_state.change_history = []
    st.session_state.db_version += 1

    show_message(t("saved"), "success")
    return change_count


# CLIENT-SIDE FILTERING (no DB calls)
def filter_dataframe(df, status_filters, search_query):
    """Filter dataframe in memory - zero DB calls"""
    filtered_df = df.copy()

    # Status filter
    if status_filters:
        filtered_df = filtered_df[filtered_df["status"].isin(status_filters)]

    # Search filter (searches both term and meaning)
    if search_query:
        search_lower = search_query.lower()
        term_mask = filtered_df["term"].str.contains(search_lower, case=False, na=False)
        meaning_mask = filtered_df["meaning"].str.contains(
            search_lower, case=False, na=False
        )
        filtered_df = filtered_df[term_mask | meaning_mask]

    return filtered_df


# CLIENT-SIDE STATS (no DB calls)
def get_stats(df):
    """Calculate stats in memory - zero DB calls"""
    if df.empty:
        return 0, 0, 0, 0

    total = len(df)
    pending = len(df[df["status"] == "pending"])
    approved = len(df[df["status"] == "approved"])
    disapproved = len(df[df["status"] == "disapproved"])

    return total, pending, approved, disapproved


# Bulk operations
def bulk_approve_filtered():
    if st.session_state.current_edited_df is None:
        return 0

    # Apply to the currently displayed/filtered terms
    filtered_df = filter_dataframe(
        st.session_state.current_edited_df, selected_statuses, search_term
    )
    count = 0

    for _, row in filtered_df.iterrows():
        if row["status"] != "approved":
            old_status = row["status"]
            mask = st.session_state.current_edited_df["term"] == row["term"]
            st.session_state.current_edited_df.loc[mask, "status"] = "approved"
            record_change("status", row["term"], old_status, "approved")
            count += 1

    if count > 0:
        show_message(t("approved_count").format(count), "success")
    return count


def bulk_disapprove_filtered():
    if st.session_state.current_edited_df is None:
        return 0

    # Apply to the currently displayed/filtered terms
    filtered_df = filter_dataframe(
        st.session_state.current_edited_df, selected_statuses, search_term
    )
    count = 0

    for _, row in filtered_df.iterrows():
        if row["status"] != "disapproved":
            old_status = row["status"]
            mask = st.session_state.current_edited_df["term"] == row["term"]
            st.session_state.current_edited_df.loc[mask, "status"] = "disapproved"
            record_change("status", row["term"], old_status, "disapproved")
            count += 1

    if count > 0:
        show_message(t("disapproved_count").format(count), "success")
    return count


def bulk_delete_filtered():
    if st.session_state.current_edited_df is None:
        return 0

    # Apply to the currently displayed/filtered terms
    filtered_df = filter_dataframe(
        st.session_state.current_edited_df, selected_statuses, search_term
    )
    count = 0

    for _, row in filtered_df.iterrows():
        # Store old value for potential undo
        old_value = (
            st.session_state.current_edited_df[
                st.session_state.current_edited_df["term"] == row["term"]
            ]
            .iloc[0]
            .to_dict()
        )

        # Remove from dataframe
        st.session_state.current_edited_df = st.session_state.current_edited_df[
            st.session_state.current_edited_df["term"] != row["term"]
        ]

        record_change("delete", row["term"], old_value, None)
        count += 1

    if count > 0:
        show_message(t("deleted_count").format(count), "success")
    return count


def bulk_delete_pending():
    if st.session_state.current_edited_df is None:
        return 0

    # Find all pending terms
    pending_df = st.session_state.current_edited_df[
        st.session_state.current_edited_df["status"] == "pending"
    ]
    count = 0

    for _, row in pending_df.iterrows():
        # Store old value for potential undo
        old_value = (
            st.session_state.current_edited_df[
                st.session_state.current_edited_df["term"] == row["term"]
            ]
            .iloc[0]
            .to_dict()
        )

        # Remove from dataframe
        st.session_state.current_edited_df = st.session_state.current_edited_df[
            st.session_state.current_edited_df["term"] != row["term"]
        ]

        record_change("delete", row["term"], old_value, None)
        count += 1

    if count > 0:
        show_message(t("deleted_count").format(count), "success")
    return count


# Page config
st.set_page_config(page_title="Term Manager", layout="wide")

# Language selector in top right
col_title, col_lang = st.columns([6, 1])
with col_title:
    st.title(t("title"))
with col_lang:
    st.write("")  # Spacing
    lang_option = st.selectbox(
        "🌐",
        options=["en", "ja"],
        index=0 if st.session_state.language == "en" else 1,
        label_visibility="collapsed",
    )
    if lang_option != st.session_state.language:
        st.session_state.language = lang_option
        st.rerun()

# Show message if exists
if st.session_state.message:
    msg = st.session_state.message
    if msg["type"] == "success":
        st.success(msg["text"])
    elif msg["type"] == "error":
        st.error(msg["text"])
    else:
        st.info(msg["text"])

# Show pending changes indicator
if st.session_state.current_edited_df is not None:
    changes = detect_changes(
        st.session_state.original_df, st.session_state.current_edited_df
    )
    num_changes = len(changes)
else:
    num_changes = 0

if num_changes > 0:
    st.warning(t("changes_pending").format(num_changes))
else:
    st.success(t("no_changes"))

# Action buttons at top
top_col1, top_col2, top_col3 = st.columns(3)
with top_col1:
    if st.button(
        t("update_db"),
        type="primary",
        disabled=num_changes == 0,
        use_container_width=True,
    ):
        saved_count = save_to_db()
        st.rerun()
with top_col2:
    if st.button(
        t("undo"),
        disabled=len(st.session_state.change_history) == 0,
        use_container_width=True,
    ):
        undo_last_change()
        st.rerun()
with top_col3:
    if st.button(t("refresh"), use_container_width=True):
        load_from_db()
        st.rerun()

st.divider()

# Sidebar - Filters (all client-side)
st.sidebar.header(t("filters"))

# Status filter with checkboxes
st.sidebar.subheader(t("status"))
selected_statuses = []
for status_key in ["pending", "approved", "disapproved"]:
    if st.sidebar.checkbox(t(status_key), value=True, key=f"status_{status_key}"):
        selected_statuses.append(status_key)

search_term = st.sidebar.text_input(t("search"), "")

# Stats (calculated in-memory)
if st.session_state.current_edited_df is not None:
    col1, col2, col3, col4 = st.columns(4)
    total, pending, approved, disapproved = get_stats(
        st.session_state.current_edited_df
    )
    col1.metric(t("total"), total)
    col2.metric(t("pending"), pending)
    col3.metric(t("approved"), approved)
    col4.metric(t("disapproved"), disapproved)

st.divider()

# Filter dataframe (all in-memory, no DB calls)
if st.session_state.current_edited_df is not None:
    filtered_df = filter_dataframe(
        st.session_state.current_edited_df, selected_statuses, search_term
    )

    if filtered_df.empty:
        st.info(t("no_terms"))
    else:
        st.subheader(t("terms_shown").format(len(filtered_df)))

        # Bulk actions
        with st.expander(t("bulk_actions"), expanded=False):
            bulk_col1, bulk_col2, bulk_col3, bulk_col4 = st.columns(4)

            with bulk_col1:
                if st.button(t("approve_all"), use_container_width=True):
                    bulk_approve_filtered()
                    st.rerun()

            with bulk_col2:
                if st.button(t("disapprove_all"), use_container_width=True):
                    bulk_disapprove_filtered()
                    st.rerun()

            with bulk_col3:
                if st.button(t("delete_all_filtered"), use_container_width=True):
                    bulk_delete_filtered()
                    st.rerun()

            with bulk_col4:
                if st.button(t("delete_all_pending"), use_container_width=True):
                    bulk_delete_pending()
                    st.rerun()

        # Display terms with radio buttons for status
        for i, term_row in filtered_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 4, 2, 1])

                with col1:
                    st.write(f"**{term_row['term']}**")

                with col2:
                    # Editable meaning
                    new_meaning = st.text_input(
                        t("edit_meaning"),
                        value=term_row["meaning"],
                        key=f"meaning_{term_row['term']}_{i}",
                        label_visibility="collapsed",
                    )

                    # Check if meaning was changed
                    if new_meaning != term_row["meaning"]:
                        mask = (
                            st.session_state.current_edited_df["term"]
                            == term_row["term"]
                        )
                        old_meaning = st.session_state.current_edited_df.loc[
                            mask, "meaning"
                        ].iloc[0]
                        st.session_state.current_edited_df.loc[mask, "meaning"] = (
                            new_meaning
                        )
                        record_change(
                            "meaning", term_row["term"], old_meaning, new_meaning
                        )

                with col3:
                    # Radio buttons for status
                    current_status = term_row["status"]
                    new_status = st.radio(
                        t("status_radio_label"),
                        options=["pending", "approved", "disapproved"],
                        index=["pending", "approved", "disapproved"].index(
                            current_status
                        ),
                        key=f"status_{term_row['term']}_{i}",
                        horizontal=True,
                        label_visibility="collapsed",
                    )

                    # Check if status was changed
                    if new_status != current_status:
                        mask = (
                            st.session_state.current_edited_df["term"]
                            == term_row["term"]
                        )
                        st.session_state.current_edited_df.loc[mask, "status"] = (
                            new_status
                        )
                        record_change(
                            "status", term_row["term"], current_status, new_status
                        )

                with col4:
                    if st.button(t("delete"), key=f"delete_{term_row['term']}_{i}"):
                        # Store old value for potential undo
                        old_value = (
                            st.session_state.current_edited_df[
                                st.session_state.current_edited_df["term"]
                                == term_row["term"]
                            ]
                            .iloc[0]
                            .to_dict()
                        )

                        # Remove from dataframe
                        st.session_state.current_edited_df = (
                            st.session_state.current_edited_df[
                                st.session_state.current_edited_df["term"]
                                != term_row["term"]
                            ]
                        )

                        record_change("delete", term_row["term"], old_value, None)
                        st.rerun()

else:
    st.error("Failed to load data from database")
