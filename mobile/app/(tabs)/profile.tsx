import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, Text, Image, ActivityIndicator, TouchableOpacity } from 'react-native';
import { Header } from '@/components/Header';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { getProfile } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';

interface ProfileData {
  tests: number;
  avgBand: number;
  wordsMastered: number;
  totalGames: number;
  totalSpeakingMins: number;
  history: Array<{
    date: string;
    band: number;
    turns: number;
  }>;
}

export default function ProfileScreen() {
  const { auth, logout } = useAuth();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await getProfile();
        setProfile(data);
      } catch (error) {
        console.error("Failed to fetch profile", error);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  if (loading || !profile) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color="#667eea" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* @ts-ignore */}
      <Header 
        title="Profile" 
        rightIcon={
          <TouchableOpacity onPress={logout}>
            <IconSymbol name="rectangle.portrait.and.arrow.right" size={22} color="#ff3b30" />
          </TouchableOpacity>
        } 
      />
      <ScrollView contentContainerStyle={styles.content}>
        
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <Image 
            source={{ uri: `https://ui-avatars.com/api/?name=${auth?.username || 'Student'}&background=random&size=200` }} 
            style={styles.avatar} 
          />
          <View style={styles.statsContainer}>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{profile.tests}</Text>
              <Text style={styles.statLabel}>Tests</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{profile.avgBand.toFixed(1)}</Text>
              <Text style={styles.statLabel}>Avg Band</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{profile.wordsMastered}</Text>
              <Text style={styles.statLabel}>Words</Text>
            </View>
          </View>
        </View>

        <View style={styles.bioContainer}>
          <Text style={styles.nameText}>@{auth?.username || 'ielts_student'}</Text>
          <Text style={styles.bioText}>Learning Journey: {profile.totalSpeakingMins} mins practiced 🎙️</Text>
          <Text style={styles.bioText}>{profile.totalGames} vocabulary games played 🎮</Text>
        </View>

        {/* Progress History Box */}
        <View style={styles.historyCard}>
          <Text style={styles.sectionTitle}>Performance History (Last 7 Days)</Text>
          {profile.history && profile.history.length > 0 ? (
            <View style={styles.historyChart}>
              {profile.history.map((day, idx) => (
                <View key={idx} style={styles.historyDay}>
                  <View style={[styles.historyBar, { height: Math.max(day.band * 12, 10), backgroundColor: day.band >= 7 ? '#4cd964' : (day.band >= 6 ? '#ffcc00' : '#ff3b30') }]} />
                  <Text style={styles.historyDate}>{day.date.split('-').slice(1).join('/')}</Text>
                </View>
              ))}
            </View>
          ) : (
            <Text style={styles.emptyHistory}>No practice data recorded yet. Start practicing to see your progress!</Text>
          )}
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>Edit Bio</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionText}>Settings</Text>
          </TouchableOpacity>
        </View>

        {/* Milestones Section */}
        <Text style={styles.sectionTitle}>Achieved Milestones</Text>
        <View style={styles.achievementGrid}>
          {profile.tests > 0 && (
            <View style={styles.achievementBox}>
              <Text style={styles.achievementEmoji}>🎓</Text>
              <Text style={styles.achievementName}>First Test</Text>
            </View>
          )}
          {profile.wordsMastered > 10 && (
            <View style={styles.achievementBox}>
              <Text style={styles.achievementEmoji}>📖</Text>
              <Text style={styles.achievementName}>Vocab Pro</Text>
            </View>
          )}
          {profile.avgBand >= 7 && (
            <View style={styles.achievementBox}>
              <Text style={styles.achievementEmoji}>🔥</Text>
              <Text style={styles.achievementName}>High Roller</Text>
            </View>
          )}
          {profile.totalGames > 5 && (
            <View style={styles.achievementBox}>
              <Text style={styles.achievementEmoji}>🕹️</Text>
              <Text style={styles.achievementName}>Gamer</Text>
            </View>
          )}
           <View style={[styles.achievementBox, { opacity: 0.3 }]}>
              <Text style={styles.achievementEmoji}>👑</Text>
              <Text style={styles.achievementName}>Band 9</Text>
            </View>
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
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    marginRight: 24,
  },
  statsContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statBox: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
  },
  bioContainer: {
    marginBottom: 24,
  },
  nameText: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
    color: '#000',
  },
  bioText: {
    fontSize: 14,
    color: '#555',
    lineHeight: 22,
  },
  historyCard: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#eee',
  },
  historyChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: 120,
    marginTop: 12,
    paddingHorizontal: 8,
  },
  historyDay: {
    alignItems: 'center',
    width: 40,
  },
  historyBar: {
    width: 12,
    borderRadius: 6,
    marginBottom: 8,
  },
  historyDate: {
    fontSize: 10,
    color: '#888',
  },
  emptyHistory: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 24,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#f0f2f5',
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
  },
  actionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 12,
  },
  achievementGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  achievementBox: {
    width: '30%',
    aspectRatio: 1,
    backgroundColor: '#fffdf0',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ffecb3',
    padding: 8,
  },
  achievementEmoji: {
    fontSize: 28,
    marginBottom: 4,
  },
  achievementName: {
    fontSize: 10,
    fontWeight: '600',
    color: '#856404',
    textAlign: 'center',
  },
});
