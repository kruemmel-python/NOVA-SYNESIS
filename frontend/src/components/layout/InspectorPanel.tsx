import { useEffect, useState } from "react";

import { JsonEditor } from "../common/JsonEditor";
import { StatusBadge } from "../common/StatusBadge";
import {
  approveFlowNode,
  fetchHumanInputRequest,
  previewAccountsReceivableDraft,
  resumeFlowNode,
  revokeFlowNodeApproval,
} from "../../lib/apiClient";
import { useFlowStore } from "../../store/useFlowStore";
import type {
  AccountsReceivableDraftPreviewResponse,
  HumanInputRequestPayload,
  ResourceType,
  RollbackStrategy,
  TaskFlowEdge,
  TaskFlowNode,
} from "../../types/api";

const rollbackStrategies: RollbackStrategy[] = [
  "FAIL_FAST",
  "RETRY",
  "COMPENSATE",
  "FALLBACK_RESOURCE",
];

const resourceTypes: ResourceType[] = ["API", "MODEL", "DATABASE", "FILE", "GPU"];
const DEFAULT_RECEIVABLE_LLM_PROMPT_TEMPLATE = `Du bist ein erfahrener Sachbearbeiter im Forderungsmanagement eines Unternehmens.
Verfasse ein finales deutsches Anschreiben zur Zahlungserinnerung.

Unternehmensdaten:
- Firma: {sender_company}
- Adresse: {sender_address}
- E-Mail: {sender_email}
- Telefon: {sender_phone}

Kundendaten:
- Name: {customer_name}
- Adresse: {customer_address}
- E-Mail: {customer_email}

Fachliche Daten:
- Stichtag: {as_of_date}
- Zahlungsfrist bis: {settle_by_date}
- Anzahl offener Rechnungen: {invoice_count}
- Anzahl ueberfaelliger Rechnungen: {overdue_invoice_count}
- Maximal ueberfaellig seit Tagen: {max_days_overdue}
- Offener Gesamtbetrag: {total_outstanding}

Offene Rechnungen:
{invoice_lines}

Zusaetzliche Schreibanweisung:
{user_instruction}

Anforderungen:
- Gib nur den finalen Brieftext zurueck.
- Keine Markdown-Codeblocks.
- Keine JSON-Ausgabe.
- Kein Begleitkommentar vor oder nach dem Brief.
- Der Brief muss direkt versandfaehig sein.`;

const DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION =
  "Formuliere ein professionelles, freundliches und bestimmtes Anschreiben in deutscher Sprache.";

