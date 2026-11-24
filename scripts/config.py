"""Load ~/.config/clockify-timesheet/config.toml (override with CLOCKIFY_TIMESHEET_CONFIG)."""
import os
import pathlib
import sys
import tomllib
from zoneinfo import ZoneInfo

PATH = pathlib.Path(os.environ.get(
    'CLOCKIFY_TIMESHEET_CONFIG', '~/.config/clockify-timesheet/config.toml')).expanduser()
REQUIRED = ('name', 'git_author', 'timezone', 'work_days', 'repo_roots')


def load():
    if not PATH.exists():
        sys.exit(f'No config at {PATH}. Run setup first (see SKILL.md step 1).')
    cfg = tomllib.loads(PATH.read_text())
    missing = [k for k in REQUIRED if not cfg.get(k)]
    if not cfg.get('clockify', {}).get('api_key'):
        missing.append('clockify.api_key')
    if missing:
        sys.exit(f'{PATH} is missing: {", ".join(missing)}')
    cfg['tz'] = ZoneInfo(cfg['timezone'])
    cfg.setdefault('exclude_projects', [])
    cfg.setdefault('fixed', [])
    cfg.setdefault('rules', {}).setdefault('max_entries', 4)
    cfg['rules'].setdefault('rest_minutes', 15)
    return cfg
