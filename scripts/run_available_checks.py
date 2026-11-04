"""Record checks that can run without installing application dependencies."""
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    commands = [
        [sys.executable, '-m', 'compileall', '-q', 'app', 'migrations', 'scripts', 'tests'],
        [sys.executable, '-m', 'unittest', 'tests.test_assessment', 'tests.test_demo_data', '-v'],
    ]
    node = shutil.which('node')
    if node:
        commands.extend([[node, '--check', 'static/portal.js'], [node, '--test', 'tests/frontend.test.cjs']])
    lines = [f'Run at {datetime.now(timezone.utc).isoformat()}',
             f'Python: {sys.version}',
             'Scope: syntax/unit checks only. No server, migration, API or browser E2E verification.']
    failed = False
    for command in commands:
        result = subprocess.run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace')
        lines.extend(['', '$ ' + ' '.join(command), result.stdout, f'Exit code: {result.returncode}'])
        failed |= result.returncode != 0
    if not node:
        lines.append('Node unavailable: frontend checks NOT RUN.')
    report = '\n'.join(lines) + '\n'
    Path('docs/available-checks.txt').write_text(report, encoding='utf-8')
    print(report)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
