export interface ProxySettings {
  proxyUrl: string;
  institutionName: string;
  enabled: boolean;
}

export interface AccessLink {
  type: 'free' | 'university' | 'publisher';
  url: string;
  label: string;
  icon: string;
  priority: number;
}

const PROXY_SETTINGS_KEY = 'openscholar_proxy_settings';

export const getProxySettings = (): ProxySettings => {
  try {
    const stored = localStorage.getItem(PROXY_SETTINGS_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Error loading proxy settings:', error);
  }
  
  return {
    proxyUrl: '',
    institutionName: '',
    enabled: false
  };
};

export const saveProxySettings = (settings: ProxySettings): void => {
  try {
    localStorage.setItem(PROXY_SETTINGS_KEY, JSON.stringify(settings));
    // Trigger event for other components to update
    window.dispatchEvent(new CustomEvent('proxySettingsChanged', { detail: settings }));
  } catch (error) {
    console.error('Error saving proxy settings:', error);
  }
};

export const generateProxyUrl = (targetUrl: string): string => {
  const settings = getProxySettings();
  if (!settings.enabled || !settings.proxyUrl || !targetUrl) {
    return targetUrl;
  }
  
  // Clean up proxy URL - ensure it ends with the right parameter
  let proxyUrl = settings.proxyUrl.trim();
  if (!proxyUrl.includes('?url=') && !proxyUrl.includes('&url=')) {
    // Add url parameter if not present
    proxyUrl = proxyUrl.endsWith('?') ? proxyUrl + 'url=' : proxyUrl + '?url=';
  }
  
  return proxyUrl + encodeURIComponent(targetUrl);
};

export const generateAccessLinks = (paper: { doi?: string; full_text_url?: string }): AccessLink[] => {
  const settings = getProxySettings();
  const links: AccessLink[] = [];
  
  // Free access (highest priority)
  if (paper.full_text_url) {
    links.push({
      type: 'free',
      url: paper.full_text_url,
      label: 'Free Access',
      icon: '🔓',
      priority: 1
    });
  }
  
  // University access (second priority)
  if (paper.doi && settings.enabled && settings.proxyUrl) {
    const doiUrl = paper.doi.startsWith('http') ? paper.doi : `https://doi.org/${paper.doi}`;
    const proxiedUrl = generateProxyUrl(doiUrl);
    
    links.push({
      type: 'university',
      url: proxiedUrl,
      label: settings.institutionName ? `${settings.institutionName} Access` : 'University Access',
      icon: '🏫',
      priority: 2
    });
  }
  
  // Publisher access (lowest priority)
  if (paper.doi) {
    const doiUrl = paper.doi.startsWith('http') ? paper.doi : `https://doi.org/${paper.doi}`;
    links.push({
      type: 'publisher',
      url: doiUrl,
      label: 'Publisher',
      icon: '💰',
      priority: 3
    });
  }
  
  // Sort by priority
  return links.sort((a, b) => a.priority - b.priority);
};

export const getBestAccessLink = (paper: { doi?: string; full_text_url?: string }): AccessLink | null => {
  const links = generateAccessLinks(paper);
  return links.length > 0 ? links[0] : null;
};

export const validateProxyUrl = (url: string): { isValid: boolean; error?: string } => {
  if (!url.trim()) {
    return { isValid: false, error: 'Proxy URL is required' };
  }
  
  try {
    const parsed = new URL(url);
    if (!parsed.protocol.startsWith('http')) {
      return { isValid: false, error: 'Proxy URL must start with http:// or https://' };
    }
    
    // Check if it looks like a proxy URL
    if (!url.includes('login') && !url.includes('proxy')) {
      return { isValid: false, error: 'URL should contain "login" or "proxy"' };
    }
    
    return { isValid: true };
  } catch (error) {
    return { isValid: false, error: 'Invalid URL format' };
  }
};