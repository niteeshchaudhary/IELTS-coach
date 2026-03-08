import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';

const mockChats = [
  { id: '1', title: 'Part 1: Hometown & Leisure', date: '10:45 AM', lastMessage: 'That was a great answer. Try to use more...', unread: 0 },
  { id: '2', title: 'Part 2: Describe a Person', date: 'Yesterday', lastMessage: 'AI: You spoke for 1 minute 45 seconds.', unread: 2 },
  { id: '3', title: 'Part 3: Technology', date: 'Monday', lastMessage: 'Let\'s practice some more abstract questions.', unread: 0 },
];

export function ChatList() {
  const renderItem = ({ item }: { item: typeof mockChats[0] }) => (
      <TouchableOpacity style={styles.chatItem} onPress={() => router.push(`/chat/${item.id}` as any)}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>🎙️</Text>
        </View>
        <View style={styles.chatInfo}>
          <View style={styles.chatHeader}>
            <Text style={styles.chatTitle}>{item.title}</Text>
            <Text style={styles.chatDate}>{item.date}</Text>
          </View>
          <View style={styles.chatFooter}>
            <Text style={styles.lastMessage} numberOfLines={1}>{item.lastMessage}</Text>
            {item.unread > 0 && (
              <View style={styles.unreadBadge}>
                <Text style={styles.unreadText}>{item.unread}</Text>
              </View>
            )}
          </View>
        </View>
      </TouchableOpacity>
  );

  return (
    <FlatList
      data={mockChats}
      keyExtractor={(item) => item.id}
      renderItem={renderItem}
      contentContainerStyle={styles.listContainer}
    />
  );
}

const styles = StyleSheet.create({
  listContainer: {
    paddingBottom: 80, // Space for FAB
  },
  chatItem: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  avatarText: {
    fontSize: 24,
  },
  chatInfo: {
    flex: 1,
    justifyContent: 'center',
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  chatTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
  },
  chatDate: {
    fontSize: 12,
    color: '#888',
  },
  chatFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lastMessage: {
    flex: 1,
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  unreadBadge: {
    backgroundColor: '#25D366', // WhatsApp green
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  unreadText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
});
