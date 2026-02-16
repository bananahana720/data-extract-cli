import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GuidedRunBuilderShell } from "./GuidedRunBuilderShell";

describe("GuidedRunBuilderShell", () => {
  it("renders the guided progression shell with context, builder, and verify content", () => {
    render(
      <GuidedRunBuilderShell
        eyebrow="Guided Flow"
        title="Create New Run"
        subtitle="Progress from context to verification."
        contextPanel={<section data-testid="context-panel">Step 1: Context</section>}
        builderPanel={<section data-testid="builder-panel">Step 2: Configure</section>}
        verifyPanel={<section data-testid="verify-panel">Step 3: Verify</section>}
      />
    );

    expect(screen.getByText("Guided Flow")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Create New Run" })).toBeInTheDocument();
    expect(screen.getByText("Progress from context to verification.")).toBeInTheDocument();
    expect(screen.getByTestId("context-panel")).toBeVisible();
    expect(screen.getByTestId("builder-panel")).toBeVisible();
    expect(screen.getByTestId("verify-panel")).toBeVisible();
  });

  it("keeps locked builder controls intact while verify remains visible", () => {
    render(
      <GuidedRunBuilderShell
        title="Progressive Run Setup"
        subtitle="Step 2 is locked until Step 1 completes."
        contextPanel={<section data-testid="context-panel">Context completed</section>}
        builderPanel={
          <button type="button" data-testid="builder-next" disabled>
            Continue to next step
          </button>
        }
        verifyPanel={<section data-testid="verify-panel">Verify section always available</section>}
      />
    );

    const contextPanel = screen.getByTestId("context-panel");
    const builderButton = screen.getByTestId("builder-next");

    expect(builderButton).toBeDisabled();
    expect(screen.getByTestId("verify-panel")).toBeVisible();
    expect(
      contextPanel.compareDocumentPosition(builderButton) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
  });
});
