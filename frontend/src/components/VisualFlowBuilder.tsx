'use client';
import React, { useState, useRef, useCallback } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useTranslations } from 'next-intl';
import { TriggerNode, ActionNode, AIHandoverNode, WaitNode } from './FlowBuilderNodes';
import { Zap, MessageSquare, Sparkles, Clock, Play } from 'lucide-react';
import FlowSimulatorDrawer from './FlowSimulatorDrawer';
import toast from 'react-hot-toast';

const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  ai_handover: AIHandoverNode,
  wait_for_input: WaitNode,
};

const initialNodes = [
  {
    id: 'node-1',
    type: 'trigger',
    position: { x: 250, y: 150 },
    data: { triggerKeyword: '' },
  },
];

const Sidebar = () => {
  const t = useTranslations('builder');

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <aside className="w-64 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 p-4 flex flex-col gap-4">
      <div className="font-bold text-slate-800 dark:text-slate-100 text-lg mb-2">
        {t('canvas_title')}
      </div>
      <p className="text-xs text-slate-500 mb-4">{t('canvas_desc')}</p>
      
      <div 
        className="bg-emerald-50 dark:bg-emerald-900/40 border border-emerald-200 dark:border-emerald-800 p-3 rounded-xl flex items-center gap-3 cursor-grab hover:shadow-md transition-all text-emerald-800 dark:text-emerald-100 font-medium text-sm" 
        onDragStart={(event) => onDragStart(event, 'trigger')} 
        draggable
      >
        <div className="bg-emerald-100 dark:bg-emerald-800/80 p-2 rounded-lg text-emerald-600 dark:text-emerald-300"><Zap className="w-4 h-4"/></div>
        {t('drag_trigger')}
      </div>
      
      <div 
        className="bg-indigo-50 dark:bg-indigo-900/40 border border-indigo-200 dark:border-indigo-800 p-3 rounded-xl flex items-center gap-3 cursor-grab hover:shadow-md transition-all text-indigo-800 dark:text-indigo-100 font-medium text-sm" 
        onDragStart={(event) => onDragStart(event, 'action')} 
        draggable
      >
        <div className="bg-indigo-100 dark:bg-indigo-800/80 p-2 rounded-lg text-indigo-600 dark:text-indigo-300"><MessageSquare className="w-4 h-4"/></div>
        {t('drag_action')}
      </div>

      <div 
        className="bg-violet-50 dark:bg-violet-900/40 border border-violet-200 dark:border-violet-800 p-3 rounded-xl flex items-center gap-3 cursor-grab hover:shadow-md transition-all text-violet-800 dark:text-violet-100 font-medium text-sm shadow-[0_0_15px_rgba(139,92,246,0.1)]" 
        onDragStart={(event) => onDragStart(event, 'ai_handover')} 
        draggable
      >
        <div className="bg-violet-600 p-2 rounded-lg text-white"><Sparkles className="w-4 h-4"/></div>
        {t('drag_ai')}
      </div>

      <div 
        className="bg-amber-50 dark:bg-amber-900/40 border border-amber-200 dark:border-amber-800 p-3 rounded-xl flex items-center gap-3 cursor-grab hover:shadow-md transition-all text-amber-800 dark:text-amber-100 font-medium text-sm" 
        onDragStart={(event) => onDragStart(event, 'wait_for_input')} 
        draggable
      >
        <div className="bg-amber-100 dark:bg-amber-800/80 p-2 rounded-lg text-amber-600 dark:text-amber-300"><Clock className="w-4 h-4"/></div>
        {t('drag_wait') || 'Wait'}
      </div>
    </aside>
  );
};

