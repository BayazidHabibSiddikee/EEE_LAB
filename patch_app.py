import re

with open("labgen/frontend/src/App.tsx", "r") as f:
    content = f.read()

content = content.replace('<h3 className="font-display text-lg', '<h2 className="font-display text-lg')
content = content.replace('</h3>', '</h2>')
content = content.replace('<h4 className="font-display text-sm', '<h3 className="font-display text-sm')
content = content.replace('</h4>', '</h3>')

with open("labgen/frontend/src/App.tsx", "w") as f:
    f.write(content)
