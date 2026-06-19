
from __future__ import annotations
from pathlib import Path
from typing import Any
import argparse, json

from .launcher_runtime_v122 import SecondBrainLauncherV122
from .launcher_runtime_v113 import _print_json
from .knowledge_graph_v123 import KnowledgeGraphEngine
from .tool_registry_v121 import ToolDefinition

class SecondBrainLauncherV123(SecondBrainLauncherV122):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.knowledge_graph_v123 = KnowledgeGraphEngine(self.config.runtime_dir, self.event_bus_v121)
        self._register_graph_tools()

    def _register_graph_tools(self) -> None:
        defs = [
            ToolDefinition('graph.status','Read knowledge graph status', {'type':'object','properties':{}}, {'type':'object'}, ['graph.read'], 1, False),
            ToolDefinition('graph.search','Search graph entities', {'type':'object','required':['query'],'properties':{'query':{'type':'string'},'limit':{'type':'integer'}}}, {'type':'array'}, ['graph.read'], 1, False),
            ToolDefinition('graph.ingest_text','Ingest text into graph', {'type':'object','required':['text'],'properties':{'text':{'type':'string'},'source_id':{'type':'string'},'title':{'type':'string'}}}, {'type':'object'}, ['graph.write'], 2, False),
        ]
        handlers = {
            'graph.status': lambda p: self.graph_status(),
            'graph.search': lambda p: self.graph_search(p.get('query',''), int(p.get('limit',20))),
            'graph.ingest_text': lambda p: self.graph_ingest_text(p.get('text',''), p.get('source_id','tool'), p.get('title')),
        }
        for d in defs:
            self.tool_registry_v121.register(d, handlers[d.name])

    def graph_status(self) -> dict[str, Any]:
        return self.knowledge_graph_v123.graph_status()
    def graph_ingest_text(self, text: str, source_id: str = 'manual', title: str | None = None) -> dict[str, Any]:
        return self.knowledge_graph_v123.ingest_text(text, source_id, title)
    def graph_ingest_file(self, path: str) -> dict[str, Any]:
        return self.knowledge_graph_v123.ingest_file(path)
    def graph_search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.knowledge_graph_v123.search_entities(query, limit)
    def graph_neighbors(self, query: str, depth: int = 1) -> dict[str, Any]:
        return self.knowledge_graph_v123.neighborhood(query, depth)
    def graph_timeline(self) -> list[dict[str, Any]]:
        return self.knowledge_graph_v123.store.timeline()
    def graph_contradictions(self) -> list[dict[str, Any]]:
        return self.knowledge_graph_v123.store.contradictions()
    def graph_export(self) -> dict[str, Any]:
        return self.knowledge_graph_v123.graph_export()
    def core123_status(self) -> dict[str, Any]:
        base=self.core122_status(); base.update({'version':'12.3','knowledge_graph':self.graph_status()}); return base

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='secondbrain', description='SecondBrain OS v12.3 launcher')
    parser.add_argument('--project-root', default=str(Path.cwd()))
    parser.add_argument('--profile', default=None)
    sub=parser.add_subparsers(dest='cmd', required=False)
    for cmd in ['core-status','graph-status','graph-timeline','graph-contradictions','graph-export']:
        sub.add_parser(cmd)
    p=sub.add_parser('graph-ingest-text'); p.add_argument('text'); p.add_argument('--source-id', default='manual'); p.add_argument('--title', default=None)
    p=sub.add_parser('graph-ingest-file'); p.add_argument('path')
    p=sub.add_parser('graph-search'); p.add_argument('query'); p.add_argument('--limit', type=int, default=20)
    p=sub.add_parser('graph-neighbors'); p.add_argument('query'); p.add_argument('--depth', type=int, default=1)
    return parser

def main(argv: list[str] | None = None) -> int:
    import sys
    raw=list(sys.argv[1:] if argv is None else argv)
    v123_cmds={'core-status','graph-status','graph-ingest-text','graph-ingest-file','graph-search','graph-neighbors','graph-timeline','graph-contradictions','graph-export'}
    first_cmd=next((x for x in raw if not x.startswith('-')), None)
    if first_cmd is not None and first_cmd not in v123_cmds:
        from .launcher_runtime_v122 import main as legacy_main
        return legacy_main(argv)
    parser=build_parser(); args=parser.parse_args(argv); cmd=args.cmd or 'core-status'
    launcher=SecondBrainLauncherV123(args.project_root, args.profile)
    try:
        if cmd=='core-status': _print_json(launcher.core123_status())
        elif cmd=='graph-status': _print_json(launcher.graph_status())
        elif cmd=='graph-ingest-text': _print_json(launcher.graph_ingest_text(args.text, args.source_id, args.title))
        elif cmd=='graph-ingest-file': _print_json(launcher.graph_ingest_file(args.path))
        elif cmd=='graph-search': _print_json(launcher.graph_search(args.query, args.limit))
        elif cmd=='graph-neighbors': _print_json(launcher.graph_neighbors(args.query, args.depth))
        elif cmd=='graph-timeline': _print_json(launcher.graph_timeline())
        elif cmd=='graph-contradictions': _print_json(launcher.graph_contradictions())
        elif cmd=='graph-export': _print_json(launcher.graph_export())
        else: return 2
        return 0
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1
if __name__ == '__main__':
    raise SystemExit(main())
