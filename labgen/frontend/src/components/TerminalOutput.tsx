import { Terminal, X, Trash2, Copy, Maximize2, Minimize2, Download } from 'lucide-react'
import { useRef, useEffect, useState, useMemo } from 'react'
import { cn } from '../lib/utils'

interface TerminalOutputProps {
  logs: string[]
  isActive: boolean
  onClose: () => void
}

export function TerminalOutput({ logs, isActive, onClose }: TerminalOutputProps) {
  const terminalRef = useRef<HTMLDivElement>(null)
  const endOfLogsRef = useRef<HTMLDivElement>(null)
  const [isMinimized, setIsMinimized] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)

  const terminalLines = useMemo(() => {
    if (logs.length === 0) {
      return [
        { type: 'system', content: 'LABGEN TERMINAL v2.4.1 INITIALIZED' },
        { type: 'system', content: 'AWAITING GENERATION COMMAND...' },
        { type: 'hint', content: 'Fill the form on the left and click INITIATE GENERATION' },
      ]
    }
    return logs.map(log => ({ type: 'log', content: log }))
  }, [logs])

  useEffect(() => {
    if (!isMinimized && endOfLogsRef.current) {
      endOfLogsRef.current.scrollIntoView({ behavior: 'auto' })
    }
  }, [logs, isMinimized])

  if (isMinimized) {
    return (
      <div className="fixed bottom-0 right-4 z-40 animate-in slide-in-from-bottom-4">
        <button 
          onClick={() => setIsMinimized(false)}
          aria-label="Restore terminal"
          className="flex items-center gap-2 px-4 py-2 min-h-[44px] bg-cyber-surface border border-cyber-border rounded-lg shadow-lg hover:bg-cyber-border transition-colors"
        >
          <Terminal className="w-4 h-4 text-cyber-primary" />
          <span className="font-mono text-xs text-cyber-text">TERMINAL</span>
          <span className="px-1.5 py-0.5 text-xs bg-cyber-primary text-cyber-bg rounded font-mono">ACTIVE</span>
        </button>
      </div>
    )
  }

  return (
    <div className={cn(
      'fixed bottom-0 left-0 right-0 z-40 flex flex-col transition-all duration-300',
      isMaximized ? 'h-[80vh]' : 'h-64'
    )}>
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-cyber-border bg-cyber-surface/95 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-cyber-secondary/50" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
            <div className="w-3 h-3 rounded-full bg-green-400/50" />
          </div>
          <span className="font-mono text-xs text-cyber-textDim">terminal.tsx</span>
          <span className="px-2 py-0.5 text-xs bg-cyber-primary/10 text-cyber-primary rounded font-mono">
            {isActive ? 'ACTIVE' : 'IDLE'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button 
            onClick={() => setIsMaximized(!isMaximized)} 
            className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-cyber-border rounded transition-colors" 
            title={isMaximized ? 'Minimize' : 'Maximize'}
            aria-label={isMaximized ? 'Minimize terminal' : 'Maximize terminal'}
          >
            {isMaximized ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
          </button>
          <button 
            onClick={() => setIsMinimized(true)} 
            className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-cyber-border rounded transition-colors" 
            title="Minimize to tray"
            aria-label="Minimize terminal to tray"
          >
            <Minimize2 className="w-5 h-5 rotate-90" />
          </button>
          <button 
            onClick={onClose} 
            className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-cyber-border rounded transition-colors" 
            title="Close"
            aria-label="Close terminal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Terminal Content */}
      <div 
        ref={terminalRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm leading-relaxed bg-cyber-bg"
        style={{ fontFamily: 'JetBrains Mono, Fira Code, Consolas, monospace' }}
      >
        <div className="space-y-1">
          {terminalLines.map((line, i) => (
            <TerminalLine key={i} line={line} />
          ))}
          <div className="flex items-center gap-2 pt-2 border-t border-cyber-border/50">
            <span className="text-cyber-primary">root@labgen:</span>
            <span className="text-cyber-accent">~</span>
            <span className="text-cyber-primary">$</span>
            <span className="w-4 h-5 bg-cyber-primary animate-pulse inline-block ml-1" />
          </div>
          <div ref={endOfLogsRef} />
        </div>
      </div>

      {/* Status Bar */}
      <div className="px-3 py-1.5 border-t border-cyber-border bg-cyber-surface/95 flex items-center justify-between text-xs text-cyber-textDim">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyber-primary animate-pulse" />
            LINE {logs.length + 1}
          </span>
          <span>COL 1</span>
          <span>UTF-8</span>
          <span>LF</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyber-primary animate-pulse" />
            LIVE
          </span>
          <span className="px-2 py-0.5 text-[10px] bg-cyber-primary/10 text-cyber-primary rounded font-mono">
            {logs.length > 0 ? 'STREAMING' : 'IDLE'}
          </span>
        </div>
      </div>
    </div>
  )
}

function TerminalLine({ line }: { line: { type: string, content: string } }) {
  const getPrefix = () => {
    switch (line.type) {
      case 'system': return <span className="text-cyber-accent">[SYS]</span>
      case 'error': return <span className="text-cyber-secondary">[ERR]</span>
      case 'warning': return <span className="text-yellow-400">[WARN]</span>
      case 'success': return <span className="text-green-400">[OK]</span>
      case 'hint': return <span className="text-cyber-textDim">[HINT]</span>
      case 'progress': return <span className="text-cyber-primary">[PROG]</span>
      default: return <span className="text-cyber-textDim">[LOG]</span>
    }
  }

  return (
    <div className="flex gap-2 px-1">
      <span className="text-cyber-textDim text-xs font-mono tabular-nums w-10 text-right">
        {Math.floor(Date.now() / 1000) % 100000}
      </span>
      <span className="flex-shrink-0 px-2">{getPrefix()}</span>
      <span className="text-cyber-text break-all whitespace-pre-wrap font-mono">{line.content}</span>
    </div>
  )
}

export default TerminalOutput