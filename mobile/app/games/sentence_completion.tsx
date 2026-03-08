import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { getNewGameRound, checkGameAnswers } from '@/services/api';
import { Colors } from '@/constants/theme';
import { Header } from '@/components/Header';

export default function SentenceCompletionScreen() {
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
      const data = await getNewGameRound('sentence_completion');
      setQuestions(data.questions || []);
      setAnswers(new Array((data.questions || []).length).fill(""));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (qIndex: number, option: string) => {
    const newAnswers = [...answers];
    newAnswers[qIndex] = option;
    setAnswers(newAnswers);
  };

  const handleSubmit = async () => {
    if (answers.some(a => !a)) {
      alert("Please answer all questions");
      return;
    }
    setSubmitting(true);
    try {
      const res = await checkGameAnswers('sentence_completion', { answers });
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
      <Header title="📝 Sentence Completion" showBack onBack={() => router.back()} />
      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.light.tint} /></View>
      ) : result ? (
        <ScrollView contentContainerStyle={styles.content}>
          <Text style={styles.scoreText}>Score: {result.score}/{result.total}</Text>
          
          {result.details.map((detail: any, idx: number) => (
            <View key={idx} style={[styles.resultCard, detail.is_correct ? styles.correct : styles.incorrect]}>
              <Text style={styles.sentence}>{detail.original_sentence}</Text>
              {detail.is_correct ? (
                <Text style={styles.resultText}>✅ Correct</Text>
              ) : (
                <View>
                  <Text style={styles.resultError}>❌ Your Answer: {detail.user_answer}</Text>
                  <Text style={styles.resultFix}>Correct: {detail.correct_word}</Text>
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
          <Text style={styles.instructions}>Fill in the blank with the correct vocabulary word.</Text>
          {questions.map((q, qIndex) => (
            <View key={qIndex} style={styles.questionCard}>
              <Text style={styles.sentence}>{qIndex + 1}. {q.sentence}</Text>
              <Text style={styles.hint}>Hint: {q.hint}</Text>
              
              <View style={styles.optionsGrid}>
                {q.options.map((opt: string, optIndex: number) => {
                  const isSelected = answers[qIndex] === opt;
                  return (
                    <TouchableOpacity 
                      key={optIndex} 
                      style={[styles.optionBtn, isSelected && styles.selectedOption]}
                      onPress={() => handleSelect(qIndex, opt)}
                    >
                      <Text style={[styles.optionText, isSelected && styles.selectedOptionText]}>{opt}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
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
  instructions: { fontSize: 16, color: '#666', marginBottom: 16, textAlign: 'center' },
  questionCard: { backgroundColor: '#fff', borderRadius: 16, padding: 16, marginBottom: 16, elevation: 2 },
  sentence: { fontSize: 18, fontWeight: 'bold', marginBottom: 8, color: '#333', lineHeight: 24 },
  hint: { fontSize: 14, color: '#888', fontStyle: 'italic', marginBottom: 16 },
  optionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  optionBtn: { paddingVertical: 8, paddingHorizontal: 12, borderRadius: 20, backgroundColor: '#f8f9fa', borderWidth: 1, borderColor: '#eee' },
  selectedOption: { backgroundColor: Colors.light.tint, borderColor: Colors.light.tint },
  optionText: { fontSize: 14, color: '#444' },
  selectedOptionText: { color: '#fff', fontWeight: 'bold' },
  submitBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 16 },
  disabledBtn: { opacity: 0.7 },
  scoreText: { fontSize: 32, fontWeight: 'bold', textAlign: 'center', color: Colors.light.tint, marginTop: 16, marginBottom: 24 },
  resultCard: { backgroundColor: '#fff', padding: 16, borderRadius: 12, marginBottom: 16, borderWidth: 1 },
  correct: { borderColor: '#4cd964', backgroundColor: '#eeffef' },
  incorrect: { borderColor: '#ff3b30', backgroundColor: '#fff5f5' },
  resultText: { color: '#4cd964', fontWeight: 'bold', marginTop: 8 },
  resultError: { color: '#ff3b30', marginTop: 8 },
  resultFix: { color: '#28a745', fontWeight: 'bold', marginTop: 4 },
  playAgainBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 24 },
  playAgainText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});
