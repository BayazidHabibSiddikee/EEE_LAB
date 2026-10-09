const fs = require('fs');
let code = fs.readFileSync('labgen/frontend/src/components/ReportGenerator.tsx', 'utf8');

code = code.replace(/\{question\.type === 'textarea' && \([\s\S]*?\)\}/, `{question.type === 'textarea' && (
              <>
                <label htmlFor={question.id} className="sr-only">{question.label}</label>
                <textarea
                  id={question.id}
                  value={localValue}
                  onChange={handleChange}
                  placeholder={question.placeholder}
                  rows={4}
                  className="cyber-input resize-y min-h-[100px]"
                />
              </>
            )}`);

code = code.replace(/<select id=\{question\.id\} aria-label=\{question\.label\} value/, '<select value'); // revert my previous bad replacement

code = code.replace(/\{question\.type === 'select' && \([\s\S]*?\)\}/, `{question.type === 'select' && (
              <>
                <label htmlFor={question.id} className="sr-only">{question.label}</label>
                <select id={question.id} value={localValue} onChange={handleChange} className="cyber-input">
                  <option value="">Select...</option>
                  {question.options?.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              </>
            )}`);

code = code.replace(/\{\(question\.type === 'text' \|\| question\.type === 'number'\) && \([\s\S]*?\)\}/, `{(question.type === 'text' || question.type === 'number') && (
              <>
                <label htmlFor={question.id} className="sr-only">{question.label}</label>
                <input
                  id={question.id}
                  type={question.type}
                  value={localValue}
                  onChange={handleChange}
                  placeholder={question.placeholder}
                  className="cyber-input"
                />
              </>
            )}`);

// Button aria-controls
code = code.replace(/aria-expanded=\{expanded\}/, 'aria-expanded={expanded}\n        aria-controls={`${question.id}-content`}');
code = code.replace(/<div className="border-t border-cyber-border pt-4 animate-in slide-in-from-top-2 duration-200">/, '<div id={`${question.id}-content`} className="border-t border-cyber-border pt-4 animate-in slide-in-from-top-2 duration-200">');

// Heading h1
code = code.replace(/<h2 className="font-display text-lg text-cyber-primary flex items-center gap-2">/, '<h1 className="font-display text-lg text-cyber-primary flex items-center gap-2">');
code = code.replace(/<\/h2>/, '</h1>');


fs.writeFileSync('labgen/frontend/src/components/ReportGenerator.tsx', code);
