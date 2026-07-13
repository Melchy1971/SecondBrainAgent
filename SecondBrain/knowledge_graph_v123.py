
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
import hashlib, json, re, time

_WORD_RE = re.compile(r"\b[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,}\b")
_TAG_RE = re.compile(r"#([A-Za-zÄÖÜäöüß0-9_-]{2,})")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2}|\d{2}\.\d{2}\.20\d{2})\b")

def _now() -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]

def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())

@dataclass
class Entity:
    id: str
    name: str
    type: str
    confidence: float
    source_id: str
    first_seen: str
    last_seen: str
    mentions: int = 1

@dataclass
class Relationship:
    id: str
    source: str
    target: str
    type: str
    confidence: float
    evidence: str
    source_id: str
    created_at: str

@dataclass
class TimelineEvent:
    id: str
    entity_id: str
    date: str
    text: str
    source_id: str
    created_at: str

@dataclass
class Contradiction:
    id: str
    entity_id: str
    field: str
    left_value: str
    right_value: str
    source_ids: list[str]
    severity: str
    created_at: str

class GraphStore:
    def __init__(self, runtime_dir: str | Path):
        self.base = Path(runtime_dir) / 'knowledge_graph_v123'
        self.base.mkdir(parents=True, exist_ok=True)
        self.entities_path = self.base / 'entities.json'
        self.relationships_path = self.base / 'relationships.json'
        self.timeline_path = self.base / 'timeline.json'
        self.contradictions_path = self.base / 'contradictions.json'
        self.ingestion_path = self.base / 'ingestions.jsonl'
        for p, default in [
            (self.entities_path, []), (self.relationships_path, []),
            (self.timeline_path, []), (self.contradictions_path, [])
        ]:
            if not p.exists():
                p.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding='utf-8')

    def _read(self, path: Path) -> list[dict[str, Any]]:
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _write(self, path: Path, rows: list[dict[str, Any]]) -> None:
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True), encoding='utf-8')

    def entities(self) -> list[dict[str, Any]]: return self._read(self.entities_path)
    def relationships(self) -> list[dict[str, Any]]: return self._read(self.relationships_path)
    def timeline(self) -> list[dict[str, Any]]: return self._read(self.timeline_path)
    def contradictions(self) -> list[dict[str, Any]]: return self._read(self.contradictions_path)

    def upsert_entities(self, entities: Iterable[Entity]) -> int:
        rows={e['id']: e for e in self.entities()}
        changed=0
        for ent in entities:
            d=asdict(ent)
            if ent.id in rows:
                prev=rows[ent.id]
                prev['mentions']=int(prev.get('mentions',1))+ent.mentions
                prev['last_seen']=ent.last_seen
                prev['confidence']=max(float(prev.get('confidence',0)), ent.confidence)
                rows[ent.id]=prev
            else:
                rows[ent.id]=d
            changed+=1
        self._write(self.entities_path, list(rows.values()))
        return changed

    def add_relationships(self, rels: Iterable[Relationship]) -> int:
        rows={r['id']: r for r in self.relationships()}
        n=0
        for rel in rels:
            rows[rel.id]=asdict(rel); n+=1
        self._write(self.relationships_path, list(rows.values()))
        return n

    def add_timeline(self, events: Iterable[TimelineEvent]) -> int:
        rows={r['id']: r for r in self.timeline()}
        n=0
        for ev in events:
            rows[ev.id]=asdict(ev); n+=1
        self._write(self.timeline_path, list(rows.values()))
        return n

    def add_contradictions(self, items: Iterable[Contradiction]) -> int:
        rows={r['id']: r for r in self.contradictions()}
        n=0
        for c in items:
            rows[c.id]=asdict(c); n+=1
        self._write(self.contradictions_path, list(rows.values()))
        return n

    def append_ingestion(self, record: dict[str, Any]) -> None:
        with self.ingestion_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True)+'\n')

class EntityExtractor:
    def extract(self, text: str, source_id: str) -> list[Entity]:
        now=_now(); found: dict[str, Entity] = {}
        def add(name: str, typ: str, conf: float):
            name=_norm(name)
            if len(name)<3: return
            eid=f'{typ}:{_hash(name.lower())}'
            if eid in found:
                found[eid].mentions += 1
                found[eid].confidence = max(found[eid].confidence, conf)
            else:
                found[eid]=Entity(eid, name, typ, conf, source_id, now, now)
        for email in _EMAIL_RE.findall(text): add(email, 'email', 0.95)
        for tag in _TAG_RE.findall(text): add(tag, 'tag', 0.9)
        for date in _DATE_RE.findall(text): add(date, 'date', 0.9)
        for word in _WORD_RE.findall(text):
            typ='concept'
            if word.endswith(('GmbH','AG')): typ='organization'
            add(word, typ, 0.55)
        return sorted(found.values(), key=lambda e: (-e.confidence, e.name))

