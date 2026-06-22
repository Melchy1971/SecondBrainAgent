"""P3 v20.4 - Cross Memory Linking."""

class CrossMemoryLinker:
    def build_links(self, semantic_ids: list[str], episodic_ids: list[str]) -> list[tuple[str, str]]:
        links = []
        for semantic_id in semantic_ids:
            for episodic_id in episodic_ids:
                links.append((semantic_id, episodic_id))
        return links
