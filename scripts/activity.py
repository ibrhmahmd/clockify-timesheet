#!/usr/bin/env python3
"""Per-day evidence of work: your git commits and Claude Code prompts.

    activity.py FROM TO [--repos DIR ...]

Settings (author, timezone, repo roots, excluded projects) come from config.toml.
A commit seen in several worktrees is listed once. Excluded projects are dropped.
"""
import argparse
import collections
import datetime
import glob
import json
import pathlib
import subprocess

import config

CFG = config.load()
TZ = CFG['tz']
SKIP = ('<', 'Base directory', 'This session', '[Request', 'Stop hook', '(Re-inv', 'Caveat')
AUTHORS = [f'--author={x}' for x in ([CFG['git_author']] if isinstance(CFG['git_author'], str) else CFG['git_author'])]
EXCLUDE = [x.lower() for x in CFG['exclude_projects']]


def excluded(name):
    return any(x in name.lower() for x in EXCLUDE)


p = argparse.ArgumentParser()
p.add_argument('start'); p.add_argument('end')
p.add_argument('--repos', nargs='*')
a = p.parse_args()
d0, d1 = datetime.date.fromisoformat(a.start), datetime.date.fromisoformat(a.end)
repos = a.repos or [str(g.parent) for root in CFG['repo_roots']
                    for g in pathlib.Path(root).expanduser().glob('*/.git')]

days = collections.defaultdict(lambda: {'commits': {}, 'prompts': set()})
for repo in repos:
    if excluded(pathlib.Path(repo).name):
        continue
    out = subprocess.run(
        ['git', '-C', repo, 'log', '--branches', '--remotes', *AUTHORS, '--no-merges',
         f'--since={d0 - datetime.timedelta(days=1)}',
         f'--until={d1 + datetime.timedelta(days=2)}', '--format=%aI|%h|%s'],
        capture_output=True, text=True).stdout
    for line in out.splitlines():
        ts, sha, subj = line.split('|', 2)
        t = datetime.datetime.fromisoformat(ts).astimezone(TZ)
        if d0 <= t.date() <= d1:
            days[t.date()]['commits'].setdefault(sha, (t, f'{pathlib.Path(repo).name} {sha} {subj[:150]}'))

for f in glob.glob(str(pathlib.Path('~/.claude/projects/*/*.jsonl').expanduser())):
    for line in open(f, errors='ignore'):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if o.get('type') != 'user' or o.get('isMeta') or 'timestamp' not in o:
            continue
        project = pathlib.Path(o.get('cwd') or pathlib.Path(f).parent.name).name
        if excluded(project):
            continue
        c = o.get('message', {}).get('content')
        if isinstance(c, list):
            if any(isinstance(x, dict) and x.get('type') == 'tool_result' for x in c):
                continue
            c = ' '.join(x.get('text', '') for x in c if isinstance(x, dict))
        if not isinstance(c, str) or c.startswith(SKIP):
            continue
        t = datetime.datetime.fromisoformat(o['timestamp'].replace('Z', '+00:00')).astimezone(TZ)
        if d0 <= t.date() <= d1:
            days[t.date()]['prompts'].add((t, f'[{project}] {c.strip()[:130]}'))

for day in sorted(days):
    ev = days[day]
    commits = sorted(ev['commits'].values())
    times = sorted(t for t, _ in commits + list(ev['prompts']))
    work = '' if day.strftime('%a') in CFG['work_days'] else '  (not a work day)'
    print(f'\n=== {day:%a %d %b}  active {times[0]:%H:%M}-{times[-1]:%H:%M}  '
          f'{len(commits)} commits, {len(ev["prompts"])} prompts{work}')
    for t, s in commits:
        print(f'  C {t:%H:%M} {s}')
    for t, s in sorted(ev['prompts']):
        print(f'  P {t:%H:%M} {s.replace(chr(10), " ")}')
