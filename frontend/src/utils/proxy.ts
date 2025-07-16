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
    
    const institutionName = settings.institutionName || 'University';
    links.push({
      type: 'university',
      url: proxiedUrl,
      label: `${institutionName} Access`,
      icon: '🔐',
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

export const autoCorrectProxyUrl = (url: string): string => {
  if (!url.trim()) return url;
  
  let corrected = url.trim();
  
  // Auto-add https:// if missing protocol
  if (!corrected.startsWith('http://') && !corrected.startsWith('https://')) {
    corrected = 'https://' + corrected;
  }
  
  // Ensure it ends with proper parameter format
  if (!corrected.includes('?url=') && !corrected.includes('&url=')) {
    if (corrected.endsWith('?') || corrected.endsWith('&')) {
      corrected += 'url=';
    } else if (corrected.includes('?')) {
      corrected += '&url=';
    } else {
      corrected += '?url=';
    }
  }
  
  return corrected;
};

export const validateProxyUrl = (url: string): { isValid: boolean; error?: string; corrected?: string } => {
  if (!url.trim()) {
    return { isValid: false, error: 'Proxy URL is required' };
  }
  
  const corrected = autoCorrectProxyUrl(url);
  
  try {
    const parsed = new URL(corrected);
    if (!parsed.protocol.startsWith('http')) {
      return { isValid: false, error: 'Proxy URL must start with http:// or https://' };
    }
    
    // Check if it looks like a proxy URL
    if (!corrected.includes('login') && !corrected.includes('proxy')) {
      return { 
        isValid: false, 
        error: 'URL should contain "login" or "proxy" to be a valid proxy URL' 
      };
    }
    
    // Check for proper URL parameter format
    if (!corrected.includes('?url=') && !corrected.includes('&url=')) {
      return { 
        isValid: false, 
        error: 'URL should end with "?url=" or "&url=" parameter' 
      };
    }
    
    return { 
      isValid: true, 
      corrected: corrected !== url ? corrected : undefined 
    };
  } catch (error) {
    return { isValid: false, error: 'Invalid URL format' };
  }
};

// Known university proxy patterns for auto-detection
export const getKnownProxyPatterns = (): { [domain: string]: string } => {
  return {
    // California State Universities (multiple common formats)
    'csus.edu': 'https://csus.idm.oclc.org/login?url=',
    'csulb.edu': 'https://csulb.idm.oclc.org/login?url=',
    'csueastbay.edu': 'https://csueastbay.idm.oclc.org/login?url=',
    'csufresno.edu': 'https://csufresno.idm.oclc.org/login?url=',
    
    // University of California
    'ucla.edu': 'https://ucla.idm.oclc.org/login?url=',
    'berkeley.edu': 'https://berkeley.idm.oclc.org/login?url=',
    'ucsd.edu': 'https://ucsd.idm.oclc.org/login?url=',
    'uci.edu': 'https://uci.idm.oclc.org/login?url=',
    
    // Common patterns
    'harvard.edu': 'https://harvard.idm.oclc.org/login?url=',
    'stanford.edu': 'https://stanford.idm.oclc.org/login?url=',
    'mit.edu': 'https://mit.idm.oclc.org/login?url=',
    'yale.edu': 'https://yale.idm.oclc.org/login?url=',
    'princeton.edu': 'https://princeton.idm.oclc.org/login?url=',
  };
};

export const suggestProxyUrl = (email: string): string | null => {
  if (!email.includes('@')) return null;
  
  const domain = email.split('@')[1];
  const patterns = getKnownProxyPatterns();
  
  return patterns[domain] || null;
};

// Alternative proxy URL patterns for common universities
export const getAlternativeProxyPatterns = (domain: string): string[] => {
  const alternatives: { [key: string]: string[] } = {
    'csus.edu': [
      'https://csus.idm.oclc.org/login?url=',
      'https://libproxy.csus.edu/login?url=',
      'https://proxy.csus.edu/login?url=',
      'https://ezproxy.csus.edu/login?url=',
      'https://csus.libguides.com/proxy/login?url='
    ],
    'csulb.edu': [
      'https://csulb.idm.oclc.org/login?url=',
      'https://libproxy.csulb.edu/login?url=',
      'https://ezproxy.csulb.edu/login?url='
    ],
    'csueastbay.edu': [
      'https://csueastbay.idm.oclc.org/login?url=',
      'https://libproxy.csueastbay.edu/login?url=',
      'https://ezproxy.csueastbay.edu/login?url='
    ]
  };
  
  return alternatives[domain] || [];
};

export const testProxyUrl = async (proxyUrl: string): Promise<{ isWorking: boolean; error?: string }> => {
  try {
    // Test with a simple DOI
    const testUrl = proxyUrl + encodeURIComponent('https://doi.org/10.1000/test');
    
    // We can't actually test the proxy due to CORS, but we can validate the URL structure
    const url = new URL(testUrl);
    
    // Check if it's a reasonable proxy URL
    if (url.hostname.includes('proxy') || url.hostname.includes('idm') || url.hostname.includes('ezproxy')) {
      return { isWorking: true };
    }
    
    return { 
      isWorking: false, 
      error: 'URL doesn\'t appear to be a proxy server' 
    };
  } catch (error) {
    return { 
      isWorking: false, 
      error: 'Invalid URL format' 
    };
  }
};