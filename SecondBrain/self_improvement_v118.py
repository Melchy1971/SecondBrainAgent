
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid
from collections import Counter, defaultdict


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    tmp.replace(path)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')


def _read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try: rows.append(json.loads(line))
        except Exception: pass
    return rows[-limit:] if limit else rows


@dataclass
class FeedbackEntry:
    feedback_id: str
    source: str                 # user | system | test | agent | workflow | api | automation
    target_type: str            # run | command | feature | doc | workflow | agent
    target_id: str
    rating: int                 # -2..2
    text: str = ''
    tags: list[str] | None = None
    created_at: str = ''


@dataclass
class ImprovementItem:
    item_id: str
    title: str
    source: str
    category: str               # bug | ux | reliability | capability | documentation | performance | security
    severity: int               # 1..5
    impact: int                 # 1..5
    effort: int                 # 1..5
    confidence: float
    status: str = 'open'        # open | accepted | rejected | done
    evidence: list[dict[str, Any]] | None = None
    created_at: str = ''
    updated_at: str = ''

    @property
    def score(self) -> float:
        return round((self.severity * 0.35 + self.impact * 0.45 + self.confidence * 5 * 0.20) / max(self.effort, 1), 3)


class SelfImprovementStore:
    def __init__(self, runtime_dir: str | Path):
        self.base = Path(runtime_dir) / 'self_improvement'
        self.feedback_path = self.base / 'feedback.jsonl'
        self.items_path = self.base / 'backlog.json'
        self.regressions_path = self.base / 'regressions.jsonl'
        self.base.mkdir(parents=True, exist_ok=True)

    def append_feedback(self, entry: dict[str, Any]) -> None:
        _append_jsonl(self.feedback_path, entry)

    def feedback(self, limit: int = 100) -> list[dict[str, Any]]:
        return _read_jsonl(self.feedback_path, limit)

    def items(self) -> list[dict[str, Any]]:
        return _read_json(self.items_path, [])

    def save_items(self, rows: list[dict[str, Any]]) -> None:
        _write_json(self.items_path, rows)

    def upsert_item(self, item: dict[str, Any]) -> dict[str, Any]:
        rows=self.items(); found=False
        for i,row in enumerate(rows):
            if row.get('item_id') == item.get('item_id'):
                rows[i]=item; found=True; break
        if not found: rows.append(item)
        rows.sort(key=lambda r: r.get('score', 0), reverse=True)
        self.save_items(rows)
        return item

    def append_regression(self, row: dict[str, Any]) -> None:
        _append_jsonl(self.regressions_path, row)

    def regressions(self, limit: int = 50) -> list[dict[str, Any]]:
        return _read_jsonl(self.regressions_path, limit)


