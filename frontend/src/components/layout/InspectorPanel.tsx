import { JsonEditor } from "../common/JsonEditor";
import { StatusBadge } from "../common/StatusBadge";
import { useFlowStore } from "../../store/useFlowStore";
import type { ResourceType, RollbackStrategy, TaskFlowNode } from "../../types/api";

const rollbackStrategies: RollbackStrategy[] = [
  "FAIL_FAST",
  "RETRY",
  "COMPENSATE",
  "FALLBACK_RESOURCE",
];

const resourceTypes: ResourceType[] = ["API", "MODEL", "DATABASE", "FILE", "GPU"];

export function InspectorPanel() {
  const handlers = useFlowStore((state) => state.handlers);
  const agents = useFlowStore((state) => state.agents);
  const resources = useFlowStore((state) => state.resources);
  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);
  const selectedNodeId = useFlowStore((state) => state.selectedNodeId);
  const selectedEdgeId = useFlowStore((state) => state.selectedEdgeId);
  const updateNodeData = useFlowStore((state) => state.updateNodeData);
  const updateEdgeCondition = useFlowStore((state) => state.updateEdgeCondition);

  const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? null;
  const selectedEdge = edges.find((edge) => edge.id === selectedEdgeId) ?? null;

  if (selectedNode) {
    return (
      <aside className="inspector panel">
        <div className="panel__header">
          <div>
            <p className="eyebrow">Node Config</p>
            <h2>{selectedNode.data.title}</h2>
          </div>
          <StatusBadge
            label={selectedNode.data.task_status}
            tone={statusTone(selectedNode.data.task_status)}
          />
        </div>

        <NodeField
          label="Title"
          value={selectedNode.data.title}
          onChange={(value) => patchNode(selectedNode, updateNodeData, { title: value })}
        />

        <label className="field">
          <span className="field__label">Handler</span>
          <select
            className="text-input"
            value={selectedNode.data.handler_name}
            onChange={(event) =>
              patchNode(selectedNode, updateNodeData, {
                handler_name: event.target.value,
              })
            }
          >
            {handlers.map((handler) => (
              <option key={handler} value={handler}>
                {handler}
              </option>
            ))}
          </select>
        </label>

        <JsonEditor
          label="Input"
          value={selectedNode.data.input}
          onCommit={(value) => patchNode(selectedNode, updateNodeData, { input: value })}
        />

        <NodeField
          label="Required capabilities"
          value={selectedNode.data.required_capabilities.join(", ")}
          placeholder="memory, messaging"
          onChange={(value) =>
            patchNode(selectedNode, updateNodeData, {
              required_capabilities: splitCsv(value),
            })
          }
        />

        <label className="field">
          <span className="field__label">Preferred agent</span>
          <select
            className="text-input"
            value={selectedNode.data.preferred_agent_id ?? ""}
            onChange={(event) =>
              patchNode(selectedNode, updateNodeData, {
                preferred_agent_id: event.target.value ? Number(event.target.value) : null,
              })
            }
          >
            <option value="">Automatic</option>
            {agents.map((agent) => (
              <option key={agent.agent_id} value={agent.agent_id}>
                {agent.name} ({agent.role})
              </option>
            ))}
          </select>
        </label>

        <fieldset className="fieldset">
          <legend>Resource types</legend>
          <div className="checkbox-grid">
            {resourceTypes.map((type) => (
              <label key={type} className="checkbox-card">
                <input
                  type="checkbox"
                  checked={selectedNode.data.required_resource_types.includes(type)}
                  onChange={(event) => {
                    const next = event.target.checked
                      ? [...selectedNode.data.required_resource_types, type]
                      : selectedNode.data.required_resource_types.filter((value) => value !== type);
                    patchNode(selectedNode, updateNodeData, {
                      required_resource_types: next,
                    });
                  }}
                />
                <span>{type}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <label className="field">
          <span className="field__label">Concrete resources</span>
          <select
            multiple
            className="text-input text-input--multiselect"
            value={selectedNode.data.required_resource_ids.map(String)}
            onChange={(event) => {
              const values = Array.from(event.target.selectedOptions).map((option) => Number(option.value));
              patchNode(selectedNode, updateNodeData, {
                required_resource_ids: values,
              });
            }}
          >
            {resources.map((resource) => (
              <option key={resource.resource_id} value={resource.resource_id}>
                #{resource.resource_id} {resource.type} {resource.endpoint}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="fieldset">
          <legend>Retry policy</legend>
          <div className="field-grid">
            <NumericField
              label="Retries"
              value={selectedNode.data.retry_policy.max_retries}
              onChange={(value) =>
                patchNode(selectedNode, updateNodeData, {
                  retry_policy: {
                    ...selectedNode.data.retry_policy,
                    max_retries: value,
                  },
                })
              }
            />
            <NumericField
              label="Backoff ms"
              value={selectedNode.data.retry_policy.backoff_ms}
              onChange={(value) =>
                patchNode(selectedNode, updateNodeData, {
                  retry_policy: {
                    ...selectedNode.data.retry_policy,
                    backoff_ms: value,
                  },
                })
              }
            />
            <NumericField
              label="Max backoff ms"
              value={selectedNode.data.retry_policy.max_backoff_ms}
              onChange={(value) =>
                patchNode(selectedNode, updateNodeData, {
                  retry_policy: {
                    ...selectedNode.data.retry_policy,
                    max_backoff_ms: value,
                  },
                })
              }
            />
            <NumericField
              label="Jitter ratio"
              value={selectedNode.data.retry_policy.jitter_ratio}
              step={0.05}
              onChange={(value) =>
                patchNode(selectedNode, updateNodeData, {
                  retry_policy: {
                    ...selectedNode.data.retry_policy,
                    jitter_ratio: value,
                  },
                })
              }
            />
          </div>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={selectedNode.data.retry_policy.exponential}
              onChange={(event) =>
                patchNode(selectedNode, updateNodeData, {
                  retry_policy: {
                    ...selectedNode.data.retry_policy,
                    exponential: event.target.checked,
                  },
                })
              }
            />
            <span>Exponential backoff</span>
          </label>
        </fieldset>

        <label className="field">
          <span className="field__label">Rollback strategy</span>
          <select
            className="text-input"
            value={selectedNode.data.rollback_strategy}
            onChange={(event) =>
              patchNode(selectedNode, updateNodeData, {
                rollback_strategy: event.target.value as RollbackStrategy,
              })
            }
          >
            {rollbackStrategies.map((strategy) => (
              <option key={strategy} value={strategy}>
                {strategy}
              </option>
            ))}
          </select>
        </label>

        <NodeField
          label="Compensation handler"
          value={selectedNode.data.compensation_handler ?? ""}
          placeholder="Optional handler name"
          onChange={(value) =>
            patchNode(selectedNode, updateNodeData, {
              compensation_handler: value || null,
            })
          }
        />

        <JsonEditor
          label="Validator rules"
          value={selectedNode.data.validator_rules}
          onCommit={(value) =>
            patchNode(selectedNode, updateNodeData, {
              validator_rules: asObject(value),
            })
          }
          minHeight={140}
        />

        <JsonEditor
          label="Metadata"
          value={selectedNode.data.metadata}
          onCommit={(value) =>
            patchNode(selectedNode, updateNodeData, {
              metadata: asObject(value),
            })
          }
          minHeight={140}
        />

        <section className="inspector__output">
          <div className="sidebar__section-header">
            <h3>Runtime output</h3>
          </div>
          <pre>{JSON.stringify(selectedNode.data.output ?? null, null, 2)}</pre>
        </section>
      </aside>
    );
  }

  if (selectedEdge) {
    return (
      <aside className="inspector panel">
        <div className="panel__header">
          <div>
            <p className="eyebrow">Edge Config</p>
            <h2>
              {selectedEdge.source} to {selectedEdge.target}
            </h2>
          </div>
        </div>
        <label className="field">
          <span className="field__label">Condition expression</span>
          <textarea
            className="json-editor"
            spellCheck={false}
            value={selectedEdge.data?.condition ?? "True"}
            onChange={(event) => updateEdgeCondition(selectedEdge.id, event.target.value)}
          />
          <span className="field__hint">
            Python-like expression evaluated by the backend for this transition.
          </span>
        </label>
      </aside>
    );
  }

  return (
    <aside className="inspector panel inspector--empty">
      <div className="panel__header">
        <div>
          <p className="eyebrow">Inspector</p>
          <h2>Selection</h2>
        </div>
      </div>
      <p>Select a task node or edge on the canvas to edit its configuration.</p>
      <ul className="empty-list">
        <li>Drag handlers from the catalog into the canvas.</li>
        <li>Connect tasks to define execution order.</li>
        <li>Use edge conditions to model branching.</li>
        <li>Run the saved flow and watch live status updates.</li>
      </ul>
    </aside>
  );
}

function patchNode(
  node: TaskFlowNode,
  updateNodeData: (nodeId: string, updater: (node: TaskFlowNode) => TaskFlowNode) => void,
  patch: Partial<TaskFlowNode["data"]>,
) {
  updateNodeData(node.id, (currentNode) => ({
    ...currentNode,
    data: {
      ...currentNode.data,
      ...patch,
    },
  }));
}

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function statusTone(status: string): "neutral" | "running" | "success" | "failed" | "paused" {
  if (status === "RUNNING") return "running";
  if (status === "SUCCESS") return "success";
  if (status === "FAILED") return "failed";
  if (status === "PAUSED") return "paused";
  return "neutral";
}

interface NodeFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

function NodeField({ label, value, onChange, placeholder }: NodeFieldProps) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <input
        className="text-input"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

interface NumericFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: number;
}

function NumericField({ label, value, onChange, step = 1 }: NumericFieldProps) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <input
        className="text-input"
        type="number"
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}
