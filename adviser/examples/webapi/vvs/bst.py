from typing import List
from utils.useract import UserActionType, UserAct

from services.bst import HandcraftedBST

class VVSBST(HandcraftedBST):

    def __init__(self, domain=None, logger=None, mode=False):
        """ super constructor of parent class is called and mode is chosen

        :param mode: Chooses between the two beliefestate modes
        """
        HandcraftedBST.__init__(self, domain=domain, logger=logger)
        self.bs_mode = mode

    def _reset_informs(self, acts: List[UserAct]):
        """
            Depending on mode the informs are reset in different ways:
            Mode=True:  If the user specifies a new value for a given slot, delete the old entry from the beliefstateleave
            Mode=False: If the user specifies a new value for an already filled slot, delete all old entries in the beliefstate
        """
        if self.bs_mode:
            slots = {act.slot for act in acts if act.type == UserActionType.Inform}
            for slot in [s for s in self.bs['informs']]:
                if slot in slots:
                    del self.bs['informs'][slot]

        else:
            reset = False
            slots = {act.slot for act in acts if act.type == UserActionType.Inform}
            for slot in [s for s in self.bs['informs']]:
                if slot in slots:
                    if self.bs['informs'][slot]:
                       reset = True
            if reset:
               for slot in [s for s in self.bs['informs']]:
                    del self.bs['informs'][slot]
        