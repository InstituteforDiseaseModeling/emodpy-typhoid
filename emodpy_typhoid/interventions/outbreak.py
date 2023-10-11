from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emod_api.interventions import common
import json

def add_outbreak_individual(start_day: int = 1,
                            demographic_coverage: float = 1.0,
                            node_ids: list = None,
                            repetitions: int = 1,
                            timesteps_between_repetitions: int = 365,
                            ind_property_restrictions: list = None):
    import emod_api.campaign as campaign
    import emod_api.interventions.outbreak as ob
    from emod_api.interventions.common import ScheduledCampaignEvent

    outbreak = ob.seed_by_coverage(
        timestep=start_day,
        campaign_builder=campaign,
        coverage=demographic_coverage,
        intervention_only=True
    )

    outbreak_event = ScheduledCampaignEvent(camp=campaign,
                                            Start_Day=start_day,
                                            Node_Ids=node_ids,
                                            Number_Repetitions=repetitions,
                                            Timesteps_Between_Repetitions=timesteps_between_repetitions,
                                            Property_Restrictions=ind_property_restrictions,
                                            Intervention_List=[outbreak],
                                            Demographic_Coverage=demographic_coverage)
    return outbreak_event