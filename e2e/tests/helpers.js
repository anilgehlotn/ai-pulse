// Every seeded account has this password (see backend/app/seed.py).
const PASSWORD = "pulse123";

// Sign in through the login form, the way a user does.
async function logIn(page, email) {
  await page.goto("/");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
}

module.exports = { logIn };
