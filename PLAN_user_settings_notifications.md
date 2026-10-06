# Plan: User Settings and Global Notification Opt-Out

## Goal

Add a Settings menu item and page where each Skillfarm user can disable all Skillfarm notifications. When disabled, no notification is delivered through Skillfarm, regardless of per-character notification toggles.

## Architecture

- Activate the existing `UserSettings` model as a managed model with one row per user and a default `disable_notifications=False`.
- Add authenticated GET and PUT endpoints for the current user's setting; require `skillfarm.basic_access`.
- Add the Settings link to the backend menu and a React route/page with an accessible toggle.
- Enforce the opt-out in the centralized `send_user_notification` task before Alliance Auth or Discord delivery. This makes the setting global across all callers.
- Generate frontend API types from OpenAPI and keep API functions/query keys centralized.

## Proposed Files

- Backend: `skillfarm/models/general.py`, `skillfarm/api/schema.py`, `skillfarm/api/general.py`, `skillfarm/helpers/discord.py`, generated migration.
- Tests: `skillfarm/tests/testdata/skillfarm.py`, API tests for settings/menu, notification helper test.
- Frontend: `frontend/src/App.tsx`, `Api/ApiCalls.ts`, `Api/query.ts`, `Api/schema.ts`, `Pages/SettingsPage.tsx` and its CSS module/test.
- Documentation: `CHANGELOG.md`.

## Open Questions

None. The requested preference is interpreted as suppressing all notifications sent by Skillfarm, including per-character-enabled notices.

## Verification

1. `make migrations` and confirm a second run reports no changes.
1. `make coverage` for backend API and sender behavior.
1. Regenerate API types with `make react-openapi`.
1. Run `make react-lint`, `make react-build`, and frontend tests.
