# Changelog

## [In Development] - Unreleased

<!--
Section Order:

### Added
### Fixed
### Changed
### Removed
-->

## [1.0.4] - 2025-12-22

### Added

- Translation for DataTable
- OpenAPI ESIStub Class
- exception handling for missing main character in skillfarm notifications
- SkillFarmTestCase with preloaded test data and request factory setup
- implement AppLogger and retry_task_on_esi_error for enhanced logging and error handling

### Changed

- Updated Translations
- Moved SkillInfo Modal to Actions
- Added DataTable v2 [Version 2.3.5](https://cdn.datatables.net/2.3.5/)
  - `ColumnControl` Extensions [Docs](https://datatables.net/extensions/columncontrol/)
  - `FixedHeader` Extensions [Docs](https://datatables.net/extensions/fixedheader/)
- Refactored JS Structure
  - Optimized Modal System
  - Optimized DataTable Structure
  - Unified Modal Structure
  - Unified Settings Structure
  - Unified DataTable Structure
- Optimized Settings System
  - Added Locale
  - Added DataTable Settings
- Refactored Template Structure
- Refactored Ajax Views
  - Optimized Structure
- use AA `numberFomatter` for Currency
- Overhaul Test Enviroment
  - SkillFarm TestCase Class
  - Doc String optimization
- moved `skillfarm` view to `index`
- simplify character_id retrieval in index view
- rename and update character retrieval functions for clarity and improved documentation
- refactor app_settings to use Django settings instead of app_utils

### Removed

- blank and null options from EveTypePrice name field for stricter validation
- `allianceauth-app-utils` dependency
- unused ESI-related functions and imports from decorators.py
- unused EVE Online and Fuzzwork API settings from app_settings
- unused add_info_to_context function
- unused custom exception classes from errors.py

## [1.0.3] - 2025-11-16

### Changed

- Downgrade `allianceauth-app-utils` to `>=1.30`

## [1.0.2] - 2025-11-13

### Changed

- Updated dependency `allianceauth-app-utils` to `2b2`

### Removed

- csrf arg from `django-ninja`
- `django-ninja` dependency pin `<1.5`
- allow-direct-references

## [1.0.1] - 2025-11-13

### Added

- Temporary pin `django-ninja` to `django-ninja<=1.5`
  - https://github.com/vitalik/django-ninja/pull/1524

## [1.0.0] - 2025-11-13

### Changed

- Switch to OPENAPI3 ESI Client
  - Dependency `django-esi` set to `>=8,<9`
  - Dependency `allianceauth-app-utils` set to `2b1`
- Updated dependencies
  - Dependency `django-eveuniverse` set to `>=1.6`
- Updated README url for translations
- Refactored API
- Updated loading spinner image
- Optimized Python HTML functions
- Updated Application Tests

### Added

- SkillfarmAudit Model
  - `get_skillqueue` property
  - `get_skills` property
  - `get_skillsetup` property
  - `is_filtered` property
  - `is_skill_ready` property
  - `is_skillqueue_ready` property
  - `notification_icon` property
  - `extraction_icon` property

### Removed

- Own Context Classes
- ESI Response Debug Logs

## [1.0.0-beta.1] - 2025-11-03

> [!CAUTION]
>
> This is a BETA version, not intended for production use!
> Please test it in a test environment first and [report any issues].

### Changed

- Switch to OPENAPI3 ESI Client
- Updated dependencies
- Updated README url for translations
- Refactored API
- loading spinner image
- optimized Python HTML functions

### Added

- SkillfarmAudit Model
  - `get_skillqueue` property
  - `get_skills` property
  - `get_skillsetup` property
  - `is_filtered` property
  - `is_skill_ready` property
  - `is_skillqueue_ready` property
  - `notification_icon` property
  - `extraction_icon` property

## [0.5.8] - 2025-10-21

### Added

- Release Workflow

### Changed

- Updated Makefile System
- Updated Translations
- Updated Contributing
- Updated README
- Optimized ESI Status Check

## [0.5.7] - 2025-10-07

### Changed

- [Enhance ESI availability check with locking mechanism to avoid hammering Endpoint](https://github.com/Geuthur/aa-skillfarm/commit/7f7b28945a49ebedba1c933a4bcf68c73ef5f162)
- Updated `npm`

## [0.5.6] - 2025-08-21

### Changed

- Optimized Search System by using SlimSelect Lib
- Filtered SkillSet now Ordered by ASC

### Removed

- Cache Buster

## [0.5.5] - 2025-07-11

### Added

- `django-esi` dependency

### Changed

- Use `django-esi` new User Agent Guidelines

## [0.5.4] - 2025-05-12

### Added

- Update Section System - Inspired by @\[[Eric Kalkoken](https://gitlab.com/ErikKalkoken/)\]
  - TokenError Handler
  - HTTPInternalServerError, HTTPGatewayTimeoutError Handler
  - Update Section retrieves information between Etag System (Not Updating if NotModified)
  - Disable Update on Token Error
  - Update Information
  - Update Issues Badge
- Disable Characters with no Owner
- Add Update Status to Skillfarm View
- Admin Menu (superuser only)

### Changed

- Make `README` logger settings optional
- Use app_utils `LoggerAddTag` Logger System
- Task System
  - Refactor Tasks
- Update Interval to 15 Minutes
- Stale to 30 Minutes
- Refactor Managers
  - Characterskill Manager
  - Skillfarmaudit Manager
  - Skillqueue Manager
- Optimized Skillfarm API
- Remove Character ID req. for navigation

### Removed

- own `get_extension_logger`

## [0.5.3] - 2025-05-02

### Added

- Discord Notification System
- Isort
- Dependbot

### Changed

- Update PyProject
- Updates deps

### Fixed

- Testing Issues in github

## [0.5.2] - 2025-04-03

### Added

- Delete Character Button

### Fixed

- No Notification Issue

## [0.5.1.2] - 2025-03-24

### Fixed

- skillfarm_load_prices Command

## [0.5.1] - 2025-02-24

> [!WARNING]
> Market Price System changed please visit the `README.md`

### Added

- EveTypePrice Model
- `skillfarm_load_prices` command
- `SKILLFARM_PRICE_SOURCE_ID` Settings
- Tests
  - Commands

### Changed

- Tests
  - Tasks
- Skillfarm Calculator Prices now used from EveTypePrice
- Update German Translation
- Update README

## Fixed

- All finished Skills are notificated instead of only filtered [#15](https://github.com/Geuthur/aa-skillfarm/issues/15)

______________________________________________________________________

##### Command

To use the new command you can execute:

```shell
python manage.py skillfarm_load_prices
```

This will load all necessary prices

##### Price Updates

- Prices are based on Jita 4-4 Station and can be changed with the `SKILLFARM_PRICE_SOURCE_ID` config
  Visit [Fuzzwork API](https://market.fuzzwork.co.uk/api/) to see supported IDs

## [0.5.0] - 2025-02-22

### Added

- Alliance Auth
  - Use `django_sri` hash integrity by [@ppfeuer](https://github.com/ppfeufer)
    - Min. requirements: Alliance Auth >= 4.6.0
- Models
  - `name` field to all models
  - `has_no_skillqueue` and `last_check` to SkillQueue model
- API
  - Progressbar, Skills, Skillqueue helper
  - SkillSet API Endpoint
- Forms
  - SkillSetForm
  - ConfirmForm
- Interactive Button System
- EveMarketPrice Data Fetch if not exist
- Admin Site for Characters
- JavsScript
  - `calculator.js`
  - `skillfarm-confirm.js`
  - `skillfarm-skillset.js`
  - `modal-system.js`
  - `overview.js`

### Fixed

- Skillfarm Notification only sent one Character per Main Character should be all Characters that finished a skill.
- old `voicesofwar` permission view error [#13](https://github.com/Geuthur/aa-skillfarm/issues/13)

### Changed

- Skillfarm CSS
  - table hover
  - table striped
- Refactor Templates Structure
- Refactor API Endpoints
- Refactor Views
- Refactor Javascript
- Button Generation handled by Python
- Moved X-Editable to `libs` folder
- Overview Design
- etag name from `etag` to `skillfarm`
- Models
  - renamed `skillfarmaudit.py` to `skillfarm.py`
  - `SkillFarmSetup` moved to `skillfarm.py`
  - `CharacterSkillqueueEntry` moved to `skillfarm.py`
  - `CharacterSkill` moved to `skillfarm.py`

### Removed

- Unnecessary Functions
- Single Character View
- Unnecessary Templates
- Django 4.0 Supprt
- Activity Switcher

## [0.3.4.1] - 2025-01-18

### Changed

- force_refresh from true to false in `update_character_skillfarm` task
- All JS moved to js folder

### Fixed

- SKillqueue Extraction Ready Bool are true if Skill is 4 instead of 5

## [0.3.4] - 2025-01-17

### Added

- Skillqueue hint if Skill is maybe Extraction ready
- ESI Information hint for Updating SkillQueue
- Skillqueue Extraction Notification
- German Translation

### Changed

- Changed Skill Task log Information from debug to info
- Notification Checker Task improved

### Fixed

- Character are not displayed in some cases #10
- Skillfarm Notification Task not reset Notification Cooldown

## [0.3.3] - 2024-11-25

### Added

- Char Link integration.

### Changed

- Inactive characters are now updated normally instead of never.
- Inactive characters are now automaticly moved to Inactive Tab.
- Removed the Status Switch button cause it now automaticly set inactive chars, the code will stay and will be removed in future.

### Fixed

- Skillqueue not updating correctly.
- Missing Set new ETag Header on not modified error
- bootstrap editable wrong path
- missing `bootstrap editable` CSS

## [0.3.2] - 2024-11-09 - HOTFIX

### Fixed

- Template Tag Error

## [0.3.1] - 2024-10-23

### Added

- Skill Extraction Checker
- FInished Skill Checker
- Notification System
- Activity Switcher
- Inactive Character Table

### Changed

- Skilltraining Bool now handled by geuthuris_active property
- JS ´No Active Training´ function to new is_active property
- Add Character init force update
- CSS Improvments
- Update only active characters

### Fixed

- ChararcterQueue is_active property not working correctly
- Last Update was not implemented to new system
- Skillfarm Overview error
- Missing Models in init
- Empty Queue not be deleted

## [0.3.0] - 2024-10-21

### Fixed

- EveMarketPrice Error on Skillfarm Calculator
- Wrong CSS Design on Skillfarm Calculator

### Added

- CharaccterSkill Model
- CharacterQueue Model
- EveMarketPrice Error Handler for Skillfarm Calculator

### Removed

- Memeberaudit dependency

## [0.1.4] - 2024-09-26

### Fixed

- Progress Bar not shown correctly if Date is over the End Date
- API Crash if memberaudit has no update

### Changed

- Progress Bar calculate in first step per skillpoints if the system detect something is wrong it calculate per date
- Add Step 0 Check dependencies are installed to README

## [0.1.3] - 2024-09-26

### Fixed

- Migration missing

## [0.1.2] - 2024-09-22

### Added

- Skillfarm
  - Skill Extraktion Icon
  - Info Button Color change when Skill Extraktion is ready

### Fixed

- Skillfarm Progressbar
  - Display more then 100%
  - If no Filter is active display 0%
  - Shows `No Active Training` although active training is in progress

### Changed

- Skillfarm API
  - Performance Optimations
  - Added Skillqueue & Skillqueue Filtered

## [0.1.1] - 2024-09-22

### Added

- Scopes
  - esi-skills.read_skills.v1
  - esi-skills.read_skillqueue.v1

## [0.1.0] - 2024-09-21

### Added

- Initial public release

[1.0.0]: https://github.com/Geuthur/aa-skillfarm/compare/v0.5.8...v1.0.0 "1.0.0"
[1.0.0-beta.1]: https://github.com/Geuthur/aa-skillfarm/compare/v0.5.8...v1.0.0-beta.1 "1.0.0-beta.1"
[1.0.1]: https://github.com/Geuthur/aa-skillfarm/compare/v1.0.0...v1.0.1 "1.0.1"
[1.0.2]: https://github.com/Geuthur/aa-skillfarm/compare/v1.0.1...v1.0.2 "1.0.2"
[1.0.3]: https://github.com/Geuthur/aa-skillfarm/compare/v1.0.2...v1.0.3 "1.0.3"
[1.0.4]: https://github.com/Geuthur/aa-skillfarm/compare/v1.0.3...v1.0.4 "1.0.4"
[in development]: https://github.com/Geuthur/aa-skillfarm/compare/v1.0.4...HEAD "In Development"
[report any issues]: https://github.com/Geuthur/aa-skillfarm/issues "report any issues"
