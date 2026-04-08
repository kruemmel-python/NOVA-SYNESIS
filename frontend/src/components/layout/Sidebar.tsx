import { useMemo, useState } from "react";

import { StatusBadge } from "../common/StatusBadge";
import { useFlowStore } from "../../store/useFlowStore";

export function Sidebar() {
  const [query, setQuery] = useState("");
  const handlers = useFlowStore((state) => state.handlers);
  const agents = useFlowStore((state) => state.agents);
  const resources = useFlowStore((state) => state.resources);

  const filteredHandlers = useMemo(
    () =>
      handlers.filter((handler) =>
        handler.toLowerCase().includes(query.trim().toLowerCase()),
      ),
    [handlers, query],
  );

  return (
    <aside className="sidebar panel">
      <div className="panel__header">
        <div>
          <p className="eyebrow">Catalog</p>
          <h2>Execution Parts</h2>
        </div>
      </div>

      <label className="field">
        <span className="field__label">Filter handlers</span>
        <input
          className="text-input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search handler names"
        />
      </label>

      <section className="sidebar__section">
        <div className="sidebar__section-header">
          <h3>Handlers</h3>
          <StatusBadge label={`${filteredHandlers.length}`} />
        </div>
        <div className="sidebar__stack">
          {filteredHandlers.map((handler) => (
            <button
              key={handler}
              type="button"
              draggable
              className="palette-item"
              onDragStart={(event) => {
                event.dataTransfer.setData("application/ao-handler", handler);
                event.dataTransfer.effectAllowed = "move";
              }}
            >
              <span className="palette-item__title">{handler}</span>
              <span className="palette-item__hint">Drag onto canvas</span>
            </button>
          ))}
        </div>
      </section>

      <section className="sidebar__section">
        <div className="sidebar__section-header">
          <h3>Agents</h3>
          <StatusBadge label={`${agents.length}`} />
        </div>
        <div className="sidebar__stack">
          {agents.map((agent) => (
            <article key={agent.agent_id} className="catalog-card">
              <header>
                <strong>{agent.name}</strong>
                <span>{agent.role}</span>
              </header>
              <p>{agent.capabilities.map((capability) => capability.name).join(", ") || "No capabilities"}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="sidebar__section">
        <div className="sidebar__section-header">
          <h3>Resources</h3>
          <StatusBadge label={`${resources.length}`} />
        </div>
        <div className="sidebar__stack">
          {resources.map((resource) => (
            <article key={resource.resource_id} className="catalog-card">
              <header>
                <strong>{resource.type}</strong>
                <span>#{resource.resource_id}</span>
              </header>
              <p>{resource.endpoint}</p>
            </article>
          ))}
        </div>
      </section>
    </aside>
  );
}
