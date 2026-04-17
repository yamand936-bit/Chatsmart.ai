with open("frontend/src/app/app/chat/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

# Import
text = text.replace(
    "import toast from 'react-hot-toast';",
    "import toast from 'react-hot-toast';\nimport { ConversationRowSkeleton, TypingIndicator } from '@/components/Skeleton';"
)

# State
text = text.replace(
    "const [conversations, setConversations] = useState<any[]>([]);",
    "const [conversations, setConversations] = useState<any[]>([]);\n  const [loadingConvos, setLoadingConvos] = useState(true);"
)

# fetchConversations
old_fetch = """  const fetchConversations = () => {
     axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/conversations`, { withCredentials: true })
      .then(res => setConversations(res.data.data || [])).catch(console.error);
  };"""
new_fetch = """  const fetchConversations = () => {
     setLoadingConvos(true);
     axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/conversations`, { withCredentials: true })
      .then(res => setConversations(res.data.data || []))
      .catch(console.error)
      .finally(() => setLoadingConvos(false));
  };"""
text = text.replace(old_fetch, new_fetch)

# Skeleton replace in JSX
old_convo_map = """            {conversations.map(c => ("""
new_convo_map = """            {loadingConvos ? Array.from({length: 4}).map((_,i) => <ConversationRowSkeleton key={i} />) : conversations.map(c => ("""
text = text.replace(old_convo_map, new_convo_map)

# Replace typing indicator
old_typing_indicator = """            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white border text-slate-500 p-3 rounded-2xl rounded-bl-none shadow-sm text-sm italic">
                  {t('typing')}
                </div>
              </div>
            )}"""
new_typing_indicator = """            {isTyping && <TypingIndicator />}"""
text = text.replace(old_typing_indicator, new_typing_indicator)

with open("frontend/src/app/app/chat/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
