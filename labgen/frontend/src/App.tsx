import { useState, useEffect, useRef } from 'react'
import { 
  Terminal, FolderOpen, FileText, Play, Stop, Settings, 
  ChevronRight, ChevronDown, RotateCcw, Trash2, Eye, 
  Zap, Brain, Database, Network, AlertTriangle, CheckCircle,
  X, Maximize2, Minimize2, Copy, Download, Search
} from 'lucide-react'
import { ReportGenerator } from './components/ReportGenerator'
import { ReportExplorer } from './components/ReportExplorer'
import { TerminalOutput } from './components/TerminalOutput'
import { StatusBar } from './components/StatusBar'
import { Header } from './components/Header'
import { useWebSocket, WebSocketMessage } from './hooks/useWebSocket'
import { cn } from './lib/utils'
import { REPORT_STATUS } from './lib/constants'

interface Report {
  id: string
  name: string
  experiment: string
  status: 'idle' | 'generating' | 'verifying' | 'complete' | 'error'
  progress: number
  createdAt: string
  path?: string
  verification?: {
    passed: boolean
    failures: number
    warnings: number
  }
}

interface Question {
  id: string
  label: string
  type: 'text' | 'select' | 'number' | 'textarea'
  required: boolean
  options?: string[]
  placeholder?: string
  value: string | number
}

const INITIAL_QUESTIONS: Question[] = [
  { id: 'experimentName', label: 'Experiment Name', type: 'text', required: true, placeholder: 'e.g., TRIAC Characteristics Analysis', value: '' },
  { id: 'circuitPrompt', label: 'Circuit Description', type: 'textarea', required: false, placeholder: 'Describe the circuit connections (optional)...', value: '' },
  { id: 'experimentNumber', label: 'Experiment Number', type: 'number', required: true, placeholder: '2', value: 2 },
  { id: 'studentName', label: 'Student Name', type: 'text', required: true, placeholder: 'John Doe', value: '' },
  { id: 'rollNumber', label: 'Roll Number', type: 'text', required: true, placeholder: '1901000', value: '' },
  { id: 'section', label: 'Section', type: 'select', required: true, options: ['A', 'B', 'C', 'D'], value: 'A' },
  { id: 'group', label: 'Group', type: 'number', required: true, placeholder: '1', value: 1 },
]

