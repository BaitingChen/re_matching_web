import React, { useState } from 'react';

const ResultsDisplay = ({ results, onStartOver, onBack }) => {
  const [viewMode, setViewMode] = useState('processed'); // 'original' or 'processed'
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const currentData = viewMode === 'processed' ? results.processed_data : results.original_data;
  const totalPages = Math.ceil(currentData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedData = currentData.slice(startIndex, endIndex);

  const downloadCSV = () => {
    const csvContent = convertToCSV(results.processed_data);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'processed_data.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const convertToCSV = (data) => {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');
    
    const csvRows = data.map(row => 
      headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value.replace(/"/g, '""')}"` 
          : value;
      }).join(',')
    );
    
    return [csvHeaders, ...csvRows].join('\n');
  };

  const getTotalReplacements = () => {
    return Object.values(results.replacement_stats || {}).reduce((sum, count) => sum + count, 0);
  };

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>Processing Results</h2>
        {results.success ? (
          <div className="success-message">
            <span className="success-icon">✅</span>
            <span>Pattern matching completed successfully!</span>
          </div>
        ) : (
          <div className="error-message">
            <span className="error-icon">❌</span>
            <span>Processing failed: {results.error}</span>
          </div>
        )}
      </div>

      {results.success && (
        <>
          <div className="results-summary">
            <div className="summary-cards">
              <div className="summary-card">
                <h3>Pattern Used</h3>
                <code className="regex-pattern">{results.regex_pattern}</code>
                {results.explanation && (
                  <p className="pattern-explanation">{results.explanation}</p>
                )}
              </div>
              
              <div className="summary-card">
                <h3>Replacements Made</h3>
                <div className="replacement-stats">
                  <div className="total-replacements">
                    <span className="stat-number">{getTotalReplacements()}</span>
                    <span className="stat-label">Total Replacements</span>
                  </div>
                  {Object.entries(results.replacement_stats || {}).map(([column, count]) => (
                    <div key={column} className="column-stat">
                      <span className="column-name">{column}:</span>
                      <span className="column-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="results-controls">
            <div className="view-toggles">
              <button 
                className={`toggle-btn ${viewMode === 'original' ? 'active' : ''}`}
                onClick={() => {
                  setViewMode('original');
                  setCurrentPage(1);
                }}
              >
                Original Data
              </button>
              <button 
                className={`toggle-btn ${viewMode === 'processed' ? 'active' : ''}`}
                onClick={() => {
                  setViewMode('processed');
                  setCurrentPage(1);
                }}
              >
                Processed Data
              </button>
            </div>
            
            <button onClick={downloadCSV} className="btn btn-download">
              📥 Download CSV
            </button>
          </div>

          <div className="data-table-container">
            <div className="table-info">
              <span>
                Showing {startIndex + 1}-{Math.min(endIndex, currentData.length)} of {currentData.length} rows
              </span>
            </div>
            
            <table className="results-table">
              <thead>
                <tr>
                  {results.columns.map((column, index) => (
                    <th key={index}>
                      {column}
                      {results.replacement_stats?.[column] > 0 && (
                        <span className="modified-indicator" title={`${results.replacement_stats[column]} replacements made`}>
                          ●
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginatedData.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {results.columns.map((column, colIndex) => {
                      const value = row[column];
                      const originalValue = results.original_data[startIndex + rowIndex]?.[column];
                      const isModified = viewMode === 'processed' && value !== originalValue;
                      
                      return (
                        <td key={colIndex} className={isModified ? 'modified-cell' : ''}>
                          {value !== null && value !== undefined ? String(value) : ''}
                          {isModified && (
                            <span className="modification-indicator" title={`Original: ${originalValue}`}>
                              ✏️
                            </span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>

            {totalPages > 1 && (
              <div className="pagination">
                <button 
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="pagination-btn"
                >
                  ← Previous
                </button>
                
                <span className="pagination-info">
                  Page {currentPage} of {totalPages}
                </span>
                
                <button 
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="pagination-btn"
                >
                  Next →
                </button>
              </div>
            )}
          </div>
        </>
      )}

      <div className="results-actions">
        <button onClick={onBack} className="btn btn-secondary">
          ← Modify Pattern
        </button>
        <button onClick={onStartOver} className="btn btn-primary">
          🔄 Process New File
        </button>
      </div>
    </div>
  );
};

export default ResultsDisplay;