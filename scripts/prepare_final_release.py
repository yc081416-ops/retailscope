"""Build license/file inventories and run a read-only Git staging rehearsal."""
import importlib.metadata as metadata
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/github-final'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def licenses():
    locked = {}
    for filename in ('requirements-lock.txt', 'api/requirements-lock.txt'):
        for line in (ROOT / filename).read_text().splitlines():
            if '==' in line and not line.startswith('#'):
                name, version = line.split('==', 1)
                assert name not in locked or locked[name] == version
                locked[name] = version
    rows = []
    for name, version in sorted(locked.items()):
        distribution = metadata.distribution(name)
        assert distribution.version == version, name
        fields = distribution.metadata
        rows.append(dict(name=name, version=version, license_expression=fields.get('License-Expression'),
                         license=fields.get('License'), license_classifiers=[v for v in fields.get_all('Classifier', []) if v.startswith('License')],
                         license_files=[str(p) for p in (distribution.files or []) if 'license' in str(p).lower() or 'copying' in str(p).lower()]))
    (OUT / 'python_licenses.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    names = {row['name'].lower().replace('_', '-') for row in rows}
    assert {'psycopg', 'certifi', 'numpy', 'fastapi'} <= names
    lines = ['# 第三方许可与引用组件', '',
             '核查日期：2026-11-13。以下依据锁定版本、已安装 Python 分发元数据与前端锁文件逐项记录；本项目不主张这些内容的版权，也不以根目录 MIT 替换其许可。', '',
             '## 源码中引用的组件', '',
             '`frontend/src/components/ui/button.tsx`、`badge.tsx` 及 `lib/utils.ts` 使用 shadcn/ui 的组件模式。保留以下上游 MIT 声明；作者自己的改动只在其拥有权利的范围内授权。', '',
             '来源：[shadcn/ui LICENSE](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md)。', '']
    # Standard MIT grant, with the upstream copyright retained separately.
    mit = (ROOT / 'LICENSE').read_text(encoding='utf-8')
    assert mit.startswith('MIT License\n\nCopyright (c) 2026 [yan]\n')
    lines += ['```text', mit.replace('Copyright (c) 2026 [yan]', 'Copyright (c) 2023 shadcn').strip(), '```', '',
              '## Python 锁定依赖', '',
              '来源：`requirements-lock.txt`、`api/requirements-lock.txt` 与本机同版本 `*.dist-info/METADATA`、许可文件。长文本仅在下表归一为名称；完整条款仍以原分发中的 LICENSE/NOTICE 为准。', '',
              '| 包 | 版本 | 许可声明 / 文件核对 |', '|---|---|---|']
    for row in rows:
        value = row['license_expression'] or row['license'] or '; '.join(row['license_classifiers'])
        if len(value) > 150 or value.startswith('Copyright'):
            value = 'Apache-2.0' if row['name'] in ('kagglehub', 'kagglesdk') else 'BSD-3-Clause（分发许可正文）'
        if row['name'] in ('Jinja2', 'colorama', 'itsdangerous'):
            value = 'BSD-3-Clause（分发许可正文）'
        if row['name'] == 'protobuf':
            value = 'BSD-3-Clause'
        assert value, row['name']
        lines.append(f"| {row['name']} | {row['version']} | {value.replace('|', '/')} |")
    lock = json.loads((ROOT / 'frontend/package-lock.json').read_text())['packages']
    node = [(path, value) for path, value in lock.items() if path]
    assert all(value.get('license') for _, value in node)
    lines += ['', '## 前端完整锁文件依赖', '',
              '包括运行、开发、传递及平台可选包；锁文件声明不等于逐个审查其内嵌的全部第三方子组件。安装后保留包内 LICENSE/NOTICE；不随源码仓库打包 node_modules 或构建产物。', '',
              '| 锁文件包路径 | 版本 | 声明许可 |', '|---|---|---|']
    for path, value in node:
        lines.append(f"| `{path}` | {value['version']} | {value['license'].replace('|', '/')} |")
    lines += ['', '## 特别说明与后续分发检查', '',
              '- `lucide-react` 图标含 Lucide ISC 与部分 Feather MIT 权利声明，完整通知位于安装包 LICENSE；不能把它们当作作者原创图形。',
              '- NumPy/SciPy 等二进制包含多种随附第三方许可；Psycopg 为 LGPL-3.0-only，certifi 为 MPL-2.0，tqdm 声明 MPL-2.0 AND MIT。它们并非由根目录 MIT 授权。当前仅分发项目源码与依赖清单，没有重打包这些二进制库。',
              '- Streamlit 元数据声明 Apache-2.0，但当前安装元数据清单未列许可文件；可核对 [上游 LICENSE](https://github.com/streamlit/streamlit/blob/develop/LICENSE)。若以后分发安装包、镜像或离线依赖，需补核完整 LICENSE/NOTICE 与二进制附带条款。',
              '- PostgreSQL 使用其 [PostgreSQL License](https://www.postgresql.org/about/licence/)；Docker Desktop 是本机外部工具，受 Docker 自身条款约束，不属于本项目 MIT 授权的代码。镜像与软件安装包未包含在拟发布清单中。',
              '- 已搜索源码中的版权、引用来源及复制标记；没有据此推定所有无标记代码都完全原创。历史生成脚本、文档模板或未标注片段的完整来源链仍需作者确认；发现第三方片段时应保留其声明，不归入作者版权。',
              '- Olist 数据、报告、截图和混合材料见 [数据许可](DATA_LICENSE.md)。将来商业使用、另行分发二进制/构建包或重授权前，应重新审查适用范围。', '']
    (ROOT / 'docs/THIRD_PARTY_LICENSES.md').write_text('\n'.join(lines), encoding='utf-8')
    return dict(python_locked=len(rows), node_locked=len(node), node_licenses=dict(Counter(v['license'] for _, v in node)))


def classify(path):
    if path.startswith('docs/screenshots/showcase/') or path in {'docs/ARCHITECTURE.md', 'docs/METRICS.md', 'docs/P1_DATA_MODEL.md', 'docs/P3_ANALYSIS_METHODS.md', 'docs/P3_BUSINESS_REPORT.md', 'docs/RESUME_PROJECT.md', 'docs/INTERVIEW_GUIDE.md', 'docs/DEMO_SCRIPT.md'}:
        return 'B', '精选展示或核心分析说明'
    if path.startswith(('docs/', 'prompts/')) or path == 'START_HERE_USER.md' or (path.startswith('scripts/') and any(w in Path(path).name for w in ('write_', 'verify_v2', 'verify_p', 'ui_', 'browser_'))):
        if path in {'docs/DATA_LICENSE.md', 'docs/THIRD_PARTY_LICENSES.md', 'docs/GITHUB_PUBLIC_FILES.md', 'docs/GITHUB_FINAL_RELEASE_REPORT.md'}:
            return 'A', '许可或最终发布索引'
        return 'C', '历史/过程资料，保留原路径供引用追溯'
    return 'A', '源码、配置、依赖、测试或必要运行检查'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    license_counts = licenses()
    paths = sorted(filter(None, git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')))
    assert 'LICENSE' in paths and 'docs/THIRD_PARTY_LICENSES.md' in paths
    rows = [dict(path=p, category=classify(p)[0], reason=classify(p)[1]) for p in paths]
    counts = Counter(row['category'] for row in rows)
    lines = ['# GitHub 最终拟公开文件清单', '',
             f'共 {len(rows)} 个实际候选文件：A 必须公开 {counts["A"]}、B 重点展示 {counts["B"]}、C 历史资料 {counts["C"]}。尚未暂存或提交。', '',
             '本清单逐文件分类。历史材料采用逻辑归档：保留物理路径，按 C 类集中索引；首页仅精选 9 张最新版图片，不把历史截图混作当前界面。没有删除本地历史文件、移动引用目标或重写 Git 历史。', '',
             'C 类中的阶段验收、旧 UI 图片、历史验证与生成脚本用于追溯，不是当前启动流程；不要用历史生成脚本覆盖当前 README 或许可配置。', '',
             '本地详细字节、SHA256、安全检查和 dry-run 证据见被忽略的 `reports/github-final/`。', '']
    for category, title in [('A', '必须公开'), ('B', '重点展示'), ('C', '历史归档索引')]:
        lines += [f'## {category} · {title}', '', '| 文件 | 用途 |', '|---|---|']
        lines += [f"| `{r['path']}` | {r['reason']} |" for r in rows if r['category'] == category]
        lines.append('')
    (ROOT / 'docs/GITHUB_PUBLIC_FILES.md').write_text('\n'.join(lines), encoding='utf-8')
    staged_before = git('diff', '--cached', '--name-only')
    rehearsal = git('add', '--dry-run', '--', '.')
    (OUT / 'git_add_dry_run.txt').write_bytes(rehearsal)
    assert git('diff', '--cached', '--name-only') == staged_before == b''
    assert len(rehearsal.splitlines()) == len(paths)
    large = [dict(path=p, bytes=(ROOT/p).stat().st_size) for p in paths if (ROOT/p).stat().st_size > 5*1024*1024]
    assert not large, large
    assert not git('remote')
    main_ref = subprocess.run(['git', 'rev-parse', '--verify', 'refs/heads/main'], cwd=ROOT, capture_output=True)
    result = dict(candidates=len(paths), categories=dict(counts), licenses=license_counts,
                  dry_run_files=len(rehearsal.splitlines()), index_unchanged=True,
                  main_exists=main_ref.returncode == 0, main_reachable_objects=0 if main_ref.returncode else None,
                  large_files_over_5mb=large)
    (OUT/'preparation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
