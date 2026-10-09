const fs = require('fs');
let code = fs.readFileSync('labgen/frontend/src/components/ReportExplorer.tsx', 'utf8');

// Modify ReportItem props
const oldProps = `function ReportItem({ report, isSelected, onSelect, onOpen, onDelete }: {
  report: Report
  isSelected: boolean
  onSelect: () => void
  onOpen: () => void
  onDelete: () => void
})`;
const newProps = `function ReportItem({ report, isSelected, onSelect, onOpen, onDelete }: {
  report: Report
  isSelected: boolean
  onSelect: (report: Report) => void
  onOpen: (report: Report) => void
  onDelete: (id: string) => void
})`;
code = code.replace(oldProps, newProps);

// Modify ReportItem handlers
code = code.replace(/onClick=\{onSelect\}/g, "onClick={() => onSelect(report)}");
code = code.replace(/onClick=\{\(e\) => \{ e\.stopPropagation\(\); onOpen\(\) \}\}/g, "onClick={(e) => { e.stopPropagation(); onOpen(report) }}");
code = code.replace(/onClick=\{\(e\) => \{ e\.stopPropagation\(\); onDelete\(\) \}\}/g, "onClick={(e) => { e.stopPropagation(); onDelete(report.id) }}");

// Modify usage in ReportExplorer map
const oldUsage = `<ReportItem
                    key={report.id}
                    report={report}
                    isSelected={selectedReport?.id === report.id}
                    onSelect={() => onSelect(report)}
                    onOpen={() => onOpen(report)}
                    onDelete={() => onDelete(report.id)}
                  />`;
const newUsage = `<ReportItem
                    key={report.id}
                    report={report}
                    isSelected={selectedReport?.id === report.id}
                    onSelect={onSelect}
                    onOpen={onOpen}
                    onDelete={onDelete}
                  />`;
code = code.replace(oldUsage, newUsage);

fs.writeFileSync('labgen/frontend/src/components/ReportExplorer.tsx', code);
