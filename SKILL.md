---
name: clockify-timesheet
description: Fill the user's Clockify timesheet with their real work hours for a day or date range, rebuilt from their git commits, Claude Code prompts and Jira tickets, then post it through the Clockify API. On request, also write matching Jira worklogs.
disable-model-invocation: true
---

# Clockify timesheet

Rebuild what the user really worked on, agree the entries with them, post them to Clockify. Every entry is **evidence-backed**: its times come from their own commits and prompts, never from a target number of hours. Settings live in `~/.config/clockify-timesheet/config.toml`; scripts are in `scripts/` next to this file.

## Steps

1. **Setup** (first run, or when a script says the config is missing).
   - Ask, through AskUserQuestion: their name, every email they commit with (`git log --format=%ae | sort -u`; a bare name can match a colleague), timezone, work days, the folders holding their repos, their Clockify project, their fixed daily blocks (time and exact wording, e.g. planning, stand-up), and the projects in their logs that are not work.
   - Write `~/.config/clockify-timesheet/config.toml` from `config.example.toml` with those answers, leave `api_key` empty, and `chmod 600` it.
   - Ask them to open that file and paste their key into `api_key` themselves (Clockify › Preferences › Advanced › Manage API keys), so it never passes through the chat.
   - Check the Atlassian MCP is connected; if not, have them connect it (`/mcp`) and sign in.
   Done when `python3 scripts/clockify.py whoami` prints their name and project, and an Atlassian MCP call returns their user.

2. **What is already logged.** `python3 scripts/clockify.py list FROM TO`. Entries they logged themselves stay untouched; plan around them.
   Done when every day in the range is marked complete, partly logged or empty.

3. **Evidence.** `python3 scripts/activity.py FROM TO` prints per day their commits (once per commit, even across worktrees) and prompts, with excluded projects already removed. Add Jira: their tickets updated in the range, so each piece of work gets its key and a plain summary.
   Done when every block of activity is matched to its ticket keys, or marked as having none.

4. **Grill the open choices** (AskUserQuestion, recommendation first): projects in the logs not yet classed as work or not (add answers to `exclude_projects`), meetings the logs cannot see (day, time, title), late-night or non-work-day activity and whether it counts.

5. **Draft.** One table per day in 12-hour time: time, duration, description; total per day and for the range, then the gaps with what the logs show in each.
   Done when the user approves the tables.

6. **Post, one day first.** Write the entries as JSON (`[{"date":"2026-11-01","start":"10:30","end":"12:30","description":"…"}]`), run `post FILE --dry-run`, post the first day with `--days`, read it back with `list`. On their go, post the rest and read the whole range back. To replace a posted entry, `delete DATE START` then post the new one.
   Done when `list` shows every day at its agreed total with no overlaps.

7. **Jira worklogs, only when the user asks.** Split each Clockify block across the tickets in it, by commit times and when each ticket was started; work with no ticket stays unlogged. Show a table per ticket: what Jira has now, the proposed time, the evidence. On approval, edit or add worklogs with their real start times through the Atlassian MCP.
   Done when the per-ticket times sum to the Clockify ticket time and no ticket's worklog exceeds it.

## Rules

- **Real times.** Entries start and end where the evidence does. A gap longer than `rules.rest_minutes` with no activity stays a gap; time is never added to reach a total.
- **Fixed blocks** from `[[fixed]]` are logged as configured on every work day the user worked.
- **Description:** Jira keys first, each with a plain-words summary: `RHD-5834: department heads can be saved without becoming their own manager; RHD-5778: every login must have an employee`. Work with no ticket has no key.
- **Entries per day:** merge adjacent work to stay within `rules.max_entries` besides fixed blocks. The limit is soft: when real gaps split the day into more blocks, keep them and say so in the draft.
- **Parallel work:** when an excluded project's prompts interleave with work, count only the stretches where work dominates, and flag the estimate.
- **Clockify fields:** project and billable from the config, no tags.
- Post and write to Jira only after the user approves; both are visible to their team.
