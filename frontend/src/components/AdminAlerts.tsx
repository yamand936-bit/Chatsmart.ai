'use client';
import { useEffect, useRef } from 'react';
import axios from 'axios';
import { useNotificationStore } from '@/store/useNotificationStore';

export default function AdminAlertsPoller() {
    const { addNotification } = useNotificationStore();
    const fetchedIds = useRef(new Set<string>());

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 60000); // refresh every minute
        return () => clearInterval(interval);
    }, []);

    const fetchAlerts = async () => {
        try {
            const res = await axios.get(`/api/admin/alerts`, { withCredentials: true });
            if (res.data && res.data.data) {
                const alerts: any[] = res.data.data;
                alerts.forEach(a => {
                    if (!fetchedIds.current.has(a.id)) {
                        fetchedIds.current.add(a.id);
                        addNotification({
                            message: `[${a.type}] ${a.message}`,
                            type: (a.severity === 'critical' || a.severity === 'high') ? 'error' : 'warning'
                        });
                    }
                });
            }
        } catch (e) {
            console.error("Failed to load alerts", e);
        }
    };

    return null;
}
