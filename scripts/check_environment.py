import importlib.util
import sys
from pathlib import Path
modules=['fastapi','sqlalchemy','alembic','jinja2','multipart','itsdangerous','argon2','dotenv','pytest','httpx','uvicorn']
missing=[m for m in modules if importlib.util.find_spec(m) is None]
print('Python:',sys.version)
print('Missing dependencies:',', '.join(missing) or 'none')
assets=['chart.umd.js','swagger-ui-bundle.js','swagger-ui.css']
missing_assets=[a for a in assets if not Path('static/vendor',a).exists()]
print('Missing local assets:', ', '.join(missing_assets) or 'none')
sys.exit(bool(missing) or bool(missing_assets))
