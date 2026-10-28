const { test, expect } = require("@playwright/test");
const { reseed } = require("../backend");
const { logIn } = require("./helpers");

test.beforeEach(() => reseed());

test("Asha sees her teams, with Sales under Act first", async ({ page }) => {
  await logIn(page, "asha@northwind.test");

  const teams = page.getByRole("region", { name: "Teams", exact: true });
  await expect(teams.getByRole("rowheader", { name: "Sales" })).toBeVisible();
  await expect(teams.getByRole("rowheader", { name: "Support" })).toBeVisible();
  await expect(teams.getByRole("rowheader", { name: "Other teams" })).toBeVisible();

  const actFirst = page.getByRole("region", { name: "Act first" });
  await expect(actFirst).toContainText("Sales");
  await expect(actFirst).not.toContainText("Support");
});

test("Ravi sees no Bluepeak totals, and only his own tabs at Northwind", async ({ page }) => {
  await logIn(page, "ravi@consult.test");
  await page.getByRole("button", { name: /Bluepeak Retail/ }).click();

  // Bluepeak's teams are too small, so the overall area explains why and shows no numbers at all.
  const overall = page.getByRole("region", { name: "Whole organization" });
  await expect(overall).toContainText("Some teams are too small to show");
  await expect(overall).not.toHaveText(/\d/);

  // At Northwind he is an employee: no Dashboard tab.
  await page.getByRole("button", { name: "Switch organization" }).click();
  await page.getByRole("button", { name: /Northwind Logistics/ }).click();
  const tabs = page.getByRole("navigation", { name: "Sections" });
  await expect(tabs.getByRole("button")).toHaveText(["My diagnostic", "My report"]);
});
