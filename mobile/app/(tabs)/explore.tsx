import React from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity, Text } from 'react-native';
import { useRouter } from 'expo-router';
import { Header } from '@/components/Header';
import { IconSymbol } from '@/components/ui/icon-symbol';

const practiceModules = [
  { id: 'speaking', title: 'Speaking Practice', icon: 'mic.fill', color: '#E1306C', desc: 'Mock interview & feedback' },
  { id: 'listening', title: 'Listening Practice', icon: 'headphones', color: '#F77737', desc: 'Audio comprehension' },
  { id: 'reading', title: 'Reading Practice', icon: 'book.fill', color: '#4cd964', desc: 'Passage analysis' },
];

export default function PracticeScreen() {
  const router = useRouter();
  return (
    <View style={styles.container}>
      <Header title="Practice" />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.grid}>
          {practiceModules.map((mod) => (
            <TouchableOpacity 
              key={mod.id} 
              style={styles.card}
              onPress={() => router.push(`/practice/${mod.id}` as any)}
            >
              <View style={[styles.iconContainer, { backgroundColor: mod.color + '20' }]}>
                 {/* @ts-ignore */}
                <IconSymbol name={mod.icon} size={32} color={mod.color} />
              </View>
              <Text style={styles.cardTitle}>{mod.title}</Text>
              <Text style={styles.cardDesc}>{mod.desc}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    padding: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    justifyContent: 'space-between',
  },
  card: {
    width: '47%',
    backgroundColor: '#f8f9fa',
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#eee',
  },
  iconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
    color: '#333',
    marginBottom: 4,
  },
  cardDesc: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
});
