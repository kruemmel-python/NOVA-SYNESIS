interface StatusBadgeProps {
  label: string;
  tone?: "neutral" | "running" | "success" | "failed" | "paused";
}

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge--${tone}`}>
      <span className="status-badge__dot" />
      {label}
    </span>
  );
}
