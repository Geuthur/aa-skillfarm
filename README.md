# Skillfarm module for AllianceAuth.<a name="aa-skillfarm"></a>

![Release](https://img.shields.io/pypi/v/aa-skillfarm?label=release)
![Licence](https://img.shields.io/github/license/geuthur/aa-skillfarm)
![Python](https://img.shields.io/pypi/pyversions/aa-skillfarm)
![Django](https://img.shields.io/pypi/frameworkversions/django/aa-skillfarm.svg?label=django)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](frontend/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-skillfarm/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-skillfarm/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Geuthur/aa-skillfarm/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-skillfarm/actions/workflows/autotester.yml)
[![codecov](https://codecov.io/gh/Geuthur/aa-skillfarm/graph/badge.svg?token=oFZPpgIXz4)](https://codecov.io/gh/Geuthur/aa-skillfarm)
[![Translation status](https://weblate.geuthur.de/widget/allianceauth/aa-skillfarm/svg-badge.svg)](https://weblate.geuthur.de/engage/allianceauth/)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W810Q5J4)

The Skillfarm Tracker Module for Alliance Auth tracks skill queues, sends notifications if skills finished and highlights them, making skill management easier for Skillfarms.

______________________________________________________________________

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=2 -->

- [Features](#features)
- [Highlights](#highlights)
- [Installation](#installation)
  - [Step 1 - Install the Package](#step-1---install-the-package)
  - [Step 2 - Configure Alliance Auth](#step-2---configure-alliance-auth)
  - [Step 3 - Add the Scheduled Tasks](#step-3---add-the-scheduled-tasks)
  - [Step 3.1 - (Optional) Add own Logger File](#step-31---optional-add-own-logger-file)
  - [Step 4 - Migrate & Preload EVE SDE Data](#step-4---migrate--preload-eve-sde-data)
  - [Step 4.1 - Migrate App and collect static](#step-41---migrate-app-and-collect-static)
  - [Step 5 - Setting up Permissions](#step-5---setting-up-permissions)
  - [Step 6 - (Optional) Setting up Compatibilies](#step-6---optional-setting-up-compatibilies)
- [Translations](#translations)
- [Contributing](#contributing)

<!-- mdformat-toc end -->

## Features<a name="features"></a>

- Graphical Design
- Characters Overview
- Skillfarm Information Sheet
  - Filtered Skillqueue
  - Filtered Skills
  - Highlight finished Skills
  - No Active Training hint
- Filter Skills for each Character
- Notification System
- Enable/Disable Characters

## Highlights<a name="highlights"></a>

![Image: dashbaord]
![Image: skillqueue]
![Image: skillsetup]
![Image: calculator]

## Installation<a name="installation"></a>

> [!NOTE]
> AA Skillfarm needs at least Alliance Auth v5
> Please make sure to update your Alliance Auth before you install this APP

### Step 1 - Install the Package<a name="step-1---install-the-package"></a>

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-skillfarm
```

### Step 2 - Configure Alliance Auth<a name="step-2---configure-alliance-auth"></a>

Configure your Alliance Auth settings (`local.py`) as follows:

```python
INSTALLED_APPS = [
    # other apps
    "eve_sde",  # only if it not already existing
    "skillfarm",
    # other apps?
]

# This line is right below the `INSTALLED_APPS` list, if not already exist!
INSTALLED_APPS = ["modeltranslation"] + INSTALLED_APPS
```

### Step 3 - Add the Scheduled Tasks<a name="step-3---add-the-scheduled-tasks"></a>

To set up the Scheduled Tasks add following code to your `local.py`

```python
if "skillfarm" in INSTALLED_APPS:
    CELERYBEAT_SCHEDULE["AA Skillfarm :: Update All Skillfarm"] = {
        "task": "skillfarm.tasks.update_all_skillfarm",
        "schedule": 1800,
    }

    CELERYBEAT_SCHEDULE["AA Skillfarm :: Check Skillfarm Notification"] = {
        "task": "skillfarm.tasks.check_skillfarm_notifications",
        "schedule": crontab(minute=0, hour="*/24"),
    }

    CELERYBEAT_SCHEDULE["AA Skillfarm :: Update All Prices"] = {
        "task": "skillfarm.tasks.update_all_prices",
        "schedule": crontab(minute=0, hour="0"),
    }
```

This also only need to be added if it is not already!

```python
if "eve_sde" in INSTALLED_APPS:
    # Run at 12:00 UTC each day
    CELERYBEAT_SCHEDULE["EVE SDE :: Check for SDE Updates"] = {
        "task": "eve_sde.tasks.check_for_sde_updates",
        "schedule": crontab(minute="0", hour="12"),
    }
```

### Step 3.1 - (Optional) Add own Logger File<a name="step-31---optional-add-own-logger-file"></a>

To set up the Logger add following code to your `local.py`
Ensure that you have writing permission in logs folder.

```python
LOGGING["handlers"]["skillfarm_file"] = {
    "level": "INFO",
    "class": "logging.handlers.RotatingFileHandler",
    "filename": os.path.join(BASE_DIR, "log/skillfarm.log"),
    "formatter": "verbose",
    "maxBytes": 1024 * 1024 * 5,
    "backupCount": 5,
}
LOGGING["loggers"]["extensions.skillfarm"] = {
    "handlers": ["skillfarm_file"],
    "level": "DEBUG",
}
```

### Step 4 - Migrate & Preload EVE SDE Data<a name="step-4---migrate--preload-eve-sde-data"></a>

AA Skillfarm uses EVE SDE data to map IDs to names for EveTypes. You will need to preload some data from SDE once.

```shell
python manage.py migrate eve_sde
python manage.py esde_load_sde
```

### Step 4.1 - Migrate App and collect static<a name="step-41---migrate-app-and-collect-static"></a>

Migrate the app and collect static.

```shell
python manage.py migrate skillfarm
python manage.py skillfarm_load_prices
python manage.py collectstatic --noinput
```

### Step 5 - Setting up Permissions<a name="step-5---setting-up-permissions"></a>

With the Following IDs you can set up the permissions for the Skillfarm

| ID             | Description                                      |                                                           |
| :------------- | :----------------------------------------------- | :-------------------------------------------------------- |
| `basic_access` | Can access the Skillfarm module                  | All Members with the Permission can access the Skillfarm. |
| `corp_access`  | Has access to all characters in the corporation. | Can see all Skillfarm Characters from own Corporation.    |
| `admin_access` | Has access to all characters                     | Can see all Skillfarm Characters.                         |

### Step 6 - (Optional) Setting up Compatibilies<a name="step-6---optional-setting-up-compatibilies"></a>

The Following Settings can be setting up in the `local.py`

| Setting Name                | Descriptioon                                             | Default       |
| --------------------------- | -------------------------------------------------------- | ------------- |
| `SKILLFARM_APP_NAME`        | Set the name of the APP                                  | `"Skillfarm"` |
| `SKILLFARM_PRICE_SOURCE_ID` | Set Station ID for fetching base prices. Default is Jita | `60003760`    |

Advanced Settings: Stale Status for Each Section

- SKILLFARM_STALE_TYPES = `{     "skills": 30,     "skillqueue": 30, }` - Defines the stale status duration (in minutes) for each section.

## Translations<a name="translations"></a>

[![Translations](https://weblate.geuthur.de/widget/allianceauth/aa-skillfarm/multi-auto.svg)](https://weblate.geuthur.de/engage/allianceauth/)

Help us translate this app into your language or improve existing translations. Join our team!"

## Contributing<a name="contributing"></a>

You want to improve the project?
Please ensure you read the [contribution guidelines](https://github.com/Geuthur/aa-skillfarm/blob/master/CONTRIBUTING.md)

[image: calculator]: https://raw.githubusercontent.com/geuthur/aa-skillfarm/master/docs/images/calculator.png "Skill Calculator"
[image: dashbaord]: https://raw.githubusercontent.com/geuthur/aa-skillfarm/master/docs/images/dashbaord.png "Dashboard"
[image: skillqueue]: https://raw.githubusercontent.com/geuthur/aa-skillfarm/master/docs/images/skillqueue.png "Character Skillqueue"
[image: skillsetup]: https://raw.githubusercontent.com/geuthur/aa-skillfarm/master/docs/images/skillsetup.png "Character Skillsetup"
