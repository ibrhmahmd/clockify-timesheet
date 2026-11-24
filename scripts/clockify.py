#!/usr/bin/env python3
"""Clockify helper. Settings come from config.toml (see config.example.toml).

    clockify.py whoami
    clockify.py list FROM TO
    clockify.py post FILE.json [--days D ...] [--dry-run]
    clockify.py delete DATE START [START ...]      # removes your entries starting at those times

Dates are YYYY-MM-DD, times HH:MM in your configured timezone.
"""
import argparse
import collections
import datetime
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

import config

CFG = config.load()
API = 'https://api.clockify.me/api/v1'
TZ = CFG['tz']


def call(path, body=None, method=None):
    req = urllib.request.Request(
        API + path, method=method or ('POST' if body else 'GET'),
        data=json.dumps(body).encode() if body else None,
        headers={'X-Api-Key': CFG['clockify']['api_key'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise SystemExit(f'Clockify refused the API key: check clockify.api_key in {config.PATH}')
        raise
    return json.loads(raw) if raw else None


def me():
    u = call('/user')
    return u['id'], u['activeWorkspace'], u['name']


def local(ts):
    return datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone(TZ)


def utc(day, hm):
    t = datetime.datetime.strptime(f'{day} {hm}', '%Y-%m-%d %H:%M').replace(tzinfo=TZ)
    return t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def entries(start, end):
    """Your entries starting on days start..end (local dates)."""
    uid, ws, _ = me()
    after = (datetime.date.fromisoformat(end) + datetime.timedelta(days=2)).isoformat()
    out = call(f'/workspaces/{ws}/user/{uid}/time-entries?page-size=1000'
               f'&start={utc(start, "00:00")}&end={utc(after, "00:00")}')
    d0, d1 = datetime.date.fromisoformat(start), datetime.date.fromisoformat(end)
    return ws, [e for e in out if d0 <= local(e['timeInterval']['start']).date() <= d1]


def cmd_list(start, end):
    _, es = entries(start, end)
    days = collections.defaultdict(list)
    for e in es:
        s, f = e['timeInterval']['start'], e['timeInterval']['end']
        days[local(s).date()].append((local(s), local(f) if f else None, e['description']))
    total_all = 0
    for day in sorted(days):
        rows = sorted(days[day], key=lambda r: r[0])
        total = sum((f - s).seconds for s, f, _ in rows if f)
        total_all += total
        print(f'{day:%a %d %b}  {len(rows)} entries  {total // 3600}h{total % 3600 // 60:02d}')
        for i, (s, f, d) in enumerate(rows):
            clash = i and rows[i - 1][1] and rows[i - 1][1] > s
            print(f'  {s:%H:%M}-{f:%H:%M}' if f else f'  {s:%H:%M}-running',
                  'OVERLAP ' if clash else '', d.replace('\n', ' ')[:90])
    print(f'total {total_all // 3600}h{total_all % 3600 // 60:02d}')


def cmd_post(path, days, dry):
    _, ws, _ = me()
    name = CFG['clockify']['project']
    projects = call(f'/workspaces/{ws}/projects?page-size=500&name={urllib.parse.quote(name)}')
    pid = next(p['id'] for p in projects if p['name'] == name)
    for e in json.loads(pathlib.Path(path).read_text()):
        if days and e['date'] not in days:
            continue
        if not dry:
            call(f'/workspaces/{ws}/time-entries', {
                'start': utc(e['date'], e['start']), 'end': utc(e['date'], e['end']),
                'projectId': pid, 'billable': CFG['clockify'].get('billable', False),
                'description': e['description']})
        print('would post' if dry else 'posted', e['date'], e['start'], e['end'], e['description'][:60])


def cmd_delete(day, starts):
    ws, es = entries(day, day)
    hit = 0
    for e in es:
        hm = local(e['timeInterval']['start']).strftime('%H:%M')
        if local(e['timeInterval']['start']).date().isoformat() == day and hm in starts:
            call(f'/workspaces/{ws}/time-entries/{e["id"]}', method='DELETE')
            print('deleted', day, hm, e['description'][:60])
            hit += 1
    if not hit:
        print('nothing starts at', ', '.join(sorted(starts)), 'on', day)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('whoami')
    ls = sub.add_parser('list'); ls.add_argument('start'); ls.add_argument('end')
    po = sub.add_parser('post'); po.add_argument('file')
    po.add_argument('--days', nargs='*', default=[])
    po.add_argument('--dry-run', action='store_true')
    de = sub.add_parser('delete'); de.add_argument('day'); de.add_argument('starts', nargs='+')
    a = p.parse_args()
    if a.cmd == 'whoami':
        uid, ws, name = me()
        print(name, 'user', uid, 'workspace', ws, 'project', CFG['clockify']['project'])
    elif a.cmd == 'list':
        cmd_list(a.start, a.end)
    elif a.cmd == 'post':
        cmd_post(a.file, set(a.days), a.dry_run)
    else:
        cmd_delete(a.day, set(a.starts))
