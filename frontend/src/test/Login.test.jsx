import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Login from "../pages/Login.jsx";
import { fakeServer } from "./fakeServer.js";

describe("Login", () => {
  it("shows the server's rate-limit message as it is", async () => {
    fakeServer({
      "POST /auth/login": { status: 429, body: { detail: "Too many attempts. Try again in 15 minutes." } },
    });
    const onLoggedIn = vi.fn();
    const user = userEvent.setup();
    render(<Login notice="" onLoggedIn={onLoggedIn} />);

    await user.type(screen.getByLabelText("Email"), "asha@northwind.test");
    await user.type(screen.getByLabelText("Password"), "pulse123");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Too many attempts. Try again in 15 minutes.");
    expect(onLoggedIn).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled(); // they can try again later
  });

  it("hides the demo accounts in a production build", () => {
    vi.stubEnv("DEV", false);
    render(<Login notice="" onLoggedIn={vi.fn()} />);

    expect(screen.queryByRole("heading", { name: "Demo accounts" })).not.toBeInTheDocument();
  });

  it("shows the demo accounts in a production build when VITE_SHOW_DEMO_ACCOUNTS is true", async () => {
    vi.stubEnv("DEV", false);
    vi.stubEnv("VITE_SHOW_DEMO_ACCOUNTS", "true");
    const user = userEvent.setup();
    render(<Login notice="" onLoggedIn={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "Demo accounts" })).toBeInTheDocument();
    expect(screen.getByText("Reviewer: human review queue")).toBeInTheDocument();

    // Clicking an account fills in the form.
    await user.click(screen.getByRole("button", { name: "reviewer@northwind.test" }));
    expect(screen.getByLabelText("Email")).toHaveValue("reviewer@northwind.test");
    expect(screen.getByLabelText("Password")).toHaveValue("pulse123");
  });
});
