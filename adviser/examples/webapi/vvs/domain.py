###############################################################################
#
# Copyright 2020, University of Stuttgart: Institute for Natural Language Processing (IMS)
#
# This file is part of Adviser.
# Adviser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3.
#
# Adviser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adviser.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

from typing import List, Iterable
from utils.domain.lookupdomain import LookupDomain
from examples.webapi.vvs.vvs_api import *
from examples.webapi.vvs import vvs_api as vvs


class VVSDomain(LookupDomain):
    """Domain for the VVS API

    Attributes:
        last_results (List[dict]): Current results which the user might request info about
    """
    counter = 0

    def __init__(self):
        LookupDomain.__init__(self, 'VVSAPI', 'VVS')
        self.last_results = []

    def find_entities(self, constraints: dict, requested: list, requested_slots: Iterable = iter(())):
        """ Returns all entities from the data backend that meet the constraints.

        Args:
            constraints (dict): Slot-value mapping of constraints.
                                If empty, all entities in the database will be returned.
            requested (list): List of user requested slots
            requested_slots (Iterable): list of slots that should be returned in addition to the
                                        system requestable slots and the primary key
        """

        if set(requested) == set(self.get_informable_slots()):
            return []

        date_time = None
        if 'datetime' in constraints:
                date_time = constraints['datetime']

        # Case for user request for departure or arrival
        if 'line' in constraints and 'station' in constraints and ('departure' in requested or 'arrival' in requested) :
            departures, arrivals = None, None

            if 'departure' in requested:
                departures = self._query(constraints['station'], constraints['line'], vvs.departure, date_time)
            if 'arrival' in requested:
                arrivals = self._query(constraints['station'], constraints['line'], vvs.arrival, date_time)

            if not departures and not arrivals:
                self.last_results = [{
                'artificial_id': str(len(self.last_results)),
                'departure': 'null',
                'arrival': 'null'
                }]
                return []  

            #Append multiple departures/arrivals to the result list considering the constraints
            results = []
            i = 0
            if 'departure' in requested:
                for departure in departures:
                    i+=1
                    results.append({
                    'artificial_id': str(i),
                    'departure': departure
                })
            if 'arrival' in requested:
                for arrival in arrivals:
                    i+=1
                    results.append({
                    'artificial_id': str(i),
                    'arrival': arrival
                })
            
            
            if list(requested_slots):
                cleaned_results = [{slot: result_dict[slot] for slot in requested_slots} for result_dict in results]
            else:
                cleaned_results = results
                
            self.last_results = results
            return cleaned_results

        # Case for user request for a trip
        elif 'from' in constraints and 'to' in constraints and 'trip' in requested:
            trips = None

            if 'trip' in requested:
                trips = self._query(constraints['from'], constraints['to'], vvs.trip, date_time)
    
            if not trips:
                self.last_results = [{
                'artificial_id': str(len(self.last_results)),
                'trip': 'null'}]
                return []

            # Append multiple trips to the result list
            results = []
            i = 0
            for trip in trips:
                i+=1
                results.append({
                'artificial_id': str(i),
                'trip': trip
            })

            if list(requested_slots):
                cleaned_results = [{slot: result_dict[slot] for slot in requested_slots} for result_dict in results]
            else:
                cleaned_results = results
                
            self.last_results = results
            return cleaned_results

        else:
            return []

    def find_info_about_entity(self, entity_id, requested_slots: Iterable):
        """ Returns the values (stored in the data backend) of the specified slots for the
            specified entity.

            No longer in use!

        Args:
            entity_id (str): primary key value of the entity
            requested_slots (dict): slot-value mapping of constraints
        """
        result = {slot: self.last_results[int(entity_id) - 1][slot] for slot in requested_slots}
        result['artificial_id'] = entity_id
        return [result]
        #return [self.last_results[int(entity_id)]]

    def get_requestable_slots(self) -> List[str]:
        """ Returns a list of all slots requestable by the user. """
        return ['departure', 'arrival', 'trip']

    def get_system_requestable_slots(self) -> List[str]:
        """ Returns a list of all slots requestable by the system. """
        return []

    def get_informable_slots(self) -> List[str]:
        """ Returns a list of all informable slots. """
        return ['station', 'line', 'from', 'to', 'datetime']

    def get_mandatory_slots(self) -> List[str]:
        """ Returns a list of lists of all mandatory slots. """
        return [['station', 'line'], ['from', 'to']]

    def get_possible_values(self, slot: str) -> List[str]:
        """ Returns all possible values for an informable slot

        Args:
            slot (str): name of the slot

        Returns:
            a list of strings, each string representing one possible value for
            the specified slot.
         """
        raise BaseException('all slots in this domain do not have a fixed set of '
                            'values, so this method should never be called')

    def get_primary_key(self) -> str:
        """ Returns the slot name that will be used as the 'name' of an entry """
        return 'artificial_id'

    def _query(self, object1, object2, method, date_time=None):
        """ Queries VVS API, given the method and its specifications, which depend on the type of request.

        :param object1: Information about station or starting station of a trip
        :param object2: Information about line or destination of a trip
        :param method: The method which has to be called for the request (vvs.departure, vvs.arrival, vvs.trip)
        :param date_time: Date and time for the query as string or None
        :return: results of the query (departures, arrivals, or trips)
        """

        try:
            result = method(object1, object2, date=date_time)
            return result
        except BaseException as e:
            raise (e)
            return None, None

    def get_keyword(self):
        return 'vvs'
