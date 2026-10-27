import { vi } from "vitest";

// Replaces fetch with canned replies, keyed by "METHOD /path".
// A reply is {status, body}; body may be an object (sent as JSON) or a string (sent as-is).
export function fakeServer(routes) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (url, options = {}) => {
    const key = `${options.method || "GET"} ${new URL(url).pathname}`;
    const reply = routes[key];
    if (!reply) throw new Error(`No fake reply for ${key}`);
    const isText = typeof reply.body === "string";
    return new Response(isText ? reply.body : JSON.stringify(reply.body), {
      status: reply.status || 200,
      headers: { "Content-Type": isText ? "text/plain" : "application/json" },
    });
  });
}
