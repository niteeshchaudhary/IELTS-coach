import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Use localhost for iOS simulator, 10.0.2.2 for Android emulator, or your computer's local IP for physical devices
const BASE_URL = Platform.OS === 'android' ? 'http://192.168.29.47:8008/api' : 'http://192.168.29.47:8008/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

// Store auth state locally in the API service so we don't have to pass it everywhere
let currentUsername = '';
let currentSessionId = '';

export const setAuthHeaders = (username: string, sessionId: string) => {
  currentUsername = username;
  currentSessionId = sessionId;
};

api.interceptors.request.use(async (config) => {
  if (!currentUsername || !currentSessionId) {
    try {
      const u = await AsyncStorage.getItem('username');
      const s = await AsyncStorage.getItem('session_id');
      if (u && s) {
        currentUsername = u;
        currentSessionId = s;
      }
    } catch (e) {
      console.warn("Failed to load auth from storage", e);
    }
  }

  if (currentUsername && currentSessionId) {
    config.params = {
      ...(config.params || {}),
      username: currentUsername,
      session_id: currentSessionId,
    };
  }
  return config;
});

// Response interceptor to catch 401 / 422 and force logout effectively
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 422)) {
      currentUsername = '';
      currentSessionId = '';
      await AsyncStorage.removeItem('username');
      await AsyncStorage.removeItem('session_id');
    }
    return Promise.reject(error);
  }
);

export const login = async (username: string, password: string) => {
  // Use a second axios instance to avoid the interceptor when not logged in
  const response = await axios.post(`${BASE_URL}/login`, { username, password });
  return response.data;
};

export const signup = async (username: string, password: string) => {
  const response = await axios.post(`${BASE_URL}/signup`, { username, password });
  return response.data;
};

export const getDailyWords = async () => {
  const response = await api.get('/words');
  return response.data.words;
};

export const getWordDetail = async (wordId: string) => {
  const response = await api.get(`/words/${wordId}`);
  return response.data;
};

export const sendChatMessage = async (message: string) => {
  const response = await api.post('/chat', { message });
  return response.data;
};

export const getProfile = async () => {
    const response = await api.get('/profile');
    return response.data;
}

export const getGames = async () => {
    const response = await api.get('/games');
    return response.data.games;
}

export const getNewGameRound = async (gameId: string) => {
    const response = await api.get(`/games/${gameId}/new`);
    return response.data;
}

export const checkGameAnswers = async (gameId: string, payload: any) => {
    const response = await api.post(`/games/${gameId}/check`, payload);
    return response.data;
}

export const getPracticeModule = async (moduleId: string) => {
    const response = await api.get(`/practice/${moduleId}`);
    return response.data;
}

export const evaluatePractice = async (moduleId: string, payload: any) => {
    const response = await api.post(`/practice/evaluate/${moduleId}`, payload);
    return response.data;
}

export default api;
