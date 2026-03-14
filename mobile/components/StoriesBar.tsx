import React, { useEffect, useState } from 'react';
import { ScrollView, View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { router } from 'expo-router';
import { getDailyWords } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';

interface Word {
  word: string;
  band_level: number | string;
}

export function StoriesBar() {
  const { auth, isLoading: authLoading } = useAuth();
  const [words, setWords] = useState<Word[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Only attempt fetch if auth has loaded and is present
    if (authLoading || !auth) {
      return;
    }

    const fetchWords = async () => {
      try {
        const data = await getDailyWords();
        if (data) {
          setWords(data);
        }
      } catch (error) {
        console.error("Failed to fetch words:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchWords();
  }, [auth, authLoading]);

  // Handle immediate UI rendering without erroring
  if (loading || authLoading || !auth) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center', height: 100 }]}>
        <ActivityIndicator size="small" color="#E1306C" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {words.map((item, index) => (
          <TouchableOpacity key={index} style={styles.storyItem} onPress={() => router.push(`/word/${item.word}` as any)}>
            <View style={styles.storyRing}>
              <View style={styles.storyInner}>
                <Text style={styles.bandText}>{item.band_level}</Text>
              </View>
            </View>
            <Text style={styles.wordText} numberOfLines={1}>
              {item.word}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  scrollContent: {
    paddingHorizontal: 16,
    gap: 16,
  },
  storyItem: {
    alignItems: 'center',
    width: 70,
  },
  storyRing: {
    width: 64,
    height: 64,
    borderRadius: 32,
    borderWidth: 2,
    borderColor: '#E1306C', // Instagram-like gradient ring color
    justifyContent: 'center',
    alignItems: 'center',
    padding: 2,
  },
  storyInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#f3e5f5', // Soft background
    justifyContent: 'center',
    alignItems: 'center',
  },
  bandText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#764ba2',
  },
  wordText: {
    marginTop: 4,
    fontSize: 12,
    color: '#333',
    textAlign: 'center',
  },
});
