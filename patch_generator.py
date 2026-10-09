import re

with open("labgen/frontend/src/components/ReportGenerator.tsx", "r") as f:
    content = f.read()

# Replace <div className="space-y-3"> with something that has <label>
# Actually, I can just replace the start of the input sections.
# Let's just use a simple string replacement.

content = content.replace(
    '<div className="space-y-3">',
    '<div className="space-y-3">\n            <label htmlFor={question.id} className="sr-only">{question.label}</label>'
)

with open("labgen/frontend/src/components/ReportGenerator.tsx", "w") as f:
    f.write(content)
