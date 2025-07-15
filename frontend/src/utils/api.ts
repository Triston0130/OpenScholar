import axios from 'axios';
import { SearchRequest, SearchResponse, ExportRequest } from '../types';

const API_BASE_URL = 'https://openscholar-nsc1.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const searchPapers = async (searchRequest: SearchRequest): Promise<SearchResponse> => {
  try {
    const response = await api.post<SearchResponse>('/search', searchRequest);
    return response.data;
  } catch (error) {
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