import datetime
import json
from typing import Dict, List

from pyhafas.exceptions import GeneralHafasError
from pyhafas.fptf import Journey, Station
from pyhafas.profile import ProfileInterface
from pyhafas.profile.interfaces.requests.journeys import \
    JourneysRequestInterface


class BaseJourneysRequest(JourneysRequestInterface):
    def format_journeys_request(
            self: ProfileInterface,
            origin: Station,
            destination: Station,
            via: List[Station],
            date: datetime.datetime,
            min_change_time: int,
            max_changes: int,
            products: Dict[str, bool]
    ) -> dict:
        """
        Creates the HaFAS request for journeys

        :param origin: Origin station
        :param destination: Destionation station
        :param via: Via stations, maybe empty list)
        :param date: Date and time to search journeys for
        :param min_change_time: Minimum time for changes at stations
        :param max_changes: Maximum number of changes
        :param products: Allowed products (e.g. ICE,IC)
        :return: Request for HaFAS
        """
        # TODO: find out, what commented-out values mean and implement options
        return {
            'req': {
                'arrLocL': [{
                    'type': 'S',
                    'lid': 'A=1@L={}@'.format(destination.id)
                }],
                'viaLocL': [{
                    'loc': {
                        'type': 'S',
                        'lid': 'A=1@L={}@'.format(via_station.id)
                    }
                } for via_station in via],
                'depLocL': [{
                    'type': 'S',
                    'lid': 'A=1@L={}@'.format(origin.id)
                }],
                'outDate': date.strftime("%Y%m%d"),
                'outTime': date.strftime("%H%M%S"),
                'jnyFltrL': [
                    self.format_products_filter(products)
                ],
                'minChgTime': min_change_time,
                'maxChg': max_changes,
                # 'getPasslist': False,
                # 'gisFltrL': [],
                # 'getTariff': False,
                # 'ushrp': True,
                # 'getPT': True,
                # 'getIV': False,
                # 'getPolyline': False,
                # 'numF': 1,
                # 'outFrwd': True,
                # 'trfReq': {
                #    'jnyCl': 2,
                #    'cType': 'PK',
                #    'tvlrProf': [{
                #        'type': 'E',
                #        'redtnCard': 4
                #    }]
                # }
            },
            # 'cfg': {
            #    'polyEnc': 'GPA',
            #    'rtMode': 'HYBRID'
            # },
            'meth': 'TripSearch'
        }

    def parse_journeys_request(
            self: ProfileInterface,
            response: str) -> List[Journey]:
        """
        Parses the HaFAS response for journeys request

        :param response: HaFAS response
        :return: List of Journey objects
        """
        data = json.loads(response)
        journeys = []

        if data.get('err') or data['svcResL'][0]['err'] != 'OK':
            raise GeneralHafasError(
                "HaFAS returned general error: " +
                data['svcResL'][0].get(
                    'errTxt',
                    ""))

        for jny in data['svcResL'][0]['res']['outConL']:
            # TODO: Add more data
            date = self.parse_date(jny['date'])
            journeys.append(
                Journey(
                    jny['ctxRecon'], date=date, duration=self.parse_timedelta(
                        jny['dur']), legs=self.parse_legs(
                        jny, data['svcResL'][0]['res']['common'], date)))
        return journeys
