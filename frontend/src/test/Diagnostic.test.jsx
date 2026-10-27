import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Diagnostic from "../pages/Diagnostic.jsx";
import { fakeServer } from "./fakeServer.js";
import { NOT_ASSESSED_REPORT, PRIYA_QUESTIONS } from "./fixtures.js";

describe("Diagnostic", () => {
  it("keeps Submit disabled until every question is answered", async () => {
    fakeServer({
      "GET /diagnostic/questions": { body: PRIYA_QUESTIONS },
      "GET /reports/me": { body: NOT_ASSESSED_REPORT },
    });
    const user = userEvent.setup();
    render(<Diagnostic onSubmitted={() => {}} />);

    const submit = await screen.findByRole("button", { name: "Submit answers" });
    expect(screen.getByText("0 of 3 answered")).toBeInTheDocument();
    expect(submit).toBeDisabled();

    await user.click(screen.getByRole("radio", { name: "Daily" }));
    await user.click(screen.getByRole("radio", { name: "To fix grammar" }));
    expect(screen.getByText("2 of 3 answered")).toBeInTheDocument();
    expect(submit).toBeDisabled();

    await user.type(screen.getByRole("textbox", { name: /Describe a work task/ }), "I drafted a reply.");
    expect(screen.getByText("3 of 3 answered")).toBeInTheDocument();
    expect(screen.getByText("18 / 2000 characters")).toBeInTheDocument();
    expect(submit).toBeEnabled();
  });

  it("warns that submitting again replaces previous answers", async () => {
    fakeServer({
      "GET /diagnostic/questions": { body: PRIYA_QUESTIONS },
      "GET /reports/me": { body: { ...NOT_ASSESSED_REPORT, answered: 2 } },
    });
    render(<Diagnostic onSubmitted={() => {}} />);
    expect(await screen.findByText("Submitting again replaces your previous answers.")).toBeInTheDocument();
  });
});
