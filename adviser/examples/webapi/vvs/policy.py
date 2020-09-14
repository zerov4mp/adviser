from services.policy.policy_api import HandcraftedPolicy

from utils.domain.lookupdomain import LookupDomain
from utils import SysAct, SysActionType
from utils.logger import DiasysLogger
from utils.beliefstate import BeliefState

class VVSPolicy(HandcraftedPolicy):

    def __init__(self, domain: LookupDomain, logger: DiasysLogger = DiasysLogger()):
        # only call super class' constructor
        HandcraftedPolicy.__init__(self, domain=domain, logger=logger)

    def _mandatory_requests_fulfilled(self, belief_state: BeliefState):
        """ whether or not all mandatory slots have a value
            the method was altered to accept a list of lists for mandatory slots

        Arguments:
            beliefstate (BeliefState): dictionary tracking the current system beliefs
        """
        filled_slots, _ = self._get_constraints(belief_state)
        mandatory_slots_list  = self.domain.get_mandatory_slots()
        for mandatory_slots in mandatory_slots_list:
            fulfilled = True
            for slot in mandatory_slots:
                if slot not in filled_slots:
                    fulfilled = False
            if fulfilled:
                return True
        return False

    def _get_open_mandatory_slot(self, belief_state: BeliefState):
        """
            the method was altered to accept a list of lists for mandatory slots
        Args:
            belief_state (dict): dictionary tracking the current system beliefs

        Returns:
            (str): a string representing a category the system might want more info on. If all
            system requestables have been filled, return none

        """
        filled_slots, _ = self._get_constraints(belief_state)
        mandatory_slots_list = self.domain.get_mandatory_slots()
        for mandatory_slots in mandatory_slots_list:
            for filled in filled_slots:
                if filled in mandatory_slots:
                    for slot in mandatory_slots:
                        if slot not in filled_slots:
                            return slot
        return None


    def _query_db(self, beliefstate: BeliefState):
        """Based on the constraints specified, uses self.domain to generate each time a query for the database

        Returns:
            iterable: representing the results of the database lookup

        --LV
        """
        
        # issue a query to find all entities which satisfy the constraints the user has given so far
        # We also provide the slots requested from the user for the query
        constraints, _ = self._get_constraints(beliefstate)
        requested = [slot for slot in beliefstate['requests']]

        return self.domain.find_entities(constraints, requested)



    def _convert_inform_by_constraints(self, q_results: iter,
                                       sys_act: SysAct, belief_state: BeliefState):
        """
            Helper function for filling in slots and values of a raw inform act when the system is
            ready to make the user an offer

            Args:
                q_results (iter): the results from the databse query
                sys_act (SysAct): the raw infor act to be filled in
                belief_state (BeliefState): the current system beliefs

        """
        # altered to add all results to the SysAct
        if list(q_results):
            self.current_suggestions = []
            self.s_index = 0
            for result in q_results:
                sys_act.add_value(self.domain_key, result[self.domain_key])

        else:
            sys_act.add_value(self.domain_key, 'none')

        sys_act.type = SysActionType.InformByName
        constraints, dontcare = self._get_constraints(belief_state)
        for c in constraints:
            # Using constraints here rather than results to deal with empty
            # results sets (eg. user requests something impossible) --LV
            sys_act.add_value(c, constraints[c])

        # altered to the changes above
        if list(q_results):
            for slot in belief_state['requests']:
                if slot not in sys_act.slot_values:
                    for result in q_results:
                        sys_act.add_value(slot, result[slot])