import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { Header } from '@/components/Header';
import { StoriesBar } from '@/components/StoriesBar';
import { ChatList } from '@/components/ChatList';
import { IconSymbol } from '@/components/ui/icon-symbol';

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Header title="Chats" rightIcon={<IconSymbol name="house.fill" color="#000" size={24} />} />
      <StoriesBar />
      <ChatList />
      
      <TouchableOpacity style={styles.fab} onPress={() => router.push('/chat/new' as any)}>
        <IconSymbol name="plus" color="#fff" size={28} />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#667eea',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
});
