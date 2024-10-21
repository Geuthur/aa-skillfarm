# Changelog

## \[0.3.0\] - 2024-10-21

### Fixed

- EveMarketPrice Error on Skillfarm Calculator
- Wrong CSS Design on Skillfarm Calculator

### Added

- CharaccterSkill Model
- CharacterQueue Model
- EveMarketPrice Error Handler for Skillfarm Calculator

### Removed

- Memeberaudit dependency

## \[0.1.4\] - 2024-09-26

### Fixed

- Progress Bar not shown correctly if Date is over the End Date
- API Crash if memberaudit has no update

### Changed

- Progress Bar calculate in first step per skillpoints if the system detect something is wrong it calculate per date
- Add Step 0 Check dependencies are installed to README

## \[0.1.3\] - 2024-09-26

### Fixed

- Migration missing

## \[0.1.2\] - 2024-09-22

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

## \[0.1.1\] - 2024-09-22

### Added

- Scopes
  - esi-skills.read_skills.v1
  - esi-skills.read_skillqueue.v1

## \[0.1.0\] - 2024-09-21

### Added

- Initial public release
