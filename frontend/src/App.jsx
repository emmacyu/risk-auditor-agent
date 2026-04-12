import React, { useState, useRef, useEffect } from 'react';
import { Send, UploadCloud, Database, Bot, User, CheckCircle2, ShieldAlert } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'System initialized. Dedicated Risk Auditing Engine online, bridged to underlying ChromaDB vector archives and Postgres memory matrix.\n\nWhat compliance document requires auditing, or what risk concerns can I assist with?' }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  // Manage the upload state here
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  // Auto-scroll to the bottom of the chat
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputVal.trim() || isTyping) return;

    const userMsg = inputVal.trim();
    setInputVal('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg, user_id: 'risk_officer_frontend' })
      });
      
      const data = await response.json();
      if (response.ok) {
        setMessages(prev => [...prev, { role: 'ai', content: data.answer }]);
      } else {
        setMessages(prev => [...prev, { role: 'ai', content: `[Engine Error]: ${data.detail || 'Unknown failure'}` }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', content: `[Connection Lost]: Unable to reach FastAPI backend, please check port 8000.` }]);
    } finally {
      setIsTyping(false);
    }
  };

  const uploadFile = async (file) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setMessages(prev => [...prev, { role: 'ai', content: `[System Notice]: Document "${file.name}" successfully parsed and ingested. ChromaDB memory updated!` }]);
      } else {
        setMessages(prev => [...prev, { role: 'ai', content: `[Upload Error]: ${data.detail || 'Unknown failure'}` }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', content: `[Network Error]: Unable to connect to backend /upload endpoint.` }]);
    } finally {
      setIsUploading(false);
      // Clear the input value so the same file name can be uploaded sequentially
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  };

  // Drag-and-Drop event handling system
  const handleDragOver = (e) => {
    e.preventDefault();
    if (!isUploading) setIsDragging(true);
  };
  
  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (isUploading) return;
    
    const file = e.dataTransfer.files?.[0];
    if (file && file.name.toLowerCase().endsWith('.pdf')) {
      uploadFile(file);
    } else {
      setMessages(prev => [...prev, { role: 'ai', content: `[System Block]: Invalid format. Only .pdf compliance documents are accepted!` }]);
    }
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center p-6 lg:p-12">
      {/* 核心双列交互卡片 */}
      <div className="glass-panel w-full h-full max-w-7xl rounded-3xl overflow-hidden flex flex-col md:flex-row relative z-10">
        
        {/* 左侧：智能交互终端 (聊天区) */}
        <div className="flex-1 flex flex-col border-r border-slate-700/50 bg-slate-900/20">
          {/* Header */}
          <div className="px-6 py-5 border-b border-slate-700/50 flex items-center gap-3 bg-slate-900/40">
            <div className="w-10 h-10 rounded-full bg-brand-cyan/20 flex items-center justify-center border border-brand-cyan/30">
              <ShieldAlert className="text-brand-cyan w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-100 tracking-wide">Nexus Auditor <span className="text-brand-cyan text-sm ml-2 px-2 py-0.5 rounded-full border border-brand-cyan/20 bg-brand-cyan/10">v1.2</span></h1>
              <p className="text-xs text-slate-400 mt-0.5">LangGraph Core • Postgres Checkpointed</p>
            </div>
          </div>

          {/* Messages Area */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  key={idx} 
                  className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
                >
                  {/* Avatar */}
                  <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center border shadow-sm ${msg.role === 'user' ? 'bg-slate-700/50 border-slate-600' : 'bg-brand-purple/20 border-brand-purple/30'}`}>
                    {msg.role === 'user' ? <User className="w-4 h-4 text-slate-300" /> : <Bot className="w-4 h-4 text-brand-purple" />}
                  </div>
                  
                  {/* Bubble */}
                  <div className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${msg.role === 'user' ? 'bg-slate-700/50 text-slate-100 rounded-tr-sm' : 'bg-slate-800/70 border border-slate-700/50 text-slate-200 rounded-tl-sm'}`}>
                    {msg.content}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {isTyping && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
                  <div className="shrink-0 w-8 h-8 rounded-full bg-brand-purple/20 border border-brand-purple/30 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-brand-purple" />
                  </div>
                  <div className="flex items-center gap-1.5 p-4 rounded-2xl bg-slate-800/70 border border-slate-700/50 rounded-tl-sm">
                    <div className="w-2 h-2 rounded-full bg-brand-cyan/60 animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 rounded-full bg-brand-cyan/60 animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 rounded-full bg-brand-cyan/60 animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </motion.div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-5 bg-slate-900/50 border-t border-slate-700/50">
            <form onSubmit={handleSend} className="relative flex items-center">
              <input 
                type="text" 
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                placeholder="Enter risk consultation or audit request here..." 
                className="glass-input w-full py-4 pl-5 pr-14 rounded-xl text-sm shadow-inner"
              />
              <button 
                type="submit" 
                disabled={!inputVal.trim() || isTyping}
                className="absolute right-2 p-2.5 rounded-lg bg-brand-cyan/20 text-brand-cyan hover:bg-brand-cyan hover:text-slate-900 transition-colors disabled:opacity-50 disabled:hover:bg-brand-cyan/20 disabled:hover:text-brand-cyan"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>

        {/* 右侧：资料库状态监测 */}
        <div className="w-full md:w-80 bg-slate-900/60 p-6 flex flex-col">
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2 mb-6">
            <Database className="w-5 h-5 text-brand-purple" />
            Matrix Neural Node Status
          </h2>

          <div className="space-y-4">
            {/* Widget 1 */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-400 font-medium">ChromaDB Connection</span>
                <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-md border border-emerald-400/20"><CheckCircle2 className="w-3 h-3"/> Mounted</span>
              </div>
              <div className="text-2xl font-bold font-outfit text-slate-200">2 <span className="text-sm font-normal text-slate-500">Memory Chunks</span></div>
            </div>

            {/* Widget 2 */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-400 font-medium">Postgres Checkpointer</span>
                <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-md border border-emerald-400/20"><CheckCircle2 className="w-3 h-3"/> Active</span>
              </div>
              <div className="text-2xl font-bold font-outfit text-slate-200"># <span className="text-sm font-normal text-slate-500">Thread Active</span></div>
            </div>

            {/* Upload Zone */}
            <div 
              onClick={() => !isUploading && fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`mt-8 border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center text-center transition-all group ${
                isUploading ? 'cursor-not-allowed border-brand-purple/40 bg-brand-purple/10' : 
                isDragging ? 'border-brand-cyan bg-brand-cyan/20 scale-[1.02] cursor-copy' : 
                'cursor-pointer border-slate-600/50 hover:border-brand-cyan/40 hover:bg-slate-800/50'
              }`}
            >
              <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".pdf" className="hidden" />
              <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mb-3 group-hover:scale-110 group-hover:bg-brand-cyan/20 transition-all">
                {isUploading ? (
                   <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-brand-purple" />
                ) : (
                   <UploadCloud className="w-6 h-6 text-slate-400 group-hover:text-brand-cyan" />
                )}
              </div>
              <p className={`text-sm font-medium ${isUploading ? 'text-brand-purple animate-pulse' : 'text-slate-300'}`}>
                {isUploading ? 'Deep slicing and ingesting...' : 'Click here to upload'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Supports PDF compliance documents</p>
            </div>
          </div>
          
          <div className="mt-auto pt-6 text-center">
            <div className="inline-block px-3 py-1 rounded-full border border-slate-700 bg-slate-800/50 text-[10px] text-slate-400 font-mono">
              SYSTEM: ALL GREEN
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;
