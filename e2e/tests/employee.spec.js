const { test, expect } = require("@playwright/test");
const { reseed } = require("../backend");
const { logIn } = require("./helpers");

test.beforeEach(() => reseed());

test("Rohan's report shows Exposed and a tip to focus on next", async ({ page }) => {
  await logIn(page, "rohan@northwind.test");

  await expect(page.getByRole("region", { name: "Where you stand" })).toContainText("Exposed");
  const focus = page.getByRole("region", { name: "Focus next" });
  await expect(focus.getByRole("paragraph")).not.toBeEmpty();
});

test("Priya takes the full diagnostic and lands on her report", async ({ page }) => {
  await logIn(page, "priya@northwind.test");
  await page.getByRole("button", { name: "My diagnostic" }).click();
  await expect(page.getByRole("heading", { name: "My diagnostic" })).toBeVisible();

  // Each multiple-choice question is a group of radio buttons: pick the first option in each.
  for (const question of await page.getByRole("group").all()) {
    await question.getByRole("radio").first().check();
  }
  // Each open question is a text box.
  for (const answer of await page.getByRole("textbox").all()) {
    await answer.fill("I summarise ticket threads with AI and check every detail before replying.");
  }

  const submit = page.getByRole("button", { name: "Submit answers" });
  await expect(submit).toBeEnabled();
  await submit.click();

  await expect(page.getByRole("heading", { name: "Your AI Pulse, Priya" })).toBeVisible();
  await expect(page.getByRole("button", { name: "My report" })).toHaveAttribute("aria-current", "page");
});

test("Priya deletes her data and is no longer assessed", async ({ page }) => {
  await logIn(page, "priya@northwind.test");

  await page.getByRole("button", { name: "Delete all my answers" }).click();
  await page.getByLabel("Type DELETE to confirm").fill("DELETE");
  await page.getByRole("button", { name: "Delete permanently" }).click();

  await expect(page.getByText("Your answers have been deleted.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Not assessed" })).toBeVisible();
});
