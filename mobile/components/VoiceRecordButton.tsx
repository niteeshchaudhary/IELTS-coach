import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, Text, Animated } from 'react-native';
import { IconSymbol } from '@/components/ui/icon-symbol';

export function VoiceRecordButton() {
  const [isRecording, setIsRecording] = useState(false);
  const scaleValue = React.useRef(new Animated.Value(1)).current;

  const startRecording = () => {
    setIsRecording(true);
    Animated.loop(
      Animated.sequence([
        Animated.timing(scaleValue, { toValue: 1.2, duration: 500, useNativeDriver: true }),
        Animated.timing(scaleValue, { toValue: 1, duration: 500, useNativeDriver: true })
      ])
    ).start();
  };

  const stopRecording = () => {
    setIsRecording(false);
    Animated.timing(scaleValue, { toValue: 1, duration: 200, useNativeDriver: true }).start();
  };

  return (
    <View style={styles.container}>
      {isRecording && <Text style={styles.recordingText}>Recording... 00:04</Text>}
      <TouchableOpacity 
        onPressIn={startRecording} 
        onPressOut={stopRecording}
        style={styles.buttonWrapper}
      >
        <Animated.View style={[styles.pulseRing, { transform: [{ scale: scaleValue }] }]} />
        <View style={[styles.button, isRecording && styles.buttonRecording]}>
           {/* @ts-ignore */}
          <IconSymbol name="mic.fill" size={28} color={isRecording ? '#fff' : '#000'} />
        </View>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 24,
    marginHorizontal: 16,
    marginBottom: 16,
  },
  recordingText: {
    flex: 1,
    color: '#ff3b30',
    fontWeight: 'bold',
    marginLeft: 16,
  },
  buttonWrapper: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  pulseRing: {
    position: 'absolute',
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 59, 48, 0.3)',
  },
  button: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  buttonRecording: {
    backgroundColor: '#ff3b30',
  },
});
