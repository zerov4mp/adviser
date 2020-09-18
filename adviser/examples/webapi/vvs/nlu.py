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

from typing import List
import re

from utils.logger import DiasysLogger
from utils import UserAct, UserActionType
from services.service import Service, PublishSubscribe
from utils.sysact import SysAct
from utils.beliefstate import BeliefState

# simple list of regexes
LINE_NAME_REGEXES = [
    re.compile(r'(?<!on )(?<!from )(?<!leave )(?<!arrive )(?<!to )\bthe ([^ ]*)\b')
]

STATION_DEPARTURE_REGEXES = [
    re.compile(r'(\bleave(\s+[a-zA-ZßäöüÄÖÜ]+)+( on\b| at\b| in \d+|\.|\?|$))')
]

STATION_ARRIVAL_REGEXES = [
    re.compile(r'(\barrive(\s+[a-zA-ZßäöüÄÖÜ]+)+( on\b| at\b| in \d+|\.|\?|$))')
]

STATION_FROM_REGEXES = [
   re.compile(r'(\bfrom(\s+(?!to\b)[a-zA-ZßäöüÄÖÜ]+)+( to\b| on\b| at\b| in \d+|\.|\?|$))')
]

STATION_TO_REGEXES = [
    re.compile(r'(\bto(\s+(?!from\b)[a-zA-ZßäöüÄÖÜ]+)+( from\b| on\b| at\b| in \d+|\.|\?|$))')
]

DATETIME_REGEXES = [
    re.compile(r'(\bon \d{2}\.\d{2}\.\d{4}( at)? \d{2}:\d{2}(\s|\.|\?|$)|\bon( the)? \d\d?(st|nd|rd|th)?( of)? \w+ \d{4}( at)? \d{2}:\d{2}(\s|\.|\?|$))'),
    re.compile(r'\bat \d{2}:\d{2}(\s|\.|\?|$)'),
    re.compile(r'\bon( the)? (\d{2}\.\d{2}\.\d{4}|\d\d?(st|nd|rd|th)?( of)? \w+ \d{4})(\s|\.|\?|$)'),
    re.compile(r'\d+\s?(min(s)?|minute(s)?|hour(s)?|h)(\s|\.|\?|$)')
]

class VVSNLU(Service):
    """NLU for the vvs domain."""
    frombool = False
    tobool = False
    startbool = True

    def __init__(self, domain, logger=DiasysLogger()):
        # only calls super class' constructor
        super(VVSNLU, self).__init__(domain, debug_logger=logger)


    @PublishSubscribe(sub_topics=["user_utterance"], pub_topics=["user_acts"])
    def extract_user_acts(self, user_utterance: str = None, sys_act: SysAct = None, beliefstate: BeliefState = None) -> dict(user_acts=List[UserAct]):
        """Main function for detecting and publishing user acts.

        Args:
            user_utterance: the user input string

        Returns:
            dict with key 'user_acts' and list of user acts as value
        """
        user_acts = []
        
        if not user_utterance and self.startbool:
            self.startbool = False
            return {'user_acts': None}
        elif not user_utterance and not self.startbool:
            user_acts.append(UserAct(user_utterance, UserActionType.Bad))
            return {'user_acts': user_acts}
        

        user_utterance = ' '.join(user_utterance.lower().split())
    
        for bye in ('bye', 'goodbye', 'byebye', 'seeyou', 'exit', 'quit'):
            if user_utterance.replace(' ', '').endswith(bye):
                return {'user_acts': [UserAct(user_utterance, UserActionType.Bye)]}
    
        for regex in STATION_DEPARTURE_REGEXES:
            # Departure
            match = regex.search(user_utterance)
            if match:
                station = re.sub(r'(\.|\?|\b(at\b|the|on\b|of\b|in \d+))', '', match.group())
                station = self.convert_match_for_station(station)
                user_acts.append(UserAct(user_utterance, UserActionType.Inform, 'station', station))
                user_acts.append(UserAct(user_utterance, UserActionType.Request, 'departure'))
                break
        for regex in STATION_ARRIVAL_REGEXES:
            # Arrival
            match = regex.search(user_utterance)
            if match:
                station = re.sub(r'(\.|\?|\b(at\b|the|on\b|of\b|in \d+))', '', match.group())
                station = self.convert_match_for_station(station)
                user_acts.append(UserAct(user_utterance, UserActionType.Inform, 'station', station))
                user_acts.append(UserAct(user_utterance, UserActionType.Request, 'arrival'))
                break
        for regex in LINE_NAME_REGEXES:
            # Line
            match = regex.search(user_utterance)
            if match:
                line = match.group().split(" ")[-1]
                user_acts.append(UserAct(user_utterance, UserActionType.Inform, 'line', line))
                break
        for regex in STATION_FROM_REGEXES:
            # From
            match = regex.search(user_utterance)
            if match:
                station = re.sub(r'(\.|\?|\b((on|to|the|at|of)\b|in \d+))', '', match.group())
                station = self.convert_match_for_station(station)
                user_acts.append(UserAct(user_utterance, UserActionType.Inform, 'from',  station))
                self.frombool = True
                break
        for regex in STATION_TO_REGEXES:
            # To
            match = regex.search(user_utterance)
            if match:
                station = re.sub(r'(\.|\?|\b((on|from|the|at|of)\b|in \d+))', '', match.group())
                station = self.convert_match_for_station(station)
                user_acts.append(UserAct(user_utterance, UserActionType.Inform, 'to',  station))
                self.tobool = True
                break
        # If both "from" and "to" information is given then append the "trip" to the user_acts
        if self.frombool and self.tobool:
            user_acts.append(UserAct(user_utterance, UserActionType.Request, 'trip'))
            self.frombool = False
            self.tobool = False
        for regex in DATETIME_REGEXES:
            #Datetime
            match = regex.search(user_utterance)
            if match:
                date_time = re.sub(r'(\bon( the)?|at|\bof)\b|\?', '', match.group())
                if re.compile(r'(\d\d?(st|nd|rd|th)?)').search(date_time):
                    date_time = re.sub(r'((st|nd|rd|th))', '', date_time, count=1)
                if re.compile(r'\d+\s(min(s)?|minute(s)?|hour(s)?|h)(\s|\.|$)').search(date_time):
                    date_time = "#".join(date_time.split(" "))
                elif re.compile(r'(\d+min(s)?|minute(s)?|hour(s)?|h)(\s|\.|$)').search(date_time):
                    if 'm'in date_time:
                        index = date_time.find('m')
                    else:
                        index = date_time.find('h')
                    date_time = date_time[:index] + "#" + date_time[index:]
                date_time = date_time.strip().replace("  ", " ")
                user_acts.append(UserAct(user_utterance, UserActionType.Inform, 'datetime',  date_time))
                break        
        if not user_acts:
             user_acts.append(UserAct(user_utterance, UserActionType.Bad))

        return {'user_acts': user_acts}
    
    def convert_match_for_station(self, match):
        """ Formats matching station name

        :param match: station name
        :return: returns formatted station name
        """
        station = " ".join(match.split(" ")[1:]).strip()
        station = station.strip().replace("  ", " ")
        return station
        
