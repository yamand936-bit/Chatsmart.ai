import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { useTranslations } from 'next-intl';
import { Zap, MessageSquare, Sparkles, Clock } from 'lucide-react';

export const TriggerNode = ({ data, isConnectable }: any) => {
  const t = useTranslations('builder');
  
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-emerald-200 dark:border-emerald-800/50 min-w-[250px] overflow-hidden transition-all hover:shadow-xl hover:border-emerald-400">
      <div className="bg-emerald-50 dark:bg-emerald-900/30 px-4 py-3 border-b border-emerald-100 dark:border-emerald-800/30 flex items-center gap-2">
        <div className="bg-emerald-100 dark:bg-emerald-800 p-1.5 rounded-lg text-emerald-600 dark:text-emerald-300">
          <Zap className="w-4 h-4" />
        </div>
        <div className="font-bold text-emerald-800 dark:text-emerald-100 text-sm">
          {t('trigger_node_title')}
        </div>
      </div>
      
      <div className="p-4">
        <input 
          autoFocus={data.autoFocus}
          className="w-full text-sm px-3 py-2 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-slate-800 dark:text-slate-100 placeholder-slate-400"
          placeholder={t('placeholder')}
          value={data.triggerKeyword || ''}
          onChange={(e) => data.onChange && data.onChange('triggerKeyword', e.target.value)}
        />
      </div>

      <Handle 
        type="source" 
        position={Position.Bottom} 
        isConnectable={isConnectable} 
        className="w-3 h-3 bg-emerald-500 border-2 border-white dark:border-slate-800"
      />
    </div>
  );
};

export const ActionNode = ({ data, isConnectable }: any) => {
  const t = useTranslations('builder');
  
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-indigo-200 dark:border-indigo-800/50 min-w-[250px] overflow-hidden transition-all hover:shadow-xl hover:border-indigo-400">
      <Handle 
        type="target" 
        position={Position.Top} 
        isConnectable={isConnectable}
        className="w-3 h-3 bg-indigo-500 border-2 border-white dark:border-slate-800"
      />
      
      <div className="bg-indigo-50 dark:bg-indigo-900/30 px-4 py-3 border-b border-indigo-100 dark:border-indigo-800/30 flex items-center gap-2">
        <div className="bg-indigo-100 dark:bg-indigo-800 p-1.5 rounded-lg text-indigo-600 dark:text-indigo-300">
          <MessageSquare className="w-4 h-4" />
        </div>
        <div className="font-bold text-indigo-800 dark:text-indigo-100 text-sm">
          {t('action_node_title')}
        </div>
      </div>
      
      <div className="p-4">
        <textarea 
          autoFocus={data.autoFocus}
          className="w-full min-h-[60px] text-sm px-3 py-2 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 dark:text-slate-100 placeholder-slate-400 resize-y"
          placeholder={t('placeholder')}
          value={data.responseText || ''}
          onChange={(e) => data.onChange && data.onChange('responseText', e.target.value)}
        />
      </div>

      <Handle 
        type="source" 
        position={Position.Bottom} 
        isConnectable={isConnectable}
        className="w-3 h-3 bg-indigo-500 border-2 border-white dark:border-slate-800"
      />
    </div>
  );
};

export const AIHandoverNode = ({ data, isConnectable }: any) => {
  const t = useTranslations('builder');
  
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-[0_0_20px_rgba(139,92,246,0.3)] dark:shadow-[0_0_20px_rgba(139,92,246,0.15)] border-2 border-violet-400 dark:border-violet-600 min-w-[250px] overflow-hidden transition-all">
      <Handle 
        type="target" 
        position={Position.Top} 
        isConnectable={isConnectable}
        className="w-3 h-3 bg-violet-600 border-2 border-white dark:border-slate-800"
      />
      
      <div className="bg-violet-600 px-4 py-3 flex items-center gap-2">
        <div className="bg-white/20 p-1.5 rounded-lg text-white">
          <Sparkles className="w-4 h-4 animate-pulse" />
        </div>
        <div className="font-bold text-white text-sm">
          {t('ai_handover_title')}
        </div>
      </div>
      
      <div className="p-4 bg-gradient-to-b from-violet-50 to-white dark:from-slate-800 dark:to-slate-800">
        <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 uppercase tracking-wide">{t('tone_label') || 'Tone'}</label>
        <select
          className="w-full mb-3 text-sm px-3 py-2 border border-violet-200 dark:border-violet-800/50 bg-white dark:bg-slate-900 rounded-lg outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 text-slate-800 dark:text-slate-100 placeholder-slate-400 cursor-pointer"
          value={data.tone || 'tone_professional'}
          onChange={(e) => data.onChange && data.onChange('tone', e.target.value)}
        >
          <option value="tone_professional">{t('tone_professional')}</option>
          <option value="tone_friendly">{t('tone_friendly')}</option>
          <option value="tone_humorous">{t('tone_humorous')}</option>
          <option value="tone_urgent">{t('tone_urgent')}</option>
        </select>

        <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 uppercase tracking-wide">AI Context</div>
        <textarea 
          autoFocus={data.autoFocus}
          className="w-full min-h-[60px] text-sm px-3 py-2 border border-violet-200 dark:border-violet-800/50 bg-white dark:bg-slate-900 rounded-lg outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 text-slate-800 dark:text-slate-100 placeholder-slate-400 resize-y"
          placeholder={t('placeholder') + " (Optional)"}
          value={data.aiInstructions || ''}
          onChange={(e) => data.onChange && data.onChange('aiInstructions', e.target.value)}
        />
      </div>

      <Handle 
        type="source" 
        position={Position.Bottom} 
        isConnectable={isConnectable}
        className="w-3 h-3 bg-violet-600 border-2 border-white dark:border-slate-800"
      />
    </div>
  );
};

export const WaitNode = ({ data, isConnectable }: any) => {
  const t = useTranslations('builder');
  
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-amber-200 dark:border-amber-800/50 min-w-[250px] overflow-hidden transition-all hover:shadow-xl hover:border-amber-400">
      <Handle 
        type="target" 
        position={Position.Top} 
        isConnectable={isConnectable}
        className="w-3 h-3 bg-amber-500 border-2 border-white dark:border-slate-800"
      />
      
      <div className="bg-amber-50 dark:bg-amber-900/30 px-4 py-3 border-b border-amber-100 dark:border-amber-800/30 flex items-center gap-2">
        <div className="bg-amber-100 dark:bg-amber-800 p-1.5 rounded-lg text-amber-600 dark:text-amber-300">
          <Clock className="w-4 h-4" />
        </div>
        <div className="font-bold text-amber-800 dark:text-amber-100 text-sm">
          {t('wait_node_title')}
        </div>
      </div>
      
      <div className="p-4">
        <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1 tracking-wide">{t('var_label') || 'Variable name'}</label>
        <input 
          autoFocus={data.autoFocus}
          className="w-full text-sm px-3 py-2 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 rounded-lg outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-500 text-slate-800 dark:text-slate-100 placeholder-slate-400"
          placeholder="e.g. budget, name"
          value={data.variableName || ''}
          onChange={(e) => data.onChange && data.onChange('variableName', e.target.value)}
        />
      </div>

      <Handle 
        type="source" 
        position={Position.Bottom} 
        isConnectable={isConnectable}
        className="w-3 h-3 bg-amber-500 border-2 border-white dark:border-slate-800"
      />
    </div>
  );
};
