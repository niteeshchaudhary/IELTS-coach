import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { getNewGameRound, checkGameAnswers } from '@/services/api';
import { Colors } from '@/constants/theme';
import { Header } from '@/components/Header';

export default function TypingSpeedScreen() {
  const router = useRouter();
  const [targetSentence, setTargetSentence] = useState('');
  const [typedText, setTypedText] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    loadRound();
  }, []);

  const loadRound = async () => {
    setLoading(true);
    setResult(null);
    setTypedText('');
    try {
      const data = await getNewGameRound('typing_speed');
      setTargetSentence(data.sentence);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!typedText.trim()) return;
    setSubmitting(true);
    try {
      const res = await checkGameAnswers('typing_speed', { answer: typedText });
      setResult(res);
    } catch (error) {
      console.error(error);
      alert("Failed to submit");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <Header title="⌨️ Typing Speed" showBack onBack={() => router.back()} />
      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.light.tint} /></View>
      ) : result ? (
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.scoreText}>Accuracy: {result.score}%</Text>
          <View style={styles.statsRow}>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>{result.details[0].wpm.toFixed(1)}</Text>
              <Text style={styles.statLabel}>WPM</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statValue}>{result.time_seconds.toFixed(1)}s</Text>
              <Text style={styles.statLabel}>Time</Text>
            </View>
          </View>
          
          <View style={styles.resultCard}>
            <Text style={styles.resultLabel}>Target:</Text>
            <Text style={styles.resultTarget}>{result.details[0].target}</Text>
            <Text style={[styles.resultLabel, {marginTop: 16}]}>You Typed:</Text>
            <Text style={styles.resultTyped}>{result.details[0].typed}</Text>
          </View>
          
          <TouchableOpacity style={styles.playAgainBtn} onPress={loadRound}>
            <Text style={styles.playAgainText}>Next Sentence</Text>
          </TouchableOpacity>
        </ScrollView>
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.instructions}>Type the sentence as fast and accurately as you can!</Text>
          
          <View style={styles.targetCard}>
            <Text style={styles.targetSentence}>{targetSentence}</Text>
          </View>
          
          <TextInput
            style={styles.input}
            multiline
            numberOfLines={4}
            value={typedText}
            onChangeText={setTypedText}
            placeholder="Start typing here..."
            placeholderTextColor="#999"
            autoCapitalize="sentences"
            autoCorrect={false}
          />
          
          <TouchableOpacity 
            style={[styles.submitBtn, (!typedText.trim() || submitting) && styles.disabledBtn]} 
            onPress={handleSubmit}
            disabled={!typedText.trim() || submitting}
          >
            {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.playAgainText}>Submit</Text>}
          </TouchableOpacity>
        </ScrollView>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 16, paddingBottom: 40 },
  instructions: { fontSize: 16, color: '#666', marginBottom: 16, textAlign: 'center' },
  targetCard: { backgroundColor: '#e3f2fd', borderRadius: 16, padding: 20, marginBottom: 24, borderWidth: 1, borderColor: '#bbdefb' },
  targetSentence: { fontSize: 22, fontWeight: 'bold', color: '#1565c0', lineHeight: 30, textAlign: 'center' },
  input: { backgroundColor: '#fff', borderRadius: 16, padding: 16, fontSize: 18, minHeight: 120, textAlignVertical: 'top', shadowColor: '#000', shadowOffset: {width: 0, height: 2}, shadowOpacity: 0.05, shadowRadius: 4, elevation: 2, marginBottom: 24 },
  submitBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center' },
  disabledBtn: { opacity: 0.5 },
  scoreText: { fontSize: 36, fontWeight: 'bold', textAlign: 'center', color: Colors.light.tint, marginTop: 16, marginBottom: 24 },
  statsRow: { flexDirection: 'row', justifyContent: 'center', gap: 16, marginBottom: 24 },
  statBox: { backgroundColor: '#fff', padding: 16, borderRadius: 12, alignItems: 'center', minWidth: 100, elevation: 2 },
  statValue: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  statLabel: { fontSize: 14, color: '#888', marginTop: 4 },
  resultCard: { backgroundColor: '#fff', padding: 20, borderRadius: 16, elevation: 2, marginBottom: 24 },
  resultLabel: { fontSize: 14, color: '#666', textTransform: 'uppercase', fontWeight: 'bold', marginBottom: 8 },
  resultTarget: { fontSize: 18, color: '#333', lineHeight: 26 },
  resultTyped: { fontSize: 18, color: Colors.light.tint, lineHeight: 26, fontStyle: 'italic' },
  playAgainBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center' },
  playAgainText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});
