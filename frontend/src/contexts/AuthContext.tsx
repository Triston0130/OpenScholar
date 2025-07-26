import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

export interface User {
  uid: string;
  username: string;
  email: string;
  full_name?: string;
  institution?: string;
  research_interests?: string[];
  is_verified: boolean;
  created_at: string;
}


interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (emailOrUsername: string, password: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
}

interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  institution?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Simple axios instance for auth only
const authApi = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkExistingSession();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const checkExistingSession = async () => {
    try {
      const accessToken = localStorage.getItem('openscholar_access_token');
      const savedUser = localStorage.getItem('openscholar_user');
      
      if (accessToken && savedUser) {
        // Verify token is still valid by getting current user
        try {
          const response = await authApi.get('/api/auth/me', {
            headers: { Authorization: `Bearer ${accessToken}` },
            timeout: 5000 // 5 second timeout
          });
          setUser(response.data);
          // Update stored user data
          localStorage.setItem('openscholar_user', JSON.stringify(response.data));
        } catch (error) {
          // Token invalid, will be handled by interceptor
          console.error('Auth check failed:', error);
          setUser(null);
        }
      }
    } catch (error) {
      console.error('Error checking session:', error);
      clearAuthData();
    } finally {
      setIsLoading(false);
    }
  };

  const clearAuthData = () => {
    localStorage.removeItem('openscholar_access_token');
    localStorage.removeItem('openscholar_refresh_token');
    localStorage.removeItem('openscholar_user');
    setUser(null);
  };

  const login = async (emailOrUsername: string, password: string): Promise<void> => {
    console.log('Login attempt:', { emailOrUsername, passwordLength: password.length });
    setIsLoading(true);
    
    try {
      const response = await authApi.post('/api/auth/login', {
        email_or_username: emailOrUsername,
        password: password
      });
      console.log('Login response:', response.data);
      
      const { access_token, refresh_token, user: userData } = response.data;
      
      // Store tokens and user data
      localStorage.setItem('openscholar_access_token', access_token);
      localStorage.setItem('openscholar_refresh_token', refresh_token);
      localStorage.setItem('openscholar_user', JSON.stringify(userData));
      
      setUser(userData);
    } catch (error: any) {
      console.error('Login error:', error);
      clearAuthData();
      throw new Error(error.response?.data?.detail || error.response?.data?.error || error.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData): Promise<void> => {
    setIsLoading(true);
    
    try {
      const response = await authApi.post('/api/auth/register', userData);
      
      const { access_token, refresh_token, user: newUser } = response.data;
      
      // Store tokens and user data
      localStorage.setItem('openscholar_access_token', access_token);
      localStorage.setItem('openscholar_refresh_token', refresh_token);
      localStorage.setItem('openscholar_user', JSON.stringify(newUser));
      
      setUser(newUser);
    } catch (error: any) {
      clearAuthData();
      throw new Error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      // Call logout endpoint to invalidate session on server
      const token = localStorage.getItem('openscholar_access_token');
      if (token) {
        await authApi.post('/api/auth/logout', {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local data regardless of server response
      clearAuthData();
      
      // Clear all user-specific data
      localStorage.removeItem('openscholar_collections');
      localStorage.removeItem('openscholar_settings');
      localStorage.removeItem('openscholar_saved_searches');
    }
  };

  const updateProfile = async (userData: Partial<User>): Promise<void> => {
    if (!user) throw new Error('No user logged in');
    
    try {
      const token = localStorage.getItem('openscholar_access_token');
      await authApi.put('/api/auth/me', userData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update local user data
      const updatedUser = { ...user, ...userData };
      setUser(updatedUser);
      localStorage.setItem('openscholar_user', JSON.stringify(updatedUser));
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update profile');
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    updateProfile
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;