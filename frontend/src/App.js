import React, { useState, useCallback } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import FilePreview from './components/FilePreview';
import PatternMatcher from './components/PatternMatcher';
import ResultsDisplay from './components/ResultsDisplay';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorAlert from './components/ErrorAlert';

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [fileData, setFileData] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [processingResults, setProcessingResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Debug: Log state changes
  console.log('🔍 App State:', { 
    currentStep, 
    loading, 
    hasFileData: !!fileData, 
    hasPreviewData: !!previewData,
    hasResults: !!processingResults,
    error 
  });

  const handleFileUpload = useCallback((data) => {
    console.log('📁 handleFileUpload called with:', data);
    setFileData(data);
    setCurrentStep(2); // Move to preview step
    setError(null);
    setLoading(false);
    console.log('📁 handleFileUpload: Moving to step 2 (Preview)');
  }, []);

  // FIX: This should only store preview data, NOT change step
  const handlePreviewLoaded = useCallback((data) => {
    console.log('👀 handlePreviewLoaded called with:', data);
    setPreviewData(data);
    // REMOVED: setCurrentStep(3); - Don't auto-advance to step 3
    setLoading(false);
    console.log('👀 handlePreviewLoaded: Preview data stored, staying on step 2');
  }, []);

  // NEW: Add explicit function to move to pattern matching
  const handleContinueToPatternMatching = useCallback(() => {
    console.log('▶️ handleContinueToPatternMatching called');
    if (previewData) {
      setCurrentStep(3);
      console.log('▶️ Moving to step 3 (Pattern Matching)');
    } else {
      setError('Preview data not loaded');
    }
  }, [previewData]);

  const handleProcessingComplete = useCallback((results) => {
    console.log('⚡ handleProcessingComplete called with:', results);
    setProcessingResults(results);
    setCurrentStep(4);
    setLoading(false);
    console.log('⚡ handleProcessingComplete: Moving to step 4 (Results)');
  }, []);

  const handleError = useCallback((errorMessage) => {
    console.log('❌ handleError called with:', errorMessage);
    setError(errorMessage);
    setLoading(false);
    console.log('❌ handleError: Error set, loading cleared');
  }, []);

  const resetApp = () => {
    console.log('🔄 resetApp called');
    setCurrentStep(1);
    setFileData(null);
    setPreviewData(null);
    setProcessingResults(null);
    setError(null);
    setLoading(false);
    console.log('🔄 resetApp: All state cleared, back to step 1');
  };

  const renderStepIndicator = () => (
    <div className="step-indicator">
      <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
        <span className="step-number">1</span>
        <span className="step-label">Upload File</span>
      </div>
      <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
        <span className="step-number">2</span>
        <span className="step-label">Preview Data</span>
      </div>
      <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
        <span className="step-number">3</span>
        <span className="step-label">Pattern Matching</span>
      </div>
      <div className={`step ${currentStep >= 4 ? 'active' : ''}`}>
        <span className="step-number">4</span>
        <span className="step-label">Results</span>
      </div>
    </div>
  );

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">🔍</div>
            <h1>Regex Pattern Matcher</h1>
          </div>
          <p className="subtitle">Upload files and transform data using natural language</p>
        </div>
      </header>

      <main className="App-main">
        {renderStepIndicator()}

        {error && (
          <ErrorAlert 
            message={error} 
            onDismiss={() => setError(null)}
            onRetry={resetApp}
          />
        )}

        {loading && <LoadingSpinner />}

        <div className="content-container">
          {currentStep === 1 && (
            <>
              {console.log('🎨 Rendering FileUpload component')}
              <FileUpload 
                onUpload={handleFileUpload}
                onError={handleError}
                loading={loading}
                setLoading={setLoading}
              />
            </>
          )}

          {currentStep === 2 && fileData && (
            <>
              {console.log('🎨 Rendering FilePreview component')}
              <FilePreview 
                fileData={fileData}
                onPreviewLoaded={handlePreviewLoaded}
                onContinue={handleContinueToPatternMatching} // NEW: Pass continue function
                onError={handleError}
                onBack={() => setCurrentStep(1)}
              />
            </>
          )}

          {currentStep === 3 && previewData && (
            <>
              {console.log('🎨 Rendering PatternMatcher component')}
              <PatternMatcher 
                fileData={fileData}
                previewData={previewData}
                onProcessingComplete={handleProcessingComplete}
                onError={handleError}
                onBack={() => setCurrentStep(2)}
                setLoading={setLoading}
              />
            </>
          )}

          {currentStep === 4 && processingResults && (
            <>
              {console.log('🎨 Rendering ResultsDisplay component')}
              <ResultsDisplay 
                results={processingResults}
                onStartOver={resetApp}
                onBack={() => setCurrentStep(3)}
              />
            </>
          )}
        </div>
      </main>

      <footer className="App-footer">
        <p>&copy; 2025 Regex Pattern Matcher. Built with Django & React.</p>
      </footer>
    </div>
  );
}

export default App;