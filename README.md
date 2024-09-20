# Skillfarm module for AllianceAuth.<a name="aa-skillfarm"></a>

The Skillfarm Tracker Module for Alliance Auth tracks skill queues, sends notifications if skills finished and highlights them, making skill management easier for Skillfarms.

______________________________________________________________________

- [AA Skillfarm](#aa-skillfarm)
  - [Features](#features)
  - [Upcoming](#upcoming)
  - [Installation](#features)
    - [Step 1 - Install the Package](#step1)
    - [Step 2 - Configure Alliance Auth](#step2)
    - [Step 3 - Add the Scheduled Tasks and Settings](#step3)
    - [Step 4 - Migration to AA](#step4)
    - [Step 5 - Setting up Permissions](#step5)
    - [Step 6 - (Optional) Setting up Compatibilies](#step6)
  - [Highlights](#highlights)

## Features<a name="features"></a>

- Graphical Design
- Skillfarm Information Sheet
  - Filtered Skill Queue
  - Filtered Skills
- Filter Skills for each Character
- Characters Overview
- Highlight finished Skills

## Upcoming<a name="upcoming"></a>

- Notififcation System

## Installation<a name="installation"></a>

> \[!NOTE\]
> AA Skillfarm needs at least Alliance Auth v4.0.0
> Please make sure to update your Alliance Auth before you install this APP

### Step 1 - Install the Package<a name="step1"></a>

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-skillfarm
```

### Step 2 - Configure Alliance Auth<a name="step2"></a>

Configure your Alliance Auth settings (`local.py`) as follows:

- Add `'eveuniverse',` to `INSTALLED_APPS`
- Add `'memberaudit',` to `INSTALLED_APPS`
- Add `'skillfarm',` to `INSTALLED_APPS`

### Step 3 - Add the Scheduled Tasks<a name="step3"></a>

To set up the Scheduled Tasks add following code to your `local.py`

```python
CELERYBEAT_SCHEDULE["skillfarm_update_all_skillfarm"] = {
    "task": "skillfarm.tasks.update_all_skillfarm",
    "schedule": crontab(minute=0, hour="*/1"),
}
```

### Step 4 - Migration to AA<a name="step4"></a>

```shell
python manage.py collectstatic
python manage.py migrate
```

### Step 5 - Setting up Permissions<a name="step5"></a>

With the Following IDs you can set up the permissions for the Skillfarm

| ID             | Description                     |                                                           |
| :------------- | :------------------------------ | :-------------------------------------------------------- |
| `basic_access` | Can access the Skillfarm module | All Members with the Permission can access the Skillfarm. |
| `admin_access` | Has access to all characters    | Can see all Skillfarm Characters.                         |

### Step 6 - (Optional) Setting up Compatibilies<a name="step6"></a>

The Following Settings can be setting up in the `local.py`

- SKILLFARM_APP_NAME:          `"YOURNAME"`     - Set the name of the APP

- SKILLFARM_LOGGER_USE:        `True / False`   - Set to use own Logger File

If you set up SKILLFARM_LOGGER_USE to `True` you need to add the following code below:

```python
LOGGING_SKILLFARM = {
    "handlers": {
        "skillfarm_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "log/skillfarm.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
        },
    },
    "loggers": {
        "skillfarm": {
            "handlers": ["skillfarm_file", "console"],
            "level": "INFO",
        },
    },
}
LOGGING["handlers"].update(LOGGING_SKILLFARM["handlers"])
LOGGING["loggers"].update(LOGGING_SKILLFARM["loggers"])
```

## Highlights<a name="highlights"></a>

![Screenshot 2024-09-21 012026](https://github.com/user-attachments/assets/8de03a03-c8b4-4e42-91c2-d78b2ea6a62a)
![Screenshot 2024-09-21 012008](https://github.com/user-attachments/assets/567197cc-c55f-4b0e-b470-d4ceeadcfb15)

> \[!NOTE\]
> Contributing
> You want to improve the project?
> Just Make a [Pull Request](https://github.com/Geuthur/aa-skillfarm/pulls) with the Guidelines.
> We Using pre-commit
