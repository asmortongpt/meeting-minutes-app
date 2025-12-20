// mobile/src/services/PushNotifications.ts

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { logger } from '../utils/logger';

/**
 * Interface defining the structure of a notification payload
 */
interface NotificationPayload {
  title: string;
  body: string;
  data?: Record<string, any>;
}

/**
 * Interface for notification preferences stored in AsyncStorage
 */
interface NotificationPreferences {
  pushToken: string | null;
  enabled: boolean;
  lastUpdated: string;
}

/**
 * PushNotifications service class for handling push notification setup and operations
 */
export class PushNotifications {
  private static instance: PushNotifications | null = null;
  private static readonly STORAGE_KEY = '@notification_prefs';
  private isInitialized = false;

  /**
   * Get singleton instance of PushNotifications
   */
  public static getInstance(): PushNotifications {
    if (!PushNotifications.instance) {
      PushNotifications.instance = new PushNotifications();
    }
    return PushNotifications.instance;
  }

  /**
   * Initialize push notifications with necessary permissions and setup
   */
  public async initialize(): Promise<boolean> {
    try {
      if (this.isInitialized) {
        logger.info('Push notifications already initialized');
        return true;
      }

      // Check if we're running on a physical device (push notifications don't work on simulators)
      if (!Device.isDevice) {
        logger.warn('Push notifications not supported on simulator/emulator');
        return false;
      }

      // Set up notification handler
      Notifications.setNotificationHandler({
        handleNotification: async () => ({
          shouldShowAlert: true,
          shouldPlaySound: true,
          shouldSetBadge: false,
        }),
      });

      // Request permissions for push notifications
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        logger.error('Push notification permissions denied');
        await this.savePreferences({ pushToken: null, enabled: false, lastUpdated: new Date().toISOString() });
        return false;
      }

      // Get push token for iOS
      if (Platform.OS === 'ios') {
        await Notifications.setNotificationChannelAsync('default', {
          name: 'default',
          importance: Notifications.AndroidImportance.MAX,
        });
      }

      // Get the push token
      const token = (await Notifications.getExpoPushTokenAsync({
        projectId: Constants.expoConfig?.extra?.eas?.projectId || '',
      })).data;

      logger.info('Push notification token obtained successfully');
      await this.savePreferences({ pushToken: token, enabled: true, lastUpdated: new Date().toISOString() });
      this.isInitialized = true;
      return true;
    } catch (error) {
      logger.error('Failed to initialize push notifications', error);
      await this.savePreferences({ pushToken: null, enabled: false, lastUpdated: new Date().toISOString() });
      return false;
    }
  }

  /**
   * Get the stored push token
   */
  public async getPushToken(): Promise<string | null> {
    try {
      const prefs = await this.getPreferences();
      return prefs.pushToken;
    } catch (error) {
      logger.error('Failed to get push token', error);
      return null;
    }
  }

  /**
   * Check if push notifications are enabled
   */
  public async areNotificationsEnabled(): Promise<boolean> {
    try {
      const prefs = await this.getPreferences();
      return prefs.enabled;
    } catch (error) {
      logger.error('Failed to check notification status', error);
      return false;
    }
  }

  /**
   * Schedule a local notification
   * @param payload Notification content
   * @param triggerSeconds Delay in seconds before showing the notification
   */
  public async scheduleLocalNotification(
    payload: NotificationPayload,
    triggerSeconds: number = 5
  ): Promise<string | null> {
    try {
      if (!(await this.areNotificationsEnabled())) {
        logger.warn('Cannot schedule notification: notifications disabled');
        return null;
      }

      // Sanitize notification data to prevent injection or malformed content
      const sanitizedPayload = {
        title: payload.title.substring(0, 100), // Limit title length
        body: payload.body.substring(0, 500),   // Limit body length
        data: payload.data || {},
      };

      const notificationId = await Notifications.scheduleNotificationAsync({
        content: sanitizedPayload,
        trigger: { seconds: triggerSeconds },
      });

      logger.info(`Scheduled local notification with ID: ${notificationId}`);
      return notificationId;
    } catch (error) {
      logger.error('Failed to schedule local notification', error);
      return null;
    }
  }

  /**
   * Cancel a scheduled notification by ID
   * @param notificationId ID of the notification to cancel
   */
  public async cancelNotification(notificationId: string): Promise<boolean> {
    try {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
      logger.info(`Cancelled notification with ID: ${notificationId}`);
      return true;
    } catch (error) {
      logger.error(`Failed to cancel notification ${notificationId}`, error);
      return false;
    }
  }

  /**
   * Cancel all scheduled notifications
   */
  public async cancelAllNotifications(): Promise<boolean> {
    try {
      await Notifications.cancelAllScheduledNotificationsAsync();
      logger.info('Cancelled all scheduled notifications');
      return true;
    } catch (error) {
      logger.error('Failed to cancel all notifications', error);
      return false;
    }
  }

  /**
   * Save notification preferences to AsyncStorage
   * @param prefs Notification preferences to save
   */
  private async savePreferences(prefs: NotificationPreferences): Promise<void> {
    try {
      await AsyncStorage.setItem(PushNotifications.STORAGE_KEY, JSON.stringify(prefs));
    } catch (error) {
      logger.error('Failed to save notification preferences', error);
    }
  }

  /**
   * Get notification preferences from AsyncStorage
   */
  private async getPreferences(): Promise<NotificationPreferences> {
    try {
      const data = await AsyncStorage.getItem(PushNotifications.STORAGE_KEY);
      if (data) {
        return JSON.parse(data) as NotificationPreferences;
      }
    } catch (error) {
      logger.error('Failed to get notification preferences', error);
    }
    return { pushToken: null, enabled: false, lastUpdated: new Date().toISOString() };
  }

  /**
   * Setup notification listeners for foreground and background events
   * @param onForeground Callback for when notification is received in foreground
   * @param onBackground Callback for when notification is received in background or tapped
   */
  public setupListeners(
    onForeground: (notification: Notifications.Notification) => void,
    onBackground: (response: Notifications.NotificationResponse) => void
  ): { removeForeground: () => void; removeBackground: () => void } {
    // Handle notifications received while app is in foreground
    const foregroundSubscription = Notifications.addNotificationReceivedListener(onForeground);

    // Handle notifications tapped or received in background
    const backgroundSubscription = Notifications.addNotificationResponseReceivedListener(onBackground);

    return {
      removeForeground: () => foregroundSubscription.remove(),
      removeBackground: () => backgroundSubscription.remove(),
    };
  }
}

export default PushNotifications.getInstance();