const fs = require('fs');
let code = fs.readFileSync('labgen/frontend/src/components/TerminalOutput.tsx', 'utf8');
code = code.replace("import AutoSizer from 'react-virtualized-auto-sizer'", "");

const autoSizerReplacement = `
function AutoSizer({ children }: { children: (props: { width: number; height: number }) => React.ReactNode }) {
  const [size, setSize] = useState({ width: 0, height: 0 })
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        setSize({ width: entry.contentRect.width, height: entry.contentRect.height })
      }
    })
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={ref} style={{ width: '100%', height: '100%' }}>
      {size.width > 0 && size.height > 0 && children(size)}
    </div>
  )
}
`;

code = code.replace("export function TerminalOutput", autoSizerReplacement + "\nexport function TerminalOutput");
fs.writeFileSync('labgen/frontend/src/components/TerminalOutput.tsx', code);
