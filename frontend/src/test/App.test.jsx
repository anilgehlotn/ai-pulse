import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "../App.jsx";
import { getToken, setToken } from "../api.js";
import { fakeServer } from "./fakeServer.js";
import { NORTHWIND_DASHBOARD, REVIEW_QUEUE } from "./fixtures.js";

const ASHA = {
  name: "Asha Rao",
  email: "asha@northwind.test",
  organizations: [{ org_id: 1, org_name: "Northwind Logistics", role: "admin" }],
  selected_org: { org_id: 1, org_name: "Northwind Logistics", role: "admin" },
};

describe("App session", () => {
  it("restores the user and organization after a refresh", async () => {
    setToken("saved-token");
    fakeServer({ "GET /auth/me": { body: ASHA }, "GET /dashboard": { body: NORTHWIND_DASHBOARD } });
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Hello, Asha" })).toBeInTheDocument();
    expect(screen.getAllByText("Northwind Logistics").length).toBeGreaterThan(0);
    expect(screen.getByText("Asha Rao")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
    expect(screen.queryByRole("button", { name: "Switch organization" })).toBeNull(); // only one org
  });

  it("goes back to login with a message when the token has expired", async () => {
    setToken("expired-token");
    fakeServer({ "GET /auth/me": { status: 401, body: { detail: "Invalid token" } } });
    render(<App />);
    expect(await screen.findByText("Your session expired. Please sign in again.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sign in to AI Pulse" })).toBeInTheDocument();
    expect(getToken()).toBe(null);
  });

  it("takes a reviewer straight to the review queue, with no dashboard tab", async () => {
    setToken("saved-token");
    const org = { org_id: 1, org_name: "Northwind Logistics", role: "reviewer" };
    fakeServer({
      "GET /auth/me": { body: { name: "Sunil Batra", organizations: [org], selected_org: org } },
      "GET /review/queue": { body: REVIEW_QUEUE },
    });
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Review" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review" })).toHaveAttribute("aria-current", "page");
    expect(screen.queryByRole("button", { name: "Dashboard" })).toBeNull();
    expect(screen.getByText("Reviewer")).toBeInTheDocument();
  });
});
