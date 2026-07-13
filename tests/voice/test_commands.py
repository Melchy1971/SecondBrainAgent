from secondbrain.voice.commands import VoiceCommandRouter, Intent


def test_route_matches_intent_with_slots():
    router = VoiceCommandRouter().register("create_note", r"note[:\s]+(?P<body>.+)")
    intent = router.route("note: buy milk")
    assert intent.name == "create_note" and intent.slots["body"] == "buy milk"


def test_unmatched_routes_to_fallback():
    router = VoiceCommandRouter()
    assert router.route("random chatter").matched is False


def test_handle_dispatches_to_handler():
    seen = {}
    router = VoiceCommandRouter().register("timer", r"timer\s+(?P<n>\d+)",
                                           handler=lambda i: seen.setdefault("n", i.slots["n"]))
    res = router.handle("timer 5")
    assert res["handled"] and res["intent"] == "timer" and seen["n"] == "5"


def test_handle_falls_back_to_agent():
    router = VoiceCommandRouter(agent=lambda t: f"agent:{t}")
    res = router.handle("what is the weather")
    assert res["handled"] and res["result"] == "agent:what is the weather" and res["matched"] is False
