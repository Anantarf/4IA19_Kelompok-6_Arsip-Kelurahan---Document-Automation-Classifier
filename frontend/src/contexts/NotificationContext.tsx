import React, { createContext, useContext, useState, useEffect } from 'react';

export type NotificationItem = {
  id: string;
  message: string;
  timestamp: string;
  read: boolean;
};

type NotificationContextType = {
  notifications: NotificationItem[];
  unreadCount: number;
  addNotification: (message: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
};

const NotificationContext = createContext<NotificationContextType>({
  notifications: [],
  unreadCount: 0,
  addNotification: () => {},
  markAllAsRead: () => {},
  clearAll: () => {},
});

export const useNotification = () => useContext(NotificationContext);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Load from local storage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('app_notifications');
      if (stored) {
        setNotifications(JSON.parse(stored));
      }
    } catch (e) {
      console.error("Failed to parse notifications", e);
    }
  }, []);

  // Sync to local storage
  useEffect(() => {
    localStorage.setItem('app_notifications', JSON.stringify(notifications));
  }, [notifications]);

  const addNotification = (message: string) => {
    const newItem: NotificationItem = {
      id: Date.now().toString(),
      message,
      timestamp: new Date().toISOString(),
      read: false,
    };
    setNotifications(prev => [newItem, ...prev].slice(0, 10)); // Keep last 10
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, addNotification, markAllAsRead, clearAll }}>
      {children}
    </NotificationContext.Provider>
  );
};
