#!/usr/bin/env python3
"""
meta:
    artifact_id: TST-G4-EVAL-007
    file: g4_deepeval.py
    author: '@juria.koga'
    source_type: human
    source: manual
    timestamp: '2026-03-03T18:35:00+09:00'
    content_hash: d42c5504d6a020a5436c114fd2347d42a161e2a68b72ed9fed9d07d8ca46dc10
---
G4 DeepEval Gate — Transform Quality Check (Faithfulness + Global Coverage + Global Consistency)
=============================================================================================

狙い:
- Faithfulness（ファイル単位）: 参照にない創作（ハルシネーション）を検出
    ※タイムアウト対策として「参照全文」ではなく「関連参照チャンク上位K」を retrieval_context に投入する
- Global Coverage（集合単位/ルールベース）: 参照の主要論点が、YAML集合として抜けていないか
- Global Consistency（横断/ルールベース）: 分割YAML間や参照との矛盾を検出

環境変数:
    AIDD_STAGE                 : 対象工程 (例: PLN, REQ)
    AIDD_YAML_DIR              : 評価対象YAMLディレクトリ
    AIDD_OUT_ROOT              : 出力ルートディレクトリ
    AIDD_EVAL_MODEL            : 使用モデル (例: gpt-5.2)  ※deepeval側に渡す

    # 参照入力（複数指定に対応）
    AIDD_REF_PATHS             : 参照ファイル/ディレクトリのカンマ区切り（md/yaml/dir/glob混在OK）
                                例: "artifacts/planning/PLN-PLN-FLW-003.md,artifacts/planning/yaml/v3"
    AIDD_FILE_PATH             : 旧互換（単一参照）
    AIDD_MD_PATH               : 旧互換（単一参照）
    AIDD_REF_MODE              : AUTO|MD|YAML（AUTOは拡張子で判定）

    # Faithfulness（タイムアウト対策あり）
    AIDD_FAITHFULNESS_SKIP     : カンマ区切りのファイル名リスト、または "*"（全スキップ）
    AIDD_FAITHFULNESS_SKIP_DERIVED_FROM_SCOPE : 1で有効（既定 1）
        - derived_from が存在し、参照セット内のいずれのファイル名も含まれない場合はスコープ外としてSKIP
    AIDD_FAITHFULNESS_TOPK_REF_CHUNKS : Faithfulnessに渡す参照チャンク数（既定 4）
    AIDD_FAITHFULNESS_REF_CHUNK_MAX_CHARS : 参照チャンク1個の最大文字数（既定 900）

    # ★追加（このスクリプトで利用可能）
    AIDD_FAITHFULNESS_USE_DERIVED_FROM_CONTEXT : 1で有効（既定 1）
        - derived_from に一致する参照ファイル名だけを Faithfulness の参照チャンク候補にする
        - derived_from が空/不一致の場合は従来どおり参照全体から選ぶ（フォールバック）

    # 重要: 未設定でも既定値で truncate する（無制限だとタイムアウトしやすい）
    AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS   : actual_output の最大文字数（既定 1800）
    AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS  : retrieval_context 合計の最大文字数（既定 2200）
    AIDD_FAITHFULNESS_TRUTHS_LIMIT       : truths抽出上限（deepevalが対応していれば効く、既定 10）

    AIDD_FAITHFULNESS_RETRY_ON_TIMEOUT   : 1で有効（既定 1）
    AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS_RETRY  : リトライ時 actual_output 最大文字数（既定 1200）
    AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS_RETRY : リトライ時 retrieval_context 最大文字数（既定 1600）
    AIDD_FAITHFULNESS_TRUTHS_LIMIT_RETRY      : リトライ時 truths上限（既定 6）

    # Global Coverage（ルールベース）
    AIDD_COVERAGE_ENABLE        : 1で有効（既定 1）
    AIDD_COVERAGE_MAX_ITEMS     : 参照から抽出する論点数の上限（既定 80）
    AIDD_COVERAGE_MIN_ITEM_LEN  : 論点として採用する最小文字数（既定 6）
    AIDD_COVERAGE_SIM_THRESHOLD : 簡易類似度閾値（既定 0.25）
    AIDD_COVERAGE_SKIP_HEADINGS : 見出し(#...)を論点抽出に含めるか（0で含めない、既定 0）

    # Global Consistency（ルールベース）
    AIDD_CONSISTENCY_ENABLE     : 1で有効（既定 1）
    AIDD_CONSISTENCY_MAX_FACTS_PER_FILE : 1ファイルから抽出するscalar fact上限（既定 1200）
    AIDD_CONSISTENCY_IGNORE_KEYS: 無視したいキー（カンマ区切り、部分一致）
    既定: "meta.,timestamp,updated_at,created_at,hash,checksum,rationale,ssot_note,primary_section,traceability.,referenced_internal_ids"
"""

import os
import sys
import glob
import json
import uuid
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Tuple, Set, Optional

import yaml

DEEPEVAL_AVAILABLE = True
try:
    from deepeval.metrics import FaithfulnessMetric
    from deepeval.test_case import LLMTestCase
except Exception:
    DEEPEVAL_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────

STAGE = os.environ.get("AIDD_STAGE", "PLN")
YAML_DIR = os.environ.get("AIDD_YAML_DIR", "artifacts/planning/yaml/v3")
OUT_ROOT = os.environ.get("AIDD_OUT_ROOT", "output/G4/transform")
EVAL_MODEL = os.environ.get("AIDD_EVAL_MODEL", "gpt-5.2")

REF_MODE = os.environ.get("AIDD_REF_MODE", "AUTO").upper().strip()

REF_PATHS_RAW = os.environ.get("AIDD_REF_PATHS", "").strip()
FILE_PATH = os.environ.get("AIDD_FILE_PATH", "").strip()
if not FILE_PATH:
    FILE_PATH = os.environ.get("AIDD_MD_PATH", "artifacts/planning/PLN-PLN-FLW-002.md").strip()

