import re

with open("labgen/frontend/src/App.tsx", "r") as f:
    content = f.read()

content = content.replace(
    '<div \n            className="lg:hidden absolute inset-0 bg-black/50 z-20" \n            onClick={() => setSidebarOpen(false)} \n          />',
    '<div className="lg:hidden absolute inset-0 bg-black/50 z-20" onClick={() => setSidebarOpen(false)} aria-hidden="true" tabIndex={-1} />'
)

# Also check for exact string match might fail if whitespace differs
content = re.sub(
    r'<div\s*className="lg:hidden absolute inset-0 bg-black/50 z-20"\s*onClick=\{\(\) => setSidebarOpen\(false\)\}\s*/>',
    '<div className="lg:hidden absolute inset-0 bg-black/50 z-20" onClick={() => setSidebarOpen(false)} aria-hidden="true" tabIndex={-1} />',
    content
)

with open("labgen/frontend/src/App.tsx", "w") as f:
    f.write(content)
