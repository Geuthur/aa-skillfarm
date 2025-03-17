from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from skillfarm import tasks
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import (
    add_skillfarmaudit_character_to_user,
    create_skill_character,
    create_skillfarm_character,
    create_skillsetup_character,
    create_user_from_evecharacter_with_access,
)

TASK_PATH = "skillfarm.tasks"


@patch(TASK_PATH + ".update_character_skillfarm", spec=True)
class TestUpdateAllSkillfarm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)

    def test_should_update_all_skillfarm(self, mock_update_all_skillfarm):
        # when
        tasks.update_all_skillfarm()
        # then
        self.assertTrue(mock_update_all_skillfarm.apply_async.called)


@patch(TASK_PATH + ".update_char_skillqueue.si", spec=True)
@patch(TASK_PATH + ".update_char_skills.si", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    APP_UTILS_OBJECT_CACHE_DISABLED=True,
)
class TestUpdateCharacterSkillfarm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)

    def test_should_not_update_character_skillfarm(
        self, mock_update_char_skillqueue, mock_update_char_skills
    ):
        self.audit.last_update_skillqueue = timezone.now()
        self.audit.last_update_skills = timezone.now()
        self.audit.save()
        # when
        tasks.update_character_skillfarm(
            character_id=self.audit.character.character_id, force_refresh=False
        )
        # then
        mock_update_char_skillqueue.assert_not_called()
        mock_update_char_skills.assert_not_called()

    def test_should_update_character_skillfarm(
        self, mock_update_char_skillqueue, mock_update_char_skills
    ):
        self.audit.last_update_skillqueue = timezone.now() - timezone.timedelta(days=8)
        self.audit.last_update_skills = timezone.now() - timezone.timedelta(days=8)
        self.audit.save()
        # when
        tasks.update_character_skillfarm(
            character_id=self.audit.character.character_id, force_refresh=False
        )
        # then
        mock_update_char_skillqueue.assert_called_once_with(
            self.audit.character.character_id, force_refresh=False
        )
        mock_update_char_skills.assert_called_once_with(
            self.audit.character.character_id, force_refresh=False
        )

    def test_should_update_character_skillfarm_forced(
        self, mock_update_char_skillqueue, mock_update_char_skills
    ):
        # when
        tasks.update_character_skillfarm(
            character_id=self.audit.character.character_id, force_refresh=True
        )
        # then
        mock_update_char_skillqueue.assert_called_once_with(
            self.audit.character.character_id, force_refresh=True
        )
        mock_update_char_skills.assert_called_once_with(
            self.audit.character.character_id, force_refresh=True
        )


@patch(TASK_PATH + ".SkillFarmAudit.objects.get", spec=True)
@patch(TASK_PATH + ".CharacterSkillqueueEntry.objects.update_or_create_esi", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    APP_UTILS_OBJECT_CACHE_DISABLED=True,
)
class TestUpdateCharSkillQueue(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)

    def test_update_char_skillqueue_should_work(
        self, mock_update_or_create_esi, mock_get_audit
    ):
        mock_get_audit.return_value = self.audit
        mock_update_or_create_esi.return_value = True
        # when
        tasks.update_char_skillqueue(
            character_id=self.audit.character.character_id, force_refresh=False
        )
        # then
        mock_get_audit.assert_called_once_with(
            character__character_id=self.audit.character.character_id
        )
        mock_update_or_create_esi.assert_called_once_with(
            self.audit, force_refresh=False
        )
        self.assertAlmostEqual(
            self.audit.last_update_skillqueue,
            timezone.now(),
            delta=timezone.timedelta(seconds=1),
        )
        self.audit.refresh_from_db()
        self.assertIsNotNone(self.audit.last_update_skillqueue)


@patch(TASK_PATH + ".SkillFarmAudit.objects.get", spec=True)
@patch(TASK_PATH + ".CharacterSkill.objects.update_or_create_esi", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    APP_UTILS_OBJECT_CACHE_DISABLED=True,
)
class TestUpdateCharSkill(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)

    def test_update_char_skills_should_work(
        self, mock_update_or_create_esi, mock_get_audit
    ):
        mock_get_audit.return_value = self.audit
        mock_update_or_create_esi.return_value = True
        # when
        tasks.update_char_skills(
            character_id=self.audit.character.character_id, force_refresh=False
        )
        # then
        mock_get_audit.assert_called_once_with(
            character__character_id=self.audit.character.character_id
        )
        mock_update_or_create_esi.assert_called_once_with(
            self.audit, force_refresh=False
        )
        self.assertAlmostEqual(
            self.audit.last_update_skills,
            timezone.now(),
            delta=timezone.timedelta(seconds=1),
        )
        self.audit.refresh_from_db()
        self.assertIsNotNone(self.audit.last_update_skills)


@patch(TASK_PATH + ".SkillFarmAudit.objects.all", spec=True)
@override_settings(
    CELERY_ALWAYS_EAGER=True,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    APP_UTILS_OBJECT_CACHE_DISABLED=True,
)
class TestCheckSkillfarmNotification(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )
        cls.user2, cls.character_ownership2 = create_user_from_evecharacter_with_access(
            1002
        )
        cls.audit = add_skillfarmaudit_character_to_user(cls.user, 1001)
        cls.audit2 = add_skillfarmaudit_character_to_user(cls.user2, 1002)
        cls.audit3 = add_skillfarmaudit_character_to_user(cls.user2, 1003)

    def _set_notifiaction_status(self, audits, status):
        for audit in audits:
            audit.notification = status
            audit.save()

    def test_no_notification_should_return_false(self, mock_audit_all):
        audits = [self.audit, self.audit2]
        self._set_notifiaction_status(audits, False)
        mock_audit_all.return_value = audits
        # when
        tasks.check_skillfarm_notifications()
        # then
        for audit in audits:
            self.assertFalse(audit.notification_sent)
            self.assertIsNone(audit.last_notification)

    def test_notifiaction_with_no_skillsetup_should_return_false(self, mock_audit_all):
        audits = [self.audit, self.audit2, self.audit3]
        self._set_notifiaction_status(audits, True)
        mock_audit_all.return_value = audits
        # when
        tasks.check_skillfarm_notifications()
        # then
        for audit in audits:
            self.assertFalse(audit.notification_sent)
            self.assertIsNone(audit.last_notification)

    def test_notifiaction_with_skillsetup_should_return_true(self, mock_audit_all):
        audits = [self.audit, self.audit2]
        self._set_notifiaction_status(audits, True)

        self.skill = create_skill_character(
            character_id=1001,
            evetype_id=1,
            skillpoints=500000,
            trained_level=5,
            active_level=5,
        )
        self.skillsetup = create_skillsetup_character(
            character_id=1001, skillset=["skill1"]
        )

        self.skill2 = create_skill_character(
            character_id=1002,
            evetype_id=2,
            skillpoints=500000,
            trained_level=5,
            active_level=5,
        )
        self.skillsetup2 = create_skillsetup_character(
            character_id=1002, skillset=["skill2"]
        )

        mock_audit_all.return_value = audits
        # when
        tasks.check_skillfarm_notifications()
        # then
        for audit in audits:
            self.assertTrue(audit.notification_sent)
            self.assertIsNotNone(audit.last_notification)
