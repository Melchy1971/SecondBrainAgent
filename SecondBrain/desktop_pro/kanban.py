DEFAULT_COLUMNS = ["backlog", "doing", "review", "done"]


class KanbanBoard:
    def __init__(self, store):
        self.store = store

    def cards(self) -> list[dict]:
        return self.store.load("kanban_cards", [])

    def add_card(self, title: str, column: str = "backlog", priority: str = "medium") -> dict:
        if column not in DEFAULT_COLUMNS:
            return {"ok": False, "error": "invalid_column"}
        card = {"id": f"card_{len(self.cards())+1}", "title": title, "column": column, "priority": priority}
        return self.store.append("kanban_cards", card)

    def move(self, card_id: str, column: str) -> dict:
        cards = []
        changed = None
        for card in self.cards():
            if card["id"] == card_id:
                card = {**card, "column": column}
                changed = card
            cards.append(card)
        self.store.save("kanban_cards", cards)
        return changed or {"ok": False, "error": "card_not_found"}
