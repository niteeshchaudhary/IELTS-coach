import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Text, TouchableOpacity, Dimensions, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getWordDetail, getDailyWords } from '@/services/api';

const { width, height } = Dimensions.get('window');

interface WordDetail {
  word: string;
  band_level: string;
  meaning: string;
  example_sentences: string[];
}

export default function WordStoryScreen() {
  const { id } = useLocalSearchParams();
  const insets = useSafeAreaInsets();
  const [wordData, setWordData] = useState<WordDetail | null>(null);
  const [dailyWords, setDailyWords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const wordsList = await getDailyWords();
        setDailyWords(wordsList);
        
        if (id) {
          const data = await getWordDetail(id as string);
          setWordData(data);
        }
      } catch (error) {
        console.error("Failed to load word details", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const navigateToBoundary = (direction: 'next' | 'prev') => {
    if (!dailyWords.length || !wordData) return;
    
    const currentIndex = dailyWords.findIndex(w => w.word.toLowerCase() === wordData.word.toLowerCase());
    if (currentIndex === -1) return;

    let targetIndex = currentIndex;
    if (direction === 'next' && currentIndex < dailyWords.length - 1) {
      targetIndex = currentIndex + 1;
    } else if (direction === 'prev' && currentIndex > 0) {
      targetIndex = currentIndex - 1;
    } else {
      // Loop or go back
      if (direction === 'prev' && currentIndex === 0) {
         router.back();
         return;
      }
      return; // End of list
    }

    if (targetIndex !== currentIndex) {
      const nextWord = dailyWords[targetIndex];
      router.replace(`/word/${nextWord.word}` as any);
    }
  };

  if (loading || !wordData) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Progress Bars (Instagram style indicator) */}
      <View style={[styles.progressContainer, { top: insets.top + 10 }]}>
        {dailyWords.map((w, idx) => {
          const currentIndex = dailyWords.findIndex(dw => dw.word.toLowerCase() === wordData.word.toLowerCase());
          const isActive = idx <= currentIndex;
          return (
            <View key={idx} style={isActive ? styles.progressBarActive : styles.progressBarInactive} />
          );
        })}
      </View>

      <TouchableOpacity style={styles.closeArea} onPress={() => router.back()}>
        <Text style={styles.closeText}>×</Text>
      </TouchableOpacity>

      <View style={styles.content}>
        <Text style={styles.word}>{wordData.word}</Text>
        <View style={styles.bandBadge}>
          <Text style={styles.bandText}>Band {wordData.band_level}</Text>
        </View>
        
        <View style={styles.meaningCard}>
          <Text style={styles.partOfSpeech}>meaning</Text>
          <Text style={styles.definition}>
            {wordData.meaning}
          </Text>
          {wordData.example_sentences && wordData.example_sentences[0] && (
            <View style={styles.exampleContainer}>
              <Text style={styles.exampleLabel}>Example:</Text>
              <Text style={styles.example}>
                &quot;{wordData.example_sentences[0]}&quot;
              </Text>
            </View>
          )}
        </View>
      </View>
      
      {/* Navigation Areas */}
      <TouchableOpacity style={styles.leftNav} onPress={() => navigateToBoundary('prev')} />
      <TouchableOpacity style={styles.rightNav} onPress={() => navigateToBoundary('next')} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#764ba2', // Gradient-like base color
  },
  progressContainer: {
    position: 'absolute',
    left: 16,
    right: 16,
    flexDirection: 'row',
    gap: 4,
    zIndex: 10,
  },
  progressBarActive: {
    flex: 1,
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.9)',
    borderRadius: 2,
  },
  progressBarInactive: {
    flex: 1,
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 2,
  },
  closeArea: {
    position: 'absolute',
    top: 60,
    right: 16,
    zIndex: 10,
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeText: {
    fontSize: 32,
    color: '#fff',
    fontWeight: '300',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  word: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  bandBadge: {
    backgroundColor: '#E1306C',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 16,
    marginBottom: 16,
  },
  bandText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  phonetic: {
    fontSize: 18,
    color: 'rgba(255,255,255,0.8)',
    fontStyle: 'italic',
    marginBottom: 32,
  },
  meaningCard: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    padding: 24,
    borderRadius: 16,
    width: '100%',
  },
  partOfSpeech: {
    color: '#E1306C',
    fontWeight: 'bold',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  definition: {
    fontSize: 20,
    color: '#fff',
    lineHeight: 28,
    marginBottom: 16,
  },
  exampleContainer: {
    marginTop: 8,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.2)',
  },
  exampleLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#E1306C',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  example: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.9)',
    fontStyle: 'italic',
    lineHeight: 24,
  },
  leftNav: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: width * 0.3,
  },
  rightNav: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: width * 0.3,
  },
});
