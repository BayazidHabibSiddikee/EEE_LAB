const fs = require('fs');
let code = fs.readFileSync('labgen/frontend/src/App.tsx', 'utf8');

code = code.replace("import { cn } from './lib/utils'", "import { cn } from './lib/utils'\nimport { REPORT_STATUS } from './lib/constants'");

const oldStatusBadge = `function StatusBadge({ status }: { status: Report['status'] }) {
  const configs = {
    idle: { bg: 'bg-cyber-textDim/10 text-cyber-textDim', icon: <Zap className="w-3 h-3" /> },
    generating: { bg: 'bg-cyber-primary/10 text-cyber-primary animate-pulse', icon: <RotateCcw className="w-3 h-3 animate-spin" /> },
    verifying: { bg: 'bg-cyber-accent/10 text-cyber-accent', icon: <Brain className="w-3 h-3 animate-pulse" /> },
    complete: { bg: 'bg-green-400/10 text-green-400', icon: <CheckCircle className="w-3 h-3" /> },
    error: { bg: 'bg-cyber-secondary/10 text-cyber-secondary', icon: <AlertTriangle className="w-3 h-3" /> },
  }
  const config = configs[status]
  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono', config.bg)}>
      {config.icon} {status.toUpperCase()}
    </span>
  )
}`;

const newStatusBadge = `function StatusBadge({ status }: { status: Report['status'] }) {
  const config = REPORT_STATUS[status]
  const Icon = status === 'idle' ? Zap : 
               status === 'generating' ? RotateCcw :
               status === 'verifying' ? Brain :
               status === 'complete' ? CheckCircle : AlertTriangle;
  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono', config.bg)}>
      <Icon className={cn("w-3 h-3", status === 'generating' ? "animate-spin" : status === 'verifying' ? "animate-pulse" : "")} />
      {config.label}
    </span>
  )
}`;

code = code.replace(oldStatusBadge, newStatusBadge);
fs.writeFileSync('labgen/frontend/src/App.tsx', code);
