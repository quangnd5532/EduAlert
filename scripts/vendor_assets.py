"""Install pinned browser libraries locally from the official npm registry."""
import io
import json
import hashlib
import base64
import tarfile
from pathlib import Path
from urllib.request import urlopen
PACKAGES=[('chart.js','4.4.9',{'package/dist/chart.umd.js':'chart.umd.js','package/LICENSE.md':'LICENSE.Chart.js.md'}),
          ('swagger-ui-dist','5.21.0',{'package/swagger-ui-bundle.js':'swagger-ui-bundle.js','package/swagger-ui.css':'swagger-ui.css','package/LICENSE':'LICENSE.SwaggerUI'})]
def main():
    target=Path('static/vendor');target.mkdir(parents=True,exist_ok=True);provenance=[]
    for package,version,members in PACKAGES:
        with urlopen(f'https://registry.npmjs.org/{package}/{version}',timeout=30) as r: metadata=json.load(r)
        with urlopen(metadata['dist']['tarball'],timeout=60) as r: blob=r.read(30_000_000)
        digest=base64.b64encode(hashlib.sha512(blob).digest()).decode()
        if metadata['dist']['integrity']!='sha512-'+digest: raise RuntimeError(package+' integrity mismatch')
        with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tar:
            # Never extract paths from the archive; read only these named members.
            assets={dest:tar.extractfile(source).read() for source,dest in members.items()}
        for dest,data in assets.items():(target/dest).write_bytes(data)
        provenance.append({'package':package,'version':version,'source':metadata['dist']['tarball'],'integrity':metadata['dist']['integrity']})
        print('Installed local '+package+' '+version)
    (target/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
if __name__=='__main__':main()
