import sys

with open("README.md", "r") as f:
    content = f.read()

content = content.replace(
    "- AST parsing for LLM-generated `schemdraw` code to prevent arbitrary execution.",
    "- AST parsing for LLM-generated `schemdraw` code to prevent arbitrary execution.\n\n### Tests\n```bash\ncd labgen/frontend\nnpm run test\n```\nVitest component testing for critical UI functionality (virtualization, form validation, routing)."
)

with open("README.md", "w") as f:
    f.write(content)
