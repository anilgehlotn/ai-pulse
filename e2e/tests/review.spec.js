const { test, expect } = require("@playwright/test");
const { reseed } = require("../backend");
const { logIn } = require("./helpers");

test.beforeEach(() => reseed());

test("The reviewer scores an answer and the queue gets shorter", async ({ page }) => {
  await logIn(page, "reviewer@northwind.test");

  // The seed leaves two of Leela's answers waiting; each has its own Save button.
  const saveButtons = page.getByRole("button", { name: "Save review" });
  await expect(saveButtons).toHaveCount(2);

  await page.getByRole("radio", { name: /^3 / }).first().check();
  await saveButtons.first().click();

  await expect(page.getByText("Review saved.")).toBeVisible();
  await expect(saveButtons).toHaveCount(1);

  // After a reload the queue comes from the server again, so this proves the review was stored.
  await page.reload();
  await expect(saveButtons).toHaveCount(1);
});
