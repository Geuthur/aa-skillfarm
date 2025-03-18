import requests

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils import timezone
from eveuniverse.models import EveType

from skillfarm.app_settings import (
    SKILLFARM_PRICE_SOURCE_ID,
)
from skillfarm.hooks import get_extension_logger
from skillfarm.models.prices import EveTypePrice

logger = get_extension_logger(__name__)


class Command(BaseCommand):
    help = "Preloads price data required for the skillfarm from Fuzzwork market API"

    # pylint: disable=unused-argument
    def handle(self, *args, **options):
        type_ids = []
        market_data = {}

        # Get all skillfarm relevant ids
        typeids = EveType.objects.filter(id__in=[44992, 40520, 40519]).values_list(
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
                print(
                    f"EveType {key} not found. Skipping... Ensure you have loaded the data from eveuniverse."
                )
                continue

        try:
            EveTypePrice.objects.bulk_create(objs)
        except IntegrityError:
            print("Error: Prices already loaded into database.")
            delete_arg = input("Would you like to replace all prices? (y/n): ")

            if delete_arg == "y":
                EveTypePrice.objects.all().delete()
                EveTypePrice.objects.bulk_create(objs)
                self.stdout.write(f"Successfully replaced {len(objs)} prices.")
            else:
                self.stdout.write("No changes made.")
            return

        logger.debug("Updated all skillfarm prices.")
        self.stdout.write(f"Successfully created {len(objs)} prices.")
