from secondbrain.desktop.dashboard.layout import (
    DashboardLayout,
    DashboardLayoutPersistence,
    DashboardLayoutService,
    DashboardLayoutValidator,
    LayoutValidationStatus,
    WidgetPosition,
)


def test_widget_position_expands_to_occupied_cells():
    position = WidgetPosition("rag_status", x=1, y=2, width=2, height=2)

    assert position.cells() == {(1, 2), (2, 2), (1, 3), (2, 3)}


def test_layout_validator_rejects_overlap():
    layout = DashboardLayout(
        positions=[
            WidgetPosition("a", x=0, y=0, width=2, height=1),
            WidgetPosition("b", x=1, y=0, width=2, height=1),
        ]
    )

    result = DashboardLayoutValidator().validate(layout)

    assert result.status == LayoutValidationStatus.INVALID
    assert any("overlaps" in error for error in result.errors)


def test_layout_validator_rejects_unknown_widget_when_enabled_set_is_supplied():
    layout = DashboardLayout(positions=[WidgetPosition("missing", x=0, y=0)])

    result = DashboardLayoutValidator().validate(layout, enabled_widgets={"known"})

    assert result.status == LayoutValidationStatus.INVALID
    assert "missing:unknown_widget" in result.errors


def test_layout_persistence_roundtrip(tmp_path):
    persistence = DashboardLayoutPersistence(tmp_path)
    layout = DashboardLayout(layout_id="main", columns=4, positions=[WidgetPosition("jobs", 0, 0, 2, 1)])

    persistence.save(layout)
    loaded = persistence.load()

    assert loaded.layout_id == "main"
    assert loaded.columns == 4
    assert loaded.positions[0].widget_id == "jobs"


def test_layout_service_persists_valid_widget_placement(tmp_path):
    service = DashboardLayoutService(DashboardLayoutPersistence(tmp_path))

    result = service.place_widget(WidgetPosition("recent_imports", 0, 0, 3, 1), enabled_widgets={"recent_imports"})

    assert result.is_valid
    assert service.load_layout().positions[0].width == 3


def test_layout_service_does_not_persist_invalid_overlap(tmp_path):
    service = DashboardLayoutService(DashboardLayoutPersistence(tmp_path))
    assert service.place_widget(WidgetPosition("a", 0, 0, 2, 1), enabled_widgets={"a", "b"}).is_valid

    result = service.place_widget(WidgetPosition("b", 1, 0, 2, 1), enabled_widgets={"a", "b"})

    assert not result.is_valid
    assert "b" not in service.load_layout().by_widget_id()
