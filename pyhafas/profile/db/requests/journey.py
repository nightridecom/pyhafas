import datetime
import json
from base64 import b64decode
from typing import Optional, List, Literal

from pyhafas.profile.base import BaseJourneyRequest
from pyhafas.profile.interfaces import JourneyRequestInterface, \
    ProfileInterface
from pyhafas.types.hafas_response import HafasResponse
from pyhafas.types.fptf import Journey, Leg


class AgeGroup:
    BABY = 'B'
    CHILD = 'K'
    YOUNG = 'Y'
    ADULT = 'E'
    SENIOR = 'S'
    upper_bound_of = {
        BABY: 6,
        CHILD: 15,
        YOUNG: 27,
        ADULT: 65,
        SENIOR: float('inf'),
    }


class Ticket:
    priceCategory: str  # e.g. "Super Sparpreis Europa"
    seatCategory: str  # e.g. "1. Klasse"
    price: int
    currency: str

    def __init__(self, price_category: str, seat_category: str, price: int,
                 currency: str):
        self.priceCategory = price_category
        self.seatCategory = seat_category
        self.price = price
        self.currency = currency


# todo instead of defining own class, Journey should have a better price attribute
# submit an issue here https://github.com/public-transport/friendly-public-transport-format/issues

class JourneyWithTickets(Journey):
    tickets: List[Ticket]

    def __init__(self, id: str,
                 date: Optional[datetime.date] = None,
                 duration: Optional[datetime.timedelta] = None,
                 legs: Optional[List[Leg]] = None,
                 prices: Optional[List[Ticket]] = None):
        super().__init__(
            id=id,
            date=date,
            duration=duration,
            legs=legs
        )
        self.tickets = prices


class DBJourneyRequest(BaseJourneyRequest, JourneyRequestInterface):
    def format_journey_request(
            self: ProfileInterface,
            journey: Journey,
            tickets: Optional[bool] = False,
            first_class: Optional[bool] = False,
            age: Optional[int] = 30,
            reduction_card: Optional[Literal[
                0, 1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15]] = 0) -> dict:
        """
        Creates the HaFAS request body for a journey request

        :param journey: Id of the journey (ctxRecon)
        :param tickets: Whether to include ticket prices
        :param first_class: Whether to include first class tickets
        :param age: Age of the passenger
        :param reduction_card: Reduction card of the passenger
        :return: Request body for HaFAS
        """
        body = {
            'req': {
                'ctxRecon': journey.id
            },
            'meth': 'Reconstruction'
        }
        age_group = DBJourneyRequest.age_group_from_age(age)
        if tickets:
            body['req']['trfReq'] = {
                'jnyCl': 1 if first_class else 2,
                'cType': 'PK',
                'rType': 'DB-PE',
                'tvlrProf': [{
                    'type': age_group,
                    'age': age,
                    'redtnCard': reduction_card
                }] # maximum 5 pax per request, apparently
            }
        return body

    def parse_journey_request(
            self: ProfileInterface,
            data: HafasResponse,
            tickets: Optional[bool] = False,
            first_class: Optional[bool] = False) -> Journey:
        """
        Parses the HaFAS response for a journey request

        :param data: Formatted HaFAS response
        :param tickets: Whether to parse ticket prices
        :param first_class: Whether to parse first class tickets
        :return: A Journey object
        """
        date = self.parse_date(data.res['outConL'][0]['date'])
        if tickets:
            prices = []
            for price in data.res['outConL'][0]['trfRes']['fareSetL']:
                add_data_decoded = json.loads(
                    b64decode(price['addData']).decode('utf-8'))
                is_first_class = ('Upsell' in add_data_decoded and
                                  add_data_decoded[
                                      'Upsell'] == 'S1') or first_class
                prices.append(Ticket(
                    price_category=price['fareL'][0]['name'],
                    seat_category='1. Klasse' if is_first_class else '2. Klasse',
                    price=price['prc'],
                    currency=price['fareL'][0]['ticketL'][0]['cur']
                ))
            return JourneyWithTickets(
                data.res['outConL'][0]['ctxRecon'],
                date=date,
                duration=self.parse_timedelta(
                    data.res['outConL'][0]['dur']),
                legs=self.parse_legs(
                    data.res['outConL'][0],
                    data.common,
                    date),
                prices=prices if tickets else None
            )
        else:
            return Journey(
                data.res['outConL'][0]['ctxRecon'],
                date=date,
                duration=self.parse_timedelta(
                    data.res['outConL'][0]['dur']),
                legs=self.parse_legs(
                    data.res['outConL'][0],
                    data.common,
                    date),
            )

    @staticmethod
    def age_group_from_age(age: int) -> str:
        upper_bound_of = AgeGroup.upper_bound_of
        if age < upper_bound_of[AgeGroup.BABY]:
            return AgeGroup.BABY
        if age < upper_bound_of[AgeGroup.CHILD]:
            return AgeGroup.CHILD
        if age < upper_bound_of[AgeGroup.YOUNG]:
            return AgeGroup.YOUNG
        if age < upper_bound_of[AgeGroup.ADULT]:
            return AgeGroup.ADULT
        if age < upper_bound_of[AgeGroup.SENIOR]:
            return AgeGroup.SENIOR
        raise TypeError(f"Invalid age '{age}'")
