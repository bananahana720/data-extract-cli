import { useId, type HTMLAttributes, type ReactNode } from "react";

export type FeedbackBannerTone = "success" | "warning" | "error" | "info";

export interface FeedbackBannerProps extends Omit<HTMLAttributes<HTMLDivElement>, "title"> {
  tone?: FeedbackBannerTone;
  title?: ReactNode;
  message?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  liveRegion?: "off" | "polite" | "assertive";
}

function cx(...values: Array<string | undefined | false>): string {
  return values.filter(Boolean).join(" ");
}

export function FeedbackBanner(props: FeedbackBannerProps) {
  const {
    tone = "info",
    title,
    message,
    icon,
    actions,
    className,
    role,
    liveRegion,
    children,
    ...divProps
  } = props;
  const headingId = useId();
  const messageId = useId();
  const resolvedMessage = message ?? children;
  const resolvedRole = role ?? (tone === "error" ? "alert" : "status");
  const resolvedLiveRegion = liveRegion ?? (tone === "error" ? "assertive" : "polite");
  const resolvedLabelledBy = cx(divProps["aria-labelledby"], title ? headingId : undefined) || undefined;
  const resolvedDescribedBy =
    cx(divProps["aria-describedby"], resolvedMessage ? messageId : undefined) || undefined;

  return (
    <div
      {...divProps}
      className={cx("feedback-banner", `feedback-banner--${tone}`, className)}
      role={resolvedRole}
      aria-live={resolvedLiveRegion}
      aria-atomic={divProps["aria-atomic"] ?? "true"}
      aria-labelledby={resolvedLabelledBy}
      aria-describedby={resolvedDescribedBy}
    >
      {icon ? (
        <div className="feedback-banner__icon" aria-hidden="true">
          {icon}
        </div>
      ) : null}
      <div className="feedback-banner__body">
        {title ? <h3 id={headingId} className="feedback-banner__title">{title}</h3> : null}
        {resolvedMessage ? (
          <div id={messageId} className="feedback-banner__message">
            {resolvedMessage}
          </div>
        ) : null}
      </div>
      {actions ? <div className="feedback-banner__actions">{actions}</div> : null}
    </div>
  );
}
