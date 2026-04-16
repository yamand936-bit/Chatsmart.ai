import { create } from 'zustand';

export interface AppNotification {
  id: string;
  message: string;
  read: boolean;
  type: 'info' | 'warning' | 'error' | 'success';
}

interface NotificationStore {
  notifications: AppNotification[];
  unreadCount: number;
  addNotification: (n: Omit<AppNotification, 'id' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  notifications: [],
  unreadCount: 0,
  addNotification: (n) => 
    set((state) => {
      const newNotif = { ...n, id: Date.now().toString(), read: false };
      return {
        notifications: [newNotif, ...state.notifications],
        unreadCount: state.unreadCount + 1
      };
    }),
  markAsRead: (id) =>
    set((state) => {
      const updated = state.notifications.map(n => 
        n.id === id ? { ...n, read: true } : n
      );
      return {
        notifications: updated,
        unreadCount: updated.filter(n => !n.read).length
      };
    }),
  markAllAsRead: () =>
    set((state) => ({
      notifications: state.notifications.map(n => ({ ...n, read: true })),
      unreadCount: 0
    }))
}));
