"""Audit the actual Git candidate set without staging, committing or publishing."""
import json
import argparse
from pathlib import Path
import re
import subprocess

from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]


def main(output=None):
    candidates=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
    candidates=sorted(set(p for p in candidates if p))
    local=dotenv_values(ROOT/'.env')
    secrets=[value.encode() for key,value in local.items() if key in ('POSTGRES_PASSWORD','DATABASE_URL') and value and len(value)>15 and 'change_me' not in value]
    blocked=[]
    patterns=[re.compile(rb'sk-[A-Za-z0-9]{24,}'),re.compile(rb'AKIA[0-9A-Z]{16}'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    for relative in candidates:
        path=ROOT/relative
        if not path.is_file():
            continue
        name=relative.replace('\\','/')
        risky=(name=='.env' or name.startswith(('data/raw/','reports/','.venv/','.venv-repro/','backups/','exports/','pgdata/')) or name.endswith(('.dump','.backup','.pem','.key','.log'))) and path.name!='.gitkeep'
        if path.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.gif','.pdf','.mp4'):
            payload=b''
        else:
            payload=path.read_bytes()
        if risky or any(secret in payload for secret in secrets) or any(pattern.search(payload) for pattern in patterns):
            blocked.append(relative)
    sentinel=['.env','data/raw/olist_orders_dataset.csv','reports/p3/sql_results/association_orders.csv','.venv/Scripts/python.exe','.venv-repro/Scripts/python.exe','backups/database.dump','exports/user_rows.csv','credentials.json']
    ignored={name:subprocess.run(['git','check-ignore','--quiet',name],cwd=ROOT).returncode==0 for name in sentinel}
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    remotes=subprocess.check_output(['git','remote'],cwd=ROOT,text=True).splitlines()
    result={'passed':not blocked and all(ignored.values()),'candidate_files':len(candidates),'blocked_paths':blocked,
            'ignore_checks':ignored,'staged_files':staged,'configured_remote_count':len(remotes),
            'publication_performed':False,'scope':'扫描实际Git候选文本、真实本地密码/连接串和常见密钥模式；不能证明不存在所有类型秘密。'}
    output=Path(output) if output else ROOT/'reports/p4/public_safety.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    raise SystemExit(main(parser.parse_args().output))
