import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { getNewGameRound, checkGameAnswers } from '@/services/api';
import { Colors } from '@/constants/theme';
import { Header } from '@/components/Header';

export default function ErrorCorrectionScreen() {
  const router = useRouter();
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    loadRound();
  }, []);

  const loadRound = async () => {
    setLoading(true);
    setResult(null);
    setAnswers([]);
    try {
      const data = await getNewGameRound('error_correction');
      setQuestions(data.questions || []);
      setAnswers(new Array((data.questions || []).length).fill(""));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleInput = (text: string, index: number) => {
    const newAnswers = [...answers];
    newAnswers[index] = text;
    setAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    if (answers.some(a => !a.trim())) {
      alert("Please provide corrections for all sentences");
      return;
    }
    setSubmitting(true);
    try {
      const res = await checkGameAnswers('error_correction', { answers });
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
      <Header title="🔍 Error Correction" showBack onBack={() => router.back()} />
      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.light.tint} /></View>
      ) : result ? (
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.scoreText}>Score: {result.score}/{result.total}</Text>
          
          {result.details.map((detail: any, idx: number) => (
            <View key={idx} style={[styles.resultCard, detail.is_correct ? styles.correct : styles.incorrect]}>
              <Text style={styles.badSentence}>❌ {detail.incorrect}</Text>
              
              {detail.is_correct ? (
                <View style={styles.correctBox}>
                  <Text style={styles.resultText}>✅ Correct!</Text>
                </View>
              ) : (
                <View style={styles.incorrectBox}>
                  <Text style={styles.resultError}>Your fix: {detail.user_answer}</Text>
                  <Text style={styles.resultFix}>Right answer: {detail.correct_answer}</Text>
                </View>
              )}
              
              <Text style={styles.explanation}>💡 {detail.explanation}</Text>
            </View>
          ))}
          
          <TouchableOpacity style={styles.playAgainBtn} onPress={loadRound}>
            <Text style={styles.playAgainText}>Play Again</Text>
          </TouchableOpacity>
        </ScrollView>
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.instructions}>Find and fix the error in each sentence.</Text>
          
          {questions.map((q, qIndex) => (
            <View key={qIndex} style={styles.questionCard}>
              <Text style={styles.badSentence}>❌ {q.sentence}</Text>
              <Text style={styles.hint}>Hint: {q.hint}</Text>
              
              <TextInput
                style={styles.input}
                placeholder="Type the corrected sentence here..."
                placeholderTextColor="#999"
                value={answers[qIndex]}
                onChangeText={(text) => handleInput(text, qIndex)}
                autoCapitalize="sentences"
                multiline
              />
            </View>
          ))}
          
          <TouchableOpacity 
            style={[styles.submitBtn, submitting && styles.disabledBtn]} 
            onPress={handleSubmit}
            disabled={submitting}
          >
            {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.playAgainText}>Check Answers</Text>}
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
  questionCard: { backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 16, elevation: 2 },
  badSentence: { fontSize: 18, color: '#ff3b30', fontWeight: '500', marginBottom: 8, lineHeight: 24 },
  hint: { fontSize: 14, color: '#888', fontStyle: 'italic', marginBottom: 16 },
  input: { backgroundColor: '#f8f9fa', borderRadius: 12, padding: 16, fontSize: 16, borderWidth: 1, borderColor: '#eee', minHeight: 80, textAlignVertical: 'top' },
  submitBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 16 },
  disabledBtn: { opacity: 0.7 },
  scoreText: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', color: Colors.light.tint, marginTop: 16, marginBottom: 24 },
  resultCard: { backgroundColor: '#fff', padding: 16, borderRadius: 12, marginBottom: 16, borderWidth: 1 },
  correct: { borderColor: '#4cd964' },
  incorrect: { borderColor: '#ff3b30' },
  correctBox: { backgroundColor: '#eeffef', padding: 12, borderRadius: 8, marginVertical: 12 },
  incorrectBox: { backgroundColor: '#fff5f5', padding: 12, borderRadius: 8, marginVertical: 12 },
  resultText: { color: '#28a745', fontWeight: 'bold' },
  resultError: { color: '#ff3b30', marginBottom: 4, textDecorationLine: 'line-through' },
  resultFix: { color: '#28a745', fontWeight: 'bold' },
  explanation: { fontSize: 14, color: '#666', fontStyle: 'italic', marginTop: 8 },
  playAgainBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 24 },
  playAgainText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});
