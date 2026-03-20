/**
 * Network status hook using @react-native-community/netinfo.
 *
 * Provides reactive online/offline state and AppState listener
 * to detect when the app comes back to the foreground.
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import NetInfo, { type NetInfoState } from '@react-native-community/netinfo';
import { AppState, type AppStateStatus } from 'react-native';

export interface NetworkStatus {
  isOnline: boolean;
  isInternetReachable: boolean | null;
}

/**
 * Hook that returns current network status and re-renders on changes.
 * Also fires an optional callback when the app comes to the foreground while online.
 */
export function useNetworkStatus(onForegroundOnline?: () => void): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>({
    isOnline: true,
    isInternetReachable: null,
  });
  const callbackRef = useRef(onForegroundOnline);
  callbackRef.current = onForegroundOnline;

  useEffect(() => {
    // Subscribe to network state changes
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      setStatus({
        isOnline: !!state.isConnected,
        isInternetReachable: state.isInternetReachable,
      });
    });

    return () => unsubscribe();
  }, []);

  // Listen for app returning to foreground
  useEffect(() => {
    const handleAppState = (nextState: AppStateStatus) => {
      if (nextState === 'active') {
        // Check network and fire callback if online
        NetInfo.fetch().then((state) => {
          if (state.isConnected && callbackRef.current) {
            callbackRef.current();
          }
        });
      }
    };

    const subscription = AppState.addEventListener('change', handleAppState);
    return () => subscription.remove();
  }, []);

  return status;
}

/**
 * One-shot check: is the device currently online?
 */
export async function isOnline(): Promise<boolean> {
  const state = await NetInfo.fetch();
  return !!state.isConnected;
}
