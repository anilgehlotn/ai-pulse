import { describe, expect, it, vi } from "vitest";
import { api, getToken, onSessionExpired, setToken } from "../api.js";
import { fakeServer } from "./fakeServer.js";

async function errorFrom(reply) {
  fakeServer({ "GET /thing": reply });
  try {
    await api("/thing");
  } catch (err) {
    return err;
  }
  throw new Error("expected api() to throw");
}

describe("api error messages", () => {
  it("uses a JSON detail string as-is", async () => {
    const err = await errorFrom({ status: 403, body: { detail: "Admins only" } });
    expect(err.message).toBe("Admins only");
    expect(err.status).toBe(403);
  });

  it("turns a FastAPI 422 detail array into one readable message", async () => {
    const err = await errorFrom({
      status: 422,
      body: {
        detail: [
          { loc: ["body", "answers", 0, "answer"], msg: "String should have at most 2000 characters", type: "x" },
          { loc: ["body", "email"], msg: "Field required", type: "missing" },
        ],
      },
    });
    expect(err.message).toBe("answers 0 answer: String should have at most 2000 characters. email: Field required.");
  });

  it("handles a body that is not JSON", async () => {
    const err = await errorFrom({ status: 502, body: "<html>Bad gateway</html>" });
    expect(err.message).toBe("The server had a problem (502). Please try again.");
  });

  it("explains when the server cannot be reached", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(api("/thing")).rejects.toThrow("Can't reach the server");
  });
});

describe("expired sessions", () => {
  it("clears the token and tells the app on a 401 when a token was sent", async () => {
    setToken("old-token");
    const expired = vi.fn();
    onSessionExpired(expired);
    await errorFrom({ status: 401, body: { detail: "Invalid token" } });
    expect(getToken()).toBe(null);
    expect(expired).toHaveBeenCalledOnce();
  });

  it("does not treat a wrong password as an expired session", async () => {
    const expired = vi.fn();
    onSessionExpired(expired);
    const err = await errorFrom({ status: 401, body: { detail: "Wrong email or password" } });
    expect(err.message).toBe("Wrong email or password");
    expect(expired).not.toHaveBeenCalled();
  });
});
