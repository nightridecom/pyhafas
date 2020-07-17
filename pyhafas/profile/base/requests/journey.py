import json

from pyhafas.exceptions import GeneralHafasError
from pyhafas.fptf import Journey
from pyhafas.profile import ProfileInterface
from pyhafas.profile.interfaces.requests.journey import JourneyRequestInterface


class BaseJourneyRequest(JourneyRequestInterface):
    def format_journey_request(
            self: ProfileInterface,
            journey: Journey) -> dict:
        """
        Creates the HaFAS request for refreshing journey details

        :param journey: Id of the journey (ctxRecon)
        :return: Request for HaFAS
        """
        return {
            'req': {
                'ctxRecon': journey.id
            },
            'meth': 'Reconstruction'
        }

    def parse_journey_request(
            self: ProfileInterface,
            data: dict) -> Journey:
        """
        Parses the HaFAS response for journeys request

        :param data: Formatted HaFAS response
        :return: List of Journey objects
        """
        date = self.parse_date(data['res']['outConL'][0]['date'])
        return Journey(
            data['res']['outConL'][0]['ctxRecon'],
            date=date,
            duration=self.parse_timedelta(
                data['res']['outConL'][0]['dur']),
            legs=self.parse_legs(
                data['res']['outConL'][0],
                data['common'],
                date))
