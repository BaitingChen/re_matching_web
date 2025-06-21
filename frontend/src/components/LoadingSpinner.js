import React from 'react';

const LoadingSpinner = () => (
  <div className="loading-overlay">
    <div className="loading-content">
      <div className="spinner-large"></div>
      <p>Processing your request...</p>
      <small>This may take a few moments</small>
    </div>
  </div>
);

export default LoadingSpinner;