import type { MetricsSummary } from "../../types/api";

interface AnalyticsPanelProps {
  open: boolean;
  summary: MetricsSummary | null;
  onClose: () => void;
}

export function AnalyticsPanel({ open, summary, onClose }: AnalyticsPanelProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="planner-modal" role="dialog" aria-modal="true">
      <div className="planner-modal__backdrop" onClick={onClose} />
      <div className="planner-modal__content">
        <div className="planner-modal__header">
          <div>
            <p className="eyebrow">Analytics</p>
            <h2>Execution Metrics</h2>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            Close
          </button>
        </div>

        {!summary ? <p>No metrics available yet.</p> : null}

        {summary ? (
          <div className="analytics-grid">
            <section className="panel">
              <div className="sidebar__section-header">
                <h3>Handlers</h3>
              </div>
              <div className="analytics-table">
                <div className="analytics-table__header">
                  <span>Handler</span>
                  <span>Runs</span>
                  <span>Failed</span>
                  <span>Avg ms</span>
                  <span>Tokens</span>
                </div>
                {summary.handlers.map((item) => (
                  <div key={item.handler_name} className="analytics-table__row">
                    <span>{item.handler_name}</span>
                    <span>{item.execution_count}</span>
                    <span>{item.failed_count}</span>
                    <span>{item.avg_latency_ms ?? "-"}</span>
                    <span>{item.prompt_tokens + item.completion_tokens}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="sidebar__section-header">
                <h3>Flows</h3>
              </div>
              <div className="analytics-table">
                <div className="analytics-table__header">
                  <span>Flow</span>
                  <span>Runs</span>
                  <span>Failed</span>
                  <span>Avg ms</span>
                  <span>Max ms</span>
                </div>
                {summary.flows.map((item) => (
                  <div key={item.flow_id} className="analytics-table__row">
                    <span>{item.flow_id}</span>
                    <span>{item.execution_count}</span>
                    <span>{item.failed_count}</span>
                    <span>{item.avg_latency_ms ?? "-"}</span>
                    <span>{item.max_latency_ms ?? "-"}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        ) : null}
      </div>
    </div>
  );
}
