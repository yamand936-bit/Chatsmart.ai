with open("frontend/src/app/app/chat/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

import_store = "import { useNotificationStore } from '@/store/useNotificationStore';\n"
text = text.replace("import toast from 'react-hot-toast';", import_store + "import toast from 'react-hot-toast';")


sse_use_effect = """  useEffect(() => {
    let es: EventSource;
    if (typeof window !== 'undefined') {
        es = new EventSource(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/stream`, { withCredentials: true });
        es.onmessage = (e) => {
            try {
                const payload = JSON.parse(e.data);
                if (payload.type === 'new_message') {
                    if (selectedConversation === payload.conversation_id) {
                        // Refresh current chat
                        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/conversations/${selectedConversation}/messages`, { withCredentials: true })
                         .then(res => setMessages(res.data.data || []));
                    } else {
                        useNotificationStore.getState().addNotification({
                            message: `New message from ${payload.customer_phone || 'a customer'}`,
                            type: 'info'
                        });
                        fetchConversations();
                    }
                }
            } catch(e) {}
        };
    }
    return () => {
        if(es) es.close();
    };
  }, [selectedConversation]);

  useEffect(() => {
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true })"""

text = text.replace("  useEffect(() => {\n    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true })", sse_use_effect)

with open("frontend/src/app/app/chat/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
