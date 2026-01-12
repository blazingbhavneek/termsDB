import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, Save, Undo, Globe, Trash2, Check, X } from 'lucide-react';

// Translations
const TRANSLATIONS = {
  en: {
    title: "Term Status Manager",
    filters: "Filters",
    status: "Status",
    search: "Search term",
    pending: "Pending",
    approved: "Approved",
    disapproved: "Disapproved",
    total: "Total Terms",
    termsShown: "Terms ({count} shown)",
    noTerms: "No terms found",
    bulkActions: "Bulk Actions",
    approveAll: "Approve All Filtered",
    disapproveAll: "Disapprove All Filtered",
    deleteAllFiltered: "Delete All Filtered",
    refresh: "Refresh from DB",
    updateDb: "Save Changes to DB",
    undo: "Undo Last Change",
    changesPending: "{count} unsaved changes",
    noChanges: "No pending changes",
    saved: "Changes saved to database!",
    undoSuccess: "Undone last change",
    noUndo: "Nothing to undo",
    editMeaning: "Edit meaning",
    loadedTerms: "Loaded {count} terms from database",
    sortBy: "Sort by",
    approvedCount: "Approved {count} terms",
    disapprovedCount: "Disapproved {count} terms",
    deletedCount: "Deleted {count} terms"
  },
  ja: {
    title: "用語ステータス管理",
    filters: "フィルター",
    status: "ステータス",
    search: "用語を検索",
    pending: "保留中",
    approved: "承認済み",
    disapproved: "却下済み",
    total: "総用語数",
    termsShown: "用語 ({count}件表示)",
    noTerms: "用語が見つかりません",
    bulkActions: "一括操作",
    approveAll: "絞込結果を全承認",
    disapproveAll: "絞込結果を全却下",
    deleteAllFiltered: "絞込結果を全削除",
    refresh: "DBから更新",
    updateDb: "変更を保存",
    undo: "元に戻す",
    changesPending: "{count}件の未保存変更",
    noChanges: "変更なし",
    saved: "データベースに保存しました！",
    undoSuccess: "変更を元に戻しました",
    noUndo: "元に戻す操作がありません",
    editMeaning: "意味を編集",
    loadedTerms: "DBから{count}件の用語を読み込みました",
    sortBy: "並び替え",
    approvedCount: "{count}件の用語を承認しました",
    disapprovedCount: "{count}件の用語を却下しました",
    deletedCount: "{count}件の用語を削除しました"
  }
};

