import csv

from vvspy import get_departures
from vvspy import get_arrivals
from vvspy import get_trip
from fuzzywuzzy import fuzz
from datetime import datetime, timedelta


def read_csv(file):
    """ Reads the VVS data from a csv file and returns a list of dictionary objects

    :param file: csv file
    :return: returns a list of dictionary objects containing information about the stations
    """
    vvs_data = list()
    with open(file, 'r', encoding='latin-1') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            vvs_station = {'id': row[3], 'name': row[1], 'place': row[5], 'part_place': row[6], 'district': row[7],
                           'tariff_zone': row[8], 'means_of_transport': row[9], 'lines': row[10]}
            vvs_data.append(vvs_station)

    return vvs_data


def search_for_station(station):
    """ Searching for the best matching station name in the vvs_data using the levenshtein distance

    :param station: the station name, and optionally the place, which is given by the user
    :return: returns id and name information for the best matching station
    """

    vvs_data = read_csv('./examples/webapi/vvs/data/vvs_haltestellen.csv')
    result, place  = None, None
    bestratio = 0
    if " in " in station:
        station_place = station.split(" in ")
        station = station_place[0]
        place = station_place[-1]
    for vvs_station in vvs_data:
        if place:
            ratio = fuzz.ratio(station.lower(), vvs_station['name'].lower()) + fuzz.ratio(place.lower(), vvs_station['part_place'].lower())
        else:
            ratio = fuzz.ratio(station.lower(), vvs_station['name'].lower()) 
        if ratio >= bestratio:
            bestratio = ratio
            result = [{'id':vvs_station['id'], 'station_name': vvs_station['name']}]

    return result


def departure(station, line, date = None):
    """ Queries the departures for the given station, line, and date

    :param station: the station name, and optionally the place, which is given by the user
    :param line: the line for which the user wants to know the departure
    :param date: the date and time for which the user wants to know the departure
    :return: return all found depatures
    """

    stations = search_for_station(station)
    result = list()

    if date:
        date = convert_to_datetime(date)
    else:
        date = datetime.now()

    for s in stations:
        deps = get_departures(station_id=s['id'],  check_time=date)
        for dep in deps:
            if dep.serving_line.symbol.lower() == line.lower():
                result.append({'dep': dep})
            elif line == '':
                result.append({'dep': dep})
    return result


def arrival(station, line, date = None):
    """ Queries the arrivals for the given station, line, and date

    :param station: the station name, and optionally the place, which is given by the user
    :param line: the line for which the user wants to know the arrival
    :param date: the date and time for which the user wants to know the arrival
    :return: return all found arrivals
    """

    stations = search_for_station(station)
    result = list()

    if date:
        date = convert_to_datetime(date)
    else:
        date = datetime.now()

    for s in stations:
        arrs = get_arrivals(station_id=s['id'], check_time=date)
        for arr in arrs:

            if arr.serving_line.symbol.lower() == line.lower():
                result.append({'arr': arr})
            elif line == '':
                result.append({'arr': arr})
    return result


def trip(station_start, station_end, date=None):
    """ Queries the trips for the given start station, destination, and date

    :param station_start: station from which the user wants to start the trip
    :param station_end: station to which the user wants to get
    :param date: the date and time for which the user wants to start the trip
    :return: return all found trips
    """

    start = search_for_station(station_start)[0]
    end = search_for_station(station_end)[0]

    result = list()

    if date:
        date = convert_to_datetime(date)
    else:
        date = datetime.now()

    # The "+ timedelta(hours=2)" is needed because of a bug in the VVS API which we use
    trip = get_trip(start['id'], end['id'],check_time=date + timedelta(hours=2))
    steps = list()
    for connection in trip.connections:
        steps.append({'line': connection.transportation.number, 'from': connection.origin.name, 'to': connection.destination.name, 'departure': connection.origin.departure_time_estimated})
    start = steps[0]['from']
    destination = steps[-1]['to'] 

    result.append({'from': start, 'to': destination, 'duration': (trip.duration/60), 'steps': steps})
    return result


def convert_to_datetime(date_time_str):
    """ Converts the date_time_str string to a formated datetime object and also fills in missing date or time information

    :param date_time_str: String which can contain information about the date and/or time
    :return: returns a datetime object in the given format
    """
    date_time_split = date_time_str.split(' ')
    date = None
    format = '%d.%m.%Y %H:%M'
    now = datetime.now()
    if len(date_time_split) == 1:
        if ':' in date_time_split[0]:
            date = now.strftime('%d.%m.%Y') + " " + date_time_split[0]
        elif '.' in date_time_split[0]:
            date = date_time_split[0] + " " + now.strftime('%H:%M')
        elif '#' in date_time_split[0]:
            shift_unit = date_time_split[0].split("#")
            duration = int(shift_unit[0])
            if 'min' in shift_unit[-1]:
                date = (now + timedelta(minutes=duration)).strftime('%d.%m.%Y %H:%M') 
            else:
                date = (now + timedelta(hours=duration)).strftime('%d.%m.%Y %H:%M')
    elif len(date_time_split) == 2:
        date = date_time_str
    elif len(date_time_split) == 3:
        if len(date_time_split[0]) == 1:
            date_time_split[0] = "0" + date_time_split[0]
        date = date_time_split[0] + " " + date_time_split[1].capitalize() + " " + date_time_split[2] + " " + now.strftime('%H:%M')
        format = '%d %B %Y %H:%M'
    elif len(date_time_split) == 4:
        if len(date_time_split[0]) == 1:
            date_time_split[0] = "0" + date_time_split[0]
        date = date_time_split[0] + " " + date_time_split[1] + " " + date_time_split[2] + " " + date_time_split[3]
        format = '%d %B %Y %H:%M'

    return datetime.strptime(date, format)

