import React, { useState, useCallback } from 'react';
import { processPatternMatching } from '../services/api';

const PatternMatcher = ({ fileData, previewData, onProcessingComplete, onError, onBack, setLoading }) => {
  const [formData, setFormData] = useState({
    naturalLanguageQuery: '',
    replacementValue: '',
    targetColumn: ''
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  const commonPatterns = [
    {
      label: 'Email Addresses',
      query: 'find email addresses',
      example: 'user@example.com → REDACTED'
    },
    {
      label: 'Phone Numbers',
      query: 'find phone numbers',
      example: '(555) 123-4567 → ***-***-****'
    },
    {
      label: 'Credit Card Numbers',
      query: 'find credit card numbers',
      example: '4532-1234-5678-9012 → ****-****-****-****'
    },
    {
      label: 'Social Security Numbers',
      query: 'find social security numbers',
      example: '123-45-6789 → ***-**-****'
    },
    {
      label: 'URLs',
      query: 'find website URLs',
      example: 'https://example.com → [LINK REMOVED]'
    },
    {
      label: 'IP Addresses',
      query: 'find IP addresses',
      example: '192.168.1.1 → [IP HIDDEN]'
    }
  ];

  const handleInputChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);

  const handlePatternSelect = useCallback((pattern) => {
    setFormData(prev => ({
      ...prev,
      naturalLanguageQuery: pattern.query
    }));
  }, []);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    
    if (!formData.naturalLanguageQuery.trim()) {
      onError('Please describe the pattern you want to find');
      return;
    }
    
    if (!formData.replacementValue.trim()) {
      onError('Please specify a replacement value');
      return;
    }

    try {
      setLoading(true);
      const result = await processPatternMatching({
        file_id: fileData.id,
        natural_language_query: formData.naturalLanguageQuery,
        replacement_value: formData.replacementValue,
        target_column: formData.targetColumn
      });
      
      onProcessingComplete(result);
    } catch (error) {
      onError(error.message || 'Failed to process pattern matching');
    }
  }, [formData, fileData.id, onProcessingComplete, onError, setLoading]);

  return (
    <div className="pattern-matcher-container">
      <div className="pattern-header">
        <h2>Pattern Matching & Replacement</h2>
        <p>Describe the pattern you want to find in natural language</p>
      </div>

      <div className="pattern-content">
        <div className="quick-patterns">
          <h3>Quick Patterns</h3>
          <div className="patterns-grid">
            {commonPatterns.map((pattern, index) => (
              <div 
                key={index} 
                className="pattern-card"
                onClick={() => handlePatternSelect(pattern)}
              >
                <h4>{pattern.label}</h4>
                <p className="pattern-example">{pattern.example}</p>
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="pattern-form">
          <div className="form-group">
            <label htmlFor="naturalLanguageQuery">
              Describe the pattern to find *
            </label>
            <textarea
              id="naturalLanguageQuery"
              name="naturalLanguageQuery"
              value={formData.naturalLanguageQuery}
              onChange={handleInputChange}
              placeholder="e.g., 'find email addresses', 'find phone numbers in format (xxx) xxx-xxxx', 'find dates in MM/DD/YYYY format'"
              rows={3}
              required
            />
            <small className="form-hint">
              Use natural language to describe what you want to find. The AI will convert this to a regex pattern.
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="replacementValue">
              Replacement value *
            </label>
            <input
              type="text"
              id="replacementValue"
              name="replacementValue"
              value={formData.replacementValue}
              onChange={handleInputChange}
              placeholder="e.g., 'REDACTED', '[HIDDEN]', '***'"
              required
            />
            <small className="form-hint">
              This text will replace all matches found by the pattern.
            </small>
          </div>

          <div className="advanced-options">
            <button
              type="button"
              className="advanced-toggle"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? '▼' : '▶'} Advanced Options
            </button>

            {showAdvanced && (
              <div className="advanced-content">
                <div className="form-group">
                  <label htmlFor="targetColumn">
                    Target column (optional)
                  </label>
                  <select
                    id="targetColumn"
                    name="targetColumn"
                    value={formData.targetColumn}
                    onChange={handleInputChange}
                  >
                    <option value="">All text columns</option>
                    {previewData.text_columns.map((column, index) => (
                      <option key={index} value={column}>
                        {column}
                      </option>
                    ))}
                  </select>
                  <small className="form-hint">
                    Leave empty to search all text columns, or select a specific column.
                  </small>
                </div>
              </div>
            )}
          </div>

          <div className="form-actions">
            <button type="button" onClick={onBack} className="btn btn-secondary">
              ← Back to Preview
            </button>
            <button type="submit" className="btn btn-primary">
              Process Data →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PatternMatcher;