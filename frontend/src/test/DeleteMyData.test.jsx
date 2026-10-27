import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DeleteMyData from "../components/DeleteMyData.jsx";
import { fakeServer } from "./fakeServer.js";

describe("Delete all my answers", () => {
  it("only deletes after the user types DELETE", async () => {
    const server = fakeServer({
      "DELETE /me/data": { body: { deleted_answers: { "Northwind Logistics": 7 }, total: 7 } },
    });
    const onDeleted = vi.fn();
    const user = userEvent.setup();
    render(<DeleteMyData onDeleted={onDeleted} />);

    await user.click(screen.getByRole("button", { name: "Delete all my answers" }));
    const confirm = screen.getByRole("button", { name: "Delete permanently" });
    expect(confirm).toBeDisabled();

    const input = screen.getByLabelText("Type DELETE to confirm");
    await user.type(input, "delete");
    expect(confirm).toBeDisabled();

    await user.clear(input);
    await user.type(input, "DELETE");
    expect(confirm).toBeEnabled();
    await user.click(confirm);

    expect(onDeleted).toHaveBeenCalledWith({ deleted_answers: { "Northwind Logistics": 7 }, total: 7 });
    const [, options] = server.mock.calls[0];
    expect(JSON.parse(options.body)).toEqual({ confirm: "DELETE" });
  });
});