export function InspectorPanel() {
  const handlers = useFlowStore((state) => state.handlers);
  const agents = useFlowStore((state) => state.agents);
  const resources = useFlowStore((state) => state.resources);
  const flowId = useFlowStore((state) => state.flowId);
  const dirty = useFlowStore((state) => state.dirty);
  const nodes = useFlowStore((state) => state.nodes);
  const edges = useFlowStore((state) => state.edges);
  const executionState = useFlowStore((state) => state.executionState);
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
  const selectedNodeFailure =
    selectedNode ? executionState.failedNodes[selectedNode.id] ?? null : null;
  const receivableDrafting =
    selectedNode?.data.handler_name === "accounts_receivable_generate_letters"
      ? readReceivableDraftingConfig(selectedNode.data.input)
      : null;
  const [previewCustomerIndex, setPreviewCustomerIndex] = useState(0);
  const [draftPreview, setDraftPreview] = useState<AccountsReceivableDraftPreviewResponse | null>(null);
  const [draftPreviewLoading, setDraftPreviewLoading] = useState(false);
  const [draftPreviewError, setDraftPreviewError] = useState<string | null>(null);
  const [humanInputRequest, setHumanInputRequest] = useState<HumanInputRequestPayload | null>(null);
  const [humanInputValue, setHumanInputValue] = useState<unknown>(null);
  const [humanInputLoading, setHumanInputLoading] = useState(false);
  const [humanInputSubmitter, setHumanInputSubmitter] = useState("web-operator");
  const [humanInputError, setHumanInputError] = useState<string | null>(null);

  useEffect(() => {
    setPreviewCustomerIndex(0);
    setDraftPreview(null);
    setDraftPreviewError(null);
    setDraftPreviewLoading(false);
    setHumanInputRequest(null);
    setHumanInputValue(null);
    setHumanInputLoading(false);
    setHumanInputError(null);
  }, [selectedNodeId]);

  useEffect(() => {
    if (!selectedNode || !flowId || selectedNode.data.task_status !== "WAITING_FOR_INPUT") {
      setHumanInputRequest(null);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const response = await fetchHumanInputRequest(flowId, selectedNode.id);
        if (cancelled) {
          return;
        }
        setHumanInputRequest(response.request);
        setHumanInputValue(response.request.default_value ?? inferDefaultHumanInput(response.request.schema));
      } catch (error) {
        if (!cancelled) {
          setHumanInputError(
            error instanceof Error ? error.message : "Failed to load human input request",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [flowId, selectedNode]);

  const handleManualApprovalGrantedChange = async (approved: boolean) => {
    if (!selectedNode) {
      return;
    }
    const approvedBy = selectedNode.data.manual_approval.approved_by?.trim() || "Inspector Approval";
    const reason = selectedNode.data.manual_approval.reason?.trim() || null;
    if (approved && flowId && !dirty) {
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
    if (!approved && flowId && !dirty) {
      const revokedBy = selectedNode.data.manual_approval.approved_by?.trim() || "Inspector Approval";
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
      requires_manual_approval: approved ? true : selectedNode.data.requires_manual_approval,
      manual_approval: {
        ...selectedNode.data.manual_approval,
        approved,
        approved_by: approved ? approvedBy : selectedNode.data.manual_approval.approved_by,
        approved_at: approved ? new Date().toISOString() : selectedNode.data.manual_approval.approved_at,
        revoked_by: approved ? null : approvedBy,
        revoked_at: approved ? null : new Date().toISOString(),
        reason,
      },
    });
    setExecutionError(null);
  };

  const handleManualApprovalRequirementChange = (required: boolean) => {
    if (!selectedNode) {
      return;
    }
    patchNode(selectedNode, updateNodeData, {
      requires_manual_approval: required,
      manual_approval: required
        ? selectedNode.data.manual_approval
        : {
            ...selectedNode.data.manual_approval,
            approved: false,
            approved_at: null,
            revoked_by: selectedNode.data.manual_approval.approved
              ? selectedNode.data.manual_approval.approved_by?.trim() || "Inspector Approval"
              : selectedNode.data.manual_approval.revoked_by,
            revoked_at: selectedNode.data.manual_approval.approved
              ? new Date().toISOString()
              : selectedNode.data.manual_approval.revoked_at,
          },
    });
    setExecutionError(null);
  };

  const handlePreviewDraft = async () => {
    if (!selectedNode || selectedNode.data.handler_name !== "accounts_receivable_generate_letters") {
      return;
    }
    const extractNode = findReceivableExtractNode(selectedNode, nodes, edges);
    if (!extractNode) {
      const message =
        "Preview Draft requires an upstream accounts_receivable_extract node connected to this letter-generation node.";
      setDraftPreview(null);
      setDraftPreviewError(message);
      setExecutionError(message);
      return;
    }

    setDraftPreviewLoading(true);
    setDraftPreviewError(null);
    setExecutionError(null);
    try {
      const preview = await previewAccountsReceivableDraft({
        extract_input: asNodeInputObject(extractNode.data.input),
        generate_input: asNodeInputObject(selectedNode.data.input),
        customer_index: Math.max(0, previewCustomerIndex),
      });
      setDraftPreview(preview);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Preview Draft failed";
      setDraftPreview(null);
      setDraftPreviewError(message);
      setExecutionError(message);
    } finally {
      setDraftPreviewLoading(false);
    }
  };

  const handleSubmitHumanInput = async () => {
    if (!selectedNode || !flowId) {
      return;
    }
    setHumanInputLoading(true);
    setHumanInputError(null);
    try {
      const snapshot = await resumeFlowNode(flowId, selectedNode.id, {
        value: humanInputValue,
        submitted_by: humanInputSubmitter.trim() || "web-operator",
        metadata: {},
        auto_run: true,
      });
      applyFlowSnapshot(snapshot, "node.input.resumed");
      setExecutionError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Submitting human input failed";
      setHumanInputError(message);
      setExecutionError(message);
    } finally {
      setHumanInputLoading(false);
    }
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

        {selectedNodeFailure ? (
          <section className="inspector__output">
            <div className="sidebar__section-header">
              <h3>Execution failure</h3>
              <StatusBadge label="Failed" tone="failed" />
            </div>
            <pre>{selectedNodeFailure}</pre>
          </section>
        ) : null}

        {selectedNode.data.task_status === "WAITING_FOR_INPUT" ? (
          <section className="inspector__llm-card">
            <div className="sidebar__section-header">
              <h3>Human Input Required</h3>
              <StatusBadge label="Waiting" tone="paused" />
            </div>
            <p>
              {humanInputRequest?.description ??
                "Dieser Node wartet auf eine manuelle Eingabe, bevor der Flow weiterlaufen kann."}
            </p>
            {humanInputRequest?.required_role ? (
              <p className="field__hint">Erforderliche Rolle: {humanInputRequest.required_role}</p>
            ) : null}
            <NodeField
              label="Submitted by"
              value={humanInputSubmitter}
              onChange={setHumanInputSubmitter}
            />
            {renderHumanInputFields(humanInputRequest?.schema ?? {}, humanInputValue, setHumanInputValue)}
            <JsonEditor
              label={humanInputRequest?.title ?? "Input value"}
              value={humanInputValue}
              onCommit={(value) => setHumanInputValue(value)}
            />
            {humanInputError ? <p className="field__hint field__hint--error">{humanInputError}</p> : null}
            <button
              type="button"
              className="primary-button"
              onClick={() => void handleSubmitHumanInput()}
              disabled={humanInputLoading}
            >
              {humanInputLoading ? "Submitting..." : "Submit Input"}
            </button>
          </section>
        ) : null}

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

        {selectedNode.data.handler_name === "accounts_receivable_generate_letters" && receivableDrafting ? (
          <section className="inspector__llm-card">
            <div className="sidebar__section-header">
              <h3>LLM Letter Drafting</h3>
              <StatusBadge
                label={receivableDrafting.generationMode === "llm" ? "Local LLM active" : "Template mode"}
                tone={receivableDrafting.generationMode === "llm" ? "running" : "neutral"}
              />
            </div>
            <p>
              Dieser Node kann die Anschreiben entweder aus dem eingebauten Template erzeugen oder den lokalen LiteRT-Stack
              verwenden. Der Prompt unten wird beim Flow-Lauf pro Kunde an das lokale Modell gesendet.
            </p>

            <label className="checkbox-inline">
              <input
                type="checkbox"
                checked={receivableDrafting.generationMode === "llm"}
                onChange={(event) =>
                  patchNodeInputObject(selectedNode, updateNodeData, {
                    generation_mode: event.target.checked ? "llm" : "template",
                    prompt_template:
                      receivableDrafting.promptTemplate || DEFAULT_RECEIVABLE_LLM_PROMPT_TEMPLATE,
                    user_instruction:
                      receivableDrafting.userInstruction || DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION,
                  })
                }
              />
              <span>Use local LLM to draft the letter text</span>
            </label>

            <label className="field">
              <span className="field__label">Business instruction</span>
              <textarea
                className="json-editor"
                spellCheck={false}
                value={receivableDrafting.userInstruction}
                onChange={(event) =>
                  patchNodeInputObject(selectedNode, updateNodeData, {
                    user_instruction: event.target.value,
                  })
                }
              />
              <span className="field__hint">
                Hier beschreibst du fachlich, wie das lokale LLM schreiben soll: Ton, Haertegrad, Kulanz, Zahlungsziel,
                rechtliche Vorsicht.
              </span>
            </label>

            <label className="field">
              <span className="field__label">Prompt template</span>
              <textarea
                className="json-editor inspector__prompt-template"
                spellCheck={false}
                value={receivableDrafting.promptTemplate}
                onChange={(event) =>
                  patchNodeInputObject(selectedNode, updateNodeData, {
                    prompt_template: event.target.value,
                  })
                }
              />
              <span className="field__hint">
                Verfuegbare Platzhalter: {"{sender_company}"}, {"{customer_name}"}, {"{customer_address}"},{" "}
                {"{customer_email}"}, {"{total_outstanding}"}, {"{invoice_lines}"}, {"{invoice_count}"},{" "}
                {"{overdue_invoice_count}"}, {"{max_days_overdue}"}, {"{as_of_date}"}, {"{settle_by_date}"},{" "}
                {"{user_instruction}"}, {"{customer_json}"}, {"{invoices_json}"}.
              </span>
            </label>

            <div className="inspector__llm-actions">
              <button
                type="button"
                className="ghost-button"
                onClick={() =>
                  patchNodeInputObject(selectedNode, updateNodeData, {
                    generation_mode: "llm",
                    prompt_template: DEFAULT_RECEIVABLE_LLM_PROMPT_TEMPLATE,
                    user_instruction:
                      receivableDrafting.userInstruction || DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION,
                  })
                }
              >
                Insert Default Prompt
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => void handlePreviewDraft()}
                disabled={draftPreviewLoading}
              >
                {draftPreviewLoading ? "Generating Preview..." : "Preview Draft"}
              </button>
            </div>
            <p className="field__hint">
              Die Vorschau ist bewusst zeitlich begrenzt. Wenn das lokale Modell nicht rechtzeitig antwortet, bricht die
              Web-UI den Request ab und du kannst den Prompt verkuerzen oder auf Template-Modus zurueckschalten.
            </p>

            <NumericField
              label="Preview customer index"
              value={previewCustomerIndex}
              onChange={(value) => setPreviewCustomerIndex(Math.max(0, Math.floor(value)))}
            />
            <p className="field__hint">
              `0` bedeutet der erste Kunde mit offenen Forderungen. Erhoehe den Wert, um einen anderen Kunden aus dem
              aktuellen Datenbestand zu pruefen.
            </p>

            <label className="checkbox-inline">
              <input
                type="checkbox"
                checked={receivableDrafting.fallbackToTemplateOnError}
                onChange={(event) =>
                  patchNodeInputObject(selectedNode, updateNodeData, {
                    fallback_to_template_on_error: event.target.checked,
                  })
                }
              />
              <span>Fallback to built-in template if the local LLM fails</span>
            </label>

            {draftPreviewError ? <p className="field__hint field__hint--error">{draftPreviewError}</p> : null}

            {draftPreview ? (
              <section className="inspector__preview-card">
                <div className="sidebar__section-header">
                  <h3>Draft preview</h3>
                  <StatusBadge
                    label={draftPreview.generation_mode.toUpperCase()}
                    tone={draftPreview.generation_mode === "llm" ? "running" : "neutral"}
                  />
                </div>
                <p className="inspector__preview-meta">
                  Kunde: {draftPreview.customer_name} | Offene Kunden insgesamt: {draftPreview.source_summary.customer_count}
                </p>
                {draftPreview.prompt ? (
                  <>
                    <h4 className="inspector__preview-heading">Resolved prompt</h4>
                    <pre className="inspector__preview-block">{draftPreview.prompt}</pre>
                  </>
                ) : null}
                <h4 className="inspector__preview-heading">Generated letter</h4>
                <pre className="inspector__preview-block">{draftPreview.letter}</pre>
                {draftPreview.warnings.length > 0 ? (
                  <>
                    <h4 className="inspector__preview-heading">Warnings</h4>
                    <ul className="inspector__docs-list">
                      {draftPreview.warnings.map((warning, index) => (
                        <li key={`preview-warning-${index}`}>{warning}</li>
                      ))}
                    </ul>
                  </>
                ) : null}
              </section>
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
              onChange={(event) => handleManualApprovalRequirementChange(event.target.checked)}
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

          <label className="checkbox-inline">
            <input
              type="checkbox"
              checked={selectedNode.data.requires_manual_approval && selectedNode.data.manual_approval.approved}
              disabled={!selectedNode.data.requires_manual_approval}
              onChange={(event) => void handleManualApprovalGrantedChange(event.target.checked)}
            />
            <span>Approval granted</span>
          </label>

          <div className="inspector__approval-status">
            <StatusBadge
              label={
                !selectedNode.data.requires_manual_approval
                  ? "Not required"
                  : selectedNode.data.manual_approval.approved
                    ? "Approved"
                    : "Pending"
              }
              tone={
                !selectedNode.data.requires_manual_approval
                  ? "neutral"
                  : selectedNode.data.manual_approval.approved
                    ? "success"
                    : "paused"
              }
            />
            {selectedNode.data.manual_approval.approved && selectedNode.data.manual_approval.approved_at ? (
              <span>Approved at: {selectedNode.data.manual_approval.approved_at}</span>
            ) : null}
            {!selectedNode.data.manual_approval.approved && selectedNode.data.manual_approval.revoked_at ? (
              <span>Revoked at: {selectedNode.data.manual_approval.revoked_at}</span>
            ) : null}
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
        {executionState.flowState === "FAILED" ? (
          <section className="inspector__output">
            <div className="sidebar__section-header">
              <h3>Last flow failure</h3>
              <StatusBadge label="Failed" tone="failed" />
            </div>
            <p>
              Persisted flow ID: <strong>{flowId ?? "unsaved"}</strong>
            </p>
            {executionState.failureDetails.length > 0 ? (
              <ul className="inspector__docs-list">
                {executionState.failureDetails.map((detail, index) => (
                  <li key={`failure-detail-${index}`}>{detail}</li>
                ))}
              </ul>
            ) : (
              <p>{executionState.error ?? "The flow failed without a surfaced detail."}</p>
            )}
          </section>
        ) : null}
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

function patchNodeInputObject(
  node: TaskFlowNode,
  updateNodeData: (nodeId: string, updater: (node: TaskFlowNode) => TaskFlowNode) => void,
  patch: Record<string, unknown>,
) {
  patchNode(node, updateNodeData, {
    input: {
      ...asNodeInputObject(node.data.input),
      ...patch,
    },
  });
}

function findReceivableExtractNode(
  letterNode: TaskFlowNode,
  nodes: TaskFlowNode[],
  edges: TaskFlowEdge[],
): TaskFlowNode | null {
  const incomingSources = edges
    .filter((edge) => edge.target === letterNode.id)
    .map((edge) => edge.source);
  const connectedExtractNode =
    nodes.find(
      (node) =>
        incomingSources.includes(node.id) &&
        node.data.handler_name === "accounts_receivable_extract",
    ) ?? null;
  if (connectedExtractNode) {
    return connectedExtractNode;
  }
  return nodes.find((node) => node.data.handler_name === "accounts_receivable_extract") ?? null;
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

function asNodeInputObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? ({ ...(value as Record<string, unknown>) } as Record<string, unknown>)
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

function readReceivableDraftingConfig(input: unknown): {
  generationMode: string;
  promptTemplate: string;
  userInstruction: string;
  fallbackToTemplateOnError: boolean;
} {
  const payload = asNodeInputObject(input);
  return {
    generationMode:
      typeof payload.generation_mode === "string" && payload.generation_mode.trim()
        ? payload.generation_mode.trim().toLowerCase()
        : "template",
    promptTemplate:
      typeof payload.prompt_template === "string" && payload.prompt_template.trim()
        ? payload.prompt_template
        : DEFAULT_RECEIVABLE_LLM_PROMPT_TEMPLATE,
    userInstruction:
      typeof payload.user_instruction === "string" && payload.user_instruction.trim()
        ? payload.user_instruction
        : DEFAULT_RECEIVABLE_LLM_USER_INSTRUCTION,
    fallbackToTemplateOnError:
      typeof payload.fallback_to_template_on_error === "boolean"
        ? payload.fallback_to_template_on_error
        : true,
  };
}

function inferDefaultHumanInput(schema: Record<string, unknown>): unknown {
  const schemaType = typeof schema.type === "string" ? schema.type : null;
  if (schemaType === "object") {
    return {};
  }
  if (schemaType === "array") {
    return [];
  }
  if (schemaType === "boolean") {
    return false;
  }
  if (schemaType === "number" || schemaType === "integer") {
    return 0;
  }
  return "";
}

function renderHumanInputFields(
  schema: Record<string, unknown>,
  value: unknown,
  setValue: (next: unknown) => void,
) {
  const schemaType = typeof schema.type === "string" ? schema.type : null;
  const properties =
    schemaType === "object" && schema.properties && typeof schema.properties === "object"
      ? (schema.properties as Record<string, unknown>)
      : null;
  if (!properties || Object.keys(properties).length === 0) {
    return null;
  }
  const current = asObject(value);
  return (
    <div className="inspector__structured-input">
      {Object.entries(properties).map(([key, definition]) => {
        const property = asObject(definition);
        const propertyType = typeof property.type === "string" ? property.type : "string";
        const label = typeof property.title === "string" ? property.title : key;
        if (propertyType === "boolean") {
          return (
            <label key={key} className="checkbox-inline">
              <input
                type="checkbox"
                checked={Boolean(current[key])}
                onChange={(event) =>
                  setValue({
                    ...current,
                    [key]: event.target.checked,
                  })
                }
              />
              <span>{label}</span>
            </label>
          );
        }
        if (propertyType === "number" || propertyType === "integer") {
          return (
            <NumericField
              key={key}
              label={label}
              value={typeof current[key] === "number" ? Number(current[key]) : 0}
              onChange={(next) =>
                setValue({
                  ...current,
                  [key]: next,
                })
              }
            />
          );
        }
        return (
          <NodeField
            key={key}
            label={label}
            value={typeof current[key] === "string" ? current[key] : String(current[key] ?? "")}
            onChange={(next) =>
              setValue({
                ...current,
                [key]: next,
              })
            }
          />
        );
      })}
    </div>
  );
}

function statusTone(status: string): "neutral" | "running" | "success" | "failed" | "paused" {
  if (status === "RUNNING") return "running";
  if (status === "WAITING_FOR_INPUT") return "paused";
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
