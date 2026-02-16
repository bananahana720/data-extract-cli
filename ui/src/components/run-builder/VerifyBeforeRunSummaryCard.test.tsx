import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { VerifyBeforeRunSummaryCard, type VerifyBeforeRunSummaryCardProps } from "./VerifyBeforeRunSummaryCard";

const baseEntries: VerifyBeforeRunSummaryCardProps["summaryEntries"] = [
  { label: "Source Mode", value: "Local Path" },
  { label: "Chunk Size", value: "512" }
];

function renderCard(overrideProps: Partial<VerifyBeforeRunSummaryCardProps> = {}) {
  const onAcknowledgedChange = vi.fn();
  const props: VerifyBeforeRunSummaryCardProps = {
    summaryEntries: baseEntries,
    blockingIssues: [],
    acknowledged: false,
    onAcknowledgedChange,
    ...overrideProps
  };

  const rendered = render(<VerifyBeforeRunSummaryCard {...props} />);
  return { ...rendered, onAcknowledgedChange };
}

describe("VerifyBeforeRunSummaryCard", () => {
  it("renders blocked state and reports acknowledgement changes", () => {
    const { onAcknowledgedChange } = renderCard({
      blockingIssues: ["Local Path is selected but Input Path is empty.", "Chunk Size must be numeric and at least 32."]
    });

    expect(screen.getByText("Blocked (2)")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Blocking Reasons");
    expect(screen.getByText("Local Path is selected but Input Path is empty.")).toBeInTheDocument();
    expect(screen.getByText("Chunk Size must be numeric and at least 32.")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("new-run-verify-ack"));
    expect(onAcknowledgedChange).toHaveBeenCalledWith(true);
  });

  it("transitions across pending, ready, blocked, and stale acknowledgement states", () => {
    const { rerender } = renderCard();

    expect(screen.getByText("Pending Verify")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Validation Clear");
    expect(screen.queryByTestId("new-run-verify-stale-note")).not.toBeInTheDocument();

    rerender(
      <VerifyBeforeRunSummaryCard
        summaryEntries={baseEntries}
        blockingIssues={[]}
        acknowledged={true}
        onAcknowledgedChange={vi.fn()}
      />
    );
    expect(screen.getByText("Verified")).toBeInTheDocument();

    rerender(
      <VerifyBeforeRunSummaryCard
        summaryEntries={baseEntries}
        blockingIssues={["Upload Files/Folder is selected but no files are attached."]}
        acknowledged={true}
        onAcknowledgedChange={vi.fn()}
      />
    );
    expect(screen.getByText("Blocked (1)")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Blocking Reasons");

    rerender(
      <VerifyBeforeRunSummaryCard
        summaryEntries={baseEntries}
        blockingIssues={["Upload Files/Folder is selected but no files are attached."]}
        acknowledged={false}
        staleAcknowledgementMessage="Verification reset because run inputs changed."
        onAcknowledgedChange={vi.fn()}
      />
    );
    expect(screen.getByTestId("new-run-verify-stale-note")).toHaveTextContent(
      "Verification reset because run inputs changed."
    );
  });
});
