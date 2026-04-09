import { JsonEditor } from "../common/JsonEditor";
import { StatusBadge } from "../common/StatusBadge";
import { approveFlowNode, revokeFlowNodeApproval } from "../../lib/apiClient";
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
  const flowId = useFlowStore((state) => state.flowId);
  const dirty = useFlowStore((state) => state.dirty);
  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);
  const selectedNodeId = useFlowStore((state) => state.selectedNodeId);
  const selectedEdgeId = useFlowStore((state) => state.selectedEdgeId);
  const updateNodeData = useFlowStore((state) => state.updateNodeData);
  const updateEdgeCondition = useFlowStore((state) => state.updateEdgeCondition);
  const applyFlowSnapshot = useFlowStore((state) => state.applyFlowSnapshot);
  const setExecutionError = useFlowStore((state) => state.setExecutionError);

  const selectedNode = nodes.find((node) => node.id === selectedNodeId) ?? null;
  const selectedEdge = edges.find((edge) => edge.id === selectedEdgeId) ?? null;
  const selectedHandler =
    selectedNode ? handlers.find((handler) => handler.name === selectedNode.data.handler_name) ?? null : null;
  const selectedNodeUiMetadata = selectedNode ? readUiMetadata(selectedNode.data.metadata) : {};

  const handleApproveNode = async () => {
    if (!selectedNode) {
      return;
    }
    const approvedBy = selectedNode.data.manual_approval.approved_by?.trim() || "Inspector Approval";
    const reason = selectedNode.data.manual_approval.reason?.trim() || null;
    if (flowId && !dirty) {
      try {
        const snapshot = await approveFlowNode(flowId, selectedNode.id, {
          approved_by: approvedBy,
          reason,
        });
        applyFlowSnapshot(snapshot, "node.approval.updated");
        setExecutionError(null);
      } catch (error) {
        setExecutionError(error instanceof Error ? error.message : "Approval failed");
      }
      return;
    }
    patchNode(selectedNode, updateNodeData, {
      manual_approval: {
        ...selectedNode.data.manual_approval,
        approved: true,
        approved_by: approvedBy,
        approved_at: new Date().toISOString(),
        revoked_by: null,
        revoked_at: null,
        reason,
      },
    });
  };

  const handleRevokeNodeApproval = async () => {
    if (!selectedNode) {
      return;
    }
    const revokedBy = selectedNode.data.manual_approval.approved_by?.trim() || "Inspector Approval";
    const reason = selectedNode.data.manual_approval.reason?.trim() || null;
    if (flowId && !dirty) {
      try {
        const snapshot = await revokeFlowNodeApproval(flowId, selectedNode.id, {
          revoked_by: revokedBy,
          reason,
        });
        applyFlowSnapshot(snapshot, "node.approval.revoked");
        setExecutionError(null);
      } catch (error) {
        setExecutionError(error instanceof Error ? error.message : "Approval revoke failed");
      }
      return;
    }
    patchNode(selectedNode, updateNodeData, {
      manual_approval: {
        ...selectedNode.data.manual_approval,
        approved: false,
        revoked_by: revokedBy,
        revoked_at: new Date().toISOString(),
        reason,
      },
    });
  };

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
              <option key={handler.name} value={handler.name}>
                {handler.name}
              </option>
            ))}
          </select>
        </label>

        <section className="inspector__trust-card">
          <div className="sidebar__section-header">
            <h3>Handler trust</h3>
            <StatusBadge
              label={selectedHandler?.trusted ? "Trusted" : "Untrusted"}
              tone={selectedHandler?.trusted ? "success" : "failed"}
            />
          </div>
          <p>{selectedHandler?.trust_reason ?? "No trust information available for this handler."}</p>
          {selectedHandler?.certificate ? (
            <div className="inspector__trust-meta">
              <span>Issuer: {selectedHandler.certificate.issuer}</span>
              <span>Fingerprint: {selectedHandler.fingerprint.slice(0, 18)}...</span>
              <span>Expires: {selectedHandler.certificate.expires_at}</span>
            </div>
          ) : null}
        </section>

        {hasNodeDocumentation(selectedNodeUiMetadata) ? (
          <section className="inspector__docs-card">
            <div className="sidebar__section-header">
              <h3>Node guide</h3>
            </div>
            {typeof selectedNodeUiMetadata.summary === "string" ? (
              <p className="inspector__docs-summary">{selectedNodeUiMetadata.summary}</p>
            ) : null}
            {typeof selectedNodeUiMetadata.description === "string" ? (
              <p>{selectedNodeUiMetadata.description}</p>
            ) : null}
            {Array.isArray(selectedNodeUiMetadata.notes) && selectedNodeUiMetadata.notes.length > 0 ? (
              <ul className="inspector__docs-list">
                {selectedNodeUiMetadata.notes.map((note, index) =>
                  typeof note === "string" && note.trim() ? <li key={`${selectedNode.id}-note-${index}`}>{note}</li> : null,
                )}
              </ul>
            ) : null}
          </section>
        ) : null}

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

        <fieldset className="fieldset">
          <legend>Manual approval</legend>
          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={selectedNode.data.requires_manual_approval}
              onChange={(event) =>
                patchNode(selectedNode, updateNodeData, {
                  requires_manual_approval: event.target.checked,
                })
              }
            />
            <span>Require manual approval before execution</span>
          </label>

          <NodeField
            label="Approved by"
            value={selectedNode.data.manual_approval.approved_by ?? ""}
            placeholder="Operator name"
            onChange={(value) =>
              patchNode(selectedNode, updateNodeData, {
                manual_approval: {
                  ...selectedNode.data.manual_approval,
                  approved_by: value || null,
                },
              })
            }
          />

          <NodeField
            label="Approval reason"
            value={selectedNode.data.manual_approval.reason ?? ""}
            placeholder="Why this node is allowed to execute"
            onChange={(value) =>
              patchNode(selectedNode, updateNodeData, {
                manual_approval: {
                  ...selectedNode.data.manual_approval,
                  reason: value || null,
                },
              })
            }
          />

          <div className="inspector__approval-status">
            <StatusBadge
              label={selectedNode.data.manual_approval.approved ? "Approved" : "Pending"}
              tone={selectedNode.data.manual_approval.approved ? "success" : "paused"}
            />
            {selectedNode.data.manual_approval.approved_at ? (
              <span>Approved at: {selectedNode.data.manual_approval.approved_at}</span>
            ) : null}
          </div>

          <div className="inspector__approval-actions">
            <button type="button" className="primary-button" onClick={() => void handleApproveNode()}>
              Approve Node
            </button>
            <button type="button" className="ghost-button" onClick={() => void handleRevokeNodeApproval()}>
              Revoke Approval
            </button>
          </div>
        </fieldset>

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

function readUiMetadata(metadata: Record<string, unknown> | undefined): Record<string, unknown> {
  if (!metadata || typeof metadata !== "object") {
    return {};
  }
  const ui = metadata.ui;
  return ui && typeof ui === "object" ? (ui as Record<string, unknown>) : {};
}

function hasNodeDocumentation(uiMetadata: Record<string, unknown>): boolean {
  return (
    typeof uiMetadata.summary === "string" ||
    typeof uiMetadata.description === "string" ||
    (Array.isArray(uiMetadata.notes) && uiMetadata.notes.some((note) => typeof note === "string" && note.trim()))
  );
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
