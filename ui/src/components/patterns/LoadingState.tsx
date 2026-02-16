import { useId, type HTMLAttributes, type ReactNode } from "react";

export type LoadingStateSize = "sm" | "md" | "lg";

export interface LoadingStateProps extends HTMLAttributes<HTMLDivElement> {
  label?: ReactNode;
  description?: ReactNode;
  size?: LoadingStateSize;
  inline?: boolean;
}

function cx(...values: Array<string | undefined | false>): string {
  return values.filter(Boolean).join(" ");
}

export function LoadingState(props: LoadingStateProps) {
  const {
    label = "Loading",
    description,
    size = "md",
    inline = false,
    className,
    role,
    children,
    ...divProps
  } = props;
  const labelId = useId();
  const resolvedDescription = description ?? children;

  return (
    <div
      {...divProps}
      className={cx(
        "loading-state",
        `loading-state--${size}`,
        inline && "loading-state--inline",
        className
      )}
      role={role ?? "status"}
      aria-live={divProps["aria-live"] ?? "polite"}
      aria-busy={divProps["aria-busy"] ?? true}
      aria-labelledby={labelId}
    >
      <span className="loading-state__spinner" aria-hidden="true" />
      <div className="loading-state__body">
        <p id={labelId} className="loading-state__label">
          {label}
        </p>
        {resolvedDescription ? (
          <div className="loading-state__description">{resolvedDescription}</div>
        ) : null}
      </div>
    </div>
  );
}
