import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator, TextInput } from 'react-native';
import { useRouter } from 'expo-router';
// @ts-ignore
import Voice from '@react-native-voice/voice';
import { getPracticeModule, evaluatePractice } from '@/services/api';
import { Colors } from '@/constants/theme';
import { Header } from '@/components/Header';
import { IconSymbol } from '@/components/ui/icon-symbol';

export default function SpeakingPracticeScreen() {
  const router = useRouter();
  const [topics, setTopics] = useState<any>(null);
  const [selectedTopic, setSelectedTopic] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  
  // Submit state
  const [spokenText, setSpokenText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [nativeVoiceAvailable, setNativeVoiceAvailable] = useState(true);

  useEffect(() => {
    loadContent();
    
    const setupVoice = async () => {
      try {
        // @ts-ignore
        if (Voice && typeof Voice.isSpeechAvailable === 'function') {
          // @ts-ignore
          const available = await Voice.isSpeechAvailable();
          setNativeVoiceAvailable(!!available);
        } else {
          // If the method doesn't exist, we assume it's available or we'll find out on start
        }
        
        Voice.onSpeechStart = () => setIsRecording(true);
        Voice.onSpeechEnd = () => setIsRecording(false);
        Voice.onSpeechError = (e: any) => {
          console.warn("Speech recognition error:", e);
          setIsRecording(false);
        };
        Voice.onSpeechResults = (e: any) => {
          if (e.value && e.value.length > 0) {
            setSpokenText(e.value[0]);
          }
        };
        Voice.onSpeechPartialResults = (e: any) => {
           if (e.value && e.value.length > 0) {
             setSpokenText(e.value[0]);
           }
        };
      } catch (e) {
        console.warn("Failed to setup native voice module:", e);
        setNativeVoiceAvailable(false);
      }
    };
    
    setupVoice();

    return () => {
      const cleanUp = async () => {
        try {
          if (Voice && typeof Voice.destroy === 'function') {
            await Voice.destroy();
          }
          if (Voice && typeof Voice.removeAllListeners === 'function') {
            Voice.removeAllListeners();
          }
        } catch (error) {
           // Silent catch for native voice errors
        }
      };
      cleanUp();
    };
  }, []);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const loadContent = async () => {
    setLoading(true);
    try {
      const data = await getPracticeModule('speaking');
      setTopics(data);
      const randomTopic = data.part2[Math.floor(Math.random() * data.part2.length)];
      setSelectedTopic(randomTopic);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleRecording = async () => {
    try {
      if (isRecording) {
        // Stop recording
        try {
          if (Voice && typeof Voice.stop === 'function') {
            await Voice.stop();
          }
        } catch(e) {
           console.warn("Voice stop failed:", e);
        }
        setIsRecording(false);
      } else {
        // Start recording
        setRecordingSeconds(0);
        setSpokenText("");
        setResult(null);
        setIsRecording(true);
        
        try {
          if (Voice && typeof Voice.start === 'function') {
            await Voice.start('en-US');
          } else {
            setNativeVoiceAvailable(false);
          }
        } catch(e) {
          console.warn("Could not start Voice module (native transcription might be missing in Expo Go):", e);
          setNativeVoiceAvailable(false);
        }
      }
    } catch (e) {
      console.error("Recording toggle logic error:", e);
      setIsRecording(!isRecording);
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async () => {
    if (!spokenText.trim()) {
      alert("Please provide the transcribed text.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await evaluatePractice('speaking', { 
        text: spokenText,
        duration_seconds: Math.max(recordingSeconds, 15), // Ensure at least 15s
        topic: selectedTopic.topic
      });
      setResult(res);
    } catch (error) {
      console.error(error);
      alert("Failed to evaluate speaking.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetPractice = () => {
    setResult(null);
    setSpokenText("");
    setRecordingSeconds(0);
    // Pick another topic
    const randomTopic = topics.part2[Math.floor(Math.random() * topics.part2.length)];
    setSelectedTopic(randomTopic);
  };

  return (
    <View style={styles.container}>
      <Header title="🎙️ Speaking Practice" showBack onBack={() => router.back()} />
      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.light.tint} /></View>
      ) : selectedTopic ? (
        <ScrollView contentContainerStyle={styles.content}>
          
          <View style={styles.cueCard}>
            <Text style={styles.partLabel}>Part 2: Long Turn</Text>
            <Text style={styles.topicText}>{selectedTopic.topic}</Text>
            <Text style={styles.instructionText}>You should say:</Text>
            {selectedTopic.points.map((pt: string, idx: number) => (
              <Text key={idx} style={styles.bulletPoint}>• {pt}</Text>
            ))}
          </View>
          
          {result ? (
            <View style={styles.resultCard}>
              <View style={styles.bandScoreContainer}>
                <Text style={styles.bandLabel}>Estimated Band</Text>
                <Text style={styles.bandValue}>{result.overall_band.toFixed(1)}</Text>
              </View>
              
              <Text style={styles.feedbackTitle}>Feedback:</Text>
              <Text style={styles.feedbackText}>{result.feedback}</Text>
              
              <Text style={styles.feedbackTitle}>Vocabulary Suggestions:</Text>
              {result.vocabulary_suggestions.map((sug: string, idx: number) => (
                <Text key={idx} style={styles.bulletPoint}>• {sug}</Text>
              ))}
              
              <TouchableOpacity style={styles.newTopicBtn} onPress={resetPractice}>
                <Text style={styles.newTopicText}>Practice Another Topic</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              <View style={styles.recordBox}>
                <Text style={styles.timerText}>{formatTime(recordingSeconds)}</Text>
                
                <TouchableOpacity 
                  style={[styles.recordBtn, isRecording && styles.recordingActiveBtn]} 
                  onPress={toggleRecording}
                >
                  {/* @ts-ignore */}
                  <IconSymbol name={isRecording ? "stop.fill" : "mic.fill"} size={40} color={isRecording ? "#fff" : Colors.light.tint} />
                </TouchableOpacity>
                <Text style={styles.recordSubtext}>
                  {isRecording ? "Tap to stop recording" : "Tap to start speaking (aim for 2 mins)"}
                </Text>
              </View>

              {!nativeVoiceAvailable && !result && (
                <View style={styles.warningBox}>
                  <Text style={styles.warningText}>⚠️ Auto-transcription is not available in the current environment. Please use your keyboard's microphone button to transcribe into the box below after stopping the timer.</Text>
                </View>
              )}

              {!isRecording && recordingSeconds > 0 && (
                <View style={styles.transcriptionBox}>
                  <Text style={styles.instructionText}>Transcription:</Text>
                  <TextInput
                    style={styles.input}
                    multiline
                    value={spokenText}
                    onChangeText={setSpokenText}
                    placeholder="Your speech will be transcribed here. You can also edit it before submitting..."
                    placeholderTextColor="#999"
                  />
                  
                  <TouchableOpacity 
                    style={[styles.submitBtn, submitting && styles.disabledBtn]} 
                    onPress={handleSubmit}
                    disabled={submitting}
                  >
                    {submitting ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>Evaluate Speech</Text>}
                  </TouchableOpacity>
                </View>
              )}
            </>
          )}

        </ScrollView>
      ) : (
        <View style={styles.center}><Text>Failed to load topics.</Text></View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f7' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 16, paddingBottom: 40 },
  cueCard: { backgroundColor: '#fff', padding: 24, borderRadius: 16, marginBottom: 24, shadowColor: '#000', shadowOffset: {width: 0, height: 2}, shadowOpacity: 0.1, shadowRadius: 4, elevation: 3, borderWidth: 1, borderColor: '#e3f2fd' },
  partLabel: { fontSize: 13, textTransform: 'uppercase', color: '#1565c0', fontWeight: 'bold', marginBottom: 8, letterSpacing: 1 },
  topicText: { fontSize: 22, fontWeight: 'bold', color: '#333', marginBottom: 16, lineHeight: 30 },
  instructionText: { fontSize: 16, color: '#666', fontStyle: 'italic', marginBottom: 12 },
  bulletPoint: { fontSize: 16, color: '#444', marginBottom: 8, lineHeight: 24, paddingLeft: 8 },
  recordBox: { backgroundColor: '#fff', padding: 32, borderRadius: 24, alignItems: 'center', marginBottom: 24, elevation: 2 },
  timerText: { fontSize: 48, fontWeight: '200', fontVariant: ['tabular-nums'], color: '#333', marginBottom: 24 },
  recordBtn: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#e3f2fd', justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  recordingActiveBtn: { backgroundColor: '#ff3b30', shadowColor: '#ff3b30', shadowOffset: {width: 0, height: 4}, shadowOpacity: 0.3, shadowRadius: 8, elevation: 8 },
  recordSubtext: { fontSize: 14, color: '#888' },
  transcriptionBox: { padding: 8 },
  input: { backgroundColor: '#fff', borderRadius: 12, padding: 16, fontSize: 16, minHeight: 150, textAlignVertical: 'top', borderWidth: 1, borderColor: '#ddd', marginBottom: 16 },
  submitBtn: { backgroundColor: '#4cd964', padding: 16, borderRadius: 12, alignItems: 'center' },
  disabledBtn: { opacity: 0.7 },
  submitText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  resultCard: { backgroundColor: '#fff', padding: 24, borderRadius: 16, elevation: 2 },
  bandScoreContainer: { alignItems: 'center', backgroundColor: '#f5f5f5', padding: 20, borderRadius: 16, marginBottom: 24 },
  bandLabel: { fontSize: 16, color: '#666', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  bandValue: { fontSize: 48, fontWeight: 'bold', color: Colors.light.tint },
  feedbackTitle: { fontSize: 18, fontWeight: 'bold', color: '#333', marginTop: 16, marginBottom: 12 },
  feedbackText: { fontSize: 16, color: '#444', lineHeight: 24, marginBottom: 16 },
  newTopicBtn: { backgroundColor: Colors.light.tint, padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 32 },
  newTopicText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  warningBox: { backgroundColor: '#fff3cd', padding: 12, borderRadius: 12, marginBottom: 16, borderWidth: 1, borderColor: '#ffeeba' },
  warningText: { color: '#856404', fontSize: 13, lineHeight: 18, textAlign: 'center' }
});