if REF_PATHS_RAW:
    REF_INPUTS = [p.strip() for p in REF_PATHS_RAW.split(",") if p.strip()]
else:
    REF_INPUTS = [FILE_PATH] if FILE_PATH else []

_skip_raw = os.environ.get("AIDD_FAITHFULNESS_SKIP", "")
FAITHFULNESS_SKIP_ALL = _skip_raw.strip() == "*"
FAITHFULNESS_SKIP_FILES = {s.strip() for s in _skip_raw.split(",") if s.strip() and s.strip() != "*"}

SKIP_DERIVED_SCOPE = os.environ.get("AIDD_FAITHFULNESS_SKIP_DERIVED_FROM_SCOPE", "1").lower() in ("1", "true", "yes")

# ★ derived_from を retrieval_context 絞り込みに使う（既定ON）
USE_DERIVED_FROM_CONTEXT = os.environ.get("AIDD_FAITHFULNESS_USE_DERIVED_FROM_CONTEXT", "1").lower() in ("1", "true", "yes")

TOPK_REF_CHUNKS = int(os.environ.get("AIDD_FAITHFULNESS_TOPK_REF_CHUNKS", "4") or "4")
REF_CHUNK_MAX_CHARS = int(os.environ.get("AIDD_FAITHFULNESS_REF_CHUNK_MAX_CHARS", "900") or "900")

# 未設定でも既定値を効かせる（無制限は事故る）
FAITH_ACTUAL_MAX = int(os.environ.get("AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS", "1800") or "1800")
FAITH_CTX_MAX = int(os.environ.get("AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS", "2200") or "2200")
FAITH_TRUTHS_LIM = int(os.environ.get("AIDD_FAITHFULNESS_TRUTHS_LIMIT", "10") or "10")

RETRY_ON_TIMEOUT = os.environ.get("AIDD_FAITHFULNESS_RETRY_ON_TIMEOUT", "1").lower() in ("1", "true", "yes")
RETRY_ACTUAL_MAX = int(os.environ.get("AIDD_FAITHFULNESS_ACTUAL_MAX_CHARS_RETRY", "1200") or "1200")
RETRY_CTX_MAX = int(os.environ.get("AIDD_FAITHFULNESS_CONTEXT_MAX_CHARS_RETRY", "1600") or "1600")
RETRY_TRUTHS_LIM = int(os.environ.get("AIDD_FAITHFULNESS_TRUTHS_LIMIT_RETRY", "6") or "6")

WARN_THRESHOLD = 0.70

COVERAGE_ENABLE = os.environ.get("AIDD_COVERAGE_ENABLE", "1").lower() in ("1", "true", "yes")
COV_MAX_ITEMS = int(os.environ.get("AIDD_COVERAGE_MAX_ITEMS", "80") or "80")
COV_MIN_ITEM_LEN = int(os.environ.get("AIDD_COVERAGE_MIN_ITEM_LEN", "6") or "6")
COV_SIM_THRESHOLD = float(os.environ.get("AIDD_COVERAGE_SIM_THRESHOLD", "0.25") or "0.25")
COV_SKIP_HEADINGS = os.environ.get("AIDD_COVERAGE_SKIP_HEADINGS", "1").lower() in ("1", "true", "yes")

CONSISTENCY_ENABLE = os.environ.get("AIDD_CONSISTENCY_ENABLE", "1").lower() in ("1", "true", "yes")
CONS_MAX_FACTS_PER_FILE = int(os.environ.get("AIDD_CONSISTENCY_MAX_FACTS_PER_FILE", "1200") or "1200")

CONS_IGNORE_KEYS_RAW = os.environ.get(
    "AIDD_CONSISTENCY_IGNORE_KEYS",
    "meta.,timestamp,updated_at,created_at,hash,checksum,rationale,ssot_note,primary_section,traceability.,referenced_internal_ids"
).strip()
CONS_IGNORE_KEYS = [k.strip().lower() for k in CONS_IGNORE_KEYS_RAW.split(",") if k.strip()]


# ──────────────────────────────────────────────────────────────────────────────
# IO / parsing
# ──────────────────────────────────────────────────────────────────────────────

def load_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()

