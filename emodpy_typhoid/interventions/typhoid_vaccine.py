from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emod_api.interventions import common
import json

def new_intervention( camp, efficacy=0.82, mode="Shedding", constant_period=0, decay_constant=6935.0 ):
    """
     Create a new TyphoidVaccine intervention with specified parameters. If you use this function directly, you'll need to distribute the intervention with a function like ScheduledCampaignEvent or TriggeredCampaignEvent from emod_api.interventions.common.

     Args:
         camp (Camp): The camp to which the intervention is applied.
         efficacy (float, optional): The efficacy of the Typhoid vaccine. Default is 0.82.
         mode (str, optional): The mode of the intervention. Default is "Shedding".
         constant_period (float, optional): The constant period of the waning effect in days. Default is 0.
         decay_constant (float, optional): The decay time constant for the waning effect. Default is 6935.0.

     Returns:
         TyphoidVaccine: A fully configured instance of the TyphoidVaccine intervention with the specified parameters.
     """

    intervention = s2c.get_class_with_defaults( "TyphoidVaccine", camp.schema_path )
    intervention.Effect = efficacy
    intervention.Mode = mode
    intervention.Changing_Effect = s2c.get_class_with_defaults( "WaningEffectBoxExponential" )
    intervention.Changing_Effect.Initial_Effect = efficacy
    intervention.Changing_Effect.Box_Duration = constant_period
    intervention.Changing_Effect.Decay_Time_Constant = decay_constant
    return intervention

def new_triggered_intervention( 
        camp, 
        efficacy=0.82,
        mode="Shedding",
        constant_period=0,
        decay_constant=6935.0,
        start_day=1, 
        triggers=[ "Births" ],
        coverage=1.0, 
        node_ids=None,
        property_restrictions_list=[],
        co_event=None # expansion slot
    ):
    """
    Create a new triggered TyphoidVaccine intervention based on specified parameters.

    Args:
         camp (Camp): The camp to which the intervention is applied.
         efficacy (float, optional): The efficacy of the Typhoid vaccine. Default is 0.82.
         mode (str, optional): The mode of the intervention. Default is "Shedding".
         constant_period (float, optional): The constant period of the waning effect in days. Default is 0.
         decay_constant (float, optional): The decay time constant for the waning effect. Default is 6935.0.
         start_day (int, optional): The day on which the intervention starts. Default is 1.
         triggers (list, optional): List of triggers for the intervention. Default is ["Births"].
         coverage (float, optional): Demographic coverage of the intervention. Default is 1.0.
         node_ids (list, optional): List of node IDs where the intervention is applied. Default is None.
         property_restrictions_list (list, optional): List of property restrictions for the intervention. Default is an empty list.
         co_event (None, optional): Expansion slot for future use.

     Returns:
         TriggeredCampaignEvent: An instance of a triggered campaign event with the TyphoidVaccine intervention.
    """
    iv = new_intervention( camp, efficacy=efficacy, mode=mode, constant_period=constant_period, decay_constant=decay_constant )

    event = common.TriggeredCampaignEvent( camp, Start_Day=start_day, Triggers=triggers, Demographic_Coverage=coverage, Intervention_List=[ iv ], Node_Ids=node_ids, Property_Restrictions=property_restrictions_list, Event_Name="Triggered Typhoid Vax" )

    return event

def new_scheduled_intervention( 
        camp, 
        efficacy=0.82,
        mode="Shedding",
        constant_period=0,
        decay_constant=6935.0,
        start_day=1, 
        coverage=1.0, 
        node_ids=None,
        property_restrictions_list=[],
        co_event=None # expansion slot
    ):
    """
    Create a new scheduled TyphoidVaccine intervention based on specified parameters.

    Args:
         camp (Camp): The camp to which the intervention is applied.
         efficacy (float, optional): The efficacy of the Typhoid vaccine. Default is 0.82.
         mode (str, optional): The mode of the intervention. Default is "Shedding".
         constant_period (float, optional): The constant period of the waning effect in days. Default is 0.
         decay_constant (float, optional): The decay time constant for the waning effect. Default is 6935.0.
         start_day (int, optional): The day on which the intervention starts. Default is 1.
         coverage (float, optional): Demographic coverage of the intervention. Default is 1.0.
         node_ids (list, optional): List of node IDs where the intervention is applied. Default is None.
         property_restrictions_list (list, optional): List of property restrictions for the intervention. Default is an empty list.
         co_event (None, optional): Expansion slot for future use.

     Returns:
         ScheduledCampaignEvent: An instance of a scheduled campaign event with the TyphoidVaccine intervention.
    
    """
    iv = new_intervention( camp, efficacy=efficacy, mode=mode, constant_period=constant_period, decay_constant=decay_constant )

    #event = common.ScheduledCampaignEvent( camp, Start_Day=start_day, Demographic_Coverage=coverage, Intervention_List=[ act_intervention, bcast_intervention ], Node_Ids=nodeIDs, Property_Restrictions=property_restrictions_list )
    event = common.ScheduledCampaignEvent( camp, Start_Day=start_day, Demographic_Coverage=coverage, Intervention_List=[ iv ], Node_Ids=node_ids, Property_Restrictions=property_restrictions_list )

    return event

def new_intervention_as_file( camp, start_day, filename=None ):
    import emod_api.campaign as camp
    camp.add( new_triggered_intervention( camp, start_day=start_day ), first=True )
    if filename is None:
        filename = "TyphoidVaccine.json"
    camp.save( filename )
    return filename
