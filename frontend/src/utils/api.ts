import axios from 'axios';
import { SearchRequest, SearchResponse, ExportRequest, Paper } from '../types';
import { getApiKeys } from './apiKeys';
import { AIConfig } from '../components/AIProcessingModal';

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minute timeout for AI processing
});

// Add request interceptor for debugging and auth
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const accessToken = localStorage.getItem('openscholar_access_token');
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    
    // Set Content-Type for JSON requests (not for FormData)
    if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    
    console.log('Making request to:', config.url);
    console.log('With baseURL:', config.baseURL);
    console.log('Full URL:', `${config.baseURL}${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('Response received:', response.status);
    return response;
  },
  (error) => {
    console.error('Response error:', error.message);
    if (error.code === 'ECONNABORTED') {
      console.error('Request timed out!');
    }
    return Promise.reject(error);
  }
);

export const searchPapers = async (searchRequest: SearchRequest): Promise<SearchResponse> => {
  try {
    // Debug: Log the search request being sent
    console.log('Search request being sent to API:', searchRequest);
    console.log('Selected sources:', searchRequest.sources);
    
    // Get API keys and include them in the request
    const apiKeys = getApiKeys();
    const requestWithKeys = {
      ...searchRequest,
      api_keys: apiKeys
    };
    
    const response = await api.post<SearchResponse>('/search', requestWithKeys);
    
    // Debug: Log the response
    console.log('API response:', response.data);
    console.log('Sources queried by backend:', response.data.sources_queried);
    if (response.data.source_counts) {
      console.log('Results per source:', response.data.source_counts);
    }
    
    return response.data;
  } catch (error) {
    console.error('Search API error:', error);
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to search papers');
    }
    throw new Error('An unexpected error occurred');
  }
};

export const exportPapers = async (exportRequest: ExportRequest): Promise<Blob> => {
  try {
    const response = await api.post('/export', exportRequest, {
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to export papers');
    }
    throw new Error('An unexpected error occurred');
  }
};

export const fetchExternalPaper = async (doi: string): Promise<Paper> => {
  try {
    const response = await api.post<{paper: Paper}>('/external-paper', { doi });
    return response.data.paper;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Failed to fetch external paper');
    }
    throw new Error('An unexpected error occurred');
  }
};

export const downloadFile = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

// AI Processing Functions
export const testOpenAIKey = async (apiKey: string): Promise<{ valid: boolean; message: string }> => {
  try {
    const response = await api.post('/api/ai/test-api-key', null, {
      params: { api_key: apiKey }
    });
    return response.data;
  } catch (error) {
    console.error('Error testing API key:', error);
    return { valid: false, message: 'Failed to test API key' };
  }
};

export const processCollectionWithAI = async (
  collectionId: string,
  folderId: string | null,
  aiConfig: AIConfig
): Promise<{
  collection_id: string;
  processed_papers: Array<{
    paper_id: string;
    title: string;
    tags: string[];
    notes: string;
    success: boolean;
    error_message?: string;
  }>;
  total_processed: number;
  total_failed: number;
  total_cost_estimate: number;
}> => {
  try {
    console.log('Processing collection with AI:', { collectionId, folderId, aiConfig });
    const response = await api.post('/api/ai/process-collection', {
      collection_id: collectionId,
      folder_id: folderId,
      ai_config: {
        api_key: aiConfig.apiKey,
        model: aiConfig.model,
        temperature: aiConfig.temperature,
        max_tokens: aiConfig.maxTokens,
        note_types: aiConfig.noteTypes,
        extract_full_text: aiConfig.extractFullText
      },
      process_empty_only: aiConfig.processEmptyOnly
    });
    return response.data;
  } catch (error) {
    console.error('Error processing collection with AI:', error);
    if (axios.isAxiosError(error)) {
      console.error('Response status:', error.response?.status);
      console.error('Response data:', error.response?.data);
    }
    throw error;
  }
};

export const processPapersWithAI = async (
  papers: any[],
  aiConfig: AIConfig
): Promise<{
  collection_id: string;
  processed_papers: Array<{
    paper_id: string;
    title: string;
    tags: string[];
    notes: string;
    flashcards?: Array<{
      front: string;
      back: string;
      category?: string;
      difficulty?: string;
    }>;
    success: boolean;
    error_message?: string;
  }>;
  total_processed: number;
  total_failed: number;
  total_cost_estimate: number;
}> => {
  try {
    console.log('Processing papers directly with AI:', { paperCount: papers.length, aiConfig });
    const response = await api.post('/api/ai/process-papers', {
      papers: papers,
      ai_config: {
        api_key: aiConfig.apiKey,
        model: aiConfig.model,
        temperature: aiConfig.temperature,
        max_tokens: aiConfig.maxTokens,
        note_types: aiConfig.noteTypes,
        extract_full_text: aiConfig.extractFullText
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error processing papers with AI:', error);
    if (axios.isAxiosError(error)) {
      console.error('Response status:', error.response?.status);
      console.error('Response data:', error.response?.data);
    }
    throw error;
  }
};

export const getAvailableAIModels = async (): Promise<{
  models: Array<{
    id: string;
    name: string;
    description: string;
    cost_per_paper: number;
  }>;
}> => {
  try {
    const response = await api.get('/api/ai/models');
    return response.data;
  } catch (error) {
    console.error('Error fetching AI models:', error);
    throw error;
  }
};

// Collection API Functions
export interface CollectionResponse {
  id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  is_public: boolean;
  share_token?: string;
  paper_count: number;
  created_at: string;
  updated_at?: string;
}

export interface CreateCollectionRequest {
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  is_public?: boolean;
}

export interface CollectionPaperResponse {
  id: string;
  paper: Paper;
  notes?: string;
  custom_tags?: string[];
  added_at: string;
}

export const getCollections = async (): Promise<CollectionResponse[]> => {
  try {
    const response = await api.get('/api/collections');
    return response.data;
  } catch (error) {
    console.error('Error fetching collections:', error);
    throw error;
  }
};

export const createCollection = async (data: CreateCollectionRequest): Promise<CollectionResponse> => {
  try {
    const response = await api.post('/api/collections', data);
    return response.data;
  } catch (error) {
    console.error('Error creating collection:', error);
    throw error;
  }
};

export const updateCollection = async (id: string, data: Partial<CreateCollectionRequest>): Promise<CollectionResponse> => {
  try {
    const response = await api.put(`/api/collections/${id}`, data);
    return response.data;
  } catch (error) {
    console.error('Error updating collection:', error);
    throw error;
  }
};

export const deleteCollection = async (id: string): Promise<void> => {
  try {
    await api.delete(`/api/collections/${id}`);
  } catch (error) {
    console.error('Error deleting collection:', error);
    throw error;
  }
};

export const getCollectionPapers = async (id: string): Promise<CollectionPaperResponse[]> => {
  try {
    const response = await api.get(`/api/collections/${id}/papers`);
    return response.data;
  } catch (error) {
    console.error('Error fetching collection papers:', error);
    throw error;
  }
};

export const addPaperToCollection = async (
  collectionId: string,
  paperData: Paper,
  notes?: string,
  tags?: string[],
  pdfFile?: File
): Promise<CollectionPaperResponse> => {
  try {
    // If we have a PDF file, upload it first and get the URL
    let customPdfUrl: string | undefined;
    if (pdfFile) {
      customPdfUrl = await uploadPdf(pdfFile);
    }

    const response = await api.post(`/api/collections/${collectionId}/papers`, {
      paper_data: {
        ...paperData,
        // Override full_text_url with uploaded PDF URL if available
        full_text_url: customPdfUrl || paperData.full_text_url
      },
      notes,
      tags,
      custom_pdf_url: customPdfUrl
    });
    return response.data;
  } catch (error) {
    console.error('Error adding paper to collection:', error);
    throw error;
  }
};

// New function to upload PDF
export const uploadPdf = async (file: File): Promise<string> => {
  try {
    const formData = new FormData();
    formData.append('pdf', file);
    
    console.log('Uploading PDF:', file.name, 'size:', file.size, 'type:', file.type);
    
    // Don't set Content-Type header - let axios set it automatically with boundary
    const response = await api.post('/api/upload-pdf', formData);
    
    return response.data.pdf_url;
  } catch (error) {
    console.error('Error uploading PDF:', error);
    if (axios.isAxiosError(error)) {
      console.error('Upload error details:', error.response?.data);
      // Handle validation errors from FastAPI
      if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
        const validationError = error.response.data.detail[0];
        console.error('Validation error:', validationError);
        throw new Error(`Validation error: ${validationError.msg || 'Invalid request'}`);
      }
      throw new Error(error.response?.data?.detail || 'Failed to upload PDF');
    }
    throw new Error('Failed to upload PDF');
  }
};

export const updatePaperInCollection = async (
  collectionId: string,
  paperId: string,
  updates: { notes?: string; tags?: string[] }
): Promise<void> => {
  try {
    await api.put(`/api/collections/${collectionId}/papers/${paperId}`, updates);
  } catch (error) {
    console.error('Error updating paper in collection:', error);
    throw error;
  }
};

export const removePaperFromCollection = async (
  collectionId: string,
  paperId: string
): Promise<void> => {
  try {
    await api.delete(`/api/collections/${collectionId}/papers/${paperId}`);
  } catch (error) {
    console.error('Error removing paper from collection:', error);
    throw error;
  }
};

// Collection Sharing Functions
export interface ShareCollectionRequest {
  email?: string;
  role: 'viewer' | 'commenter' | 'editor' | 'admin';
  can_reshare?: boolean;
  message?: string;
  expires_in_days?: number;
  share_type: 'user' | 'link';
}

export interface ShareResponse {
  share_link?: string;
  expires_at?: string;
  message?: string;
  share_id?: string;
}

export interface PendingShare {
  share_id: string;
  collection_id: string;
  collection_name: string;
  collection_description?: string;
  shared_by: {
    id?: string;
    name: string;
    email?: string;
  };
  role: string;
  can_reshare: boolean;
  message?: string;
  shared_at: string;
  expires_at?: string;
}

export interface SharedCollection {
  id: string;
  name: string;
  description?: string;
  color?: string;
  icon?: string;
  paper_count: number;
  owner: {
    id?: string;
    name: string;
    email?: string;
  };
  my_role: string;
  can_reshare: boolean;
  accepted_at: string;
  created_at: string;
  updated_at?: string;
}

export const shareCollection = async (
  collectionId: string,
  request: ShareCollectionRequest
): Promise<ShareResponse> => {
  try {
    const response = await api.post(`/api/collections/${collectionId}/share`, request);
    return response.data;
  } catch (error) {
    console.error('Error sharing collection:', error);
    throw error;
  }
};

export const getCollectionShares = async (collectionId: string): Promise<any[]> => {
  try {
    const response = await api.get(`/api/collections/${collectionId}/shares`);
    return response.data;
  } catch (error) {
    console.error('Error fetching collection shares:', error);
    throw error;
  }
};

export const removeCollectionShare = async (
  collectionId: string,
  shareId: string
): Promise<void> => {
  try {
    await api.delete(`/api/collections/${collectionId}/shares/${shareId}`);
  } catch (error) {
    console.error('Error removing share:', error);
    throw error;
  }
};

export const acceptShare = async (shareId: string): Promise<{ message: string; collection_id: string }> => {
  try {
    const response = await api.post(`/api/shares/${shareId}/accept`);
    return response.data;
  } catch (error) {
    console.error('Error accepting share:', error);
    throw error;
  }
};

export const rejectShare = async (shareId: string): Promise<void> => {
  try {
    await api.post(`/api/shares/${shareId}/reject`);
  } catch (error) {
    console.error('Error rejecting share:', error);
    throw error;
  }
};

export const getPendingShares = async (): Promise<PendingShare[]> => {
  try {
    const response = await api.get('/api/shares/pending');
    return response.data;
  } catch (error) {
    console.error('Error fetching pending shares:', error);
    throw error;
  }
};

export const getSharedCollections = async (): Promise<SharedCollection[]> => {
  try {
    const response = await api.get('/api/collections/shared');
    return response.data;
  } catch (error) {
    console.error('Error fetching shared collections:', error);
    throw error;
  }
};

export const acceptShareLink = async (shareLink: string): Promise<{ message: string; collection_id: string }> => {
  try {
    const response = await api.post(`/api/shares/link/${shareLink}`);
    return response.data;
  } catch (error) {
    console.error('Error accepting share link:', error);
    throw error;
  }
};

export const getShareLinkInfo = async (shareLink: string): Promise<{
  collection: {
    id: string;
    name: string;
    description?: string;
    paper_count: number;
  };
  owner: {
    name: string;
  };
  role: string;
  expires_at?: string;
}> => {
  try {
    const response = await api.get(`/api/shares/link/${shareLink}/info`);
    return response.data;
  } catch (error) {
    console.error('Error fetching share link info:', error);
    throw error;
  }
};

// Email Settings Functions
export interface EmailSettingsRequest {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_password: string;
  smtp_use_tls?: boolean;
  smtp_use_ssl?: boolean;
  from_email?: string;
  from_name?: string;
}

export interface EmailSettingsResponse {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  from_email?: string;
  from_name: string;
  is_configured: boolean;
  is_verified: boolean;
}

export interface NotificationPreferences {
  share_invitations: boolean;
  share_acceptances: boolean;
  annotation_replies: boolean;
  collection_updates: boolean;
}

export const getEmailSettings = async (): Promise<EmailSettingsResponse> => {
  try {
    const response = await api.get('/api/settings/email');
    return response.data;
  } catch (error) {
    console.error('Error fetching email settings:', error);
    throw error;
  }
};

export const updateEmailSettings = async (settings: EmailSettingsRequest): Promise<void> => {
  try {
    await api.post('/api/settings/email', settings);
  } catch (error) {
    console.error('Error updating email settings:', error);
    throw error;
  }
};

export const testEmailSettings = async (): Promise<void> => {
  try {
    await api.post('/api/settings/email/test');
  } catch (error) {
    console.error('Error testing email settings:', error);
    throw error;
  }
};

export const deleteEmailSettings = async (): Promise<void> => {
  try {
    await api.delete('/api/settings/email');
  } catch (error) {
    console.error('Error deleting email settings:', error);
    throw error;
  }
};

export const getNotificationPreferences = async (): Promise<NotificationPreferences> => {
  try {
    const response = await api.get('/api/settings/notifications');
    return response.data;
  } catch (error) {
    console.error('Error fetching notification preferences:', error);
    throw error;
  }
};

export const updateNotificationPreferences = async (prefs: NotificationPreferences): Promise<void> => {
  try {
    await api.post('/api/settings/notifications', prefs);
  } catch (error) {
    console.error('Error updating notification preferences:', error);
    throw error;
  }
};