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
