import React, { useState, useCallback } from 'react';
import { processPatternMatching } from '../services/api';

const PatternMatcher = ({ fileData, previewData, onProcessingComplete, onError, onBack, setLoading }) => {
  const [formData, setFormData] = useState({
    naturalLanguageQuery: '',
    replacementValue: '',
    geminiApiKey: ''
  });
  
  const [showApiKeyHelp, setShowApiKeyHelp] = useState(false);

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

    if (!formData.geminiApiKey.trim()) {
      onError('Please enter your Gemini API key');
      return;
    }

    if (!formData.geminiApiKey.startsWith('AIza')) {
      onError('Invalid API key format. Gemini API keys should start with "AIza"');
      return;
    }

    try {
      setLoading(true);
      
      const requestData = {
        file_id: fileData.id,
        natural_language_query: formData.naturalLanguageQuery,
        replacement_value: formData.replacementValue,
        gemini_api_key: formData.geminiApiKey
        // NO target_column - let AI decide!
      };
      
      console.log('🎯 Intelligent processing request:', requestData);
      const result = await processPatternMatching(requestData);
      
      onProcessingComplete(result);
    } catch (error) {
      console.error('🎯 Processing failed:', error);
      setLoading(false);
      onError(error.message || 'Failed to process pattern matching');
    }
  }, [formData, fileData.id, onProcessingComplete, onError, setLoading]);

  // Smart pattern suggestions
  const smartPatterns = [
    {
      label: 'Hide Email Addresses',
      query: 'find email addresses',
      example: 'user@example.com → REDACTED'
    },
    {
      label: 'Hide Names and Emails',
      query: 'find names and email addresses',
      example: 'Hide both personal names and emails'
    },
    {
      label: 'Hide Phone Numbers',
      query: 'find phone numbers',
      example: '(555) 123-4567 → ***'
    },
    {
      label: 'Hide All Personal Info',
      query: 'find names, emails, and phone numbers',
      example: 'Hide all personally identifiable information'
    },
    {
      label: 'Hide URLs',
      query: 'find website URLs',
      example: 'https://example.com → [LINK]'
    },
    {
      label: 'Hide IP Addresses',
      query: 'find IP addresses',
      example: '192.168.1.1 → [IP]'
    }
  ];

  return (
    <div className="pattern-matcher-container">
      <div className="pattern-header">
        <h2>🤖 Smart Pattern Matching</h2>
        <p>Describe what you want to find - AI will automatically detect the right columns!</p>
      </div>

      <div className="pattern-content">
        {/* API Key Section - Same as before */}
        <div className="api-key-section" style={{
          background: '#f8f9fa',
          padding: '1.5rem',
          borderRadius: '8px',
          marginBottom: '2rem',
          border: '1px solid #dee2e6'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, color: '#495057' }}>🔑 Gemini API Key</h3>
            <button
              type="button"
              onClick={() => setShowApiKeyHelp(!showApiKeyHelp)}
              style={{
                background: 'none',
                border: '1px solid #6c757d',
                borderRadius: '50%',
                width: '24px',
                height: '24px',
                cursor: 'pointer',
                color: '#6c757d',
                fontSize: '12px'
              }}
            >
              ?
            </button>
          </div>
          
          <input
            type="password"
            name="geminiApiKey"
            value={formData.geminiApiKey}
            onChange={handleInputChange}
            placeholder="Enter your Gemini API key (AIza...)"
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #ced4da',
              borderRadius: '6px',
              fontSize: '1rem',
              fontFamily: 'monospace'
            }}
          />
          <small style={{ color: '#6c757d', fontSize: '0.875rem' }}>
            Your API key is used securely and not stored
          </small>

          {showApiKeyHelp && (
            <div style={{
              background: '#e3f2fd',
              padding: '1rem',
              borderRadius: '6px',
              marginTop: '1rem'
            }}>
              <h4>How to get your Gemini API key:</h4>
              <ol>
                <li>Go to <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">Google AI Studio</a></li>
                <li>Click "Create API Key"</li>
                <li>Copy the key that starts with "AIza..."</li>
              </ol>
            </div>
          )}
        </div>

        {/* Smart Patterns Section */}
        <div className="quick-patterns">
          <h3>💡 Smart Pattern Examples</h3>
          <div className="patterns-grid" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            {smartPatterns.map((pattern, index) => (
              <div 
                key={index} 
                className="pattern-card"
                onClick={() => handlePatternSelect(pattern)}
                style={{
                  border: '1px solid #dee2e6',
                  borderRadius: '8px',
                  padding: '1rem',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  background: 'white'
                }}
              >
                <h4 style={{ margin: '0 0 0.5rem', color: '#333' }}>{pattern.label}</h4>
                <p style={{ margin: 0, color: '#666', fontSize: '0.85rem' }}>
                  {pattern.example}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Form Section - Simplified */}
        <form onSubmit={handleSubmit} className="pattern-form" style={{
          background: '#f8f9fa',
          padding: '2rem',
          borderRadius: '12px'
        }}>
          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="naturalLanguageQuery">
              Describe what you want to find *
            </label>
            <textarea
              id="naturalLanguageQuery"
              name="naturalLanguageQuery"
              value={formData.naturalLanguageQuery}
              onChange={handleInputChange}
              placeholder="e.g., 'find email addresses', 'find names and emails', 'find phone numbers'"
              rows={3}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
            <small style={{ color: '#28a745', fontSize: '0.85rem' }}>
              ✨ AI will automatically detect which columns contain this type of data
            </small>
          </div>

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
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
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '1rem'
              }}
            />
          </div>

          <div className="form-actions" style={{
            display: 'flex',
            justifyContent: 'space-between',
            gap: '1rem',
            marginTop: '2rem',
            paddingTop: '1rem',
            borderTop: '1px solid #eee'
          }}>
            <button 
              type="button" 
              onClick={onBack}
              style={{
                padding: '0.75rem 1.5rem',
                border: 'none',
                borderRadius: '6px',
                background: '#6c757d',
                color: 'white'
              }}
            >
              ← Back to Preview
            </button>
            <button 
              type="submit"
              style={{
                padding: '0.75rem 1.5rem',
                border: 'none',
                borderRadius: '6px',
                background: '#667eea',
                color: 'white'
              }}
            >
              🤖 Smart Process →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PatternMatcher;