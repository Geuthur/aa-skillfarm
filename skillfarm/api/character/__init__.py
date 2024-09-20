from .filter import SkillFarmFilterApiEndpoints
from .skillfarm import SkillFarmApiEndpoints


def setup(api):
    SkillFarmApiEndpoints(api)
    SkillFarmFilterApiEndpoints(api)