def load_yaml_file(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_yaml_dir(yaml_dir: str) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for fp in sorted(glob.glob(str(Path(yaml_dir) / "*.yaml"))):
        content = load_text(fp)
        data = yaml.safe_load(content) or {}
        result[fp] = {"content": content, "data": data}
    return result

def infer_ref_mode_by_ext(file_path: str, ref_mode: str) -> str:
    if ref_mode in ("MD", "YAML"):
        return ref_mode
    ext = Path(file_path).suffix.lower()
    if ext == ".md":
        return "MD"
    if ext in (".yaml", ".yml"):
        return "YAML"
    return "MD"

def normalize_filename(p: str) -> str:
    try:
        return Path(str(p)).name
    except Exception:
        return str(p)

def expand_ref_inputs(ref_inputs: List[str]) -> List[str]:
    out: List[str] = []
    for p in ref_inputs:
        if not p:
            continue
        pp = Path(p)
        if pp.is_dir():
            for ext in ("*.md", "*.yaml", "*.yml"):
                out.extend([str(x) for x in sorted(pp.rglob(ext))])
        elif pp.is_file():
            out.append(str(pp))
        else:
            matches = sorted(glob.glob(p, recursive=True))
            for m in matches:
                mp = Path(m)
                if mp.is_dir():
                    for ext in ("*.md", "*.yaml", "*.yml"):
                        out.extend([str(x) for x in sorted(mp.rglob(ext))])
                elif mp.is_file():
                    out.append(str(mp))
    seen: Set[str] = set()
    uniq: List[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

def truncate(s: str, max_chars: int) -> str:
    if not max_chars or max_chars <= 0:
        return s
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n...(truncated)"


# ──────────────────────────────────────────────────────────────────────────────
# Tiny similarity utils (Jaccard)
# ──────────────────────────────────────────────────────────────────────────────

_TOKEN_SPLIT = re.compile(r"[\s、。．，,;；:：\(\)\[\]\{\}<>「」『』【】/\\|]+")
_PUNCT = re.compile(r"[^\wぁ-んァ-ン一-龥]+")

def tokenize_ja_en(s: str) -> Set[str]:
    s = s.lower()
    s = _PUNCT.sub(" ", s)
    parts = [p for p in _TOKEN_SPLIT.split(s) if p]
    return {p for p in parts if len(p) >= 2}

def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni else 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Reference chunking (timeout mitigation)
# ──────────────────────────────────────────────────────────────────────────────

def _strip_md_formatting(s: str) -> str:
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)  # links
    s = re.sub(r"[*_~]", "", s)
    return s.strip()

def chunk_md(text: str, file_name: str, max_chars: int) -> List[dict]:
    """
    MDを「見出し単位」でチャンク化。見出しが無い場合は段落単位で分割。
    """
    lines = text.splitlines()
    chunks: List[dict] = []
    cur_title = ""
    buf: List[str] = []

    def flush():
        nonlocal buf, cur_title
        if not buf:
            return
        body = "\n".join(buf).strip()
        if body:
            body = truncate(body, max_chars)
            chunks.append({
                "ref": file_name,
                "title": cur_title or file_name,
                "text": body,
                "tokens": tokenize_ja_en(body),
            })
        buf = []

    for ln in lines:
        s = ln.rstrip()
        if re.match(r"^#{1,6}\s+", s):
            flush()
            cur_title = _strip_md_formatting(re.sub(r"^#{1,6}\s+", "", s).strip())
            continue
        # separator lines break chunk too
        if s.strip().startswith("====="):
            flush()
            continue
        buf.append(s)

        # prevent huge chunks
        if sum(len(x) + 1 for x in buf) >= max_chars * 2:
            flush()

    flush()

    # fallback: if no chunks (empty md), make one
    if not chunks:
        t = truncate(text.strip(), max_chars)
        chunks = [{
            "ref": file_name,
            "title": file_name,
            "text": t,
            "tokens": tokenize_ja_en(t),
        }]
    return chunks

def chunk_yaml(data: Any, file_name: str, max_chars: int) -> List[dict]:
    """
    YAMLを「トップレベルキー」単位でダンプしてチャンク化。
    """
    chunks: List[dict] = []
    if isinstance(data, dict):
        for k, v in data.items():
            sub = {k: v}
            dumped = yaml.dump(sub, allow_unicode=True, sort_keys=False, default_flow_style=False)
            dumped = truncate(dumped, max_chars)
            chunks.append({
                "ref": file_name,
                "title": f"{file_name}:{k}",
                "text": dumped,
                "tokens": tokenize_ja_en(dumped),
            })
    else:
        dumped = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
        dumped = truncate(dumped, max_chars)
        chunks.append({
            "ref": file_name,
            "title": file_name,
            "text": dumped,
            "tokens": tokenize_ja_en(dumped),
        })
    return chunks

def build_reference_chunks(ref_files: List[str], ref_mode: str, chunk_max_chars: int) -> Tuple[List[dict], Set[str]]:
    all_chunks: List[dict] = []
    names: Set[str] = set()
    for fp in ref_files:
        mode = infer_ref_mode_by_ext(fp, ref_mode)
        name = Path(fp).name
        names.add(name)
        if mode == "MD":
            txt = load_text(fp)
            all_chunks.extend(chunk_md(txt, name, chunk_max_chars))
        else:
            data = load_yaml_file(fp)
            all_chunks.extend(chunk_yaml(data, name, chunk_max_chars))
    return all_chunks, names

def select_topk_ref_chunks(yaml_content: str, ref_chunks: List[dict], topk: int, total_ctx_max: int) -> List[str]:
    """
    YAML内容に対して類似度の高い参照チャンクを上位K個選び、合計文字数を total_ctx_max に収める。
    """
    qtok = tokenize_ja_en(yaml_content[:4000])  # query側は先頭だけで十分
    scored: List[Tuple[float, dict]] = []
    for ch in ref_chunks:
        s = jaccard(qtok, ch.get("tokens") or set())
        scored.append((s, ch))
    scored.sort(key=lambda x: x[0], reverse=True)

    chosen: List[str] = []
    used = 0
    for s, ch in scored[:max(1, topk * 4)]:  # topk候補の母集団を少し広げる
        txt = ch["text"]
        header = f"===== REF_CHUNK: {ch['ref']} :: {ch['title']} (sim={s:.3f}) =====\n"
        block = header + txt.strip() + "\n"
        if not block.strip():
            continue
        if used + len(block) > total_ctx_max and chosen:
            break
        # 1個目だけは必ず入れる（空を避ける）
        if used + len(block) > total_ctx_max and not chosen:
            block = truncate(block, total_ctx_max)
        chosen.append(block)
        used += len(block)
        if len(chosen) >= topk:
            break

    if not chosen:
        # 最低限
        chosen = [truncate(ref_chunks[0]["text"], total_ctx_max)] if ref_chunks else [""]
    return chosen


# ──────────────────────────────────────────────────────────────────────────────
# Faithfulness: derived_from scope control
# ──────────────────────────────────────────────────────────────────────────────

def derived_from_list(yaml_data: dict) -> List[str]:
    df = yaml_data.get("derived_from") or []
    if isinstance(df, str):
        return [df]
    if isinstance(df, list):
        return [str(x) for x in df if x is not None]
    return []

def _derived_from_name_candidates(yaml_data: dict) -> Set[str]:
    """
    derived_from の表記揺れ（パス/ファイル名）を吸収するために、
    - basename（例: PLN-PLN-ALLURE-001.md）
    - もし拡張子が無ければ .md/.yaml/.yml も候補に追加
    を返す。
    """
    out: Set[str] = set()
    for x in derived_from_list(yaml_data):
        n = normalize_filename(x)
        if not n:
            continue
        out.add(n)
        p = Path(n)
        if p.suffix == "":
            out.add(p.name + ".md")
            out.add(p.name + ".yaml")
            out.add(p.name + ".yml")
    return out

def should_skip_by_derived_from_scope(yaml_data: dict, ref_names: Set[str]) -> Tuple[bool, str]:
    df = derived_from_list(yaml_data)
    if not df:
        return False, ""
    df_names = {normalize_filename(x) for x in df}
    if df_names.isdisjoint(ref_names):
        return True, f"[SKIP] derived_from に参照セット({sorted(ref_names)})が無いためスコープ外（derived_from={sorted(df_names)})"
    return False, ""

def is_qa_supplement(yaml_data: dict, ref_names: Set[str]) -> bool:
    for ref in derived_from_list(yaml_data):
        ref_name = normalize_filename(ref)
        if ref_name in ref_names:
            continue
        if ref_name.lower().endswith((".md", ".yaml", ".yml")):
            return True
    return False

def filter_ref_chunks_by_derived_from(
    yaml_data: dict,
    ref_chunks: List[dict],
    ref_names: Set[str],
) -> Tuple[List[dict], Set[str]]:
    """
    derived_from に一致する ref 名だけに ref_chunks を絞る。
    - 一致候補が参照セット(ref_names)に1つでも存在すれば、その集合でフィルタ
    - 一致が無ければフォールバックで全体を返す
    """
    df_candidates = _derived_from_name_candidates(yaml_data)
    df_hits = {n for n in df_candidates if n in ref_names}
    if not df_hits:
        return ref_chunks, set()

    filtered = [ch for ch in ref_chunks if ch.get("ref") in df_hits]
    if not filtered:
        # チャンク生成の ref 名が想定とズレた場合の保険
        return ref_chunks, set()

    return filtered, df_hits


# ──────────────────────────────────────────────────────────────────────────────
# Timeout detection
# ──────────────────────────────────────────────────────────────────────────────

_TIMEOUT_HINT = re.compile(
    r"(Timeout|ReadTimeout|timed out|TimeoutError|Deadline|LengthFinishReasonError|RetryError)",
    re.IGNORECASE,
)

def is_timeout_like(exc: Exception) -> bool:
    msg = str(exc) or ""
    if _TIMEOUT_HINT.search(msg):
        return True
    cause = getattr(exc, "__cause__", None)
    if cause and _TIMEOUT_HINT.search(str(cause) or ""):
        return True
    ctx = getattr(exc, "__context__", None)
    if ctx and _TIMEOUT_HINT.search(str(ctx) or ""):
        return True
    return False


# ──────────────────────────────────────────────────────────────────────────────
# deepeval Faithfulness builder
# ──────────────────────────────────────────────────────────────────────────────

def build_faith_metric(truths_limit: int):
    base_kwargs = {
        "threshold": WARN_THRESHOLD,
        "model": EVAL_MODEL,
        "include_reason": False,   # タイムアウト優先で理由は切る
        "async_mode": False,
    }
    extra_kwargs = {}
    if truths_limit and truths_limit > 0:
        extra_kwargs["truths_extraction_limit"] = truths_limit
    extra_kwargs["penalize_ambiguous_claims"] = True
    try:
        return FaithfulnessMetric(**base_kwargs, **extra_kwargs)
    except TypeError:
        return FaithfulnessMetric(**base_kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Faithfulness evaluation
# ──────────────────────────────────────────────────────────────────────────────

def auto_pass_result(fname: str, fp: str, reason: str, category: str = "faithfulness") -> dict:
    return {
        "test_name": f"{category.capitalize()} :: {fname}",
        "category": category,
        "file": fp,
        "score": 1.0,
        "passed": True,
        "status": "pass",
        "reason": reason,
        "duration_ms": 0,
        "retried": False,
    }

def eval_one_faithfulness(
    fname: str,
    yaml_content: str,
    ref_context_list: List[str],
    actual_max: int,
    ctx_max: int,
    truths_limit: int,
) -> Tuple[float, bool, str]:
    metric = build_faith_metric(truths_limit)

    # retrieval_context は複数要素OKだが、合計で ctx_max に抑える
    joined = "\n".join(ref_context_list)
    joined = truncate(joined, ctx_max)

    tc = LLMTestCase(
        input=(
            f"この構造化YAMLファイル（{fname}）は、参照の内容を忠実に構造化したものですか？"
            "参照に存在しない内容の創作（ハルシネーション）がないかを評価してください。"
        ),
        actual_output=truncate(yaml_content, actual_max),
        retrieval_context=[joined],
    )
    metric.measure(tc)
    score = float(metric.score)
    passed = bool(metric.is_successful())
    return score, passed, ""

def eval_faithfulness(
    ref_chunks: List[dict],
    ref_names: Set[str],
    yaml_files: Dict[str, Dict[str, Any]],
) -> List[dict]:
    results: List[dict] = []

    if not DEEPEVAL_AVAILABLE:
        for fp in yaml_files.keys():
            fname = Path(fp).name
            results.append({
                "test_name": f"Faithfulness :: {fname}",
                "category": "faithfulness",
                "file": fp,
                "score": 0.0,
                "passed": False,
                "status": "error",
                "reason": "deepeval is not available in this runtime (cannot import deepeval).",
                "duration_ms": 0,
                "retried": False,
            })
        return results

    for fp, info in yaml_files.items():
        fname = Path(fp).name
        yaml_data = info["data"]
        yaml_content = info["content"]
        start = time.time()

        if FAITHFULNESS_SKIP_ALL:
            r = auto_pass_result(fname, fp, "[SKIP] AIDD_FAITHFULNESS_SKIP=* により全スキップ")
            r["duration_ms"] = int((time.time() - start) * 1000)
            results.append(r)
            continue

        if fname in FAITHFULNESS_SKIP_FILES:
            r = auto_pass_result(fname, fp, f"[SKIP] AIDD_FAITHFULNESS_SKIP に明示指定（{fname}）")
            r["duration_ms"] = int((time.time() - start) * 1000)
            results.append(r)
            continue

        if SKIP_DERIVED_SCOPE:
            skip_df, msg_df = should_skip_by_derived_from_scope(yaml_data, ref_names)
            if skip_df:
                r = auto_pass_result(fname, fp, msg_df)
                r["duration_ms"] = int((time.time() - start) * 1000)
                results.append(r)
                continue

        if is_qa_supplement(yaml_data, ref_names):
            r = auto_pass_result(fname, fp, "[AUTO-PASS] 補足資料由来のファイルとしてFaithfulness自動PASS")
            r["duration_ms"] = int((time.time() - start) * 1000)
            results.append(r)
            continue

        # ★ derived_from による参照候補の絞り込み（ヒット無しなら全体フォールバック）
        used_ref_chunks = ref_chunks
        df_hits: Set[str] = set()
        if USE_DERIVED_FROM_CONTEXT:
            used_ref_chunks, df_hits = filter_ref_chunks_by_derived_from(yaml_data, ref_chunks, ref_names)

        # 参照チャンク上位Kを選ぶ（ここがタイムアウト対策の本体）
        ref_ctx = select_topk_ref_chunks(
            yaml_content=yaml_content,
            ref_chunks=used_ref_chunks,
            topk=TOPK_REF_CHUNKS,
            total_ctx_max=FAITH_CTX_MAX,
        )

        extra_note = f" derived_from_ctx={sorted(df_hits)}" if df_hits else ""
        print(f"  [EVAL] Faithfulness: {fname} ...{extra_note}", end=" ", flush=True)
        try:
            score, passed, reason = eval_one_faithfulness(
                fname=fname,
                yaml_content=yaml_content,
                ref_context_list=ref_ctx,
                actual_max=FAITH_ACTUAL_MAX,
                ctx_max=FAITH_CTX_MAX,
                truths_limit=FAITH_TRUTHS_LIM,
            )
            status = "pass" if passed else ("warn" if score >= 0.5 else "fail")
            print(f"score={score:.3f} → {status.upper()}")

            results.append({
                "test_name": f"Faithfulness :: {fname}",
                "category": "faithfulness",
                "file": fp,
                "score": round(score, 4),
                "passed": bool(passed),
                "status": status,
                "reason": reason,
                "duration_ms": int((time.time() - start) * 1000),
                "retried": False,
                "derived_from_context": sorted(df_hits) if df_hits else [],
            })

        except Exception as exc:
            if RETRY_ON_TIMEOUT and is_timeout_like(exc):
                print("TIMEOUT → RETRY", flush=True)
                try:
                    # リトライ時は context もさらに絞る（Kを減らす＋文字数を減らす）
                    ref_ctx_retry = select_topk_ref_chunks(
                        yaml_content=yaml_content,
                        ref_chunks=used_ref_chunks,
                        topk=max(1, TOPK_REF_CHUNKS // 2),
                        total_ctx_max=RETRY_CTX_MAX,
                    )
                    score, passed, reason = eval_one_faithfulness(
                        fname=fname,
                        yaml_content=yaml_content,
                        ref_context_list=ref_ctx_retry,
                        actual_max=RETRY_ACTUAL_MAX,
                        ctx_max=RETRY_CTX_MAX,
                        truths_limit=RETRY_TRUTHS_LIM,
                    )
                    status = "pass" if passed else ("warn" if score >= 0.5 else "fail")
                    print(f"  [RETRY OK] score={score:.3f} → {status.upper()}")

                    results.append({
                        "test_name": f"Faithfulness :: {fname}",
                        "category": "faithfulness",
                        "file": fp,
                        "score": round(score, 4),
                        "passed": bool(passed),
                        "status": status,
                        "reason": "",
                        "duration_ms": int((time.time() - start) * 1000),
                        "retried": True,
                        "retry_params": {
                            "topk_ref_chunks": max(1, TOPK_REF_CHUNKS // 2),
                            "actual_max_chars": RETRY_ACTUAL_MAX,
                            "context_max_chars": RETRY_CTX_MAX,
                            "truths_limit": RETRY_TRUTHS_LIM,
                        },
                        "first_error": str(exc),
                        "derived_from_context": sorted(df_hits) if df_hits else [],
                    })
                    continue
                except Exception as exc2:
                    print(f"  [RETRY FAIL] {exc2}", flush=True)
                    results.append({
                        "test_name": f"Faithfulness :: {fname}",
                        "category": "faithfulness",
                        "file": fp,
                        "score": 0.0,
                        "passed": False,
                        "status": "error",
                        "reason": f"Timeout-like error then retry failed. first={exc} / retry={exc2}",
                        "duration_ms": int((time.time() - start) * 1000),
                        "retried": True,
                        "first_error": str(exc),
                        "retry_error": str(exc2),
                        "derived_from_context": sorted(df_hits) if df_hits else [],
                    })
                    continue

            print(f"ERROR: {exc}", flush=True)
            results.append({
                "test_name": f"Faithfulness :: {fname}",
                "category": "faithfulness",
                "file": fp,
                "score": 0.0,
                "passed": False,
                "status": "error",
                "reason": str(exc),
                "duration_ms": int((time.time() - start) * 1000),
                "retried": False,
                "derived_from_context": sorted(df_hits) if df_hits else [],
            })

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Global Coverage (rule-based)
# ──────────────────────────────────────────────────────────────────────────────

def extract_reference_items_for_coverage(ref_texts: List[str], max_items: int, min_len: int, skip_headings: bool) -> List[str]:
    items: List[str] = []
    for txt in ref_texts:
        for line in txt.splitlines():
            raw = line.strip()
            if not raw:
                continue
            if raw.startswith("====="):
                continue

            is_heading = bool(re.match(r"^#{1,6}\s+", raw))
            is_bullet = bool(re.match(r"^([-*+]|(\d+\.))\s+", raw))

            if skip_headings and is_heading:
                continue

            if not (is_heading or is_bullet):
                continue

            s = raw
            s = re.sub(r"^#{1,6}\s+", "", s)
            s = re.sub(r"^([-*+]|(\d+\.))\s+", "", s)
            s = _strip_md_formatting(s)

            if s.lower() in ("todo", "tbd", "pending"):
                continue
            if len(s) < min_len:
                continue

            items.append(s)
            if len(items) >= max_items:
                break
        if len(items) >= max_items:
            break

    seen: Set[str] = set()
    uniq: List[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq

def compute_global_coverage(ref_items: List[str], yaml_files: Dict[str, Dict[str, Any]], sim_th: float) -> Tuple[float, List[dict]]:
    corpus_lines: List[str] = []
    for info in yaml_files.values():
        for ln in info["content"].splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            corpus_lines.append(ln)

    line_tokens: List[Set[str]] = [tokenize_ja_en(l) for l in corpus_lines]

    details: List[dict] = []
    covered = 0

    for item in ref_items:
        it_tok = tokenize_ja_en(item)
        best = 0.0
        best_line = ""
        for ln, tok in zip(corpus_lines, line_tokens):
            if not tok:
                continue
            s = jaccard(it_tok, tok)
            if s > best:
                best = s
                best_line = ln
            if best >= 0.85:
                break

        is_cov = best >= sim_th
        if is_cov:
            covered += 1

        details.append({
            "item": item,
            "covered": is_cov,
            "best_sim": round(best, 4),
            "best_match": best_line[:240] + ("..." if len(best_line) > 240 else ""),
        })

    score = (covered / len(ref_items)) if ref_items else 1.0
    return score, details


# ──────────────────────────────────────────────────────────────────────────────
# Global Consistency (rule-based)
# ──────────────────────────────────────────────────────────────────────────────

def should_ignore_key(path_key: str) -> bool:
    lk = path_key.lower()
    for ig in CONS_IGNORE_KEYS:
        if ig and ig in lk:
            return True
    return False

def is_scalar(x: Any) -> bool:
    return isinstance(x, (str, int, float, bool)) or x is None

def scalar_norm(x: Any) -> str:
    if x is None:
        return "null"
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, (int, float)):
        if isinstance(x, float) and x.is_integer():
            x = int(x)
        return str(x)
    s = str(x).strip()
    s = re.sub(r"\s+", " ", s)
    return s

def collect_scalar_facts(data: Any, prefix: str = "", out: Optional[List[Tuple[str, str]]] = None, limit: int = 1200) -> List[Tuple[str, str]]:
    if out is None:
        out = []
    if len(out) >= limit:
        return out

    if isinstance(data, dict):
        for k, v in data.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            if should_ignore_key(p):
                continue
            collect_scalar_facts(v, p, out, limit)
            if len(out) >= limit:
                break
    elif isinstance(data, list):
        for i, v in enumerate(data):
            p = f"{prefix}[{i}]"
            collect_scalar_facts(v, p, out, limit)
            if len(out) >= limit:
                break
    else:
        if is_scalar(data) and prefix:
            out.append((prefix, scalar_norm(data)))

    return out

_NUM_FACT = re.compile(
    r"(?P<label>(threshold|thresh|warn|warning|pass|fail|fatal|score|avg|average|minimum|max|maximum))[^0-9]{0,20}(?P<num>\d+(\.\d+)?)",
    re.IGNORECASE,
)

def extract_numeric_constraints(ref_texts: List[str]) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    blob = "\n".join(ref_texts)
    for m in _NUM_FACT.finditer(blob):
        label = (m.group("label") or "").lower()
        num = m.group("num")
        if label and num:
            out.setdefault(label, set()).add(num)
    return out

def scan_numeric_in_yaml(yaml_files: Dict[str, Dict[str, Any]]) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    for info in yaml_files.values():
        txt = info["content"]
        for m in _NUM_FACT.finditer(txt):
            label = (m.group("label") or "").lower()
            num = m.group("num")
            if label and num:
                out.setdefault(label, set()).add(num)
    return out

def compute_global_consistency(
    yaml_files: Dict[str, Dict[str, Any]],
    ref_texts: List[str],
) -> Tuple[float, List[dict]]:
    path_map: Dict[str, Dict[str, List[str]]] = {}

    for fp, info in yaml_files.items():
        facts = collect_scalar_facts(info["data"], limit=CONS_MAX_FACTS_PER_FILE)
        for path, val in facts:
            if not path:
                continue
            if should_ignore_key(path):
                continue
            pv = path_map.setdefault(path, {})
            pv.setdefault(val, []).append(Path(fp).name)

    contradictions: List[dict] = []
    checked_paths = 0
    consistent_paths = 0

    for path, vmap in path_map.items():
        vals = list(vmap.keys())
        checked_paths += 1
        if len(vals) <= 1:
            consistent_paths += 1
            continue
        contradictions.append({
            "type": "path_value_conflict",
            "path": path,
            "values": [{"value": v, "files": sorted(fs)} for v, fs in vmap.items()],
        })

    ref_nums = extract_numeric_constraints(ref_texts)
    yaml_nums = scan_numeric_in_yaml(yaml_files)
    for label, expected in ref_nums.items():
        observed = yaml_nums.get(label, set())
        if not observed:
            continue
        if not observed.issubset(expected) or not expected.issubset(observed):
            contradictions.append({
                "type": "numeric_mismatch",
                "label": label,
                "expected": sorted(expected),
                "observed": sorted(observed),
            })

    path_conflicts = sum(1 for c in contradictions if c["type"] == "path_value_conflict")
    numeric_conflicts = sum(1 for c in contradictions if c["type"] == "numeric_mismatch")

    if checked_paths <= 0:
        base = 1.0
    else:
        base = 1.0 - (path_conflicts / checked_paths)

    score = max(0.0, min(1.0, base - (0.05 * numeric_conflicts)))
    return score, contradictions


# ──────────────────────────────────────────────────────────────────────────────
# Output / Allure
# ──────────────────────────────────────────────────────────────────────────────

def summary(results: List[dict]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    scores = [float(r.get("score", 0.0)) for r in results if "score" in r]
    avg = (sum(scores) / len(scores)) if scores else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "avg_score": round(avg, 4),
        "warning": avg < WARN_THRESHOLD,
    }

def make_out_paths(out_root: str) -> Tuple[Path, Path]:
    yaml_subdir = YAML_DIR.replace("\\", "_").replace("/", "_").strip("_")
    ts_fname = datetime.now().strftime("%m%d_%H%M") + ".json"
    base_dir = Path(out_root) / yaml_subdir
    return base_dir / ts_fname, base_dir / "allure-results"

def write_results(all_results: List[dict], out_root: str, meta: dict) -> dict:
    json_path, allure_dir = make_out_paths(out_root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    allure_dir.mkdir(parents=True, exist_ok=True)

    overall_pass = all(r.get("passed", False) for r in all_results)

    faith_results = [r for r in all_results if r["category"] == "faithfulness"]
    cov_results = [r for r in all_results if r["category"] == "coverage"]
    cons_results = [r for r in all_results if r["category"] == "consistency"]

    output = {
        "gate_id": "G4",
        "stage": STAGE,
        "model": EVAL_MODEL,
        "timestamp": datetime.now().isoformat(),
        "inputs": meta.get("inputs", {}),
        "summary": {
            "total": len(all_results),
            "passed": sum(1 for r in all_results if r.get("passed")),
            "failed": sum(1 for r in all_results if not r.get("passed")),
            "overall_status": "pass" if overall_pass else "fail",
            "faithfulness": summary(faith_results),
            "coverage": summary(cov_results),
            "consistency": summary(cons_results),
        },
        "results": all_results,
        "details": meta.get("details", {}),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    ts_ms = int(time.time() * 1000)
    for r in all_results:
        if r.get("status") == "error":
            allure_status = "broken"
        else:
            allure_status = "passed" if r.get("passed") else "failed"

        ar = {
            "uuid": str(uuid.uuid4()),
            "name": r["test_name"],
            "status": allure_status,
            "stage": "finished",
            "start": ts_ms,
            "stop": ts_ms + int(r.get("duration_ms", 0)),
            "labels": [
                {"name": "suite", "value": f"G4 {STAGE} Transform"},
                {"name": "feature", "value": r["category"].capitalize()},
                {"name": "severity", "value": r.get("severity", "normal")},
                {"name": "tag", "value": "G4"},
            ],
            "parameters": [
                {"name": "score", "value": str(r.get("score", ""))},
                {"name": "model", "value": EVAL_MODEL},
                {"name": "status", "value": r.get("status", "")},
            ],
            "description": r.get("reason", ""),
            "steps": [],
        }
        allure_path = allure_dir / f"{ar['uuid']}-result.json"
        with open(allure_path, "w", encoding="utf-8") as f:
            json.dump(ar, f, ensure_ascii=False, indent=2)

    output["_meta"] = {"json_path": str(json_path), "allure_dir": str(allure_dir)}
    return output


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    ref_files = expand_ref_inputs(REF_INPUTS)

    # 参照が無いと Coverage/Consistency は評価不能（Faithfulness全スキップならOK）
    if not ref_files and not FAITHFULNESS_SKIP_ALL and (COVERAGE_ENABLE or CONSISTENCY_ENABLE):
        print("[G4] ERROR: 参照ファイルが見つかりません。AIDD_REF_PATHS または AIDD_FILE_PATH を設定してください。")
        sys.exit(2)

    # 参照チャンク生成（Faithfulnessのタイムアウト対策の本体）
    ref_chunks: List[dict] = []
    ref_names: Set[str] = set()
    ref_texts_for_rule: List[str] = []

    if ref_files:
        ref_chunks, ref_names = build_reference_chunks(ref_files, REF_MODE, REF_CHUNK_MAX_CHARS)
        # Coverage/Consistency 用には、参照ファイルを軽く束ねる（全文は不要だが、抽出のために最低限）
        for fp in ref_files:
            mode = infer_ref_mode_by_ext(fp, REF_MODE)
            if mode == "MD":
                ref_texts_for_rule.append(load_text(fp))
            else:
                data = load_yaml_file(fp)
                ref_texts_for_rule.append(yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False))

    yaml_files = load_yaml_dir(YAML_DIR)

    print(f"\n{'=' * 72}")
    print(f"[G4] Transform Quality Check")
    print(f"[G4] Stage : {STAGE}")
    print(f"[G4] Model : {EVAL_MODEL}")
    print(f"[G4] YAMLs : {YAML_DIR}  ({len(yaml_files)} files)")
    print(f"[G4] REF  : {', '.join(ref_files) if ref_files else '(none)'}")
    print(f"[G4] deepeval available: {DEEPEVAL_AVAILABLE}")
    print(f"[G4] Faithfulness topK ref chunks: {TOPK_REF_CHUNKS} (chunk_max_chars={REF_CHUNK_MAX_CHARS}, ctx_max={FAITH_CTX_MAX})")
    print(f"[G4] Faithfulness derived_from context filter: {'ON' if USE_DERIVED_FROM_CONTEXT else 'OFF'}")
    print(f"[G4] Coverage    : {'ON' if COVERAGE_ENABLE else 'OFF'}")
    print(f"[G4] Consistency : {'ON' if CONSISTENCY_ENABLE else 'OFF'}")
    print(f"{'=' * 72}\n")

    all_results: List[dict] = []
    details_meta: dict = {}

    # 1) Faithfulness
    print("[G4] ── Faithfulness（ファイル単位）──")
    faith_results = eval_faithfulness(ref_chunks, ref_names, yaml_files)
    all_results.extend(faith_results)

    # 2) Global Coverage
    if COVERAGE_ENABLE:
        print("\n[G4] ── Global Coverage（YAML集合単位）──")
        start = time.time()
        if not ref_texts_for_rule:
            all_results.append({
                "test_name": "Coverage :: GLOBAL",
                "category": "coverage",
                "file": YAML_DIR,
                "score": 0.0,
                "passed": False,
                "status": "error",
                "reason": "No reference content available for coverage.",
                "duration_ms": int((time.time() - start) * 1000),
            })
        else:
            ref_items = extract_reference_items_for_coverage(
                ref_texts_for_rule,
                COV_MAX_ITEMS,
                COV_MIN_ITEM_LEN,
                skip_headings=COV_SKIP_HEADINGS,
            )
            cov_score, cov_details = compute_global_coverage(ref_items, yaml_files, COV_SIM_THRESHOLD)
            passed = cov_score >= WARN_THRESHOLD
            status = "pass" if passed else ("warn" if cov_score >= 0.5 else "fail")

            all_results.append({
                "test_name": "Coverage :: GLOBAL",
                "category": "coverage",
                "file": YAML_DIR,
                "score": round(float(cov_score), 4),
                "passed": bool(passed),
                "status": status,
                "reason": f"covered_items={sum(1 for d in cov_details if d['covered'])}/{len(cov_details)} (sim_th={COV_SIM_THRESHOLD})",
                "duration_ms": int((time.time() - start) * 1000),
            })

            details_meta["coverage"] = {
                "ref_items_count": len(ref_items),
                "covered_count": sum(1 for d in cov_details if d["covered"]),
                "sim_threshold": COV_SIM_THRESHOLD,
                "skip_headings": COV_SKIP_HEADINGS,
                "items": cov_details[:min(len(cov_details), 200)],
            }
            print(f"  [COVERAGE] score={cov_score:.3f}  covered={details_meta['coverage']['covered_count']}/{len(ref_items)}  status={status.upper()}")

    # 3) Global Consistency
    if CONSISTENCY_ENABLE:
        print("\n[G4] ── Global Consistency（横断）──")
        start = time.time()
        if not yaml_files:
            all_results.append({
                "test_name": "Consistency :: GLOBAL",
                "category": "consistency",
                "file": YAML_DIR,
                "score": 1.0,
                "passed": True,
                "status": "pass",
                "reason": "No YAML files to check.",
                "duration_ms": int((time.time() - start) * 1000),
            })
        else:
            cons_score, cons_details = compute_global_consistency(yaml_files, ref_texts_for_rule)
            passed = cons_score >= WARN_THRESHOLD
            status = "pass" if passed else ("warn" if cons_score >= 0.5 else "fail")

            all_results.append({
                "test_name": "Consistency :: GLOBAL",
                "category": "consistency",
                "file": YAML_DIR,
                "score": round(float(cons_score), 4),
                "passed": bool(passed),
                "status": status,
                "reason": f"contradictions={len(cons_details)}",
                "duration_ms": int((time.time() - start) * 1000),
            })

            details_meta["consistency"] = {
                "contradictions_count": len(cons_details),
                "ignore_keys": CONS_IGNORE_KEYS,
                "contradictions": cons_details[:min(len(cons_details), 200)],
            }
            print(f"  [CONSISTENCY] score={cons_score:.3f}  contradictions={len(cons_details)}  status={status.upper()}")

    meta = {
        "inputs": {
            "yaml_dir": YAML_DIR,
            "ref_inputs": REF_INPUTS,
            "ref_files": ref_files,
            "ref_mode": REF_MODE,
            "faithfulness_skip_all": FAITHFULNESS_SKIP_ALL,
            "faithfulness_skip_files": sorted(list(FAITHFULNESS_SKIP_FILES)),
            "skip_derived_from_scope": SKIP_DERIVED_SCOPE,
            "faithfulness_use_derived_from_context": USE_DERIVED_FROM_CONTEXT,
            "faithfulness_topk_ref_chunks": TOPK_REF_CHUNKS,
            "faithfulness_ref_chunk_max_chars": REF_CHUNK_MAX_CHARS,
            "faithfulness_actual_max_chars": FAITH_ACTUAL_MAX,
            "faithfulness_context_max_chars": FAITH_CTX_MAX,
            "faithfulness_truths_limit": FAITH_TRUTHS_LIM,
            "coverage_enable": COVERAGE_ENABLE,
            "consistency_enable": CONSISTENCY_ENABLE,
        },
        "details": details_meta,
    }

    output = write_results(all_results, OUT_ROOT, meta)

    s = output["summary"]
    print(f"\n{'=' * 72}")
    print("[G4] SUMMARY")
    print(f"     Overall      : {s['overall_status'].upper()}  (total={s['total']}, passed={s['passed']}, failed={s['failed']})")
    fs = s["faithfulness"]
    print(f"     Faithfulness : avg={fs['avg_score']:.3f}  passed={fs['passed']}/{fs['total']}{' ⚠ WARNING' if fs['warning'] else ''}")
    cs = s["coverage"]
    print(f"     Coverage     : avg={cs['avg_score']:.3f}  passed={cs['passed']}/{cs['total']}{' ⚠ WARNING' if cs['warning'] else ''}")
    ks = s["consistency"]
    print(f"     Consistency  : avg={ks['avg_score']:.3f}  passed={ks['passed']}/{ks['total']}{' ⚠ WARNING' if ks['warning'] else ''}")
    print(f"\n[G4] Output : {output['_meta']['json_path']}")
    print(f"[G4] Allure : {output['_meta']['allure_dir']}")
    print(f"{'=' * 72}\n")

    sys.exit(0 if s["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
