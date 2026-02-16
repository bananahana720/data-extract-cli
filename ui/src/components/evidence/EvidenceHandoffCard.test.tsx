import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceHandoffCard } from "./EvidenceHandoffCard";

describe("EvidenceHandoffCard", () => {
  it("transitions readiness states across ready, stale, missing, and in-progress", () => {
    const baseProps = {
      title: "Evidence Handoff",
      what: "Input files and metadata",
      why: "Preserve traceability and audit confidence",
      how: "Verify checksums and source linkage"
    };

    const { rerender } = render(<EvidenceHandoffCard {...baseProps} state="ready" />);

    expect(screen.getByText("Readiness: Ready")).toBeInTheDocument();
    expect(screen.getByText("Evidence handoff is aligned and ready for execution.")).toBeInTheDocument();
    expect(screen.queryByText("Remediation Hints")).not.toBeInTheDocument();

    rerender(
      <EvidenceHandoffCard
        {...baseProps}
        state="stale"
        remediationHints={["Refresh evidence snapshot before launch."]}
      />
    );
    expect(screen.getByText("Readiness: Stale")).toBeInTheDocument();
    expect(screen.getByText("Evidence has drifted from current runtime intent.")).toBeInTheDocument();
    expect(screen.getByText("Remediation Hints")).toBeInTheDocument();
    expect(screen.getByText("Refresh evidence snapshot before launch.")).toBeInTheDocument();

    rerender(
      <EvidenceHandoffCard
        {...baseProps}
        state="missing"
        actionHints={["Notify operator and halt run start."]}
      />
    );
    expect(screen.getByText("Readiness: Missing")).toBeInTheDocument();
    expect(screen.getByText("Required evidence inputs are missing and need remediation.")).toBeInTheDocument();
    expect(screen.getByText("Action Hints")).toBeInTheDocument();
    expect(screen.getByText("Notify operator and halt run start.")).toBeInTheDocument();

    rerender(
      <EvidenceHandoffCard
        {...baseProps}
        state="in-progress"
        summary="Evidence checks are currently running."
      />
    );
    expect(screen.getByText("Readiness: In Progress")).toBeInTheDocument();
    expect(screen.getByText("Evidence checks are currently running.")).toBeInTheDocument();
  });
});
