import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import Dashboard from "../pages/Dashboard.jsx";
import { fakeServer } from "./fakeServer.js";
import { BLUEPEAK_DASHBOARD, NORTHWIND_DASHBOARD } from "./fixtures.js";

function showDashboard(body) {
  fakeServer({ "GET /dashboard": { body } });
  render(<Dashboard />);
}

describe("Dashboard", () => {
  it("shows the backend's reason and no numbers when the overall figure is hidden", async () => {
    showDashboard(BLUEPEAK_DASHBOARD);
    const overall = await screen.findByRole("region", { name: "Whole organization" });
    expect(overall).toHaveTextContent(BLUEPEAK_DASHBOARD.overall.reason);
    expect(overall.textContent).not.toMatch(/\d/);
  });

  it("shows only the message on a hidden group row", async () => {
    showDashboard(BLUEPEAK_DASHBOARD);
    const table = await screen.findByRole("table", { name: "Teams" });
    const row = within(table).getByRole("row", { name: /Other teams/ });
    const cells = within(row).getAllByRole("cell");
    expect(cells.map((c) => c.textContent)).toEqual(["Hidden", "3 teams hidden to protect anonymity"]);
  });

  it("lists Exposed teams under Act first", async () => {
    showDashboard(NORTHWIND_DASHBOARD);
    const actFirst = await screen.findByRole("region", { name: "Act first" });
    expect(actFirst).toHaveTextContent("Sales");
    expect(actFirst).toHaveTextContent("Uses AI often (3.2) but safety habits are low (2.2)");
  });

  it("hides Act first when no team is Exposed", async () => {
    showDashboard(BLUEPEAK_DASHBOARD);
    await screen.findByRole("table", { name: "Teams" });
    expect(screen.queryByRole("region", { name: "Act first" })).toBeNull();
  });

  it("shows 'fewer than 5' as text, never as a number", async () => {
    showDashboard(NORTHWIND_DASHBOARD);
    const overall = await screen.findByRole("region", { name: "Whole organization" });
    expect(within(overall).getAllByText("fewer than 5").length).toBe(1);  // awaiting review
    const risks = screen.getByRole("region", { name: "Top risks" });
    expect(within(risks).getAllByText("fewer than 5").length).toBe(3);
  });

  it("replaces the KPI row with the reason, and shows no figures anywhere, when the overall is hidden", async () => {
    showDashboard(BLUEPEAK_DASHBOARD);
    const overall = await screen.findByRole("region", { name: "Whole organization" });
    expect(within(overall).getByText("Organization totals are hidden")).toBeInTheDocument();
    expect(within(overall).queryByText("Respondents")).toBeNull();
    expect(screen.queryByRole("region", { name: "Maturity" })).toBeNull();
    expect(screen.queryByRole("region", { name: "Top risks" })).toBeNull();
    expect(screen.queryByRole("img", { name: /Average score/ })).toBeNull();
  });

  it("shows the backend's KPI values unchanged", async () => {
    const overall = { ...NORTHWIND_DASHBOARD.overall, respondents: 16, average_score: 2.95, awaiting_review: 7 };
    showDashboard({ ...NORTHWIND_DASHBOARD, overall });
    const tiles = await screen.findByRole("region", { name: "Whole organization" });
    expect(within(tiles).getByText("16")).toBeInTheDocument();
    expect(within(tiles).getByText("2.95")).toBeInTheDocument();   // not rounded to 3.0 or 3
    expect(within(tiles).getByText("Exploring")).toBeInTheDocument();
    expect(within(tiles).getByText("7")).toBeInTheDocument();
    const maturity = screen.getByRole("region", { name: "Maturity" });
    expect(within(maturity).getByText("2.95")).toBeInTheDocument();
  });

  it("says so calmly when no team needs urgent action", async () => {
    showDashboard({ ...NORTHWIND_DASHBOARD, act_first: [] });
    const actFirst = await screen.findByRole("region", { name: "Act first" });
    expect(actFirst).toHaveTextContent("No team needs urgent action.");
  });

  it("shows an error when the dashboard cannot be loaded", async () => {
    fakeServer({ "GET /dashboard": { status: 403, body: { detail: "Admins only" } } });
    render(<Dashboard />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Admins only");
  });
});
