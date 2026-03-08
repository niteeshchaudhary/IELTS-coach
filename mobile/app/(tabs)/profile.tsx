import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, Text, Image, ActivityIndicator } from 'react-native';
import { Header } from '@/components/Header';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { getProfile } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';

interface ProfileData {
  tests: number;
  avgBand: number;
  wordsMastered: number;
}

export default function ProfileScreen() {
  const { auth } = useAuth();
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
      <Header title="Profile" rightIcon={<IconSymbol name="gear" size={24} color="#000" />} />
      <ScrollView contentContainerStyle={styles.content}>
        
        {/* Profile Header (Instagram Style) */}
        <View style={styles.profileHeader}>
          <Image 
            source={{ uri: 'https://ui-avatars.com/api/?name=IELTS+Student&background=random' }} 
            style={styles.avatar} 
          />
          <View style={styles.statsContainer}>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{profile.tests}</Text>
              <Text style={styles.statLabel}>Tests</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{profile.avgBand}</Text>
              <Text style={styles.statLabel}>Avg Band</Text>
            </View>
            <View style={styles.statBox}>
              <Text style={styles.statNumber}>{profile.wordsMastered}</Text>
              <Text style={styles.statLabel}>Words</Text>
            </View>
          </View>
        </View>

        <View style={styles.bioContainer}>
          <Text style={styles.nameText}>{auth?.username || 'IELTS Student'}</Text>
          <Text style={styles.bioText}>Targeting Band 8.0 🎯</Text>
          <Text style={styles.bioText}>Practicing every day!</Text>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <View style={styles.actionButton}>
            <Text style={styles.actionText}>Edit Profile</Text>
          </View>
          <View style={styles.actionButton}>
            <Text style={styles.actionText}>Share Progress</Text>
          </View>
        </View>

        {/* Progress Section */}
        <Text style={styles.sectionTitle}>Recent Achievements</Text>
        <View style={styles.achievementGrid}>
          {[1, 2, 3, 4, 5, 6].map((it) => (
            <View key={it} style={styles.achievementBox}>
              <Text style={styles.achievementEmoji}>🏆</Text>
            </View>
          ))}
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
    marginBottom: 16,
  },
  nameText: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
    color: '#000',
  },
  bioText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 24,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#f0f0f0',
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 12,
  },
  achievementGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  achievementBox: {
    width: '31%',
    aspectRatio: 1,
    backgroundColor: '#fff3e0',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#ffe0b2',
  },
  achievementEmoji: {
    fontSize: 32,
  },
});
