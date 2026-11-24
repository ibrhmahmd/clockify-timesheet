# clockify-timesheet

A Claude Code skill that fills your Clockify timesheet with your **real** hours, rebuilt from your git commits, your Claude Code prompts and your Jira tickets. It drafts a table per day, you approve it, it posts. On request it also writes Jira worklogs that add up to the Clockify time.

## Install

```bash
git clone https://github.com/ibrhmahmd/clockify-timesheet.git ~/Desktop/skills/clockify-timesheet
ln -s ~/Desktop/skills/clockify-timesheet ~/.claude/skills/clockify-timesheet
```

Then in Claude Code run `/clockify-timesheet`. The first run asks your settings, writes `~/.config/clockify-timesheet/config.toml`, and asks you to paste your Clockify API key into that file yourself (Clockify › Preferences › Advanced › Manage API keys).

Jira is reached through the Atlassian MCP; connect it with `/mcp` if it is not already.

## How it works

```text
 git commits ─┐
 Claude Code  ├─► activity per day ─► matched to Jira tickets ─► draft table ─► you approve ─► Clockify
 prompts     ─┘        (your timezone,      (keys + plain           (12-hour,                    │
 Jira tickets ────────  excluded projects    summary per             gaps shown)                 ▼
                        removed)             ticket)                              Jira worklogs (on request)
```

1. **Setup (first run only).** Claude asks your name, the emails you commit with, timezone, work days, where your repos live, your Clockify project, your fixed daily blocks (planning, stand-up) and which projects are not work. It writes `~/.config/clockify-timesheet/config.toml`; you paste your API key into it yourself, so the key never goes through the chat.
2. **What's already logged.** It reads your Clockify entries for the range and keeps anything you logged yourself.
3. **Evidence.** `scripts/activity.py` lists, per day, your commits in every repo under your repo folders (once per commit, even across worktrees) and every prompt you typed in Claude Code, with timestamps. Commits are matched by your emails, so a colleague with a similar name never counts. Projects you marked as not work are removed.
4. **Tickets.** Through the Atlassian MCP it pulls your Jira tickets updated in the range, so each block of work gets its keys and a plain summary.
5. **Open questions.** It asks only what the logs can't show: meetings, late-night work, projects it hasn't classified yet.
6. **Draft.** One table per day: start, end, duration and description, plus the gaps and what the logs show in each. Times are **real**: an entry starts and ends where your activity does, gaps stay gaps, and nothing is padded to reach a target.
7. **Post.** After you approve, it posts one day, reads it back from Clockify, then posts the rest on your go.
8. **Jira worklogs (only when you ask).** It splits each Clockify block across the tickets in it, using commit times and when each ticket was started, and shows Jira's current time next to the proposed one. Jira never ends up with more time than Clockify.

## Use

Run `/clockify-timesheet` in Claude Code, then say what you want:

- "fill my timesheet for this week"
- "what did I work on today"
- "post it" after approving the draft
- "update Jira worklogs to match"

The scripts also work on their own:

```bash
python3 scripts/activity.py 2026-11-23 2026-11-23     # evidence for a day
python3 scripts/clockify.py list 2026-11-23 2026-11-24 # what's logged
python3 scripts/clockify.py post entries.json --days 2026-11-23 --dry-run
python3 scripts/clockify.py delete 2026-11-23 10:45    # remove the entry starting at 10:45
```

## Entry rules

- Description: Jira keys first, each with a plain summary, e.g. `RHD-5834: department heads can be saved without becoming their own manager`.
- A few entries a day (`max_entries`, default 4) besides fixed blocks: nearby work is merged; a day split by real gaps may have more, and the draft says so.
- Gaps up to `rest_minutes` (default 15) count as part of the work around them; longer ones stay gaps.

## Settings

See [`config.example.toml`](config.example.toml): name, git emails, timezone, work days, repo folders, projects that are not work, Clockify project, fixed daily blocks, and the entry rules.

## Safety

- Your API key lives only in your config file (chmod 600). Never commit or share it.
- Nothing is posted to Clockify or Jira without your approval in that run.
- Everything posted is visible to your team.

## Requirements

Python 3.11+, git, Claude Code with the Atlassian MCP.
