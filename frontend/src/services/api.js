const API_BASE_URL = 'http://localhost:8000/api';

class APIError extends Error {
  constructor(message, status = null) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}

const handleResponse = async (response) => {
  console.log('🌐 API Response received:', {
    url: response.url,
    status: response.status,
    statusText: response.statusText,
    ok: response.ok
  });
  
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    
    try {
      const errorData = await response.json();
      errorMessage = errorData.error || errorData.detail || errorMessage;
      console.log('🌐 API Error data:', errorData);
    } catch {
      console.log('🌐 API Error: Could not parse error JSON');
    }
    
    console.error('🌐 API Error:', errorMessage);
    throw new APIError(errorMessage, response.status);
  }
  
  const data = await response.json();
  console.log('🌐 API Success data:', data);
  return data;
};

export const uploadFile = async (file) => {
  console.log('🌐 uploadFile called with:', { 
    name: file.name, 
    size: file.size, 
    type: file.type 
  });
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    console.log('🌐 Making POST request to:', `${API_BASE_URL}/upload/`);
    
    const response = await fetch(`${API_BASE_URL}/upload/`, {
      method: 'POST',
      body: formData,
    });
    
    const result = await handleResponse(response);
    console.log('🌐 uploadFile success:', result);
    return result;
  } catch (error) {
    console.error('🌐 uploadFile error:', error);
    throw error;
  }
};

export const processPatternMatching = async (data) => {
  console.log('🌐 processPatternMatching called with:', data);
  
  try {
    console.log('🌐 Making POST request to:', `${API_BASE_URL}/process/`);
    
    const response = await fetch(`${API_BASE_URL}/process/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    const result = await handleResponse(response);
    console.log('🌐 processPatternMatching success:', result);
    return result;
  } catch (error) {
    console.error('🌐 processPatternMatching error:', error);
    throw error;
  }
};


export const getProcessingJob = async (jobId) => {
  console.log('🌐 getProcessingJob called with jobId:', jobId);
  
  try {
    console.log('🌐 Making GET request to:', `${API_BASE_URL}/jobs/${jobId}/`);
    
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/`);
    const result = await handleResponse(response);
    console.log('🌐 getProcessingJob success:', result);
    return result;
  } catch (error) {
    console.error('🌐 getProcessingJob error:', error);
    throw error;
  }
};



export const getFilePreview = async (fileId) => {
  console.log('🌐 getFilePreview called with fileId:', fileId);
  
  try {
    console.log('🌐 Making GET request to:', `${API_BASE_URL}/files/${fileId}/preview/`);
    
    const response = await fetch(`${API_BASE_URL}/files/${fileId}/preview/`);
    const result = await handleResponse(response);
    console.log('🌐 getFilePreview success:', result);
    return result;
  } catch (error) {
    console.error('🌐 getFilePreview error:', error);
    throw error;
  }
};