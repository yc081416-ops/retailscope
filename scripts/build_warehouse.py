"""python scripts/build_warehouse.py; rebuild only P1 objects, leave raw/P0 untouched."""
from pathlib import Path
from dotenv import load_dotenv
from retailscope.warehouse import build_warehouse, save_json, snapshot_mart

load_dotenv()
build_warehouse()
snapshot = snapshot_mart()
save_json(snapshot, Path('reports/p1/build_snapshot.json'))
print({name: result['rows'] for name, result in snapshot.items()})
