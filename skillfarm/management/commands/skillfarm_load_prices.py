# Third Party
import requests

# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveType

# AA Skillfarm
from skillfarm import __title__
from skillfarm.app_settings import SKILLFARM_PRICE_SOURCE_ID
from skillfarm.models.prices import EveTypePrice

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class Command(BaseCommand):
    help = "Preloads price data required for the skillfarm from Fuzzwork market API"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        type_ids = []
        market_data = {}

        # Ensure that the required types are loaded into the database
        EveType.objects.get_or_create_esi(id=44992)
        EveType.objects.get_or_create_esi(id=40520)
        EveType.objects.get_or_create_esi(id=40519)

        # Get all skillfarm relevant ids
        typeids = EveType.objects.filter(id__in=[44992, 40520, 40519]).values_list(
            "id", flat=True
        )

        if len(typeids) != 3:
            self.stdout.write(
                "Error: Not all required types are loaded into the database."
            )
            return

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
                    f"EveType {key} not found. Skipping... Ensure you have loaded the data from eveuniverse."
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
