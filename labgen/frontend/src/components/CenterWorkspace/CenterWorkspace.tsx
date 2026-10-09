import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { useState, useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { FileText, Code2, Box, Download, ChevronRight } from 'lucide-react';
import { Asset } from '../../types/pipeline';

interface CenterWorkspaceProps {
  assets: Asset[];
  markdownContent: string;
  latexContent: string;
  cadModelUrl?: string;
  activeTab: 'preview' | 'code' | '3d';
  onTabChange: (tab: 'preview' | 'code' | '3d') => void;
  onAssetDownload: (asset: Asset) => void;
  isGenerating: boolean;
}

const TABS = [
  { id: 'preview', label: 'Preview', icon: FileText },
  { id: 'code', label: 'Source', icon: Code2 },
  { id: '3d', label: '3D View', icon: Box },
] as const;

export function CenterWorkspace({ 
  assets, 
  markdownContent, 
  latexContent, 
  cadModelUrl,
  activeTab, 
  onTabChange, 
  onAssetDownload,
  isGenerating
}: CenterWorkspaceProps) {
  const [assetDrawerOpen, setAssetDrawerOpen] = useState(false);

  return (
    <div className="flex-1 flex flex-col bg-slate-950 relative overflow-hidden">
      {/* Tab Bar */}
      <div className="flex items-center border-b border-slate-800 bg-slate-900/80 px-4 h-10">
        <div className="flex gap-1">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onTabChange(id as 'preview' | 'code' | '3d')}
              className={cn(
                'px-3 py-1.5 rounded-t-lg text-sm font-medium transition-all duration-150 flex items-center gap-1.5',
                activeTab === id
                  ? 'bg-slate-800 text-white border-b-2 border-blue-500'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
        
        <div className="flex-1" />
        
        {/* Asset Drawer Toggle */}
        {assets.length > 0 && (
          <button
            onClick={() => setAssetDrawerOpen(!assetDrawerOpen)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-150 flex items-center gap-1.5',
              assetDrawerOpen
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            )}
          >
            <Download className="w-4 h-4" />
            Assets ({assets.length})
            <ChevronRight className={cn('w-3 h-3 transition-transform', assetDrawerOpen && 'rotate-90')} />
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === 'preview' && (
          <MarkdownPreview content={markdownContent} isGenerating={isGenerating} />
        )}
        {activeTab === 'code' && (
          <CodeView content={latexContent || markdownContent} isGenerating={isGenerating} />
        )}
        {activeTab === '3d' && (
          <CADViewer modelUrl={cadModelUrl} isGenerating={isGenerating} />
        )}
      </div>

      {/* Asset Drawer */}
      {assetDrawerOpen && assets.length > 0 && (
        <div className="fixed right-0 top-0 bottom-0 w-72 bg-slate-900 border-l border-slate-700 z-50 animate-in slide-in-from-right duration-200 flex flex-col">
          <div className="p-4 border-b border-slate-700 flex items-center justify-between">
            <h3 className="font-medium text-white">Generated Assets</h3>
            <button 
              onClick={() => setAssetDrawerOpen(false)}
              className="p-1 text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {assets.map((asset) => (
              <button
                key={asset.path}
                onClick={() => onAssetDownload(asset)}
                className="w-full p-3 bg-slate-800/50 border border-slate-700 rounded-lg text-left hover:border-blue-500/50 hover:bg-slate-800 transition-all flex items-center gap-3"
              >
                <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-slate-700">
                  {asset.type === 'pdf' && <FileText className="w-5 h-5 text-red-400" />}
                  {asset.type === 'fcstd' && <Box className="w-5 h-5 text-orange-400" />}
                  {asset.type === 'net' && <Code2 className="w-5 h-5 text-yellow-400" />}
                  {asset.type === 'csv' && <FileText className="w-5 h-5 text-green-400" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{asset.label}</p>
                  <p className="text-xs text-slate-500 truncate">{asset.type.toUpperCase()}</p>
                </div>
                <Download className="w-4 h-4 text-slate-400" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MarkdownPreview({ content, isGenerating }: { content: string; isGenerating: boolean }) {
  if (!content && !isGenerating) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        <div className="text-center">
          <FileText className="w-16 h-16 mx-auto text-slate-700 mb-4" />
          <p className="text-lg">No preview available</p>
          <p className="text-sm mt-1">Generate a report to see live preview</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="h-full overflow-y-auto p-6 prose prose-invert prose-slate max-w-3xl mx-auto"
      style={{ fontFamily: 'Inter, system-ui, sans-serif' }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          pre({ node, inline, className, children, ...props }: any) {
            return (
              <pre className="bg-slate-900 rounded p-4 overflow-x-auto text-sm border border-slate-800" {...props}>
                {children}
              </pre>
            )
          },
          code({ node, inline, className, children, ...props }: any) {
            return inline ? (
              <code className="bg-slate-800 rounded px-1.5 py-0.5 font-mono text-sm" {...props}>{children}</code>
            ) : (
              <code className="block font-mono text-sm" {...props}>{children}</code>
            )
          },
          table({ node, ...props }: any) {
            return (
              <div className="overflow-x-auto my-4 border border-slate-700 rounded-lg">
                <table className="w-full text-sm text-left divide-y divide-slate-700" {...props} />
              </div>
            )
          },
          th({ node, ...props }: any) {
            return <th className="px-4 py-3 bg-slate-800 font-semibold" {...props} />
          },
          td({ node, ...props }: any) {
            return <td className="px-4 py-2 border-t border-slate-800" {...props} />
          }
        }}
      >
        {content}
      </ReactMarkdown>
      
      {isGenerating && (
        <div className="animate-pulse space-y-4 mt-6">
          <div className="h-4 bg-slate-800 rounded w-full"></div>
          <div className="h-4 bg-slate-800 rounded w-5/6"></div>
          <div className="h-4 bg-slate-800 rounded w-4/6"></div>
        </div>
      )}
    </div>
  );
}

function CADViewer({ modelUrl, isGenerating }: { modelUrl?: string; isGenerating: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    if (!canvasRef.current || !modelUrl) return;
    
    // Three.js initialization would go here
    // For now, show placeholder
  }, [modelUrl]);

  if (!modelUrl && !isGenerating) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        <div className="text-center">
          <Box className="w-16 h-16 mx-auto text-slate-700 mb-4" />
          <p className="text-lg">No 3D model available</p>
          <p className="text-sm mt-1">Generate CAD to view 3D geometry</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative bg-slate-950">
      <canvas 
        ref={canvasRef} 
        className="h-full w-full" 
        style={{ display: 'block' }}
      />
      {isGenerating && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-10">
          <div className="text-center">
            <div className="w-12 h-12 border-3 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-blue-400">Loading CAD model...</p>
          </div>
        </div>
      )}
    </div>
  );
}

// Simple markdown to HTML converter (placeholder - use react-markdown in production)
function simpleMarkdownToHtml(md: string): string {
  return md
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n/g, '<br>');
}