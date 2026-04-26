# Core App

The `core` package houses cross-cutting infrastructure that every other Campfire Connections
app relies on.

## Responsibilities

- Shared model mixins (`core/mixins`) for names, slugs, hierarchies, addresses, auditing,
  timestamps, and settings.
- View mixins (`core/mixins/views.py`) that scope requests to the active organization,
  facility, or faction and enforce portal-specific permissions.
- Table/action mixins (`core/mixins/tables.py`) that generate row-level action links and safely
  fall back when a route cannot be reversed.
- Dashboard plumbing (`core/views/base.py`, `core/dashboard_registry.py`,
  `core/widgets.py`) that renders modular widgets with per-user layout preferences
  stored in `core.models.dashboard.DashboardLayout`.
- Navigation registry + context processors (`core/menu_registry.py`,
  `core/context_processors.py`) that feed the dynamic navbar, top links, user info
  row, and color scheme into every template.
- Portal registry (`core/portals.py`) describing each portal’s label, template,
  widgets, and allowed user types.
- Utility helpers (`core/utils.py`, `core/dashboard_data.py`, `core/widgets.py`)
  reused by enrollment, facility, faction, and pages apps.

## Key Files

- `models/navigation.py` – per-user quick-access preferences for the navbar.
- `context_processors.py` – injects menu items, user profile fallbacks, enrollment
  summaries, color palette, and info-row data into templates.
- `views/base.py` – base classes for CRUD, manage, and dashboard views (includes
  layout persistence, widget rendering, and Ajax helpers).
- `mixins/tables.py` – action URL generation, permission checks, and organization-aware table
  labels.
- `menu_registry.py` – declarative description of main/quick navigation links
  (supports conditions, nested menus, and favorite pinning).

## Working With Core

- Add new widgets by implementing `core.widgets.BaseWidget` subclasses and
  referencing them in `core/dashboard_registry.py`.
- Extend the navbar by adding entries to `core/menu_registry.py`; the template
  automatically renders dropdowns and pin buttons.
- Use the scoped view mixins from `core/mixins/views.py` whenever you build a portal
  view—this keeps URLs consistent and enforces permissions.

## Tests

Core’s unit tests live in `core/tests.py` and can be executed via:

```bash
python manage.py test core
```

These tests cover the menu registry, dashboard layout handling, and profile context
processor fallbacks. Add new cases here when you enhance shared infrastructure.
