import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Review from "../pages/Review.jsx";
import { fakeServer } from "./fakeServer.js";
import { REVIEW_QUEUE } from "./fixtures.js";

const [INJECTION, INCONSISTENT] = REVIEW_QUEUE;

describe("Review", () => {
  it("shows the answer, the AI's reason and flags, and nothing about who wrote it", async () => {
    // Even if the server ever sent identifying fields by mistake, the page must not show them.
    const leaky = { ...INCONSISTENT, name: "Leela Varma", email: "leela@northwind.test", department: "HR",
                    job_role: "manager", seniority: "senior" };
    fakeServer({ "GET /review/queue": { body: [leaky] } });
    render(<Review />);

    const card = await screen.findByRole("region", { name: INCONSISTENT.question });
    expect(card).toHaveTextContent(INCONSISTENT.answer);
    expect(card).toHaveTextContent("much higher than");
    expect(card).toHaveTextContent("Shared confidential company information with an AI tool");
    for (const detail of ["Leela", "Varma", "leela@northwind.test", "HR", "manager", "senior"]) {
      expect(card.textContent).not.toContain(detail);
    }
  });

  it("warns about a possible prompt injection", async () => {
    fakeServer({ "GET /review/queue": { body: [INJECTION] } });
    render(<Review />);
    const card = await screen.findByRole("region", { name: INJECTION.question });
    expect(within(card).getByText("Possible prompt injection")).toBeInTheDocument();
  });

  it("sends the chosen score and flags, then removes the answer from the list", async () => {
    const server = fakeServer({
      "GET /review/queue": { body: REVIEW_QUEUE },
      [`POST /review/${INJECTION.review_id}`]: { body: { review_id: INJECTION.review_id, score: 2, flags: ["unreviewed_output"] } },
    });
    const user = userEvent.setup();
    render(<Review />);

    const card = await screen.findByRole("region", { name: INJECTION.question });
    const save = within(card).getByRole("button", { name: "Save review" });
    expect(save).toBeDisabled(); // no score yet

    await user.click(within(card).getByRole("radio", { name: /^2/ }));
    await user.click(within(card).getByRole("checkbox", { name: "Used AI output without checking it" }));
    await user.click(save);

    const [url, options] = server.mock.calls.find(([, o]) => o && o.method === "POST");
    expect(new URL(url).pathname).toBe(`/review/${INJECTION.review_id}`);
    expect(JSON.parse(options.body)).toEqual({ score: 2, flags: ["unreviewed_output"] });

    expect(await screen.findByRole("status")).toHaveTextContent("Review saved");
    expect(screen.queryByRole("region", { name: INJECTION.question })).toBeNull();
    expect(screen.getByRole("region", { name: INCONSISTENT.question })).toBeInTheDocument();
  });

  it("shows a calm empty state when nothing is waiting", async () => {
    fakeServer({ "GET /review/queue": { body: [] } });
    render(<Review />);
    expect(await screen.findByRole("heading", { name: "Nothing to review" })).toBeInTheDocument();
  });

  it("shows the server's error when saving fails", async () => {
    fakeServer({
      "GET /review/queue": { body: [INJECTION] },
      [`POST /review/${INJECTION.review_id}`]: { status: 404, body: { detail: "No answer with this id is waiting for review" } },
    });
    const user = userEvent.setup();
    render(<Review />);
    const card = await screen.findByRole("region", { name: INJECTION.question });
    await user.click(within(card).getByRole("radio", { name: /^3/ }));
    await user.click(within(card).getByRole("button", { name: "Save review" }));
    expect(await within(card).findByRole("alert")).toHaveTextContent("No answer with this id is waiting for review");
  });
});