export function App() {
  const [currentView, setCurrentView] = useState<'generator' | 'explorer' | 'settings'>('generator')
  const [questions, setQuestions] = useState<Question[]>(INITIAL_QUESTIONS)
  const [reports, setReports] = useState<Report[]>([])
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationLog, setGenerationLog] = useState<string[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [terminalOpen, setTerminalOpen] = useState(true)
  
  const { sendMessage, lastMessage, connectionStatus } = useWebSocket()

  // Load reports from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('labgen_reports')
    if (saved) {
      try {
        setReports(JSON.parse(saved))
      } catch {}
    }
  }, [])

  // Save reports to localStorage (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      localStorage.setItem('labgen_reports', JSON.stringify(reports))
    }, 500)
    return () => clearTimeout(timeoutId)
  }, [reports])

  const handleQuestionChange = (id: string, value: string | number) => {
    setQuestions(prev => prev.map(q => q.id === id ? { ...q, value } : q))
  }

  const validateQuestions = () => {
    return questions.filter(q => q.required).every(q => 
      q.value !== '' && q.value !== null && q.value !== undefined
    )
  }

  const startGeneration = async () => {
    if (!validateQuestions()) return
    
    setIsGenerating(true)
    setGenerationLog([])
    
    const formData = questions.reduce((acc, q) => ({ ...acc, [q.id]: q.value }), {})
    
    const newReport: Report = {
      id: `report_${Date.now()}`,
      name: formData.experimentName as string,
      experiment: formData.experimentName as string,
      status: 'generating',
      progress: 0,
      createdAt: new Date().toISOString(),
    }
    
    setReports(prev => [newReport, ...prev])
    setSelectedReport(newReport)
    setCurrentView('explorer')
    
    // Send to backend via WebSocket
    sendMessage({
      type: 'generate',
      payload: formData,
      reportId: newReport.id,
    })
  }

  const handleWebSocketMessage = (msg: WebSocketMessage) => {
    if (msg.type === 'progress') {
      setReports(prev => prev.map(r => 
        r.id === msg.reportId ? { ...r, progress: msg.progress, status: msg.status } : r
      ))
      if (msg.log) setGenerationLog(prev => [...prev, msg.log])
    } else if (msg.type === 'complete') {
      setReports(prev => prev.map(r => 
        r.id === msg.reportId ? { 
          ...r, 
          status: 'complete', 
          progress: 100, 
          path: msg.path,
          verification: msg.verification
        } : r
      ))
      setIsGenerating(false)
    } else if (msg.type === 'error') {
      setReports(prev => prev.map(r => 
        r.id === msg.reportId ? { ...r, status: 'error', progress: 0 } : r
      ))
      setGenerationLog(prev => [...prev, `ERROR: ${msg.message}`])
      setIsGenerating(false)
    } else if (msg.type === 'verification') {
      setReports(prev => prev.map(r => 
        r.id === msg.reportId ? { ...r, verification: msg.verification } : r
      ))
    }
  }

  useEffect(() => {
    if (lastMessage) handleWebSocketMessage(lastMessage)
  }, [lastMessage])

  const openReport = (report: Report) => {
    setSelectedReport(report)
    if (report.path) {
      window.open(report.path, '_blank')
    }
  }

  const deleteReport = (id: string) => {
    setReports(prev => prev.filter(r => r.id !== id))
    if (selectedReport?.id === id) setSelectedReport(null)
  }

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen)
  const toggleTerminal = () => setTerminalOpen(!terminalOpen)

  // Boot sequence removed (Anti-pattern fix)

  return (
    <div className="h-screen w-full flex flex-col overflow-hidden bg-cyber-bg text-cyber-text">
      <Header 
        onMenuClick={toggleSidebar}
        onTerminalClick={toggleTerminal}
        connectionStatus={connectionStatus}
        isGenerating={isGenerating}
      />
      
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar - Generator/Explorer */}
        {sidebarOpen && (
          <div className="lg:hidden absolute inset-0 bg-black/50 z-20" onClick={() => setSidebarOpen(false)} aria-hidden="true" tabIndex={-1} />
        )}
        <aside className={cn(
          'absolute lg:relative z-30 h-full w-full lg:w-96 flex-shrink-0 flex flex-col border-r border-cyber-border bg-cyber-surface',
          'transition-transform duration-300',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:block'
        )}>
          <div className="flex-1 flex flex-col overflow-hidden">
            <nav className="flex border-b border-cyber-border px-4 py-2" role="tablist" aria-label="Sidebar Views">
              <button
                role="tab"
                aria-controls="generator-panel"
                aria-selected={currentView === 'generator'}
                onClick={() => setCurrentView('generator')}
                className={cn(
                  'px-3 py-1.5 rounded text-sm font-mono transition-all',
                  currentView === 'generator' 
                    ? 'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30' 
                    : 'text-cyber-textDim hover:text-cyber-text hover:bg-cyber-border'
                )}
              >
                <Brain className="w-4 h-4 inline mr-1" /> GENERATE
              </button>
              <button
                role="tab"
                aria-selected={currentView === 'explorer'}
                onClick={() => setCurrentView('explorer')}
                className={cn(
                  'px-3 py-1.5 rounded text-sm font-mono transition-all ml-2',
                  currentView === 'explorer' 
                    ? 'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30' 
                    : 'text-cyber-textDim hover:text-cyber-text hover:bg-cyber-border'
                )}
              >
                <Database className="w-4 h-4 inline mr-1" /> REPORTS
              </button>
            </nav>

            <div className="flex-1 overflow-y-auto p-4">
              {currentView === 'generator' && (
                <ReportGenerator
                  questions={questions}
                  onChange={handleQuestionChange}
                  onSubmit={startGeneration}
                  isGenerating={isGenerating}
                  validation={validateQuestions()}
                />
              )}
              
              {currentView === 'explorer' && (
                <ReportExplorer
                  reports={reports}
                  selectedReport={selectedReport}
                  onSelect={openReport}
                  onDelete={deleteReport}
                  onOpen={openReport}
                />
              )}
              
              {currentView === 'settings' && (
                <SettingsPanel />
              )}
            </div>
          </div>
          
          <StatusBar 
            reportCount={reports.length} 
            generating={isGenerating}
            connectionStatus={connectionStatus}
          />
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {selectedReport && (
            <ReportDetailPanel 
              report={selectedReport} 
              onClose={() => setSelectedReport(null)}
              onOpen={openReport}
            />
          )}
          
          {terminalOpen && (
            <TerminalOutput 
              logs={generationLog} 
              isActive={isGenerating}
              onClose={() => setTerminalOpen(false)}
            />
          )}
        </main>

        {/* Right Sidebar - Report Detail (when selected) */}
        {selectedReport && !terminalOpen && (
          <aside className="absolute right-0 inset-y-0 z-20 w-full lg:w-96 lg:relative flex-shrink-0 border-l border-cyber-border bg-cyber-surface/95 lg:bg-cyber-surface/50 backdrop-blur lg:backdrop-blur-none animate-in slide-in-from-right shadow-2xl lg:shadow-none">
            <ReportDetailPanel 
              report={selectedReport} 
              onClose={() => setSelectedReport(null)}
              onOpen={openReport}
            />
          </aside>
        )}
      </div>
    </div>
  )
}