const Flow = ({ onClose, onSave, defaultUiState }: { onClose: () => void, onSave: (data: any) => void, defaultUiState?: any }) => {
  const t = useTranslations('builder');
  const [nodes, setNodes] = useState<any>(defaultUiState?.nodes || initialNodes);
  const [edges, setEdges] = useState<any>(defaultUiState?.edges || []);
  const [isSimulatorOpen, setIsSimulatorOpen] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  const onNodesChange = useCallback(
    (changes: any) => setNodes((nds: any) => applyNodeChanges(changes, nds)),
    []
  );
  
  const onEdgesChange = useCallback(
    (changes: any) => setEdges((eds: any) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (params: any) => setEdges((eds: any) => addEdge({ ...params, animated: true }, eds)),
    []
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (typeof type === 'undefined' || !type) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      
      const newNodeId = `dndnode_${new Date().getTime()}`;

      const updateNodeData = (key: string, value: string) => {
        setNodes((nds: any) =>
          nds.map((node: any) => {
            if (node.id === newNodeId) {
              node.data = { ...node.data, [key]: value };
            }
            return node;
          })
        );
      };

      const newNode = {
        id: newNodeId,
        type,
        position,
        data: { autoFocus: true, onChange: updateNodeData },
      };

      setNodes((nds: any) => nds.concat(newNode));
    },
    [reactFlowInstance]
  );
  
  // Also enrich the initial node with the update function
  const initializedNodes = nodes.map((n: any) => {
    if (!n.data.onChange) {
      n.data.onChange = (key: string, value: string) => {
        setNodes((nds: any) =>
          nds.map((node: any) => {
            if (node.id === n.id) {
              node.data = { ...node.data, [key]: value };
            }
            return node;
          })
        );
      };
    }
    return n;
  });

  const handleSave = () => {
    const triggerNodes = nodes.filter((n: any) => n.type === 'trigger');
    if (triggerNodes.length === 0) {
      toast.error(t('err_no_trigger') || "Cannot save. You must have at least one Trigger Node.");
      return;
    }

    const connectedTargets = new Set(edges.map((e: any) => e.target));
    const floatingNodes = nodes.filter((n: any) => n.type !== 'trigger' && !connectedTargets.has(n.id));
    if (floatingNodes.length > 0) {
      toast.error(t('err_floating_node') || "Cannot save. Some nodes are disconnected.");
      return;
    }

    const connectedSources = new Set(edges.map((e: any) => e.source));
    const deadEnds = nodes.filter((n: any) => n.type === 'action' && !connectedSources.has(n.id));
    if (deadEnds.length > 0) {
      toast.error(t('err_dead_end') || "Warning: Action node leads nowhere.");
      return;
    }

    const activeNodes = nodes.filter((n:any) => n.id !== 'floating'); // simple dummy filter
    const uiState = { nodes, edges };
    const { logicState } = buildLogicGraph();

    onSave({ flow_ui_state: uiState, flow_logic_state: logicState });
  };

  const buildLogicGraph = () => {
    const nodesMap: any = {};
    const triggers: any[] = [];
    const edgeMap: any = {};
    
    edges.forEach((edge: any) => {
        if(!edgeMap[edge.source]) edgeMap[edge.source] = [];
        edgeMap[edge.source].push(edge.target);
    });

    nodes.forEach((n: any) => {
      nodesMap[n.id] = {
        type: n.type,
        payload: { ...n.data },
        next: edgeMap[n.id] || []
      };
      
      delete nodesMap[n.id].payload.onChange;
      delete nodesMap[n.id].payload.autoFocus;

      if (n.type === 'trigger') {
        let kwps = n.data.triggerKeyword ? n.data.triggerKeyword.split(",").map((s:string) => s.trim()) : [];
        triggers.push({ node_id: n.id, keywords: kwps });
      }
    });

    return { logicState: { triggers, nodes: nodesMap } };
  };


  return (
    <div className="flex w-full h-[700px] border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden bg-white shadow-xl relative z-[100]">
      <Sidebar />
      <div className="flex-1 relative" ref={reactFlowWrapper}>
        <div className="absolute top-4 right-4 z-10 flex gap-2 rtl:left-4 rtl:right-auto">
           <button onClick={() => setIsSimulatorOpen(true)} className="px-3 py-2 bg-pink-100 text-pink-700 rounded-lg shadow-md font-bold text-sm hover:bg-pink-200 transition flex items-center gap-1 border border-pink-200">
             <Play className="w-4 h-4" /> Test Flow
           </button>
           <button onClick={onClose} className="px-4 py-2 bg-white text-slate-600 rounded-lg shadow-md font-medium text-sm hover:bg-slate-50 transition border border-slate-200">
             Cancel
           </button>
           <button onClick={handleSave} className="px-4 py-2 bg-indigo-600 text-white rounded-lg shadow-md font-bold text-sm hover:bg-indigo-700 transition">
             {t('save_flow')}
           </button>
        </div>
        <ReactFlow
          nodes={initializedNodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          className="bg-slate-50 dark:bg-slate-900"
        >
          <Controls />
          <MiniMap zoomable pannable nodeClassName={(n) => {
            if (n.type === 'trigger') return '!bg-emerald-500';
            if (n.type === 'action') return '!bg-indigo-500';
            if (n.type === 'ai_handover') return '!bg-violet-600';
            return '#eee';
          }} />
          <Background color="#cbd5e1" gap={16} />
        </ReactFlow>
      </div>
      <FlowSimulatorDrawer isOpen={isSimulatorOpen} onClose={() => setIsSimulatorOpen(false)} flowGraph={buildLogicGraph().logicState} />
    </div>
  );
};

export default function VisualFlowBuilder(props: any) {
  return (
    <ReactFlowProvider>
      <Flow {...props} />
    </ReactFlowProvider>
  );
}
