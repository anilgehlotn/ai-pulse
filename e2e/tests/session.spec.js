const { test, expect } = require("@playwright/test");
const { reseed } = require("../backend");
const { logIn } = require("./helpers");

test.beforeEach(() => reseed());

test("A tampered token sends the user back to login", async ({ page }) => {
  await logIn(page, "rohan@northwind.test");
  await expect(page.getByRole("heading", { name: "Your AI Pulse, Rohan" })).toBeVisible();

  // Keep the token's content but replace its signature, as someone editing it by hand would.
  await page.evaluate(() => {
    const [header, payload] = localStorage.getItem("token").split(".");
    localStorage.setItem("token", `${header}.${payload}.not-the-real-signature`);
  });
  await page.reload();

  await expect(page.getByText("Your session expired. Please sign in again.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sign in to AI Pulse" })).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("token"))).toBeNull();
});
