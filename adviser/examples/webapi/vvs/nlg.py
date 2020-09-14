############################################################################################
#
# Copyright 2020, University of Stuttgart: Institute for Natural Language Processing (IMS)
#
# This file is part of Adviser.
# Adviser is free software: you can redistribute it and/or modify'
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
############################################################################################
from utils import DiasysLogger
from utils import SysAct, SysActionType
from services.service import Service, PublishSubscribe
import re


class VVSNLG(Service):
    """Simple NLG for the vvs domain"""

    def __init__(self, domain, logger=DiasysLogger()):
        # only calls super class' constructor
        #HandcraftedNLG.__init__(self, domain, logger)
        super(VVSNLG, self).__init__(domain, debug_logger=logger)

    @PublishSubscribe(sub_topics=["sys_act"], pub_topics=["sys_utterance"])
    def generate_system_utterance(self, sys_act: SysAct = None) -> dict(sys_utterance=str):
        """Main function for generating and publishing the system utterance

        Args:
            sys_act: the system act for which to create a natural language realisation

        Returns:
            dict with "sys_utterance" as key and the system utterance as value
        """

        if sys_act is None or sys_act.type == SysActionType.Welcome:
            return {'sys_utterance': 'Hi! What do you want to know about the vvs?'}

        if sys_act.type == SysActionType.Bad:
            return {'sys_utterance': 'Sorry, I could not understand you.'}
        elif sys_act.type == SysActionType.Bye:
            return {'sys_utterance': 'Thank you, good bye'}
        elif sys_act.type == SysActionType.Request:
            slot = list(sys_act.slot_values.keys())[0]
            if slot == 'station':
                return {'sys_utterance': 'For which station are you looking for?'}
            elif slot == 'line':
                return {'sys_utterance': 'Which line are you looking for?'}
            elif slot == 'from':
                return {'sys_utterance': 'From where do you want to leave?'}
            elif slot == 'to':
                return {'sys_utterance': 'Which is your destination?'}
            else:
                assert False, 'Only the station and the line can be requested'
        else:            
            if sys_act.slot_values["artificial_id"][0] == "none":
                #print("nlgslots:" + str(sys_act.slot_values))
                return {'sys_utterance': "This line does not stop at this station, you need to specify a place, or your request was invalid!"}    

            sentence = ""
            if 'departure' in sys_act.slot_values:
                # limit for maximum of outputs
                limit = min(5, len(sys_act.slot_values['departure']))
                for i in range(limit):
                    dep = sys_act.slot_values['departure'][i]['dep']
                    date = dep.datetime
                    date_str = date.strftime('at %H:%M %p on %B %-d')
                    serving_line = re.sub(r'[\[\]]', '', str(dep.serving_line)).replace(":", " from").replace("-", "to")
                    sentence += f'The {serving_line} leaves {dep.stop_name} {date_str}.\n' 
                            
            elif 'arrival' in sys_act.slot_values:
                limit = min(5, len(sys_act.slot_values['arrival']))
                for i in range(limit):
                    arr = sys_act.slot_values['arrival'][i]['arr']
                    date = arr.datetime
                    date_str = date.strftime('at %H:%M %p on %B %-d')
                    serving_line = re.sub(r'[\[\]]', '', str(arr.serving_line)).replace(":", " from").replace("-", "to")
                    sentence += f'The {serving_line} arrives at {arr.stop_name} {date_str}.\n' 

            elif 'trip' in sys_act.slot_values:
                start = sys_act.slot_values['trip'][0]['from']
                end = sys_act.slot_values['trip'][0]['to']
                duration = sys_act.slot_values['trip'][0]['duration']

                sentence += f'The trip from {start} to {end} takes {duration} minutes.\n'
                sentence += 'Stops: \n'
                for i, step in enumerate(sys_act.slot_values['trip'][0]['steps']):
                    date = step['departure']
                    date_str = date.strftime('at %H:%M %p on %B %-d')
                    start = step['from']
                    end = step['to']
                    line = step['line']
                    sentence += f'{i+1}: From {start} to {end} with line {line} {date_str}.\n'
                
        return {'sys_utterance': sentence}    
