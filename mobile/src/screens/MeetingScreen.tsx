// mobile/src/screens/MeetingScreen.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Platform,
  AppState,
  Vibration,
} from 'react-native';
import { RTCView, mediaDevices, RTCPeerConnection } from 'react-native-webrtc';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import PushNotification from 'react-native-push-notification';
import NetInfo from '@react-native-community/netinfo';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Type definitions for meeting data and WebRTC streams
interface MeetingData {
  id: string;
  title: string;
  participants: string[];
  isActive: boolean;
}

interface StreamState {
  localStream: MediaStream | null;
  remoteStreams: { [key: string]: MediaStream };
}

// WebRTC configuration with secure ICE servers
const RTC_CONFIG = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ],
};

const MeetingScreen: React.FC<{ route: { params: { meetingId: string } } }> = ({ route }) => {
  const { meetingId } = route.params;
  const navigation = useNavigation();
  const [meetingData, setMeetingData] = useState<MeetingData | null>(null);
  const [streamState, setStreamState] = useState<StreamState>({
    localStream: null,
    remoteStreams: {},
  });
  const [isMuted, setIsMuted] = useState(false);
  const [isCameraOff, setIsCameraOff] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const peerConnection = useRef<RTCPeerConnection | null>(null);
  const appState = useRef(AppState.currentState);

  // Load meeting data from local storage (offline-first)
  const loadMeetingData = useCallback(async () => {
    try {
      const storedData = await AsyncStorage.getItem(`meeting_${meetingId}`);
      if (storedData) {
        setMeetingData(JSON.parse(storedData));
      } else {
        // Fallback to API call if online
        if (isConnected) {
          fetchMeetingData();
        } else {
          Alert.alert('Offline', 'Meeting data unavailable offline.');
        }
      }
    } catch (error) {
      console.error('Error loading meeting data:', error);
      Alert.alert('Error', 'Failed to load meeting data.');
    }
  }, [meetingId, isConnected]);

  // Fetch meeting data from API with error handling
  const fetchMeetingData = useCallback(async () => {
    try {
      const response = await fetch(`https://api.example.com/meetings/${meetingId}`, {
        headers: {
          'Authorization': `Bearer ${await getAuthToken()}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) throw new Error('Failed to fetch meeting data');
      const data: MeetingData = await response.json();
      setMeetingData(data);
      await AsyncStorage.setItem(`meeting_${meetingId}`, JSON.stringify(data));
    } catch (error) {
      console.error('API fetch error:', error);
      Alert.alert('Error', 'Could not retrieve meeting details.');
    }
  }, [meetingId]);

  // Get secure auth token from storage
  const getAuthToken = async (): Promise<string> => {
    const token = await AsyncStorage.getItem('auth_token');
    if (!token) throw new Error('No authentication token found');
    return token;
  };

  // Initialize WebRTC camera and microphone
  const setupWebRTC = useCallback(async () => {
    try {
      const stream = await mediaDevices.getUserMedia({
        audio: true,
        video: { facingMode: 'user', frameRate: 30 },
      });
      setStreamState((prev) => ({ ...prev, localStream: stream }));

      peerConnection.current = new RTCPeerConnection(RTC_CONFIG);
      stream.getTracks().forEach((track) => {
        peerConnection.current?.addTrack(track, stream);
      });

      // Handle incoming streams from remote participants
      peerConnection.current.ontrack = (event) => {
        setStreamState((prev) => ({
          ...prev,
          remoteStreams: {
            ...prev.remoteStreams,
            [event.streams[0].id]: event.streams[0],
          },
        }));
      };

      // Handle ICE candidates and connection state changes
      peerConnection.current.onicecandidate = (event) => {
        if (event.candidate) {
          // Securely send ICE candidate to signaling server
          sendIceCandidate(event.candidate);
        }
      };
      peerConnection.current.onconnectionstatechange = () => {
        console.log('Connection state:', peerConnection.current?.connectionState);
      };
    } catch (error) {
      console.error('WebRTC setup error:', error);
      Alert.alert('Error', 'Failed to initialize camera or microphone.');
    }
  }, []);

  // Placeholder for sending ICE candidates (implementation depends on signaling server)
  const sendIceCandidate = (candidate: RTCIceCandidate) => {
    console.log('Sending ICE candidate:', candidate);
    // Securely send to signaling server with authentication
  };

  // Toggle microphone mute/unmute
  const toggleMute = () => {
    if (streamState.localStream) {
      streamState.localStream.getAudioTracks().forEach((track) => {
        track.enabled = !isMuted;
      });
      setIsMuted(!isMuted);
    }
  };

  // Toggle camera on/off
  const toggleCamera = () => {
    if (streamState.localStream) {
      streamState.localStream.getVideoTracks().forEach((track) => {
        track.enabled = !isCameraOff;
      });
      setIsCameraOff(!isCameraOff);
    }
  };

  // Handle app state changes for background/foreground
  const handleAppStateChange = (nextAppState: string) => {
    if (
      appState.current.match(/inactive|background/) &&
      nextAppState === 'active'
    ) {
      // App is back in foreground, check connection and refresh if needed
      NetInfo.fetch().then((state) => setIsConnected(state.isConnected || false));
    }
    appState.current = nextAppState;
  };

  // Setup push notifications for meeting updates
  const setupPushNotifications = () => {
    PushNotification.configure({
      onNotification: (notification) => {
        Vibration.vibrate([0, 500]);
        Alert.alert('Meeting Update', notification.message || 'New update received');
        notification.finish(PushNotification.FetchResult.NoData);
      },
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },
      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });
  };

  // Cleanup WebRTC resources on unmount
  const cleanupWebRTC = () => {
    if (streamState.localStream) {
      streamState.localStream.getTracks().forEach((track) => track.stop());
    }
    if (peerConnection.current) {
      peerConnection.current.close();
    }
    setStreamState({ localStream: null, remoteStreams: {} });
  };

  // Load data and setup on screen focus
  useFocusEffect(
    useCallback(() => {
      loadMeetingData();
      setupWebRTC();
      setupPushNotifications();
      const subscription = AppState.addEventListener('change', handleAppStateChange);
      const netInfoSubscription = NetInfo.addEventListener((state) => {
        setIsConnected(state.isConnected || false);
      });

      return () => {
        cleanupWebRTC();
        subscription.remove();
        netInfoSubscription();
      };
    }, [loadMeetingData, setupWebRTC])
  );

  // Render video streams (local and remote)
  const renderStreams = () => {
    const streams = [];
    if (streamState.localStream) {
      streams.push(
        <View key="local" style={styles.videoContainer}>
          <RTCView
            streamURL={streamState.localStream.toURL()}
            style={styles.video}
            objectFit="cover"
            mirror={true}
          />
          <Text style={styles.videoLabel}>You</Text>
        </View>
      );
    }
    Object.entries(streamState.remoteStreams).forEach(([id, stream]) => {
      streams.push(
        <View key={id} style={styles.videoContainer}>
          <RTCView
            streamURL={stream.toURL()}
            style={styles.video}
            objectFit="cover"
          />
          <Text style={styles.videoLabel}>Participant</Text>
        </View>
      );
    });
    return streams;
  };

  if (!meetingData) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading meeting...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{meetingData.title}</Text>
      <Text style={styles.status}>
        {isConnected ? 'Online' : 'Offline Mode'}
      </Text>
      <View style={styles.videoGrid}>{renderStreams()}</View>
      <View style={styles.controls}>
        <TouchableOpacity style={styles.controlButton} onPress={toggleMute}>
          <Icon
            name={isMuted ? 'mic-off' : 'mic'}
            size={24}
            color={isMuted ? '#ff5252' : '#fff'}
          />
        </TouchableOpacity>
        <TouchableOpacity style={styles.controlButton} onPress={toggleCamera}>
          <Icon
            name={isCameraOff ? 'videocam-off' : 'videocam'}
            size={24}
            color={isCameraOff ? '#ff5252' : '#fff'}
          />
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.controlButton, styles.endButton]}
          onPress={() => navigation.goBack()}
        >
          <Icon name="call-end" size={24} color="#fff" />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
    padding: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
    textAlign: 'center',
  },
  status: {
    fontSize: 14,
    color: '#aaa',
    textAlign: 'center',
    marginBottom: 16,
  },
  loadingText: {
    fontSize: 18,
    color: '#fff',
    textAlign: 'center',
    marginTop: 50,
  },
  videoGrid: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
  },
  videoContainer: {
    width: '45%',
    height: 200,
    marginBottom: 16,
    borderRadius: 8,
    overflow: 'hidden',
    position: 'relative',
  },
  video: {
    flex: 1,
    backgroundColor: '#000',
  },
  videoLabel: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    color: '#fff',
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 4,
    borderRadius: 4,
    fontSize: 12,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  controlButton: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 10,
  },
  endButton: {
    backgroundColor: '#ff5252',
  },
});

export default MeetingScreen;