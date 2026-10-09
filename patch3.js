const fs = require('fs');
let code = fs.readFileSync('labgen/frontend/src/components/ReportGenerator.tsx', 'utf8');

code = code.replace(/<h2 className="font-display text-lg text-cyber-primary flex items-center gap-2">/, '<h1 className="font-display text-lg text-cyber-primary flex items-center gap-2">');
code = code.replace(/<\/h2>/, '</h1>');

code = code.replace(/aria-expanded=\{expanded\}/, 'aria-expanded={expanded}\n        aria-controls={`${question.id}-content`}');

code = code.replace(/<div className="border-t border-cyber-border pt-4 animate-in slide-in-from-top-2 duration-200">/, '<div id={`${question.id}-content`} className="border-t border-cyber-border pt-4 animate-in slide-in-from-top-2 duration-200">');

code = code.replace(/<textarea/, '<textarea id={question.id} aria-label={question.label}');
code = code.replace(/<select value/, '<select id={question.id} aria-label={question.label} value');
code = code.replace(/<input\n                type=\{question\.type\}/, '<input id={question.id} aria-label={question.label}\n                type={question.type}');

fs.writeFileSync('labgen/frontend/src/components/ReportGenerator.tsx', code);
