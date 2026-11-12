"""Run application checks and retain the actual output for the release report."""
import os
import shutil
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

root=Path(__file__).resolve().parent.parent
os.chdir(root)
commands=[[sys.executable,'-m','compileall','-q','app','migrations','scripts','tests'],[sys.executable,'-m','pytest','-q']]
node=shutil.which('node')
if node:commands.extend([[node,'--check',path] for path in ('static/student.js','static/auth.js','static/configuration.js','static/portal.js')]+[[node,'--test','tests/frontend.test.cjs']])
report=[f'EduAlert 3.4 verification: {datetime.now(timezone.utc).isoformat()}',f'Python: {sys.version}',
        'Scope: Python integration/unit tests and JavaScript unit/syntax checks. Browser visual checks are separate.']
failed=False
for command in commands:
    result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    report.extend(['','$ '+' '.join(command),result.stdout,'Exit code: '+str(result.returncode)])
    print(' '.join(command[1:]),'exit',result.returncode,flush=True)
    failed|=result.returncode!=0
Path('docs/release-checks.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
raise SystemExit(int(failed))
