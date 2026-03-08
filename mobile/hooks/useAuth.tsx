import { useRouter, useSegments } from 'expo-router';
import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { setAuthHeaders } from '../services/api';

type AuthType = {
  username: string;
  session_id: string;
} | null;

interface AuthContextType {
  auth: AuthType;
  setAuth: (auth: AuthType) => void;
  isLoading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthType>(null);
  const [isLoading, setIsLoading] = useState(true);
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    // Check existing session
    const loadSession = async () => {
      try {
        const storedUsername = await AsyncStorage.getItem('username');
        const storedSessionId = await AsyncStorage.getItem('session_id');

        if (storedUsername && storedSessionId) {
          setAuth({ username: storedUsername, session_id: storedSessionId });
          setAuthHeaders(storedUsername, storedSessionId);
        }
      } catch (error) {
        console.error('Error loading session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadSession();
  }, []);

  useEffect(() => {
    if (isLoading) return;

    // Check if the current route segment is a protected route by ensuring it's not the login page
    // The login page is typically at the root where segments[0] is undefined
    const isLogin = segments[0] === undefined;

    if (!auth && !isLogin) { 
      // Redirect to the login page if not authenticated and not on login page
      router.replace('/');
    } else if (auth && isLogin) { 
      // Redirect away from login to tabs if authenticated
      router.replace('/(tabs)');
    }
  }, [auth, segments, isLoading]);

  const logout = async () => {
    try {
      await AsyncStorage.removeItem('username');
      await AsyncStorage.removeItem('session_id');
      setAuth(null);
      // Remove headers when logging out
      setAuthHeaders('', ''); 
    } catch (e) {
      console.error('Error on logout:', e);
    }
  };

  return (
    <AuthContext.Provider value={{ auth, setAuth, isLoading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