class RelationshipDiscoverer:
    def discover(self, text: str, entities: list[Entity], source_id: str) -> list[Relationship]:
        now=_now(); rels=[]; seen=set()
        sentence_parts=re.split(r'[.!?\n]+', text)
        entity_by_name={e.name:e for e in entities}
        for sentence in sentence_parts:
            present=[e for name,e in entity_by_name.items() if name in sentence]
            if len(present)<2: continue
            for a,b in zip(present, present[1:]):
                typ='mentioned_with'
                low=sentence.lower()
                if any(k in low for k in ['gehört zu','part of','teil von']): typ='part_of'
                elif any(k in low for k in ['nutzt','uses','verwendet']): typ='uses'
                rid=f'{typ}:{a.id}:{b.id}:{_hash(sentence[:180])}'
                if rid in seen: continue
                seen.add(rid)
                rels.append(Relationship(rid,a.id,b.id,typ,0.62,_norm(sentence)[:240],source_id,now))
        return rels

class TimelineBuilder:
    def build(self, text: str, entities: list[Entity], source_id: str) -> list[TimelineEvent]:
        now=_now(); events=[]
        dates=[d for d in entities if d.type=='date']
        others=[e for e in entities if e.type!='date'][:10]
        if not dates: return []
        for d in dates:
            for e in others:
                if d.name in text and e.name in text:
                    eid=f'timeline:{e.id}:{_hash(d.name+source_id+text[:80])}'
                    snippet=_norm(text[max(0,text.find(d.name)-80):text.find(d.name)+160]) if d.name in text else text[:160]
                    events.append(TimelineEvent(eid,e.id,d.name,snippet,source_id,now))
        return events

class ContradictionDetector:
    def detect(self, store: GraphStore, entities: list[Entity], source_id: str) -> list[Contradiction]:
        # Deterministic low-cost heuristic: same canonical name seen as multiple types.
        by_name: dict[str,set[str]]={}
        source_map: dict[str,set[str]]={}
        all_rows=store.entities()+[asdict(e) for e in entities]
        for r in all_rows:
            key=str(r.get('name','')).lower()
            if not key: continue
            by_name.setdefault(key,set()).add(str(r.get('type','unknown')))
            source_map.setdefault(key,set()).add(str(r.get('source_id','unknown')))
        out=[]; now=_now()
        for key, types in by_name.items():
            if len(types)>1:
                cid=f'contradiction:type:{_hash(key+"|".join(sorted(types)))}'
                out.append(Contradiction(cid, f'name:{_hash(key)}','type', sorted(types)[0], sorted(types)[-1], sorted(source_map.get(key,[])), 'medium', now))
        return out

class KnowledgeGraphEngine:
    def __init__(self, runtime_dir: str | Path, event_bus: Any | None = None):
        self.store=GraphStore(runtime_dir)
        self.event_bus=event_bus
        self.extractor=EntityExtractor()
        self.relationships=RelationshipDiscoverer()
        self.timeline=TimelineBuilder()
        self.contradictions=ContradictionDetector()

    def ingest_text(self, text: str, source_id: str = 'manual', title: str | None = None) -> dict[str, Any]:
        source_id = source_id or f'manual:{_hash(text[:100])}'
        entities=self.extractor.extract(text, source_id)
        rels=self.relationships.discover(text, entities, source_id)
        timeline=self.timeline.build(text, entities, source_id)
        contradictions=self.contradictions.detect(self.store, entities, source_id)
        self.store.upsert_entities(entities)
        self.store.add_relationships(rels)
        self.store.add_timeline(timeline)
        self.store.add_contradictions(contradictions)
        record={'source_id':source_id,'title':title,'created_at':_now(),'entities':len(entities),'relationships':len(rels),'timeline_events':len(timeline),'contradictions':len(contradictions)}
        self.store.append_ingestion(record)
        self._publish('knowledge.ingested', record)
        return record

    def ingest_file(self, path: str | Path) -> dict[str, Any]:
        p=Path(path)
        text=p.read_text(encoding='utf-8', errors='ignore')
        return self.ingest_text(text, source_id=str(p), title=p.name)

    def search_entities(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q=query.lower()
        rows=[r for r in self.store.entities() if q in str(r.get('name','')).lower() or q in str(r.get('type','')).lower()]
        return sorted(rows, key=lambda r: (-int(r.get('mentions',1)), -float(r.get('confidence',0))))[:limit]

    def graph_status(self) -> dict[str, Any]:
        return {'version':'12.3','entities':len(self.store.entities()),'relationships':len(self.store.relationships()),'timeline_events':len(self.store.timeline()),'contradictions':len(self.store.contradictions()),'storage':str(self.store.base)}

    def neighborhood(self, entity_query: str, depth: int = 1) -> dict[str, Any]:
        matches=self.search_entities(entity_query, 5)
        entity_ids={m['id'] for m in matches}
        rels=[]
        frontier=set(entity_ids)
        for _ in range(max(1, depth)):
            next_frontier=set()
            for r in self.store.relationships():
                if r.get('source') in frontier or r.get('target') in frontier:
                    rels.append(r); next_frontier.add(r.get('source')); next_frontier.add(r.get('target'))
            frontier=next_frontier-entity_ids; entity_ids |= next_frontier
        entities=[r for r in self.store.entities() if r.get('id') in entity_ids]
        return {'entities':entities,'relationships':rels[:100]}

    def graph_export(self) -> dict[str, Any]:
        return {'entities':self.store.entities(),'relationships':self.store.relationships(),'timeline':self.store.timeline(),'contradictions':self.store.contradictions()}

    def _publish(self, topic: str, payload: dict[str, Any]) -> None:
        if self.event_bus is None: return
        try:
            self.event_bus.publish(topic, payload, source='knowledge_graph_v123')
        except Exception:
            pass
