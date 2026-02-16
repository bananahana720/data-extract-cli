import { useId, type HTMLAttributes, type ReactNode } from "react";

export interface EmptyStateProps extends Omit<HTMLAttributes<HTMLDivElement>, "title"> {
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  primaryAction?: ReactNode;
  secondaryAction?: ReactNode;
}

function cx(...values: Array<string | undefined | false>): string {
  return values.filter(Boolean).join(" ");
}

export function EmptyState(props: EmptyStateProps) {
  const {
    title,
    description,
    icon,
    primaryAction,
    secondaryAction,
    className,
    role,
    children,
    ...divProps
  } = props;
  const headingId = useId();
  const hasActions = Boolean(primaryAction) || Boolean(secondaryAction);

  return (
    <div
      {...divProps}
      className={cx("empty-state-pattern", className)}
      role={role ?? "status"}
      aria-live={divProps["aria-live"] ?? "polite"}
      aria-labelledby={headingId}
    >
      {icon ? (
        <div className="empty-state-pattern__icon" aria-hidden="true">
          {icon}
        </div>
      ) : null}
      <h3 id={headingId} className="empty-state-pattern__title">
        {title}
      </h3>
      {description ? <div className="empty-state-pattern__description">{description}</div> : null}
      {children ? <div className="empty-state-pattern__content">{children}</div> : null}
      {hasActions ? (
        <div className="empty-state-pattern__actions">
          {primaryAction}
          {secondaryAction}
        </div>
      ) : null}
    </div>
  );
}
