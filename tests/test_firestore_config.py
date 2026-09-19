"""INF-403 — Configuracao Firestore NoSQL (southamerica-east1), regras e indices.

Valida que a infraestrutura declarativa do Firestore esta presente e coerente:
firebase.json referencia regras e indices; as regras negam acesso direto de
cliente (o backend usa Admin SDK, que ignora as regras); e o script de
provisionamento cria o banco em southamerica-east1 (Sao Paulo).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_firebase_json_declares_firestore():
    cfg = json.loads((ROOT / "firebase.json").read_text(encoding="utf-8"))
    assert "firestore" in cfg
    assert cfg["firestore"]["rules"] == "firestore.rules"
    assert cfg["firestore"]["indexes"] == "firestore.indexes.json"


def test_firestore_rules_deny_client_access_by_default():
    rules = (ROOT / "firestore.rules").read_text(encoding="utf-8")
    assert "rules_version = '2'" in rules
    assert "allow read, write: if false" in rules


def test_firestore_indexes_declare_messages_timestamp():
    idx = json.loads((ROOT / "firestore.indexes.json").read_text(encoding="utf-8"))
    assert "indexes" in idx
    assert any(i.get("collectionGroup") == "messages" for i in idx["indexes"])


def test_firestore_region_is_southamerica_east1():
    script = (ROOT / "scripts" / "setup-firestore.sh").read_text(encoding="utf-8")
    assert "gcloud firestore databases create" in script
    assert "--location=southamerica-east1" in script
