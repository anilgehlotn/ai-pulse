import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import RingGauge from "../components/RingGauge.jsx";

function arc(container) {
  return container.querySelector(".ring-arc");
}

describe("RingGauge", () => {
  it("shows the value it is given, unchanged", () => {
    const { container } = render(<RingGauge value={2.9} label="Average score" />);
    expect(screen.getByText("2.9")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Average score: 2.9 out of 5" })).toBeInTheDocument();
    expect(arc(container)).toHaveAttribute("stroke-dasharray", "47.5 100");
  });

  it("keeps the arc between an empty ring (1) and a full ring (5)", () => {
    const { container, rerender } = render(<RingGauge value={7} label="Average score" />);
    expect(arc(container)).toHaveAttribute("stroke-dasharray", "100 100");
    expect(screen.getByText("7")).toBeInTheDocument(); // the number itself is never clamped
    rerender(<RingGauge value={0} label="Average score" />);
    expect(arc(container)).toHaveAttribute("stroke-dasharray", "0 100");
    rerender(<RingGauge value={5} label="Average score" />);
    expect(arc(container)).toHaveAttribute("stroke-dasharray", "100 100");
  });

  it("draws no arc and a dash when there is no value", () => {
    const { container } = render(<RingGauge value={null} label="Average score" />);
    expect(arc(container)).toBeNull();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
