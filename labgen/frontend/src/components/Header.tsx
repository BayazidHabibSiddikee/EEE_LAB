import { Menu, Terminal, Wifi, WifiOff, AlertTriangle, Zap, Brain } from 'lucide-react'
import { cn } from '../lib/utils'

interface HeaderProps {
  onMenuClick: () => void
  onTerminalClick: () => void
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  isGenerating: boolean
}

export function Header({ onMenuClick, onTerminalClick, connectionStatus, isGenerating }: HeaderProps) {
  const statusConfig = {
    connected: { color: 'text-cyber-primary', icon: Wifi, label: 'LINK ESTABLISHED' },
    connecting: { color: 'text-cyber-accent animate-pulse', icon: Zap, label: 'HANDSHAKE IN PROGRESS' },
    disconnected: { color: 'text-cyber-textDim', icon: WifiOff, label: 'LINK SEVERED' },
    error: { color: 'text-cyber-secondary animate-pulse', icon: AlertTriangle, label: 'COMMUNICATION ERROR' },
  }

  const config = statusConfig[connectionStatus]

  return (
    <header className="h-14 border-b border-cyber-border bg-cyber-surface/80 backdrop-blur-sm flex items-center justify-between px-4 z-20">
      <div className="flex items-center gap-4">
        <button onClick={onMenuClick} className="p-2 hover:bg-cyber-border rounded transition-colors lg:hidden" aria-label="Toggle sidebar">
          <Menu className="w-5 h-5 text-cyber-text" />
        </button>
        
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-cyber-primary to-cyber-accent flex items-center justify-center">
            <Brain className="w-5 h-5 text-cyber-bg" />
          </div>
          <div>
            <div className="font-display text-xl font-bold text-cyber-primary tracking-wider">LAB<span className="text-cyber-secondary">GEN</span></div>
            <div className="font-mono text-xs text-cyber-textDim tracking-widest">CYBERDECK TERMINAL v2.4.1</div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Connection Status */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded border border-cyber-border/50 bg-cyber-bg/50">
          <config.icon className={cn('w-4 h-4', config.color)} />
          <span className={cn('font-mono text-xs', config.color)}>{config.label}</span>
        </div>

        {/* Generation Indicator */}
        {isGenerating && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded border border-cyber-primary/50 bg-cyber-primary/10 animate-pulse-slow">
            <Zap className="w-4 h-4 text-cyber-primary animate-spin" />
            <span className="font-mono text-xs text-cyber-primary">GENERATING REPORT...</span>
          </div>
        )}

        {/* Terminal Toggle */}
        <button 
          onClick={onTerminalClick}
          className="p-2 hover:bg-cyber-border rounded transition-colors"
          aria-label="Toggle terminal"
        >
          <Terminal className="w-5 h-5 text-cyber-text hover:text-cyber-primary transition-colors" />
        </button>
      </div>
    </header>
  )
}