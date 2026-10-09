const fs = require('fs');

// Patch Header.tsx
let headerCode = fs.readFileSync('labgen/frontend/src/components/Header.tsx', 'utf8');
headerCode = headerCode.replace("import { cn } from '../lib/utils'", "import { cn } from '../lib/utils'\nimport { CONNECTION_STATUS } from '../lib/constants'");

const headerStatusConfigRegex = /const statusConfig = {[\s\S]*?}\n\n  const config = statusConfig\[connectionStatus\]/;
const headerReplacement = `const config = CONNECTION_STATUS[connectionStatus]
  const Icon = connectionStatus === 'connected' ? Wifi : 
               connectionStatus === 'connecting' ? Zap :
               connectionStatus === 'disconnected' ? WifiOff : AlertTriangle;`;

headerCode = headerCode.replace(headerStatusConfigRegex, headerReplacement);
headerCode = headerCode.replace(/<config\.icon/g, '<Icon');
headerCode = headerCode.replace(/config\.label/g, 'config.headerLabel');
fs.writeFileSync('labgen/frontend/src/components/Header.tsx', headerCode);

// Patch StatusBar.tsx
let statusCode = fs.readFileSync('labgen/frontend/src/components/StatusBar.tsx', 'utf8');
statusCode = statusCode.replace("import { cn } from '../lib/utils'", "import { cn } from '../lib/utils'\nimport { CONNECTION_STATUS } from '../lib/constants'");

const statusConfigRegex = /const statusConfig = {[\s\S]*?}\n\n  const config = statusConfig\[connectionStatus\]/;
const statusReplacement = `const config = CONNECTION_STATUS[connectionStatus]
  const Icon = connectionStatus === 'connected' ? Wifi : 
               connectionStatus === 'connecting' ? Zap :
               connectionStatus === 'disconnected' ? WifiOff : AlertTriangle;`;

statusCode = statusCode.replace(statusConfigRegex, statusReplacement);
statusCode = statusCode.replace(/<config\.icon/g, '<Icon');
fs.writeFileSync('labgen/frontend/src/components/StatusBar.tsx', statusCode);
