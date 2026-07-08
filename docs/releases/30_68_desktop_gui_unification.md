# v30.68 — Desktop-GUI: Design-System, Accessibility, Unified Shell

## Ehrliche Rahmenbedingung
Die Desktop-GUI ist Windows/Tkinter. „Produktionsreife Oberflaeche" ist in der Build-Sandbox **nicht
renderbar oder screenshot-testbar** (kein Display). Deshalb ist die **Substanz** als testbare Logik
gebaut (gruen) und der eigentliche Fenster-Code additiv + ehrlich als ungetestet deklariert.

## Analyse
Es existieren bereits strukturierte native Center (theme/notification/job_queue/layout/dashboard),
je mit `models/service/gui`. **Keine Funktion entfernt** — statt zu duplizieren, ergaenzt v30.68 eine
vereinheitlichende Design-System- und Interaktions-Schicht (`secondbrain/ui/`), die alle Fenster
konsistent umrahmen kann.

## Neu (Logik, voll getestet - 17 Tests)
- `ui/tokens.py` — Spacing-/Typo-/Radii-Skalen + **Light- und Dark-Palette** mit semantischen Rollen.
- `ui/contrast.py` — **WCAG-2.1-Kontrast** + AA/AAA. Beide Paletten verifiziert AA (fg/bg, muted, on_primary).
- `ui/theme.py` — `ThemeRegistry` (**Dark-Mode-Toggle**) + `ttk_style_map` (Style als Daten, GUI bleibt duenn).
- `ui/states.py` — **Loading/Error**-Async-`ViewState` mit Progress.
- `ui/keymap.py` — **Keyboard-Navigation** mit Konflikterkennung (Default-Bindings).
- `ui/responsive.py` — **Responsive** Breakpoints -> compact/regular/wide + Sidebar/Spalten.
- `ui/status_bar.py`, `ui/workspace_selector.py`, `ui/activity_feed.py` — **Status Bar**,
  **Workspace Selector**, **Activity Feed** als testbare Modelle (Notifications/Jobs als Badges).

## Unified Shell (ehrlich deklariert)
`secondbrain/gui/app_shell.py` (`UnifiedShell`): gemeinsame Chrome fuer alle Fenster — Nav-Sidebar,
Status Bar, Theming (Dark/Light), Keyboard-Nav, Responsive-Reflow. Bestehende Center werden in den
Content-Bereich gemountet; der Shell standardisiert nur den Rahmen. **Tkinter, in der Sandbox nicht
ausgefuehrt/abgenommen** (kein Display); tkinter lazy. Logik dahinter (`secondbrain/ui/*`) getestet.

## Launcher
```
python launcher.py ui-theme --theme dark
python launcher.py ui-contrast-check      # Accessibility-Audit; Exit 4 bei AA-Verstoss
```

## Abdeckung der Anforderungen
Navigation, Abstaende, Farbschema, Dark Mode, Responsive Layout, Keyboard Navigation, Accessibility,
Loading/Error States, Status Bar, Workspace Selector, Activity Feed — als getestete Modelle.
Notifications/Job Monitor als Badge-Anbindung an die vorhandenen Center. **Performance** und die
finale Fenster-Vereinheitlichung/Abnahme laufen am Windows-Zielsystem.
