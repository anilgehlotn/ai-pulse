# Client request (received after the previous developer left)

> **From:** HR team, Northwind Logistics
> **Subject:** AI Pulse pilot: two changes before rollout
>
> Hi team, our legal and HR teams reviewed the AI Pulse pilot and need two changes before we can roll it out:
>
> 1. **No small groups on the dashboard.** If a department has fewer than 5 people who completed the diagnostic, leadership must not see that department's scores or risks on their own. Group them under "Other teams" or hide them, but individuals must never be identifiable.
> 2. **Right to delete.** Any employee must be able to delete all their answers and their report themselves, and it must disappear from every dashboard immediately.
>
> Thanks, Northwind HR

---

## Status

Both items are done, in PR #10.

1. **No small groups on the dashboard:** done (closes #1). Teams under 5 respondents are merged into "Other teams" or
   hidden, the overall figure is hidden whenever anyone is hidden, and risk counts under 5 read "fewer than 5". Risks
   are never shown per team.
2. **Right to delete:** done (closes #2). Employees can delete all their answers from My report by typing `DELETE`.
   Dashboards are computed on every request, so the change shows on the next load.

Open questions for Northwind (full list in the README under
[What I'd ask Northwind](README.md#what-id-ask-northwind)):

- Is it OK that "Other teams" names the small teams it contains?
- Should visible teams' risks still show when some teams are hidden?
- Which fix for the snapshot-over-time leak (#14): scheduled refresh, levels only, or noise?
- Is "5" counted against people who completed the diagnostic, or people invited?
- Should deletion also cover backups, and how long are answers kept?
