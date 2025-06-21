import React from 'react';

const ErrorAlert = ({ message, onDismiss, onRetry }) => (
  <div className="error-alert">
    <div className="error-content">
      <span className="error-icon">⚠️</span>
      <div className="error-text">
        <strong>Error:</strong> {message}
      </div>
      <div className="error-actions">
        {onRetry && (
          <button onClick={onRetry} className="btn btn-small btn-primary">
            Try Again
          </button>
        )}
        <button onClick={onDismiss} className="btn btn-small btn-secondary">
          Dismiss
        </button>
      </div>
    </div>
  </div>
);

export default ErrorAlert;