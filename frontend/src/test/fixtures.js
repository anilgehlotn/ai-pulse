// Real responses from the seeded backend (python -m app.seed), trimmed where noted.

export const NORTHWIND_DASHBOARD = {
  organization: "Northwind Logistics",
  min_group_size: 5,
  groups: [
    { name: "Sales", privacy: "shown", employees: 6, respondents: 5, average_score: 2.78, level: "Exploring",
      adoption: 3.2, safety: 2.2, quadrant: "Exposed" },
    { name: "Support", privacy: "shown", employees: 6, respondents: 6, average_score: 3.08, level: "Practitioner",
      adoption: 3.0, safety: 3.2, quadrant: "Leading" },
    { name: "Other teams", privacy: "merged", teams: ["Engineering", "HR", "Unassigned"], employees: 6,
      respondents: 5, average_score: 2.8, level: "Exploring", adoption: 2.8, safety: 2.8, quadrant: "Getting started" },
  ],
  act_first: [
    { name: "Sales", adoption: 3.2, safety: 2.2, gap: 1.0, reason: "Uses AI often (3.2) but safety habits are low (2.2)" },
  ],
  overall: {
    privacy: "shown", respondents: 16, average_score: 2.9, level: "Exploring",
    top_risks: [
      { risk: "unreviewed_output", people: 5 },
      { risk: "confidential_data_shared", people: "fewer than 5" },
      { risk: "customer_data_shared", people: "fewer than 5" },
      { risk: "policy_unaware", people: "fewer than 5" },
    ],
    awaiting_review: "fewer than 5",
  },
};

export const BLUEPEAK_DASHBOARD = {
  organization: "Bluepeak Retail",
  min_group_size: 5,
  groups: [{ name: "Other teams", privacy: "hidden", teams_hidden: 3, message: "3 teams hidden to protect anonymity" }],
  act_first: [],
  overall: {
    privacy: "hidden",
    reason: "Some teams are too small to show. An overall figure would let their results be worked out by subtracting the visible teams.",
  },
};

// Priya (support, junior): four common MCQs, the open question, and one role MCQ. Options trimmed.
export const PRIYA_QUESTIONS = [
  { id: "common-freq", type: "mcq", dimension: "adoption", roles: ["all"], text: "How often do you use AI tools for work?",
    options: ["Never", "Daily"] },
  { id: "common-open", type: "open", roles: ["all"], text: "Describe a work task where you used AI." },
  { id: "sup-drafts", type: "mcq", dimension: "adoption", roles: ["support"], min_seniority: "junior",
    text: "How do you use AI when replying to customers?", options: ["I don't", "To fix grammar"] },
];

export const NOT_ASSESSED_REPORT = {
  name: "Priya Nair", organization: "Northwind Logistics", answered: 0, awaiting_review: 0,
  average_score: null, level: "Not assessed", risks: [], next_steps: [],
  adoption: null, safety: null, quadrant: null,
  quadrant_explanation: "Answer both the usage and the safety questions to see where you stand.", focus_next: null,
};
