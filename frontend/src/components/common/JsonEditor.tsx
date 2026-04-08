import { useEffect, useMemo, useState } from "react";

import { prettyJson, safeJsonParse } from "../../lib/json";

interface JsonEditorProps {
  label: string;
  value: unknown;
  onCommit: (value: unknown) => void;
  minHeight?: number;
}

export function JsonEditor({
  label,
  value,
  onCommit,
  minHeight = 180,
}: JsonEditorProps) {
  const formattedValue = useMemo(() => prettyJson(value ?? {}), [value]);
  const [text, setText] = useState(formattedValue);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setText(formattedValue);
    setError(null);
  }, [formattedValue]);

  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <textarea
        className={`json-editor ${error ? "json-editor--invalid" : ""}`}
        style={{ minHeight }}
        spellCheck={false}
        value={text}
        onChange={(event) => {
          setText(event.target.value);
          try {
            safeJsonParse(event.target.value);
            setError(null);
          } catch (parseError) {
            setError(parseError instanceof Error ? parseError.message : "Invalid JSON");
          }
        }}
        onBlur={() => {
          try {
            onCommit(safeJsonParse(text));
            setError(null);
          } catch (parseError) {
            setError(parseError instanceof Error ? parseError.message : "Invalid JSON");
          }
        }}
      />
      <span className={`field__hint ${error ? "field__hint--error" : ""}`}>
        {error ?? "Valid JSON. Changes are applied when the field loses focus."}
      </span>
    </label>
  );
}
