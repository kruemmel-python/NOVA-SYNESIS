import { useEffect, useState } from "react";

import { StatusBadge } from "../common/StatusBadge";
import type { PlannerGenerateResponse, PlannerStatus } from "../../types/api";

interface PlannerComposerProps {
  open: boolean;
  plannerStatus: PlannerStatus | null;
  onClose: () => void;
  onGenerate: (payload: { prompt: string; maxNodes: number }) => Promise<void>;
  lastResult: PlannerGenerateResponse | null;
}

const defaultPrompt = `Design a workflow that:
- fetches remote data from a provided API
- validates the response
- stores the result in memory
- sends a completion message`;

export function PlannerComposer({
  open,
  plannerStatus,
  onClose,
  onGenerate,
  lastResult,
}: PlannerComposerProps) {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [maxNodes, setMaxNodes] = useState(8);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setSubmitting(false);
      setError(null);
    }
  }, [open]);

  if (!open) {
    return null;
  }

  const available = plannerStatus?.available ?? false;

  return (
    <div className="planner-overlay" onClick={onClose}>
      <section
        className="planner-modal panel"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="panel__header">
          <div>
            <p className="eyebrow">LLM Planner</p>
            <h2>Autonomous Graph Designer</h2>
          </div>
          <div className="planner-modal__badges">
            <StatusBadge
              label={available ? "Model Ready" : "Model Missing"}
              tone={available ? "success" : "failed"}
            />
            {plannerStatus ? (
              <StatusBadge label={plannerStatus.backend.toUpperCase()} tone="neutral" />
            ) : null}
          </div>
        </div>

        <label className="field">
          <span className="field__label">Planning prompt</span>
          <textarea
            className="json-editor planner-modal__prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            spellCheck={false}
          />
          <span className="field__hint">
            Describe the intended workflow in plain language. The model returns a real graph using only registered handlers, agents and resources.
          </span>
        </label>

        <label className="field">
          <span className="field__label">Max nodes</span>
          <input
            className="text-input"
            type="number"
            min={1}
            max={40}
            value={maxNodes}
            onChange={(event) => setMaxNodes(Number(event.target.value))}
          />
        </label>

        {plannerStatus ? (
          <div className="planner-modal__meta">
            <div>
              <strong>Binary</strong>
              <span>{plannerStatus.binary_path}</span>
            </div>
            <div>
              <strong>Model</strong>
              <span>{plannerStatus.model_path}</span>
            </div>
            <div>
              <strong>Timeout</strong>
              <span>{plannerStatus.timeout_s}s</span>
            </div>
          </div>
        ) : null}

        {error ? <p className="planner-modal__error">{error}</p> : null}

        {lastResult ? (
          <section className="planner-modal__result">
            <div className="sidebar__section-header">
              <h3>Latest plan</h3>
              <StatusBadge
                label={`${lastResult.flow_request.nodes.length} nodes`}
                tone="neutral"
              />
            </div>
            {lastResult.explanation ? <p>{lastResult.explanation}</p> : null}
            {lastResult.warnings.length > 0 ? (
              <ul className="empty-list">
                {lastResult.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : (
              <p>No normalization warnings.</p>
            )}
          </section>
        ) : null}

        <div className="planner-modal__actions">
          <button type="button" className="ghost-button" onClick={onClose}>
            Close
          </button>
          <button
            type="button"
            className="accent-button"
            disabled={!available || submitting || !prompt.trim()}
            onClick={async () => {
              try {
                setSubmitting(true);
                setError(null);
                await onGenerate({ prompt, maxNodes });
              } catch (generationError) {
                setError(
                  generationError instanceof Error
                    ? generationError.message
                    : "Planner generation failed",
                );
              } finally {
                setSubmitting(false);
              }
            }}
          >
            {submitting ? "Planning..." : "Generate Graph"}
          </button>
        </div>
      </section>
    </div>
  );
}
