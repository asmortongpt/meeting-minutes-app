// mobile/src/navigation/RootNavigator.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import { LogBox } from 'react-native';

// Screens
import HomeScreen from '../screens/HomeScreen';
import CameraScreen from '../screens/CameraScreen';
import SettingsScreen from '../screens/SettingsScreen';
import OfflineQueueScreen from '../screens/OfflineQueueScreen';

// Types for navigation
export type RootStackParamList = {
  Home: undefined;
  Camera: undefined;
  Settings: undefined;
  OfflineQueue: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

// Ignore specific warnings if needed (use sparingly)
LogBox.ignoreLogs(['Possible Unhandled Promise Rejection']);

/**
 * RootNavigator - Main navigation component for the app
 * Handles the stack navigation between screens and sets up the navigation container
 * with necessary configurations for a secure and offline-first experience.
 */
const RootNavigator: React.FC = () => {
  return (
    <NavigationContainer
      onUnhandledAction={(action) => {
        // Log unhandled navigation actions for debugging and monitoring
        console.warn('Unhandled navigation action:', action);
      }}
    >
      <StatusBar style="auto" />
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          // Disable gestures for security to prevent accidental navigation
          gestureEnabled: false,
          // Set consistent header style across screens
          headerStyle: {
            backgroundColor: '#f8f8f8',
          },
          headerTintColor: '#333',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          // Prevent back navigation to sensitive screens
          headerBackTitleVisible: false,
        }}
      >
        {/* Home Screen */}
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{
            title: 'Home',
            // Prevent header from being shown if not needed
            headerShown: true,
          }}
        />

        {/* Camera Screen - For capturing images/videos */}
        <Stack.Screen
          name="Camera"
          component={CameraScreen}
          options={{
            title: 'Camera',
            // Lock orientation or hide header if needed for camera
            headerShown: false,
          }}
        />

        {/* Settings Screen - For app configurations */}
        <Stack.Screen
          name="Settings"
          component={SettingsScreen}
          options={{
            title: 'Settings',
          }}
        />

        {/* Offline Queue Screen - For managing offline data sync */}
        <Stack.Screen
          name="OfflineQueue"
          component={OfflineQueueScreen}
          options={{
            title: 'Offline Queue',
            // Restrict access or visibility if needed
            headerShown: true,
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default RootNavigator;