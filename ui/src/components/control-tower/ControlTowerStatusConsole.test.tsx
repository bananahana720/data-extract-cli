import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ControlTowerStatusConsole } from "./ControlTowerStatusConsole";

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location-probe">{`${location.pathname}${location.search}`}</div>;
}

describe("ControlTowerStatusConsole", () => {
  it("wires action chips for click, disabled, internal link, and external link behavior", () => {
    const onRefresh = vi.fn();
    const onDisabledRetry = vi.fn();

    render(
      <MemoryRouter initialEntries={["/jobs"]}>
        <ControlTowerStatusConsole
          title="Control Tower"
          statusLabel="Monitoring"
          metrics={[
            {
              id: "jobs-total",
              label: "Jobs",
              value: "12",
              detail: "4 active runs"
            }
          ]}
          actionChips={[
            {
              id: "refresh",
              label: "Refresh",
              onClick: onRefresh,
              ariaLabel: "refresh status"
            },
            {
              id: "retry-disabled",
              label: "Retry",
              onClick: onDisabledRetry,
              disabled: true,
              ariaLabel: "retry disabled"
            },
            {
              id: "disabled-link",
              label: "Disabled link",
              href: "/jobs?status=running",
              disabled: true,
              ariaLabel: "disabled link"
            },
            {
              id: "job-link",
              label: "Job details",
              href: "/jobs/demo-run"
            },
            {
              id: "docs-link",
              label: "Runbook",
              href: "https://example.com/runbook"
            }
          ]}
        />
        <LocationProbe />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByLabelText("refresh status"));
    expect(onRefresh).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByLabelText("retry disabled"));
    expect(onDisabledRetry).not.toHaveBeenCalled();

    expect(screen.getByTestId("location-probe")).toHaveTextContent("/jobs");
    fireEvent.click(screen.getByLabelText("disabled link"));
    expect(screen.getByTestId("location-probe")).toHaveTextContent("/jobs");
    expect(screen.queryByRole("link", { name: "Disabled link" })).not.toBeInTheDocument();

    const internalLink = screen.getByRole("link", { name: "Job details" });
    expect(internalLink).toHaveAttribute("href", "/jobs/demo-run");

    const externalLink = screen.getByRole("link", { name: "Runbook" });
    expect(externalLink).toHaveAttribute("href", "https://example.com/runbook");
    expect(externalLink).toHaveAttribute("target", "_blank");
    expect(externalLink).toHaveAttribute("rel", "noreferrer");
  });
});
