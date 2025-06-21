import React, { useEffect, useState } from 'react';
import { getFilePreview } from '../services/api';

const FilePreview = ({ fileData, onPreviewLoaded, onContinue, onError, onBack }) => {
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPreview = async () => {
      try {
        console.log('👀 FilePreview: Loading preview for file:', fileData.id);
        setLoading(true);
        
        const preview = await getFilePreview(fileData.id);
        console.log('👀 FilePreview: Preview loaded successfully:', preview);
        
        setPreviewData(preview);
        
        // FIX: Only call onPreviewLoaded to store data, don't advance step
        onPreviewLoaded(preview);
        console.log('👀 FilePreview: Called onPreviewLoaded, staying on preview screen');
        
      } catch (error) {
        console.error('👀 FilePreview: Preview loading failed:', error);
        onError(error.message || 'Failed to load file preview');
      } finally {
        console.log('👀 FilePreview: Setting loading to false');
        setLoading(false);
      }
    };

    if (fileData && fileData.id) {
      loadPreview();
    }
  }, [fileData, onPreviewLoaded, onError]); // Removed onContinue from dependencies

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading file preview...</p>
      </div>
    );
  }

  if (!previewData) {
    return (
      <div className="error-container">
        <p>Failed to load file preview</p>
        <button onClick={onBack} className="btn btn-secondary">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="file-preview-container">
      <div className="preview-header">
        <h2>File Preview</h2>
        <div className="file-info">
          <span className="file-name">{fileData.filename}</span>
          <span className="file-stats">
            {previewData.total_rows} rows • {previewData.columns.length} columns
          </span>
        </div>
      </div>

      <div className="preview-content">
        <div className="table-container">
          <table className="preview-table">
            <thead>
              <tr>
                {previewData.columns.map((column, index) => (
                  <th key={index} className={previewData.text_columns.includes(column) ? 'text-column' : ''}>
                    {column}
                    {previewData.text_columns.includes(column) && (
                      <span className="column-badge">Text</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewData.preview_data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {previewData.columns.map((column, colIndex) => (
                    <td key={colIndex}>
                      {row[column] !== null && row[column] !== undefined ? String(row[column]) : ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {previewData.total_rows > 10 && (
          <div className="preview-note">
            <p>Showing first 10 rows of {previewData.total_rows} total rows</p>
          </div>
        )}

        <div className="text-columns-info">
          <h3>Text Columns Available for Pattern Matching</h3>
          <div className="columns-list">
            {previewData.text_columns.length > 0 ? (
              previewData.text_columns.map((column, index) => (
                <span key={index} className="column-tag">{column}</span>
              ))
            ) : (
              <p className="no-text-columns">No text columns detected in this file</p>
            )}
          </div>
        </div>
      </div>

      <div className="preview-actions">
        <button onClick={onBack} className="btn btn-secondary">
          ← Upload Different File
        </button>
        
        {/* FIX: Call onContinue instead of onPreviewLoaded */}
        <button 
          onClick={onContinue} 
          className="btn btn-primary"
          disabled={previewData.text_columns.length === 0}
        >
          Continue to Pattern Matching →
        </button>
      </div>
    </div>
  );
};

export default FilePreview;