// Replace the entire API object definition with this:
const API = {
  async loadTerms() {
    // Replace with your actual backend URL if different
    const response = await fetch('http://localhost:8000/terms');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  async saveChanges(changes) {
    // This endpoint might require adjustment depending on how you implement batch updates in FastAPI.
    // For now, assuming you send the history to apply changes.
    // You might need separate endpoints for status updates, meaning updates, and deletions.
    const response = await fetch('http://localhost:8000/terms/batch-update', { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ changes }),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json(); // Assuming the backend returns success info
  },
  
  // Add other potential API calls if needed by your UI interactions
  async updateTermStatus(term, status) {
     const response = await fetch(`http://localhost:8000/terms/${encodeURIComponent(term)}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
  },
  
   async updateTermMeaning(term, meaning) {
     const response = await fetch(`http://localhost:8000/terms/${encodeURIComponent(term)}/meaning`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ meaning }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
  },
  
  async deleteTerm(term) {
      const response = await fetch(`http://localhost:8000/terms/${encodeURIComponent(term)}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
  }
};

function App() {
  const [language, setLanguage] = useState('en');
  const [localTerms, setLocalTerms] = useState({});
  const [changeHistory, setChangeHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(null);
  
  // Filters
  const [statusFilters, setStatusFilters] = useState({
    pending: true,
    approved: true,
    disapproved: true
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState(null); // Can be null for default sort
  const [editingMeaning, setEditingMeaning] = useState({});

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 200;

  const t = (key, params = {}) => {
    let text = TRANSLATIONS[language][key] || key;
    Object.keys(params).forEach(k => {
      text = text.replace(`{${k}}`, params[k]);
    });
    return text;
  };

  useEffect(() => {
    loadFromDb();
  }, []);

  const loadFromDb = async () => {
    setLoading(true);
    try {
      const terms = await API.loadTerms();
      const termsMap = {};
      terms.forEach(term => {
        termsMap[term.term] = term; 
      });
      setLocalTerms(termsMap);
      setChangeHistory([]); // Clear local history on fresh load
      setCurrentPage(1); // Reset to first page when data loads
      showMessage(t('loadedTerms', { count: terms.length }), 'success');
    } catch (error) {
      console.error("Failed to load terms from DB:", error);
      showMessage('Error loading terms: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (text, type = 'info') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 3000);
  };

  const recordChange = (type, termName, oldValue, newValue) => {
    setChangeHistory(prev => [...prev, {
      type,
      term: termName,
      old: oldValue,
      new: newValue,
      timestamp: new Date()
    }]);
  };

  const updateLocalStatus = async (termName, newStatus) => {
    if (localTerms[termName] && localTerms[termName].status !== newStatus) {
      const oldStatus = localTerms[termName].status;
      recordChange('status', termName, oldStatus, newStatus);
      
      // Optimistically update local state
      setLocalTerms(prev => ({
        ...prev,
        [termName]: { ...prev[termName], status: newStatus }
      }));

      try {
         await API.updateTermStatus(termName, newStatus); 
      } catch (error) {
         console.error(`Failed to update status for ${termName}:`, error);
         setLocalTerms(prev => ({
           ...prev,
           [termName]: { ...prev[termName], status: oldStatus } // Revert
         }));
         setChangeHistory(prev => prev.slice(0, -1)); 
         showMessage(`Error updating ${termName}: ${error.message}`, 'error');
      }
    }
  };

  const updateLocalMeaning = (termName, newMeaning) => {
    if (localTerms[termName]) {
      const oldMeaning = localTerms[termName].meaning || '';
      if (oldMeaning !== newMeaning) {
        recordChange('meaning', termName, oldMeaning, newMeaning);
        setLocalTerms(prev => ({
          ...prev,
          [termName]: { ...prev[termName], meaning: newMeaning }
        }));
        setEditingMeaning(prev => {
          const next = { ...prev };
          delete next[termName];
          return next;
        });
      }
    }
  };

  const deleteLocalTerm = (termName) => {
    if (localTerms[termName]) {
      const oldTerm = { ...localTerms[termName] };
      recordChange('delete', termName, oldTerm, null);
      setLocalTerms(prev => {
        const next = { ...prev };
        delete next[termName];
        return next;
      });
    }
  };

  const undoLastChange = () => {
    if (changeHistory.length === 0) {
      showMessage(t('noUndo'), 'info');
      return;
    }

    const lastChange = changeHistory[changeHistory.length - 1];
    setChangeHistory(prev => prev.slice(0, -1));

    if (lastChange.type === 'status' && localTerms[lastChange.term]) {
      setLocalTerms(prev => ({
        ...prev,
        [lastChange.term]: { ...prev[lastChange.term], status: lastChange.old }
      }));
    } else if (lastChange.type === 'meaning' && localTerms[lastChange.term]) {
      setLocalTerms(prev => ({
        ...prev,
        [lastChange.term]: { ...prev[lastChange.term], meaning: lastChange.old }
      }));
    } else if (lastChange.type === 'delete') {
      setLocalTerms(prev => ({
        ...prev,
        [lastChange.term]: lastChange.old
      }));
    }

    showMessage(t('undoSuccess'), 'success');
  };

  const saveToDb = async () => {
    if (changeHistory.length === 0) {
       showMessage(t('noChanges'), 'info');
       return; 
    }

    try {
      const result = await API.saveChanges(changeHistory); 
      setChangeHistory([]); // Clear history after successful save
      showMessage(t('saved'), 'success');
    } catch (error) {
      console.error("Failed to save changes to DB:", error);
      showMessage('Error saving: ' + error.message, 'error');
    }
  };

  // Filter and sort terms
  const getFilteredTerms = () => {
    const selectedStatuses = Object.keys(statusFilters).filter(k => statusFilters[k]);
    const searchLower = searchQuery.toLowerCase();

    let filtered = Object.values(localTerms).filter(term => {
      if (selectedStatuses.length && !selectedStatuses.includes(term.status)) {
        return false;
      }
      if (searchLower) {
        const termMatch = term.term.toLowerCase().includes(searchLower);
        const meaningMatch = (term.meaning || '').toLowerCase().includes(searchLower);
        return termMatch || meaningMatch;
      }
      return true;
    });

    // Sort
    if (sortBy) {
      const priority = { [sortBy]: 0, pending: 1, approved: 2, disapproved: 3 };
      filtered.sort((a, b) => {
        const aPri = priority[a.status] || 999;
        const bPri = priority[b.status] || 999;
        return aPri - bPri;
      });
    } else {
      filtered.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    }

    return filtered;
  };

  // Get paginated terms
  const getPaginatedTerms = () => {
    const filtered = getFilteredTerms();
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filtered.slice(startIndex, endIndex);
  };

  const getStats = () => {
    const terms = Object.values(localTerms);
    return {
      total: terms.length,
      pending: terms.filter(t => t.status === 'pending').length,
      approved: terms.filter(t => t.status === 'approved').length,
      disapproved: terms.filter(t => t.status === 'disapproved').length
    };
  };

  const bulkApprove = () => {
    let count = 0;
    filteredTerms.forEach(term => {
      if (term.status !== 'approved') {
        updateLocalStatus(term.term, 'approved');
        count++;
      }
    });
    showMessage(t('approvedCount', { count }), 'success');
  };

  const bulkDisapprove = () => {
    let count = 0;
    filteredTerms.forEach(term => {
      if (term.status !== 'disapproved') {
        updateLocalStatus(term.term, 'disapproved');
        count++;
      }
    });
    showMessage(t('disapprovedCount', { count }), 'success');
  };

  const bulkDelete = () => {
    const count = filteredTerms.length;
    filteredTerms.forEach(term => {
      deleteLocalTerm(term.term);
    });
    showMessage(t('deletedCount', { count }), 'success');
  };

  const filteredTerms = getPaginatedTerms(); // Use paginated terms
  const allFilteredTerms = getFilteredTerms(); // For pagination controls
  const totalPages = Math.ceil(allFilteredTerms.length / itemsPerPage);
  const stats = getStats();
  const selectedStatuses = Object.keys(statusFilters).filter(k => statusFilters[k]);

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    disapproved: 'bg-red-100 text-red-800'
  };

  const statusIcons = {
    pending: '🟡',
    approved: '🟢',
    disapproved: '🔴'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-500" />
          <p className="text-gray-600">Loading terms...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">
              📚 {t('title')}
            </h1>
            <button
              onClick={() => setLanguage(language === 'en' ? 'ja' : 'en')}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
            >
              <Globe className="w-5 h-5" />
              {language === 'en' ? 'EN' : '日本語'}
            </button>
          </div>
        </div>
      </div>

      {/* Message Toast */}
      {message && (
        <div className="fixed top-4 right-4 z-50 animate-slide-in">
          <div className={`px-6 py-3 rounded-lg shadow-lg ${
            message.type === 'success' ? 'bg-green-500' :
            message.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
          } text-white`}>
            {message.text}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Status Banner */}
        <div className={`mb-6 p-4 rounded-lg ${
          changeHistory.length > 0 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'
        }`}>
          <p className={`text-sm font-medium ${
            changeHistory.length > 0 ? 'text-yellow-800' : 'text-green-800'
          }`}>
            {changeHistory.length > 0 
              ? `⚠️ ${t('changesPending', { count: changeHistory.length })}`
              : `✓ ${t('noChanges')}`
            }
          </p>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button
            onClick={saveToDb}
            disabled={changeHistory.length === 0}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            <Save className="w-5 h-5" />
            {t('updateDb')}
          </button>
          <button
            onClick={undoLastChange}
            disabled={changeHistory.length === 0}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            <Undo className="w-5 h-5" />
            {t('undo')}
          </button>
          <button
            onClick={loadFromDb}
            className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
          >
            <RefreshCw className="w-5 h-5" />
            {t('refresh')}
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">{t('total')}</p>
            <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">{t('pending')}</p>
            <p className="text-3xl font-bold text-yellow-600">{stats.pending}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">{t('approved')}</p>
            <p className="text-3xl font-bold text-green-600">{stats.approved}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">{t('disapproved')}</p>
            <p className="text-3xl font-bold text-red-600">{stats.disapproved}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Filters */}
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold mb-4">{t('filters')}</h2>
              
              {/* Search */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('search')}
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder={t('search')}
                  />
                </div>
              </div>

              {/* Status Filters */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('status')}
                </label>
                {['pending', 'approved', 'disapproved'].map(status => (
                  <label key={status} className="flex items-center mb-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={statusFilters[status]}
                      onChange={(e) => setStatusFilters(prev => ({
                        ...prev,
                        [status]: e.target.checked
                      }))}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">{t(status)}</span>
                  </label>
                ))}
              </div>

              {/* Sort Options */}
              {selectedStatuses.length > 1 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('sortBy')}
                  </label>
                  <label className="flex items-center mb-2 cursor-pointer">
                    <input
                      type="radio"
                      name="sort"
                      checked={sortBy === null}
                      onChange={() => setSortBy(null)}
                      className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Default</span>
                  </label>
                  {selectedStatuses.map(status => (
                    <label key={status} className="flex items-center mb-2 cursor-pointer">
                      <input
                        type="radio"
                        name="sort"
                        checked={sortBy === status}
                        onChange={() => setSortBy(status)}
                        className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{t(status)}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold">
                  {t('termsShown', { count: allFilteredTerms.length })}
                </h2>
              </div>

              {/* Bulk Actions */}
              <div className="p-6 border-b border-gray-200 bg-gray-50">
                <details className="cursor-pointer">
                  <summary className="font-medium text-gray-900 mb-4">
                    {t('bulkActions')}
                  </summary>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
                    <button
                      onClick={bulkApprove}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                    >
                      {t('approveAll')}
                    </button>
                    <button
                      onClick={bulkDisapprove}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
                    >
                      {t('disapproveAll')}
                    </button>
                    <button
                      onClick={bulkDelete}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition"
                    >
                      {t('deleteAllFiltered')}
                    </button>
                  </div>
                </details>
              </div>

              {/* Terms List */}
              <div className="divide-y divide-gray-200">
                {filteredTerms.length === 0 ? (
                  <div className="p-12 text-center text-gray-500">
                    {t('noTerms')}
                  </div>
                ) : (
                  filteredTerms.map((term, i) => (
                    <div key={term.term} className="p-6 hover:bg-gray-50 transition">
                      <div className="grid grid-cols-12 gap-4 items-center">
                        {/* Term Name */}
                        <div className="col-span-12 md:col-span-2">
                          <p className="font-semibold text-gray-900">{term.term}</p>
                        </div>

                        {/* Meaning */}
                        <div className="col-span-12 md:col-span-4">
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={editingMeaning[term.term] !== undefined 
                                ? editingMeaning[term.term] 
                                : term.meaning || ''}
                              onChange={(e) => setEditingMeaning(prev => ({
                                ...prev,
                                [term.term]: e.target.value
                              }))}
                              className="flex-1 px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              placeholder={t('editMeaning')}
                            />
                            {editingMeaning[term.term] !== undefined && 
                             editingMeaning[term.term] !== term.meaning && (
                              <button
                                onClick={() => updateLocalMeaning(term.term, editingMeaning[term.term])}
                                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                              >
                                💾
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Status Badge */}
                        <div className="col-span-12 md:col-span-2">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColors[term.status]}`}>
                            {statusIcons[term.status]} {t(term.status)}
                          </span>
                        </div>

                        {/* Actions */}
                        <div className="col-span-12 md:col-span-4 flex gap-2 justify-end">
                          {term.status !== 'approved' && (
                            <button
                              onClick={() => updateLocalStatus(term.term, 'approved')}
                              className="p-2 bg-green-100 text-green-700 rounded hover:bg-green-200 transition"
                              title={t('approved')}
                            >
                              <Check className="w-5 h-5" />
                            </button>
                          )}
                          {term.status !== 'disapproved' && (
                            <button
                              onClick={() => updateLocalStatus(term.term, 'disapproved')}
                              className="p-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition"
                              title={t('disapproved')}
                            >
                              <X className="w-5 h-5" />
                            </button>
                          )}
                          {term.status !== 'pending' && (
                            <button
                              onClick={() => updateLocalStatus(term.term, 'pending')}
                              className="p-2 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition"
                              title={t('pending')}
                            >
                              🔄
                            </button>
                          )}
                          <button
                            onClick={() => deleteLocalTerm(term.term)}
                            className="p-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition"
                            title="Delete"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="p-6 border-t border-gray-200 flex justify-between items-center">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  <span className="text-gray-700">
                    Page {currentPage} of {totalPages} ({allFilteredTerms.length} total items)
                  </span>
                  
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;