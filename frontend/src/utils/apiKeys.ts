const API_KEYS_STORAGE_KEY = 'openscholar_api_keys';

export interface ApiKeys {
  [key: string]: string;
}

export const getApiKeys = (): ApiKeys => {
  try {
    const stored = localStorage.getItem(API_KEYS_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Error loading API keys:', error);
    return {};
  }
};

export const saveApiKeys = (keys: ApiKeys): void => {
  try {
    localStorage.setItem(API_KEYS_STORAGE_KEY, JSON.stringify(keys));
  } catch (error) {
    console.error('Error saving API keys:', error);
    throw error;
  }
};

export const getApiKey = (sourceId: string): string | undefined => {
  const keys = getApiKeys();
  return keys[sourceId];
};

export const hasApiKey = (sourceId: string): boolean => {
  if (sourceId === 'Google Search') {
    // For Google Search, check both API key and Search Engine ID
    const apiKey = getApiKey(sourceId);
    const searchEngineId = getApiKey(`${sourceId}_ENGINE_ID`);
    return !!(apiKey && apiKey.length > 0 && searchEngineId && searchEngineId.length > 0);
  }
  
  const key = getApiKey(sourceId);
  return !!key && key.length > 0;
};