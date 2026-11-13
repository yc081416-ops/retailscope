"""Read-only audit of actual public candidates, tracked files, refs and every Git blob."""
import hashlib
import json
import re
import subprocess
from collections import Counter,defaultdict
from pathlib import Path
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/github-release'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    candidates=sorted(set(filter(None,git('ls-files','--cached','--others','--exclude-standard','-z').decode().split('\0'))))
    tracked=list(filter(None,git('ls-files','-z').decode().split('\0')))
    config=dotenv_values(ROOT/'.env')
    secrets=[v.encode() for k,v in config.items() if k in ('POSTGRES_PASSWORD','DATABASE_URL') and v and len(v)>12 and not v.startswith('change_me')]
    key_patterns=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'AKIA[0-9A-Z]{16}'),re.compile(rb'(?:ghp_|github_pat_|sk-)[A-Za-z0-9_-]{25,}')]
    uri=re.compile(rb"postgres(?:ql)?(?:\+psycopg)?://([^:\s/'\"<>]+):([^@\s'\"<>]+)@([^/\s'\"<>]+)")
    findings=[]
    example_uris=[]
    def scan(payload,label):
        if any(s in payload for s in secrets):findings.append({'location':label,'kind':'actual_local_secret_match'})
        if any(p.search(payload) for p in key_patterns):findings.append({'location':label,'kind':'private_key_or_access_token_pattern'})
        for match in uri.finditer(payload):
            password=match.group(2).lower()
            # Literal examples are classified, never silently counted as live credentials.
            fixture=b'def test_' in payload and b'pytest' in payload
            if password.startswith(b'change_me') or (fixture and (password in (b'p',b'pw',b'pass',b'password',b'test',b'fake',b'secret') or password.startswith((b'fake',b'dummy')))):
                example_uris.append({'location':label,'classification':'placeholder_or_test_fixture','test_context':fixture})
            else:findings.append({'location':label,'kind':'credential_uri_requires_review'})
    def risky(name):
        value=name.replace('\\','/');parts=value.lower().split('/')
        return (value=='.env' or any(part in ('data/raw','.venv','node_modules','pgdata','backups','exports') for part in parts)
            or value.startswith(('data/raw/','reports/','output/','.venv/','.venv-repro/','frontend/dist/','backups/','exports/','pgdata/'))
            or Path(value).suffix.lower() in ('.csv','.parquet','.pkl','.pickle','.dump','.backup','.key','.pem','.log')) and Path(value).name!='.gitkeep'
    manifest=[]
    for name in candidates:
        p=ROOT/name
        if not p.is_file():continue
        payload=p.read_bytes();scan(payload,name)
        if risky(name):findings.append({'location':name,'kind':'excluded_data_or_environment_path'})
        manifest.append({'path':name,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
    objects=[line.split() for line in git('cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype) %(objectsize)').decode().splitlines()]
    paths=defaultdict(set)
    for sha,kind,_ in objects:
        if kind=='tree':
            for entry in git('ls-tree','-r','-z',sha).split(b'\0'):
                if not entry:continue
                meta,name=entry.split(b'\t',1);blob=meta.split()[2].decode();paths[blob].add(name.decode('utf-8','replace'))
    blobs=[row[0] for row in objects if row[1]=='blob']
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    for sha in blobs:
        proc.stdin.write((sha+'\n').encode());proc.stdin.flush()
        header=proc.stdout.readline().decode().split();size=int(header[2]);payload=proc.stdout.read(size);assert proc.stdout.read(1)==b'\n'
        scan(payload,'git-object:'+sha)
        for name in paths[sha]:
            if risky(name):findings.append({'location':'git-object:'+sha,'path':name,'kind':'historical_sensitive_path'})
    proc.stdin.close();assert proc.wait()==0
    sentinels=['.env','data/raw/olist_orders_dataset.csv','reports/p3/sql_results/association_orders.csv','.venv/Scripts/python.exe','node_modules/example','frontend/dist/index.html','backups/database.dump','exports/user_rows.csv','credentials.json','.playwright-cli/state.json']
    ignored={p:subprocess.run(['git','check-ignore','--quiet',p],cwd=ROOT).returncode==0 for p in sentinels}
    fsck=subprocess.run(['git','fsck','--full','--no-reflogs','--unreachable'],cwd=ROOT,capture_output=True,text=True)
    result={'passed':not findings and all(ignored.values()),'branch':git('branch','--show-current').decode().strip(),
        'candidate_files':len(manifest),'candidate_bytes':sum(r['bytes'] for r in manifest),'tracked_files':len(tracked),
        'branch_commits':int(git('rev-list','--all','--count').decode()),'refs':git('for-each-ref','--format=%(refname)').decode().splitlines(),
        'git_object_counts':dict(Counter(row[1] for row in objects)),'git_blobs_content_scanned':len(blobs),
        'unreachable_objects':len(fsck.stdout.splitlines()),'fsck_exit':fsck.returncode,
        'reflog_entries':len(git('reflog','show','--all','--format=%H').decode().splitlines()),
        'configured_remote_count':len(git('remote').decode().splitlines()),'staged_files':git('diff','--cached','--name-only').decode().splitlines(),
        'findings':findings,'example_uri_occurrences':example_uris,'ignore_checks':ignored,
        'scope':'实际候选文件全部字节、所有Git blob（含工具快照和不可达对象）、路径及真实本地秘密/常见凭证模式；仅记录位置和类型，不输出秘密值。非绝对无泄露保证。',
        'git_mutations_performed':False}
    (OUT/'public_safety.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'public_files.json').write_text(json.dumps({'files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
