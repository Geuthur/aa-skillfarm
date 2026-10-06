"""Calculator API endpoints for Skillfarm V2."""

# Standard Library
from http import HTTPStatus

# Third Party
from ninja import NinjaAPI

# Django
from django.utils.translation import gettext as _

# AA Skillfarm
from skillfarm.api import schema
from skillfarm.models.prices import EveTypePrice


class ApiEndpoints:
    tags = ["Calculator"]

    def __init__(self, api: NinjaAPI):
        @api.get(
            "calculator/",
            response={
                HTTPStatus.OK: schema.CalculatorResponse,
                HTTPStatus.FORBIDDEN: dict,
            },
            tags=self.tags,
            summary="Get skillfarm market prices and profit margins",
        )
        def get_calculator_data(request):
            if not request.user.has_perm("skillfarm.basic_access"):
                return HTTPStatus.FORBIDDEN, {"error": _("Permission Denied")}

            try:
                plex = EveTypePrice.objects.select_related("eve_type").get(
                    eve_type__id=44992
                )
                injector = EveTypePrice.objects.select_related("eve_type").get(
                    eve_type__id=40520
                )
                extractor = EveTypePrice.objects.select_related("eve_type").get(
                    eve_type__id=40519
                )

                plex_price = float(plex.sell)
                injector_price = float(injector.sell)
                extractor_price = float(extractor.sell)

                month_calc = (injector_price * 3.5) - (
                    (plex_price * 500) + (extractor_price * 3.5)
                )
                month12_calc = (injector_price * 3.5) - (
                    (plex_price * 300) + (extractor_price * 3.5)
                )
                month24_calc = (injector_price * 3.5) - (
                    (plex_price * 275) + (extractor_price * 3.5)
                )

                def to_item(p: EveTypePrice) -> schema.CalculatorItemSchema:
                    return schema.CalculatorItemSchema(
                        type_id=p.eve_type_id,
                        name=p.eve_type.name,
                        buy=float(p.buy),
                        sell=float(p.sell),
                        updated_at=(
                            p.updated_at.strftime("%Y-%m-%d %H:%M")
                            if p.updated_at
                            else None
                        ),
                    )

                return schema.CalculatorResponse(
                    error=False,
                    plex=to_item(plex),
                    injector=to_item(injector),
                    extractor=to_item(extractor),
                    month_calc=round(month_calc, 2),
                    month12_calc=round(month12_calc, 2),
                    month24_calc=round(month24_calc, 2),
                )
            except EveTypePrice.DoesNotExist:
                return schema.CalculatorResponse(
                    error=True,
                    error_message=_(
                        "Market price data is currently not available. Please run market update tasks."
                    ),
                )
