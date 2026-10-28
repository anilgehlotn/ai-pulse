// Plain-English wording for the codes the backend sends.

// For a person's own report.
export const RISK_FOR_YOU = {
  customer_data_shared: "You've shared customer information with an AI tool.",
  confidential_data_shared: "You've shared confidential company information with an AI tool.",
  unreviewed_output: "You've used AI output without checking it first.",
  policy_unaware: "You're not sure what your company's AI policy says.",
};

// For the leadership dashboard, about people in general.
export const RISK_FOR_TEAMS = {
  customer_data_shared: "Shared customer information with an AI tool",
  confidential_data_shared: "Shared confidential company information with an AI tool",
  unreviewed_output: "Used AI output without checking it",
  policy_unaware: "Unsure what the AI policy says",
};

export function riskText(map, flag) {
  return map[flag] || flag;
}

// Shown when the backend sends null: there was not enough to calculate a value.
export const NO_VALUE = "—";

export function show(value) {
  return value === null || value === undefined ? NO_VALUE : value;
}

export function hasValue(value) {
  return value !== null && value !== undefined;
}

// "Asha Rao" -> "Asha"
export function firstName(name) {
  return name.split(" ")[0];
}

// "Asha Rao" -> "AR"
export function initials(name) {
  return name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}

export const ROLE_LABELS = { admin: "Admin", employee: "Employee" };

// "Wednesday 28 October", for the greeting at the top of a page.
export function today() {
  return new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });
}
