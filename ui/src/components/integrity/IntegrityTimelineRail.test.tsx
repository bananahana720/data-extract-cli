import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { IntegrityTimelineRail, type IntegrityTimelineEntry } from "./IntegrityTimelineRail";

const events: IntegrityTimelineEntry[] = [
  {
    id: "event-queued",
    title: "Queued",
    occurredAt: "2026-02-14T10:00:00.000Z",
    detail: "Run was queued for processing.",
    severity: "info",
    remediation: "Monitor queue depth."
  },
  {
    id: "event-running",
    title: "Running",
    occurredAt: "2026-02-14T10:01:00.000Z",
    detail: "Workers started extraction.",
    severity: "success",
    remediation: "No action required."
  },
  {
    id: "event-review",
    title: "Needs review",
    occurredAt: "2026-02-14T10:02:00.000Z",
    detail: "Output warning threshold reached.",
    severity: "warning",
    remediation: "Review anomaly details before release."
  },
  {
    id: "event-failure",
    title: "Failure",
    occurredAt: "2026-02-14T10:03:00.000Z",
    detail: "Final stage failed integrity checks.",
    severity: "error",
    remediation: "Fix source input and retry."
  }
];

describe("IntegrityTimelineRail", () => {
  it("renders severity labels for each event and preserves timeline order", () => {
    render(<IntegrityTimelineRail events={events} />);

    expect(screen.getByTestId("integrity-timeline-rail")).toBeVisible();
    expect(screen.getAllByRole("listitem")).toHaveLength(events.length);
    expect(screen.getByText("Info")).toBeInTheDocument();
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("Needs Review")).toBeInTheDocument();
    expect(screen.getAllByText("Failure").length).toBeGreaterThan(0);
  });

  it("supports basic event navigation using stable item test ids", () => {
    render(<IntegrityTimelineRail events={events} itemTestIdPrefix="timeline-event-" />);

    events.forEach((event, index) => {
      const item = screen.getByTestId(`timeline-event-${index}`);
      expect(within(item).getByRole("heading", { name: event.title })).toBeInTheDocument();
      expect(within(item).getByText(event.detail)).toBeInTheDocument();
      expect(within(item).getByText(event.remediation)).toBeInTheDocument();
      expect(item.querySelector(`time[datetime="${event.occurredAt}"]`)).not.toBeNull();
    });

    const first = screen.getByTestId("timeline-event-0");
    const second = screen.getByTestId("timeline-event-1");
    expect(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
