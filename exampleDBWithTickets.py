import datetime

from pyhafas import HafasClient
from pyhafas.profile import DBProfile


if __name__ == "__main__":
    profile = DBProfile()
    profile.activate_retry()
    client = HafasClient(profile, debug=True)

    origin = 8096009
    destinations = [
        8011160,
        8010060,
    ]
    stations_basel = client.locations('Basel', 'S')
    stations_amsterdam = client.locations('Amsterdam', 'S')

    station_basel_sbb = [
        station for station in stations_basel if station.name == 'Basel SBB'
    ][0]
    station_amsterdam_centraal = [
        station
        for station in stations_amsterdam
        if station.name == 'Amsterdam Centraal'
    ][0]
    overnight_journeys = client.journeys(
        origin=station_basel_sbb,
        destination=station_amsterdam_centraal,
        date=datetime.datetime.now(),
        max_changes=0,
        products={
            'regional_express': False,
            'regional': False,
            'ferry': False,
            'bus': False,
            'suburban': False,
            'subway': False,
            'tram': False,
            'taxi': False,
        },
    )
    # filter for journes with only one leg
    overnight_journeys = [
        journey for journey in overnight_journeys if len(journey.legs) == 1
    ]
    # filter for IC or ICE trains
    overnight_ic_journeys = [
        journey
        for journey in overnight_journeys
        if 'IC' in journey.legs[0].name
    ]
    overnight_ic_journey = overnight_ic_journeys[0]
    # get tickets
    details = client.journey(overnight_ic_journey,
                             tickets=True,
                             first_class=False,
                             age=30,
                             reduction_card=0)
    pass
