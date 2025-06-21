import React, { useCallback, useState } from 'react';
import { uploadFile } from '../services/api';

const FileUpload = ({ onUpload, onError, loading, setLoading }) => {
  const [dragActive, setDragActive] = useState(false);
  
  console.log('📁 FileUpload rendered with props:', { loading });
  
  const handleFiles = useCallback(async (files) => {
    if (files.length === 0) return;
    
    const file = files[0];
    console.log('📁 FileUpload: Processing file:', file.name);
    
    // Validate file type
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      console.log('📁 FileUpload: Invalid file type:', fileExtension);
      onError('Please upload a CSV or Excel file (.csv, .xlsx, .xls)');
      return;
    }
    
    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      console.log('📁 FileUpload: File too large:', file.size);
      onError('File size must be less than 10MB');
      return;
    }
    
    try {
      console.log('📁 FileUpload: Setting loading to true');
      setLoading(true);
      
      console.log('📁 FileUpload: Calling uploadFile API...');
      const result = await uploadFile(file);
      console.log('📁 FileUpload: Upload successful:', result);
      
      console.log('📁 FileUpload: Calling onUpload callback...');
      onUpload(result);
      console.log('📁 FileUpload: onUpload callback completed');
      
    } catch (error) {
      console.error('📁 FileUpload: Upload failed:', error);
      setLoading(false);
      onError(error.message || 'Failed to upload file');
    }
  }, [onUpload, onError, setLoading]);

  // ... rest of component stays the same ...
  
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, [handleFiles]);

  const handleChange = useCallback((e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(Array.from(e.target.files));
    }
  }, [handleFiles]);

  return (
    <div className="file-upload-container">
      <div className="upload-header">
        <h2>Upload Your Data File</h2>
        <p>Upload a CSV or Excel file to get started with pattern matching</p>
      </div>

      <div 
        className={`file-upload-zone ${dragActive ? 'drag-active' : ''} ${loading ? 'disabled' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload-input"
          className="file-input"
          accept=".csv,.xlsx,.xls"
          onChange={handleChange}
          disabled={loading}
        />
        
        <label htmlFor="file-upload-input" className="file-upload-label">
          <div className="upload-icon">
            {loading ? '⏳' : '📁'}
          </div>
          <div className="upload-text">
            <h3>{loading ? 'Uploading...' : 'Choose a file or drag it here'}</h3>
            <p>CSV, XLSX, or XLS files up to 10MB</p>
          </div>
        </label>
      </div>

      {loading && (
        <div className="upload-status">
          <div className="spinner"></div>
          <p>Uploading and processing file...</p>
        </div>
      )}

      <div className="upload-info">
        <div className="info-item">
          <span className="info-icon">✅</span>
          <span>Supported formats: CSV, XLSX, XLS</span>
        </div>
        <div className="info-item">
          <span className="info-icon">🔒</span>
          <span>Your data is processed securely</span>
        </div>
        <div className="info-item">
          <span className="info-icon">⚡</span>
          <span>Fast processing with AI-powered pattern matching</span>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
