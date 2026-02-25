# Third Party
import requests

# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from eve_sde.models.types import ItemType as EveType

# AA Skillfarm
from skillfarm import __title__
from skillfarm.app_settings import SKILLFARM_PRICE_SOURCE_ID
from skillfarm.models.prices import EveTypePrice
from skillfarm.providers import AppLogger, esi

logger = AppLogger(my_logger=get_extension_logger(__name__), prefix=__title__)


# pylint: disable=too-many-locals
class Command(BaseCommand):
    help = "Preloads price data required for the skillfarm from Fuzzwork market API"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        type_ids = []
        market_data = {}
        skillfarm_ids = [44992, 40520, 40519]

        # Get all skillfarm relevant ids
        typeids = EveType.objects.filter(id__in=skillfarm_ids).values_list(
            "id", flat=True
        )

        if len(typeids) != 3:
            missing_ids = set(skillfarm_ids) - set(typeids)
            for type_id in missing_ids:
                esi.get_type_or_create_from_esi(eve_id=type_id)
            self.stdout.write(
                "One or more skillfarm relevant types not found. Attempting to fetch from ESI and create in database."
            )
            typeids = EveType.objects.filter(id__in=skillfarm_ids).values_list(
                "id", flat=True
            )

        for item in typeids:
            type_ids.append(item)

        request = requests.get(
            "https://market.fuzzwork.co.uk/aggregates/",
            params={
                "types": ",".join([str(x) for x in type_ids]),
                "station": SKILLFARM_PRICE_SOURCE_ID,
            },
        ).json()

        market_data.update(request)

        # Create Bulk Object
        objs = []

        for key, value in market_data.items():
            try:
                eve_type = EveType.objects.get(id=key)

                item = EveTypePrice(
                    name=eve_type.name,
                    eve_type=eve_type,
                    buy=float(value["buy"]["percentile"]),
                    sell=float(value["sell"]["percentile"]),
                    updated_at=timezone.now(),
                )

                objs.append(item)
            except EveType.DoesNotExist:
                self.stdout.write(
                    f"EveType {key} not found. Skipping... Ensure you have loaded the data."
                )
                continue

        try:
            with transaction.atomic():
                EveTypePrice.objects.bulk_create(objs)
                self.stdout.write(f"Successfully created {len(objs)} prices.")
                logger.debug("Created all skillfarm prices.")
                return
        except IntegrityError:
            self.stdout.write("Error: Prices already loaded into database.")
            update_arg = input("Would you like to update all prices? (y/n): ")

            if update_arg == "y":
                count = 0
                for obj in objs:
                    with transaction.atomic():
                        EveTypePrice.objects.update_or_create(
                            eve_type_id=obj.eve_type_id,
                            defaults={
                                "name": obj.name,
                                "buy": obj.buy,
                                "sell": obj.sell,
                                "updated_at": obj.updated_at,
                            },
                        )
                    count += 1
                self.stdout.write(f"Successfully updated {count} prices.")
                logger.debug("Updated all skillfarm prices.")
            else:
                self.stdout.write("No changes made.")
            return