class SelfImprovementEngine:
    FAILURE_TERMS = {
        'error','exception','failed','fail','timeout','permission','denied','blocked','missing','not found','crash','invalid'
    }
    CATEGORY_TERMS = {
        'security': {'permission','secret','token','approval','risk','audit','pii'},
        'reliability': {'failed','exception','timeout','crash','retry','offline','not found'},
        'ux': {'confusing','unclear','gui','start','launcher','command','dashboard'},
        'documentation': {'docs','documentation','readme','guide','manual'},
        'performance': {'slow','latency','token','cost','memory','cpu'},
        'capability': {'missing','feature','connector','agent','workflow','mobile','voice','rag'},
    }

    def __init__(self, runtime_dir: str | Path):
        self.runtime_dir = Path(runtime_dir)
        self.store = SelfImprovementStore(runtime_dir)

    def status(self) -> dict[str, Any]:
        items=self.store.items(); feedback=self.store.feedback(10000); regs=self.store.regressions(10000)
        open_items=[x for x in items if x.get('status') == 'open']
        avg_rating = None
        if feedback:
            avg_rating = round(sum(int(x.get('rating',0)) for x in feedback)/len(feedback), 2)
        return {
            'version':'11.8',
            'feedback_count': len(feedback),
            'avg_rating': avg_rating,
            'backlog_items': len(items),
            'open_items': len(open_items),
            'top_score': max([x.get('score',0) for x in items], default=0),
            'regressions': len(regs),
        }

    def record_feedback(self, source: str, target_type: str, target_id: str, rating: int, text: str = '', tags: list[str] | None = None) -> dict[str, Any]:
        rating=max(-2, min(2, int(rating)))
        row=asdict(FeedbackEntry(
            feedback_id='fb_' + uuid.uuid4().hex[:12],
            source=source,
            target_type=target_type,
            target_id=target_id,
            rating=rating,
            text=text,
            tags=tags or [],
            created_at=_now(),
        ))
        self.store.append_feedback(row)
        if rating < 0 or any(term in text.lower() for term in self.FAILURE_TERMS):
            self._create_item_from_feedback(row)
        return row

    def _classify_category(self, text: str) -> str:
        lower=text.lower()
        scores={cat:sum(1 for t in terms if t in lower) for cat,terms in self.CATEGORY_TERMS.items()}
        best=max(scores.items(), key=lambda x:x[1])
        if best[1] <= 0:
            return 'bug' if any(t in lower for t in self.FAILURE_TERMS) else 'capability'
        return best[0]

    def _create_item_from_feedback(self, fb: dict[str, Any]) -> dict[str, Any]:
        text=fb.get('text','') or f"Negative feedback for {fb.get('target_type')} {fb.get('target_id')}"
        rating=int(fb.get('rating',0))
        category=self._classify_category(text)
        severity=5 if rating <= -2 else 3
        if any(t in text.lower() for t in {'security','token','secret','permission','approval'}): severity=max(severity,4)
        impact=4 if fb.get('target_type') in {'run','command','feature'} else 3
        effort=2 if category in {'documentation','ux'} else 3
        confidence=0.65 if text else 0.45
        title=self._make_title(category, text, fb)
        item=ImprovementItem(
            item_id='imp_' + uuid.uuid4().hex[:12],
            title=title[:120],
            source='feedback',
            category=category,
            severity=severity,
            impact=impact,
            effort=effort,
            confidence=confidence,
            evidence=[fb],
            created_at=_now(),
            updated_at=_now(),
        )
        row=asdict(item); row['score']=item.score
        return self.store.upsert_item(row)

    def _make_title(self, category: str, text: str, fb: dict[str, Any]) -> str:
        clean=' '.join(text.strip().split())
        if clean:
            return f"{category}: {clean[:90]}"
        return f"{category}: improve {fb.get('target_type')} {fb.get('target_id')}"

    def backlog(self, status: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
        rows=self.store.items()
        if status:
            rows=[r for r in rows if r.get('status') == status]
        return rows[:limit]

    def set_item_status(self, item_id: str, status: str) -> dict[str, Any]:
        if status not in {'open','accepted','rejected','done'}:
            raise ValueError('unsupported status')
        rows=self.store.items()
        for row in rows:
            if row.get('item_id') == item_id:
                row['status']=status; row['updated_at']=_now()
                self.store.save_items(rows)
                return row
        raise KeyError(f'item not found: {item_id}')

    def analyze_runs(self) -> dict[str, Any]:
        sources = {
            'automation': self.runtime_dir / 'automation' / 'runs.jsonl',
            'api': self.runtime_dir / 'api' / 'audit.jsonl',
            'agent': self.runtime_dir / 'agent_runs.jsonl',
            'workflow': self.runtime_dir / 'workflow' / 'runs.jsonl',
        }
        evidence=[]
        for source,path in sources.items():
            for row in _read_jsonl(path, 500):
                text=json.dumps(row, ensure_ascii=False).lower()
                failed = row.get('ok') is False or row.get('status') in {'failed','blocked'} or any(t in text for t in self.FAILURE_TERMS)
                if failed:
                    evidence.append({'source':source, 'row':row})
        clusters=self._cluster_failures(evidence)
        created=[]
        for key, rows in clusters.items():
            created.append(self._create_item_from_cluster(key, rows))
        return {'analyzed_failures': len(evidence), 'clusters': len(clusters), 'created_items': created}

    def _cluster_failures(self, evidence: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        clusters=defaultdict(list)
        for ev in evidence:
            raw=json.dumps(ev.get('row',{}), ensure_ascii=False).lower()
            matched=[term for term in sorted(self.FAILURE_TERMS) if term in raw]
            key=(ev.get('source') or 'unknown') + ':' + (matched[0] if matched else 'failed')
            clusters[key].append(ev)
        return dict(clusters)

    def _create_item_from_cluster(self, key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        source, _, reason = key.partition(':')
        count=len(rows)
        category=self._classify_category(reason + ' ' + source)
        severity=5 if count >= 5 else 4 if count >= 2 else 3
        impact=5 if source in {'api','agent','workflow'} else 4
        effort=3
        confidence=min(0.95, 0.55 + count*0.08)
        item=ImprovementItem(
            item_id='imp_' + uuid.uuid4().hex[:12],
            title=f"{category}: {count} {source} failure(s) clustered by '{reason}'",
            source='run-analysis',
            category=category,
            severity=severity,
            impact=impact,
            effort=effort,
            confidence=confidence,
            evidence=rows[:5],
            created_at=_now(),
            updated_at=_now(),
        )
        row=asdict(item); row['score']=item.score
        return self.store.upsert_item(row)

    def detect_regressions(self, current: dict[str, Any], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
        baseline = baseline or {'tests_failed':0, 'health_errors':0, 'open_security_items':0}
        regressions=[]
        for key, old in baseline.items():
            new=current.get(key, old)
            try:
                if float(new) > float(old):
                    regressions.append({'metric':key, 'baseline':old, 'current':new, 'delta':float(new)-float(old)})
            except Exception:
                if new != old:
                    regressions.append({'metric':key, 'baseline':old, 'current':new, 'delta':'changed'})
        row={'regression_id':'reg_' + uuid.uuid4().hex[:12], 'created_at':_now(), 'current':current, 'baseline':baseline, 'regressions':regressions, 'ok': not regressions}
        self.store.append_regression(row)
        if regressions:
            text='; '.join(f"{r['metric']} {r['baseline']}→{r['current']}" for r in regressions)
            self.record_feedback('system','regression',row['regression_id'],-2,'Regression detected: ' + text, ['regression'])
        return row

    def recommend_next(self, limit: int = 5) -> list[dict[str, Any]]:
        rows=[r for r in self.store.items() if r.get('status') in {'open','accepted'}]
        rows.sort(key=lambda r: (r.get('score',0), r.get('impact',0), r.get('severity',0)), reverse=True)
        out=[]
        for r in rows[:limit]:
            out.append({
                'item_id': r['item_id'],
                'title': r['title'],
                'category': r['category'],
                'score': r.get('score'),
                'why': f"impact={r.get('impact')} severity={r.get('severity')} effort={r.get('effort')} confidence={r.get('confidence')}",
                'next_action': self._next_action(r),
            })
        return out

    def _next_action(self, item: dict[str, Any]) -> str:
        cat=item.get('category')
        if cat == 'security': return 'add policy/test before expanding execution scope'
        if cat == 'documentation': return 'update docs and add smoke command example'
        if cat == 'reliability': return 'add failing test, retry rule, and diagnostic output'
        if cat == 'ux': return 'simplify launcher command and add clearer error message'
        if cat == 'performance': return 'measure latency/cost before optimization'
        return 'define acceptance criteria and implement smallest vertical slice'

    def export_report(self) -> dict[str, Any]:
        return {'status': self.status(), 'recommendations': self.recommend_next(10), 'backlog': self.backlog(limit=50), 'regressions': self.store.regressions(20)}
