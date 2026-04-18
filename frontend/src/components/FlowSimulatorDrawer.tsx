import React, { useState, useEffect, useRef } from 'react';
import { X, Send, Bot } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

export default function FlowSimulatorDrawer({ isOpen, onClose, flowGraph }: any) {
  const [messages, setMessages] = useState<{id: string, role: string, content: string}[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(() => uuidv4());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      setSessionId(uuidv4()); // start fresh session on open
      setMessages([{ id: '1', role: 'system', content: 'Sandbox Session Started. Type a trigger keyword.' }]);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = { id: uuidv4(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const res = await axios.post('/api/merchant/flows/simulate', {
        message: userMsg.content,
        session_id: sessionId,
        flow_logic_state: flowGraph
      });

      // Humanizing delay 1.5s as requested
      setTimeout(() => {
        setIsTyping(false);
        if (res.data.response) {
            setMessages(prev => [...prev, { id: uuidv4(), role: 'bot', content: res.data.response }]);
        }
      }, 1500);

    } catch (e: any) {
      setIsTyping(false);
      setMessages(prev => [...prev, { id: uuidv4(), role: 'system', content: 'Simulator engine offline or syntax error.' }]);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="absolute top-0 right-0 h-full w-[400px] z-[50] bg-white dark:bg-slate-900 shadow-[-10px_0_30px_rgba(0,0,0,0.1)] flex flex-col border-l border-slate-200 dark:border-slate-800">
      <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-indigo-500" />
          <h2 className="font-bold text-slate-800 dark:text-slate-100">Live Simulator Engine</h2>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-full">
          <X className="w-4 h-4 text-slate-500 dark:text-slate-400" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-900/20">
        {messages.map(m => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm drop-shadow-sm ${
                m.role === 'user' ? 'bg-indigo-600 text-white rounded-br-sm' : 
                m.role === 'system' ? 'bg-amber-100/50 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200 text-xs text-center mx-auto' :
                'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 rounded-bl-sm whitespace-pre-wrap'
            }`}>
               {m.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
             <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5 drop-shadow-sm">
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]"></span>
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]"></span>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <input 
            type="text"
            className="flex-1 bg-slate-100 dark:bg-slate-900 border-0 rounded-full px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 dark:text-white outline-none"
            placeholder="Type your message..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
          />
          <button onClick={handleSend} disabled={!input.trim() || isTyping} className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white p-2 w-9 h-9 rounded-full flex items-center justify-center transition-colors">
            <Send className="w-4 h-4 ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
