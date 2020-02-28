from __future__ import annotations

import datetime
import json
from enum import Enum
from hashlib import md5
from typing import Dict, List

import requests

from ..fptf import Journey, Station


class Profile:
    baseUrl: str = None
    defaultUserAgent: str = 'pyhafas'

    addMicMac: bool = False
    addChecksum: bool = False
    salt: str = None

    locale: str = 'de-DE'
    timezone: str = 'Europe/Berlin'

    requestBody: dict = {}

    def __init__(self, ua=defaultUserAgent):
        self.userAgent = ua

    def urlFormatter(self, data):
        url = self.baseUrl

        if self.addChecksum or self.addMicMac:
            parameters = []
            if self.addChecksum:
                parameters.append(
                    'checksum={}'.format(
                        self.calculateChecksum(data)))
            if self.addMicMac:
                parameters.append(
                    'mic={}&mac={}'.format(
                        *self.calculateMicMac(data)))
            url += '?{}'.format('&'.join(parameters))

        return url

    def request(self, body):
        data = {
            'svcReqL': [body]
        }
        data.update(self.requestBody)
        data = json.dumps(data)

        req = requests.post(
            self.urlFormatter(data),
            data=data,
            headers={
                'User-Agent': self.userAgent,
                'Content-Type': 'application/json'})
        return req

    def calculateChecksum(self, data):
        to_hash = data + self.salt
        to_hash = to_hash.encode('utf-8')
        return md5(to_hash).hexdigest()

    def calculateMicMac(self, data):
        mic = md5(data.encode('utf-8')).hexdigest()
        mac = md5((mic + self.salt).encode('utf-8')).hexdigest()
        return mic, mac

    def formatStationBoardRequest(
            self,
            station: Station,
            request_type: StationBoardRequestType) -> Dict:
        return {
            'req': {
                'type': request_type.value,
                'stbLoc': {
                    'lid': 'A=1@L={}@'.format(station.id)
                },
                'dur': 1,
            },
            'meth': 'StationBoard'
        }

    def formatJourneyRequest(self, journey: Journey) -> Dict:
        return {
            'req': {
                'ctxRecon': journey.id
            },
            'meth': 'Reconstruction'
        }

    def formatJourneysRequest(self, origin: Station, destination: Station) -> Dict:
        # TODO: find out, what commented-out values mean and implement options
        return {
            'req': {
                'arrLocL': [{
                    'type': 'S',
                    'lid': 'A=1@L={}@'.format(origin.id)
                }],
                #'viaLocL': None,
                'depLocL': [{
                    'type': 'S',
                    'lid': 'A=1@L={}@'.format(destination.id)
                }],
                #'jnyFltrL': [{
                #    'type': 'PROD',
                #    'mode': 'INC',
                #    'value': '1023'
                #}],
                #'outDate': '20200212',
                #'outTime': '124226',
                #'maxChg': -1,
                #'getPasslist': False,
                #'gisFltrL': [],
                #'getTariff': False,
                #'ushrp': True,
                #'getPT': True,
                #'getIV': False,
                #'getPolyline': False,
                #'numF': 1,
                #'outFrwd': True,
                #'trfReq': {
                #    'jnyCl': 2,
                #    'cType': 'PK',
                #    'tvlrProf': [{
                #        'type': 'E',
                #        'redtnCard': 4
                #    }]
                #}
            },
            #'cfg': {
            #    'polyEnc': 'GPA',
            #    'rtMode': 'HYBRID'
            #},
            'meth': 'TripSearch'
        }

    def parseTime(self, TimeString) -> datetime.time:
        pass

    def parseDate(self, dateString) -> datetime.date:
        pass

    def parseStationBoardRequest(self, response: str) -> List[Journey]:
        data = json.loads(response)
        journeys = []

        if data['svcResL'][0]['err'] != 'OK':
            raise

        for jny in data['svcResL'][0]['res']['jnyL']:
            journey = Journey(jny['jid'])
            # TODO: Add more data
            # ...
            # ...
            journeys.append(journey)

        return journeys

    def parseJourneyRequest(self, response: str) -> Journey:
        pass

    def parseJourneysRequest(self, response: str) -> List[Journey]:
        pass

class StationBoardRequestType(Enum):
    DEPARTURE = 'DEP'
    ARRIVAL = 'ARR'

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)