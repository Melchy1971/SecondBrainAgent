from secondbrain.desktop.notifications import NotificationCenter, NotificationLevel


def test_notification_center_pushes_items():
    center = NotificationCenter()
    item = center.push("Import", "done", NotificationLevel.SUCCESS)

    assert item.level == NotificationLevel.SUCCESS
    assert center.list() == [item]