function SettingsPanel() {
  return (
    <div className="cyber-panel h-full overflow-y-auto">
      <h2 className="font-display text-lg text-cyber-primary mb-6 flex items-center gap-2">
        <Settings className="w-5 h-5" />
        SYSTEM CONFIGURATION
      </h2>
      <div className="space-y-6">
        <section>
          <h3 className="font-display text-sm text-cyber-textDim mb-3 uppercase tracking-wider">LLM PROVIDER</h3>
          <div className="space-y-3">
            <ProviderConfig />
          </div>
        </section>
        <section>
          <h3 className="font-display text-sm text-cyber-textDim mb-3 uppercase tracking-wider">VERIFICATION</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 accent-cyber-primary rounded border-cyber-border bg-cyber-bg" defaultChecked />
              <span className="text-sm">Auto-verify after generation</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 accent-cyber-primary rounded border-cyber-border bg-cyber-bg" defaultChecked />
              <span className="text-sm">Run LightGBM classifier</span>
            </label>
          </div>
        </section>
        <section>
          <h3 className="font-display text-sm text-cyber-textDim mb-3 uppercase tracking-wider">FREECAD</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 accent-cyber-primary rounded border-cyber-border bg-cyber-bg" defaultChecked />
              <span className="text-sm">Enable FreeCAD validation</span>
            </label>
            <div className="flex items-center gap-3">
              <span className="text-sm text-cyber-textDim w-24">Timeout (s):</span>
              <input type="number" defaultValue={120} className="cyber-input w-24" />
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

function ProviderConfig() {
  return (
    <div className="cyber-panel p-4 space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-cyber-textDim mb-1">Provider</label>
          <select className="cyber-input">
            <option>Custom (OpenAI-compatible)</option>
            <option>Gemini</option>
            <option>Ollama (Local)</option>
            <option>vLLM</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-cyber-textDim mb-1">Model</label>
          <input type="text" defaultValue="gemini-2.5-pro" className="cyber-input" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-cyber-textDim mb-1">Base URL</label>
          <input type="text" defaultValue="https://generativelanguage.googleapis.com/v1beta" className="cyber-input" />
        </div>
        <div>
          <label className="block text-xs text-cyber-textDim mb-1">API Key</label>
          <input type="password" defaultValue="••••••••" className="cyber-input" />
        </div>
      </div>
      <div>
        <label className="block text-xs text-cyber-textDim mb-1">Temperature</label>
        <input type="range" min={0} max={1} step={0.1} defaultValue={0.2} className="w-full accent-cyber-primary" />
      </div>
    </div>
  )
}

function ReportDetailPanel({ report, onClose, onOpen }: { report: Report, onClose: () => void, onOpen: (r: Report) => void }) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-cyber-border">
        <h2 className="font-display text-lg text-cyber-primary flex items-center gap-2">
          <FileText className="w-5 h-5" />
          REPORT DETAIL
        </h2>
        <button onClick={onClose} className="p-1 hover:bg-cyber-border rounded transition-colors">
          <X className="w-5 h-5 text-cyber-textDim hover:text-cyber-secondary" />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <div className="cyber-panel">
          <h3 className="font-display text-sm text-cyber-textDim mb-3 uppercase tracking-wider">METADATA</h3>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div><dt className="text-cyber-textDim">ID</dt><dd className="font-mono text-cyber-text">{report.id}</dd></div>
            <div><dt className="text-cyber-textDim">Experiment</dt><dd>{report.experiment}</dd></div>
            <div><dt className="text-cyber-textDim">Status</dt><dd><StatusBadge status={report.status} /></dd></div>
            <div><dt className="text-cyber-textDim">Progress</dt><dd>{report.progress}%</dd></div>
            <div><dt className="text-cyber-textDim">Created</dt><dd className="font-mono">{new Date(report.createdAt).toLocaleString()}</dd></div>
            <div><dt className="text-cyber-textDim">Path</dt><dd className="font-mono text-xs truncate">{report.path || 'N/A'}</dd></div>
          </dl>
        </div>
        
        {report.verification && (
          <div className="cyber-panel">
            <h3 className="font-display text-sm text-cyber-textDim mb-3 uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyber-secondary" />
              VERIFICATION RESULT
            </h3>
            <div className="flex items-center gap-4">
              <div className={cn('flex items-center gap-2 px-4 py-2 rounded', report.verification.passed ? 'bg-green-500/10 border border-green-500/30' : 'bg-cyber-secondary/10 border border-cyber-secondary/30')}>
                <CheckCircle className={cn('w-5 h-5', report.verification.passed ? 'text-green-400' : 'text-cyber-secondary')} />
                <span className="font-mono">{report.verification.passed ? 'PASSED' : 'FAILED'}</span>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1 text-red-400">
                  <AlertTriangle className="w-4 h-4" /> {report.verification.failures} failures
                </span>
                <span className="flex items-center gap-1 text-yellow-400">
                  <AlertTriangle className="w-4 h-4" /> {report.verification.warnings} warnings
                </span>
              </div>
            </div>
          </div>
        )}
        
        <div className="flex gap-3">
          <button onClick={() => onOpen(report)} className="cyber-btn cyber-btn-primary flex-1 flex items-center justify-center gap-2">
            <Eye className="w-4 h-4" /> OPEN REPORT
          </button>
          <button className="cyber-btn cyber-btn-danger flex items-center gap-2">
            <Download className="w-4 h-4" /> DOWNLOAD
          </button>
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: Report['status'] }) {
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
}

export default App