import json
from pathlib import Path

_data = json.loads((Path(__file__).parent / 'especies.json').read_text(encoding='utf-8'))

def get_todas() -> list:
    return _data

def get_por_cultivo(cultivo: str) -> list:
    return [e for e in _data if cultivo in e.get('compatible_con', [])]

def get_por_uso(uso: str) -> list:
    return [e for e in _data if uso in e.get('usos', [])]
