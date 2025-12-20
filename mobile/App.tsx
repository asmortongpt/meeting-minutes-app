// mobile/App.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Platform, Alert, LogBox, StatusBar } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import * as Notifications from 'expo-notifications';
import * as Permissions from 'expo-permissions';
import * as Camera from 'expo-camera';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Provider as PaperProvider, DefaultTheme } from 'react-native-paper';

// Screens
import HomeScreen from './screens/HomeScreen';
import CameraScreen from './screens/CameraScreen';
import SettingsScreen from './screens/SettingsScreen';

// Types
export type RootStackParamList = {
  Home: undefined;
  Camera: undefined;
  Settings: undefined;
};

interface AppState {
  isConnected: boolean;
  notificationToken: string | null;
  cameraPermission: boolean;
  queuedData: any[];
}

// Theme customization
const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#3498db',
    accent: '#f1c40f',
  },
};

// Ignore specific warnings if needed
LogBox.ignoreLogs(['Possible Unhandled Promise Rejection']);

const Stack = createStackNavigator<RootStackParamList>();

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>({
    isConnected: false,
    notificationToken: null,
    cameraPermission: false,
    queuedData: [],
  });

  // Handle network connectivity changes
  const handleNetworkChange = useCallback((state: any) => {
    setAppState(prev => ({ ...prev, isConnected: state.isConnected }));
    if (state.isConnected) {
      syncOfflineData();
    }
  }, []);

  // Request permissions for notifications and camera
  const setupPermissions = useCallback(async () => {
    try {
      // Request notification permissions
      const { status: notificationStatus } = await Notifications.requestPermissionsAsync();
      if (notificationStatus === 'granted') {
        if (Platform.OS === 'android') {
          Notifications.setNotificationChannelAsync('default', {
            name: 'default',
            importance: Notifications.AndroidImportance.MAX,
          });
        }
        const token = (await Notifications.getExpoPushTokenAsync()).data;
        setAppState(prev => ({ ...prev, notificationToken: token }));
      } else {
        Alert.alert('Permission Denied', 'Notification permissions are required for app functionality.');
      }

      // Request camera permissions
      const { status: cameraStatus } = await Camera.requestCameraPermissionsAsync();
      setAppState(prev => ({ ...prev, cameraPermission: cameraStatus === 'granted' }));
      if (cameraStatus !== 'granted') {
        Alert.alert('Permission Denied', 'Camera access is required for app functionality.');
      }
    } catch (error) {
      console.error('Error setting up permissions:', error);
      Alert.alert('Error', 'Failed to setup permissions. Some features may not work.');
    }
  }, []);

  // Sync offline data when connection is restored
  const syncOfflineData = useCallback(async () => {
    try {
      const queuedDataStr = await AsyncStorage.getItem('queuedData');
      if (queuedDataStr) {
        const queuedData = JSON.parse(queuedDataStr);
        if (queuedData.length > 0) {
          // Simulate API call to sync data
          console.log('Syncing offline data:', queuedData);
          // Clear queue after successful sync
          await AsyncStorage.setItem('queuedData', JSON.stringify([]));
          setAppState(prev => ({ ...prev, queuedData: [] }));
        }
      }
    } catch (error) {
      console.error('Error syncing offline data:', error);
    }
  }, []);

  // Save data to offline queue
  const saveToOfflineQueue = useCallback(async (data: any) => {
    try {
      const queuedDataStr = await AsyncStorage.getItem('queuedData');
      let queuedData = queuedDataStr ? JSON.parse(queuedDataStr) : [];
      queuedData.push(data);
      await AsyncStorage.setItem('queuedData', JSON.stringify(queuedData));
      setAppState(prev => ({ ...prev, queuedData }));
    } catch (error) {
      console.error('Error saving to offline queue:', error);
    }
  }, []);

  // Initialize app
  useEffect(() => {
    // Setup permissions on app start
    setupPermissions();

    // Setup network connectivity listener
    const unsubscribe = NetInfo.addEventListener(handleNetworkChange);

    // Load initial offline data
    const loadOfflineData = async () => {
      try {
        const queuedDataStr = await AsyncStorage.getItem('queuedData');
        if (queuedDataStr) {
          setAppState(prev => ({ ...prev, queuedData: JSON.parse(queuedDataStr) }));
        }
      } catch (error) {
        console.error('Error loading offline data:', error);
      }
    };
    loadOfflineData();

    // Cleanup on unmount
    return () => {
      unsubscribe();
    };
  }, [setupPermissions, handleNetworkChange]);

  // Handle incoming notifications
  useEffect(() => {
    const subscription = Notifications.addNotificationReceivedListener(notification => {
      console.log('Notification received:', notification);
      Alert.alert(
        notification.request.content.title || 'Notification',
        notification.request.content.body || 'You have a new message.'
      );
    });

    return () => subscription.remove();
  }, []);

  return (
    <PaperProvider theme={theme}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Home"
          screenOptions={{
            headerStyle: {
              backgroundColor: theme.colors.primary,
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Stack.Screen
            name="Home"
            component={HomeScreen}
            options={{ title: 'Home' }}
            initialParams={{
              isConnected: appState.isConnected,
              saveToOfflineQueue,
            }}
          />
          <Stack.Screen
            name="Camera"
            component={CameraScreen}
            options={{ title: 'Camera' }}
            initialParams={{ hasPermission: appState.cameraPermission }}
          />
          <Stack.Screen
            name="Settings"
            component={SettingsScreen}
            options={{ title: 'Settings' }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </PaperProvider>
  );
};

export default App;