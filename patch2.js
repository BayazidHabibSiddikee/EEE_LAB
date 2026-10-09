const fs = require('fs');
let code = fs.readFileSync('labgen/frontend/src/components/ReportExplorer.tsx', 'utf8');

// Replace the return of ReportItem to wrap everything properly
const wrongReturn = `  return (
    <div className={cn(
      'group file-item flex items-center justify-between w-full pr-2',
      isSelected && 'active'
    )}>
      <button className="flex items-center gap-2 flex-1 text-left min-w-0 py-2" onClick={onSelect} aria-label={\`Select report \${report.name}\`}>
        <span className={cn('text-lg', config.color)}>{config.icon}</span>
        <div className="flex-1 min-w-0">
          <p className="font-mono text-sm truncate">{report.name}</p>
          <p className="text-xs text-cyber-textDim truncate">{report.experiment}</p>
        </div>
      </button>
      <div className="flex items-center gap-1 opacity-0 group-[.active]:opacity-100 lg:group-hover:opacity-100 transition-opacity focus-within:opacity-100">
        <button 
          onClick={(e) => { e.stopPropagation(); onOpen() }} 
          className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-cyber-border rounded text-cyber-textDim hover:text-cyber-primary" 
          title="Open"
          aria-label={\`Open report \${report.name}\`}
        >
          <Eye className="w-4 h-4" />
        </button>
        <button 
          onClick={(e) => { e.stopPropagation(); onDelete() }} 
          className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-cyber-border rounded text-cyber-textDim hover:text-cyber-secondary" 
          title="Delete"
          aria-label={\`Delete report \${report.name}\`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
      
      <div className="ml-6 h-1 bg-cyber-border/20 mt-1">
        <div className={cn('h-full transition-all duration-300', report.status === 'generating' || report.status === 'verifying' ? 'animate-pulse-slow' : '')} style={{ width: \`\${report.progress}%\` }} />
      </div>
    </div>
  )
}`;

const correctReturn = `  return (
    <div>
      <div className={cn(
        'group file-item flex items-center justify-between w-full pr-2',
        isSelected && 'active'
      )}>
        <button className="flex items-center gap-2 flex-1 text-left min-w-0 py-2" onClick={onSelect} aria-label={\`Select report \${report.name}\`}>
          <span className={cn('text-lg', config.color)}>{config.icon}</span>
          <div className="flex-1 min-w-0">
            <p className="font-mono text-sm truncate">{report.name}</p>
            <p className="text-xs text-cyber-textDim truncate">{report.experiment}</p>
          </div>
        </button>
        <div className="flex items-center gap-1 opacity-0 group-[.active]:opacity-100 lg:group-hover:opacity-100 transition-opacity focus-within:opacity-100">
          <button 
            onClick={(e) => { e.stopPropagation(); onOpen() }} 
            className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-cyber-border rounded text-cyber-textDim hover:text-cyber-primary" 
            title="Open"
            aria-label={\`Open report \${report.name}\`}
          >
            <Eye className="w-4 h-4" />
          </button>
          <button 
            onClick={(e) => { e.stopPropagation(); onDelete() }} 
            className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-cyber-border rounded text-cyber-textDim hover:text-cyber-secondary" 
            title="Delete"
            aria-label={\`Delete report \${report.name}\`}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="ml-6 h-1 bg-cyber-border/20 mt-1">
        <div className={cn('h-full transition-all duration-300', report.status === 'generating' || report.status === 'verifying' ? 'animate-pulse-slow' : '')} style={{ width: \`\${report.progress}%\` }} />
      </div>
    </div>
  )
}`;

code = code.replace(wrongReturn, correctReturn);
fs.writeFileSync('labgen/frontend/src/components/ReportExplorer.tsx', code);
