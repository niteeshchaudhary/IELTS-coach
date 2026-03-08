import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { getPracticeModule, evaluatePractice } from '@/services/api';
import { Colors } from '@/constants/theme';
import { Header } from '@/components/Header';

export default function ReadingPracticeScreen() {
  const router = useRouter();
  const [content, setContent] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [resultMode, setResultMode] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    loadContent();
  }, []);

  const loadContent = async () => {
    setLoading(true);
    setResultMode(false);
    setAnswers({});
    try {
      const data = await getPracticeModule('reading');
      setContent(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (qId: string, option: string) => {
    if (resultMode) return;
    setAnswers(prev => ({ ...prev, [qId]: option }));
  };

  const handleSubmit = async () => {
    if (!content) return;
    if (Object.keys(answers).length < content.questions.length) {
      alert("Please answer all questions");
      return;
    }
    setSubmitting(true);
    try {
      await evaluatePractice('reading', { answers });
      setResultMode(true);
      if (scrollViewRef.current) {
         scrollViewRef.current.scrollTo({ y: 0, animated: true });
      }
    } catch (error) {
      console.error(error);
      alert("Failed to submit");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Header title="📖 Reading Practice" showBack onBack={() => router.back()} />
      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.light.tint} /></View>
      ) : content ? (
        <ScrollView ref={scrollViewRef} contentContainerStyle={styles.content}>
          <Text style={styles.title}>{content.title}</Text>
          <View style={styles.passageCard}>
            <Text style={styles.passageText}>{content.passage}</Text>
          </View>
          
          <Text style={styles.sectionTitle}>Questions</Text>
          {content.questions.map((q: any, qIndex: number) => {
            const userAnswer = answers[q.id];
            const isCorrect = userAnswer === q.answer;
            
            return (
              <View key={q.id} style={styles.questionCard}>
                <Text style={styles.questionText}>{qIndex + 1}. {q.question}</Text>
                
                {q.options.map((opt: string, optIndex: number) => {
                  const isSelected = userAnswer === opt;
                  
                  let optionStyle: any = styles.optionBtn;
                  let textStyle: any = styles.optionText;
                  
                  if (resultMode) {
                    if (opt === q.answer) {
                      optionStyle = [styles.optionBtn, styles.correctOption];
                      textStyle = [styles.optionText, styles.correctText];
                    } else if (isSelected && !isCorrect) {
                      optionStyle = [styles.optionBtn, styles.incorrectOption];
                      textStyle = [styles.optionText, styles.incorrectText];
                    }
                  } else if (isSelected) {
                    optionStyle = [styles.optionBtn, styles.selectedOption];
                    textStyle = [styles.optionText, styles.selectedText];
                  }
                  
                  return (
                    <TouchableOpacity 
                      key={optIndex} 
                      style={optionStyle}
                      onPress={() => handleSelect(q.id, opt)}
                      disabled={resultMode}
                    >
                      <Text style={textStyle}>{opt}</Text>
                    </TouchableOpacity>
                  );
                })}
                
                {resultMode && (
                  <View style={styles.explanationBox}>
                    <Text style={isCorrect ? styles.resultCorrect : styles.resultIncorrect}>
                      {isCorrect ? '✅ Correct' : '❌ Incorrect'}
                    </Text>
                    <Text style={styles.explanationText}>💡 {q.explanation}</Text>
                  </View>
                )}
              </View>
            );
          })}
          
          {!resultMode ? (
            <TouchableOpacity 
              style={[styles.submitBtn, submitting && styles.disabledBtn]} 
              onPress={handleSubmit}
              disabled={submitting}
            >
              {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Check Answers</Text>}
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.submitBtn} onPress={loadContent}>
              <Text style={styles.btnText}>Try Another Passage</Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      ) : (
        <View style={styles.center}><Text>Failed to load content.</Text></View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 16, paddingBottom: 40 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 16, color: '#333' },
  passageCard: { backgroundColor: '#fff', padding: 16, borderRadius: 12, marginBottom: 24, shadowColor: '#000', shadowOffset: {width: 0, height: 1}, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
  passageText: { fontSize: 16, lineHeight: 26, color: '#444' },
  sectionTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 16, color: '#333' },
  questionCard: { backgroundColor: '#fff', padding: 16, borderRadius: 12, marginBottom: 16, shadowColor: '#000', shadowOffset: {width: 0, height: 1}, shadowOpacity: 0.1, shadowRadius: 2, elevation: 2 },
  questionText: { fontSize: 16, fontWeight: '600', marginBottom: 12, color: '#333' },
  optionBtn: { padding: 14, borderRadius: 8, backgroundColor: '#f8f9fa', marginBottom: 8, borderWidth: 1, borderColor: '#eee' },
  selectedOption: { backgroundColor: Colors.light.tint, borderColor: Colors.light.tint },
  correctOption: { backgroundColor: '#eeffef', borderColor: '#4cd964' },
  incorrectOption: { backgroundColor: '#fff5f5', borderColor: '#ff3b30' },
  optionText: { fontSize: 15, color: '#444' },
  selectedText: { color: '#fff', fontWeight: 'bold' },
  correctText: { color: '#28a745', fontWeight: 'bold' },
  incorrectText: { color: '#ff3b30', fontWeight: 'bold' },
  explanationBox: { marginTop: 12, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 8 },
  resultCorrect: { color: '#28a745', fontWeight: 'bold', marginBottom: 4 },
  resultIncorrect: { color: '#ff3b30', fontWeight: 'bold', marginBottom: 4 },
  explanationText: { fontSize: 14, color: '#666', fontStyle: 'italic', lineHeight: 20 },
  submitBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 16 },
  disabledBtn: { opacity: 0.7 },
  btnText: { color: '#fff', fontSize: 18, fontWeight: 'bold' }
});
