'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLocale } from 'next-intl';
import toast from 'react-hot-toast';

export default function KanbanPage() {
  const [board, setBoard] = useState<{ [key: string]: any[] }>({
    Cold: [], Warm: [], Hot: [], Ordered: []
  });
  const [loading, setLoading] = useState(true);
  const locale = useLocale();
  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  const fetchBoard = async () => {
    try {
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/kanban`, { withCredentials: true });
      if (res.data.status === 'ok') {
        setBoard(res.data.data);
      }
    } catch (e) {
      toast.error('Failed to load Kanban board');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBoard();
  }, []);

  const handleDragStart = (e: React.DragEvent, id: string, fromCol: string) => {
    e.dataTransfer.setData('cardId', id);
    e.dataTransfer.setData('fromCol', fromCol);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault(); // necessary to allow dropping
  };

  const handleDrop = async (e: React.DragEvent, targetCol: string) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('cardId');
    const fromCol = e.dataTransfer.getData('fromCol');

    if (fromCol === targetCol || !id) return;

    // Optimistic Update
    const card = board[fromCol].find(c => c.id === id);
    if (!card) return;

    setBoard(prev => {
        const newBoard = { ...prev };
        newBoard[fromCol] = newBoard[fromCol].filter(c => c.id !== id);
        newBoard[targetCol] = [card, ...newBoard[targetCol]];
        return newBoard;
    });

    try {
        await axios.put(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/kanban/${id}`, 
            { new_priority: targetCol }, 
            { withCredentials: true }
        );
        toast.success(`Moved to ${targetCol}`);
    } catch (err) {
        toast.error('Failed to move lead');
        fetchBoard(); // rollback
    }
  };

  const columns = [
    { id: 'Cold', title: '❄️ Cold Lead', color: 'border-blue-200 bg-blue-50/50 dark:bg-blue-900/10 dark:border-blue-800' },
    { id: 'Warm', title: '✨ Warm Lead', color: 'border-amber-200 bg-amber-50/50 dark:bg-amber-900/10 dark:border-amber-800' },
    { id: 'Hot', title: '🔥 Hot Lead', color: 'border-red-200 bg-red-50/50 dark:bg-red-900/10 dark:border-red-800' },
    { id: 'Ordered', title: '✅ Ordered', color: 'border-green-200 bg-green-50/50 dark:bg-green-900/10 dark:border-green-800' },
  ];

  if (loading) {
     return <div className="p-8 text-center text-slate-500">Loading Funnel...</div>;
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]" dir={dir}>
      <h2 className="text-3xl font-bold text-slate-800 dark:text-slate-100 mb-6 tracking-tight">Sales CRM Funnel</h2>
      
      <div className="flex flex-1 gap-6 overflow-x-auto pb-4">
        {columns.map(col => (
           <div 
             key={col.id} 
             className={`w-80 min-w-[320px] flex flex-col rounded-2xl border-2 ${col.color} shadow-sm backdrop-blur-sm`}
             onDragOver={handleDragOver}
             onDrop={(e) => handleDrop(e, col.id)}
           >
              <div className="p-4 border-b border-inherit bg-white/50 dark:bg-slate-800/50 rounded-t-2xl flex justify-between items-center">
                  <h3 className="font-bold text-slate-800 dark:text-slate-100 text-lg">{col.title}</h3>
                  <span className="bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold px-2 py-0.5 rounded-full text-xs shadow-sm shadow-slate-200 dark:shadow-slate-800">
                      {board[col.id]?.length || 0}
                  </span>
              </div>
              <div className="p-4 flex flex-col gap-3 flex-1 overflow-y-auto">
                 {board[col.id]?.map(item => (
                    <div 
                      key={item.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, item.id, col.id)}
                      className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 cursor-grab active:cursor-grabbing hover:shadow-md transition group"
                    >
                        <div className="font-mono text-sm font-bold text-slate-700 dark:text-slate-200 mb-2" dir="ltr">{item.customer_phone}</div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2">{item.last_message || '...'}</p>
                        <div className="mt-3 flex justify-between text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                           <span>{new Date(item.updated_at).toLocaleDateString()}</span>
                           <span className="opacity-0 group-hover:opacity-100 transition">Drag to Move</span>
                        </div>
                    </div>
                 ))}
                 {board[col.id]?.length === 0 && (
                     <div className="text-center p-8 border-2 border-dashed border-inherit rounded-xl text-slate-400 dark:text-slate-500 text-sm font-medium">
                         Drop leads here
                     </div>
                 )}
              </div>
           </div>
        ))}
      </div>
    </div>
  );
}
