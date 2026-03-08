import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { getNewGameRound, checkGameAnswers } from '@/services/api';
import { Colors } from '@/constants/theme';
import { Header } from '@/components/Header';

export default function WordMatchingScreen() {
  const router = useRouter();
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    loadRound();
  }, []);

  const loadRound = async () => {
    setLoading(true);
    setResult(null);
    setAnswers({});
    try {
      const data = await getNewGameRound('word_matching');
      setQuestions(data.questions || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (word: string, option: string) => {
    setAnswers(prev => ({ ...prev, [word]: option }));
  };

  const handleSubmit = async () => {
    if (Object.keys(answers).length < questions.length) {
      alert("Please answer all questions");
      return;
    }
    setSubmitting(true);
    try {
      const res = await checkGameAnswers('word_matching', { answers });
      setResult(res);
    } catch (error) {
      console.error(error);
      alert("Failed to submit");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Header title="🔤 Word Matching" showBack onBack={() => router.back()} />
      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.light.tint} /></View>
      ) : result ? (
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.scoreText}>Score: {result.score}/{result.total}</Text>
          <Text style={styles.timeText}>Time: {result.time_seconds.toFixed(1)}s</Text>
          
          {result.details.map((detail: any, idx: number) => (
            <View key={idx} style={[styles.resultCard, detail.is_correct ? styles.correct : styles.incorrect]}>
              <Text style={styles.resultWord}>{detail.word}</Text>
              {detail.is_correct ? (
                <Text style={styles.resultText}>✅ Correct</Text>
              ) : (
                <View>
                  <Text style={styles.resultError}>❌ {detail.user_answer}</Text>
                  <Text style={styles.resultFix}>Correct: {detail.correct_answer}</Text>
                </View>
              )}
            </View>
          ))}
          
          <TouchableOpacity style={styles.playAgainBtn} onPress={loadRound}>
            <Text style={styles.playAgainText}>Play Again</Text>
          </TouchableOpacity>
        </ScrollView>
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          {questions.map((q, qIndex) => (
            <View key={qIndex} style={styles.questionCard}>
              <Text style={styles.word}>{q.word}</Text>
              {q.options.map((opt: string, optIndex: number) => {
                const isSelected = answers[q.word] === opt;
                return (
                  <TouchableOpacity 
                    key={optIndex} 
                    style={[styles.optionBtn, isSelected && styles.selectedOption]}
                    onPress={() => handleSelect(q.word, opt)}
                  >
                    <Text style={[styles.optionText, isSelected && styles.selectedOptionText]}>{opt}</Text>
                  </TouchableOpacity>
                );
              })}
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 16, paddingBottom: 40 },
  questionCard: { backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 16, elevation: 2 },
  word: { fontSize: 20, fontWeight: 'bold', marginBottom: 12, color: '#333' },
  optionBtn: { padding: 12, borderRadius: 8, backgroundColor: '#f8f9fa', marginBottom: 8, borderWidth: 1, borderColor: '#eee' },
  selectedOption: { backgroundColor: Colors.light.tint, borderColor: Colors.light.tint },
  optionText: { fontSize: 16, color: '#444' },
  selectedOptionText: { color: '#fff', fontWeight: 'bold' },
  submitBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 16 },
  disabledBtn: { opacity: 0.7 },
  scoreText: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', color: Colors.light.tint, marginTop: 16 },
  timeText: { fontSize: 16, textAlign: 'center', color: '#666', marginBottom: 24 },
  resultCard: { backgroundColor: '#fff', padding: 16, borderRadius: 12, marginBottom: 16, borderWidth: 1 },
  correct: { borderColor: '#4cd964', backgroundColor: '#eeffef' },
  incorrect: { borderColor: '#ff3b30', backgroundColor: '#fff5f5' },
  resultWord: { fontSize: 18, fontWeight: 'bold', marginBottom: 8 },
  resultText: { color: '#4cd964', fontWeight: 'bold' },
  resultError: { color: '#ff3b30', textDecorationLine: 'line-through', marginBottom: 4 },
  resultFix: { color: '#28a745', fontWeight: 'bold' },
  playAgainBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 24 },
  playAgainText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});
