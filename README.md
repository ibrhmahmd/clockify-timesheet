# clockify-timesheet

A Claude Code skill that fills your Clockify timesheet with your **real** hours, rebuilt from your git commits, your Claude Code prompts and your Jira tickets. It drafts a table per day, you approve it, it posts. On request it also writes Jira worklogs that add up to the Clockify time.

## Install

```bash
git clone <this repo> ~/Desktop/skills/clockify-timesheet
ln -s ~/Desktop/skills/clockify-timesheet ~/.claude/skills/clockify-timesheet
```

Then in Claude Code run `/clockify-timesheet`. The first run asks your settings, writes `~/.config/clockify-timesheet/config.toml`, and asks you to paste your Clockify API key into that file yourself (Clockify › Preferences › Advanced › Manage API keys).

Jira is reached through the Atlassian MCP; connect it with `/mcp` if it is not already.

## Use

- "fill my timesheet for this week"
- "what did I work on today"
- "post it" after approving the draft
- "update Jira worklogs to match" (only when you ask)

## Settings

See [`config.example.toml`](config.example.toml): name, git author, timezone, work days, repo folders, projects that are not work, Clockify project, fixed daily blocks, and the entry rules.

## Safety

- Your API key lives only in your config file (chmod 600). Never commit or share it.
- Nothing is posted to Clockify or Jira without your approval in that run.
- Everything posted is visible to your team.

## Requirements

Python 3.11+, git, Claude Code with the Atlassian MCP.
