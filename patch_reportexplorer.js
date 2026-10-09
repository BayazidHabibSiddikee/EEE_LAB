const fs = require('fs');
let code = fs.readFileSync('labgen/frontend/src/components/ReportExplorer.tsx', 'utf8');

// Replace date formatting
code = code.replace(/new Date\(report\.createdAt\)\.toLocaleDateString\(\)/g, "new Date(report.createdAt).toISOString().split('T')[0]");

// Extract REPORT_STATUS
code = code.replace("import { Report } from '../../App'", "import { Report } from '../../App'\nimport { REPORT_STATUS } from '../lib/constants'");
code = code.replace(/const statusConfig = {[\s\S]*?}[\s\n]*const config = statusConfig\[report\.status\]/, "const config = REPORT_STATUS[report.status]");

fs.writeFileSync('labgen/frontend/src/components/ReportExplorer.tsx', code);
