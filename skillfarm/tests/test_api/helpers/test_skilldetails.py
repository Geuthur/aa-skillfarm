from django.test import TestCase
from django.utils import timezone
from eveuniverse.models import EveType

from skillfarm.api.character.helpers.skilldetails import (
    _calculate_single_progress_bar,
    _calculate_sum_progress_bar,
)
from skillfarm.api.character.helpers.skillqueue import _get_character_skillqueue
from skillfarm.api.helpers import generate_progressbar
from skillfarm.models.skillfarm import CharacterSkillqueueEntry
from skillfarm.tests.testdata.allianceauth import load_allianceauth
from skillfarm.tests.testdata.eveuniverse import load_eveuniverse
from skillfarm.tests.testdata.skillfarm import create_skillfarm_character

MODULE_PATH = "skillfarm.api.character.helpers."


class Test_Calculate_Single_Progress_Bar(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)
        cls.skill1 = EveType.objects.get(name="skill1")
        cls.skill2 = EveType.objects.get(name="skill2")

    def test_calc_single_progress_bar_no_end_sp(self):
        """Test should return 0 if the skill has no end SP"""
        characterskillqueue = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now(),
            finish_date=timezone.now() + timezone.timedelta(days=3),
            level_end_sp=0,
        )

        self.assertEqual(_calculate_single_progress_bar(characterskillqueue), 0)

    def test_calc_single_progress_bar_100_percent(self):
        """Test should return 100 if the skill is already finished"""
        characterskillqueue = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=2),
            finish_date=timezone.now() - timezone.timedelta(days=1),
            level_end_sp=1000,
        )

        self.assertEqual(_calculate_single_progress_bar(characterskillqueue), 100)

    def test_calc_single_progress_bar_below_zero(self):
        """Test should return 100 if the skill is already finished"""
        characterskillqueue = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now() + timezone.timedelta(days=1),
            finish_date=timezone.now() + timezone.timedelta(days=3),
            level_end_sp=1000,
        )

        self.assertEqual(_calculate_single_progress_bar(characterskillqueue), 0)

    def test_calc_single_progress_bar(self):
        """Test should return 25 if the skill is 25% finished"""
        characterskillqueue = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=1),
            finish_date=timezone.now() + timezone.timedelta(days=3),
            level_end_sp=1000,
        )

        self.assertEqual(_calculate_single_progress_bar(characterskillqueue), 25.0)


class Test_Calculate_Sum_Progress_bar(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        load_eveuniverse()

        cls.audit = create_skillfarm_character(1001)
        cls.skill1 = EveType.objects.get(name="skill1")
        cls.skill2 = EveType.objects.get(name="skill2")

    def test_calc_sum_progress_bar_no_skills(self):
        """Test should return 0 if there are no skills"""
        excepted_progressbar = generate_progressbar(0)
        self.assertEqual(_calculate_sum_progress_bar({}), excepted_progressbar)

    def test_calc_sum_progress_bar_no_end_sp(self):
        """Test should return 0.0% if the skill has no end SP"""

        characterskillqueue = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now(),
            finish_date=timezone.now() + timezone.timedelta(days=3),
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue.save()

        skillqueue = _get_character_skillqueue(self.audit)

        excepted_progressbar = generate_progressbar(0.0)

        self.assertEqual(
            _calculate_sum_progress_bar(skillqueue["skillqueue"]), excepted_progressbar
        )

    def test_calc_sum_progress_bar_partial_progress(self):
        """Test should return 50.0%"""
        characterskillqueue = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=1),
            finish_date=timezone.now() + timezone.timedelta(days=1),
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue.save()

        skillqueue = _get_character_skillqueue(self.audit)

        excepted_progressbar = generate_progressbar(50.0)

        self.assertEqual(
            _calculate_sum_progress_bar(skillqueue["skillqueue"]), excepted_progressbar
        )

    def test_calc_sum_progress_bar_multiple_skills(self):
        """Test should return 75.0%"""
        characterskillqueue1 = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=2),
            finish_date=timezone.now() - timezone.timedelta(days=1),
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue1.save()

        characterskillqueue2 = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=2,
            eve_type=self.skill2,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=1),
            finish_date=timezone.now() + timezone.timedelta(days=1),
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue2.save()

        skillqueue = _get_character_skillqueue(self.audit)

        excepted_progressbar = generate_progressbar(75.0)

        self.assertEqual(
            _calculate_sum_progress_bar(skillqueue["skillqueue"]), excepted_progressbar
        )

    def test_calc_sum_progress_bar_multiple_skills_below_zero(self):
        """Test should return 0.0%"""
        characterskillqueue1 = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now() + timezone.timedelta(days=1),
            finish_date=timezone.now() + timezone.timedelta(days=3),
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue1.save()

        characterskillqueue2 = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=2,
            eve_type=self.skill2,
            finished_level=5,
            start_date=timezone.now() + timezone.timedelta(days=1),
            finish_date=timezone.now() + timezone.timedelta(days=3),
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue2.save()

        skillqueue = _get_character_skillqueue(self.audit)

        excepted_progressbar = generate_progressbar(0.0)

        self.assertEqual(
            _calculate_sum_progress_bar(skillqueue["skillqueue"]), excepted_progressbar
        )

    def test_calc_sum_progress_bar_with_nodate(self):
        """Test should return 50.0%"""
        characterskillqueue1 = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=1,
            eve_type=self.skill1,
            finished_level=5,
            start_date=timezone.now() - timezone.timedelta(days=2),
            finish_date=timezone.now() - timezone.timedelta(days=1),
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue1.save()

        characterskillqueue2 = CharacterSkillqueueEntry.objects.create(
            character=self.audit,
            queue_position=2,
            eve_type=self.skill2,
            finished_level=5,
            start_date=None,
            finish_date=None,
            level_start_sp=0,
            training_start_sp=100,
            level_end_sp=1000,
        )
        characterskillqueue2.save()

        skillqueue = _get_character_skillqueue(self.audit)

        excepted_progressbar = generate_progressbar(50.0)

        self.assertEqual(
            _calculate_sum_progress_bar(skillqueue["skillqueue"]), excepted_progressbar
        )
