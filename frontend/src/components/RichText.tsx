import type { ReactNode } from "react";

function formatLine(line: string): ReactNode {
  const nodes: ReactNode[] = [];
  let key = 0;
  const boldParts = line.split(/(\*\*[^*]+\*\*)/g);
  for (const part of boldParts) {
    if (part.startsWith("**") && part.endsWith("**")) {
      nodes.push(<strong key={key++}>{part.slice(2, -2)}</strong>);
      continue;
    }
    const italicParts = part.split(/(_[^_]+_)/g);
    for (const segment of italicParts) {
      if (
        segment.startsWith("_") &&
        segment.endsWith("_") &&
        segment.length > 2
      ) {
        nodes.push(<em key={key++}>{segment.slice(1, -1)}</em>);
      } else if (segment.length > 0) {
        nodes.push(<span key={key++}>{segment}</span>);
      }
    }
  }
  return <>{nodes}</>;
}

/** Minimal inline markdown: **bold** and _italic_ */
export function RichText({ text }: { text: string }) {
  const blocks = text.split(/\n\n+/);
  return (
    <div className="rich-text">
      {blocks.map((block, bi) => (
        <p key={bi} className="rich-text__block">
          {block.split("\n").map((line, li) => (
            <span key={li}>
              {li > 0 ? <br /> : null}
              {formatLine(line)}
            </span>
          ))}
        </p>
      ))}
    </div>
  );
}
