# Changelog

## [0.5.x] - IN Development

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
