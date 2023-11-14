from emod_api import schema_to_class as s2c
from emod_api.interventions import utils
from emod_api.interventions import common
import json

def _get_waning( constant_period=0, decay_constant=0, expected_expiration=0 ):
    Changing_Effect = None # for scope
    if decay_constant>0:
        Changing_Effect = s2c.get_class_with_defaults( "WaningEffectBoxExponential" )
        Changing_Effect.Box_Duration = constant_period
        Changing_Effect.Decay_Time_Constant = decay_constant
    else:
        Changing_Effect = s2c.get_class_with_defaults( "WaningEffectRandomBox" )
        Changing_Effect.Expected_Discard_Time = expected_expiration 
    return Changing_Effect 

def new_intervention( camp, efficacy=0.82, mode="Shedding", constant_period=0, decay_constant=0, expected_expiration=0 ):
    """
     Create a new TyphoidVaccine intervention with specified parameters. If you use this function directly, you'll need to distribute the intervention with a function like ScheduledCampaignEvent or TriggeredCampaignEvent from emod_api.interventions.common.

     Args:
         camp (Camp): The camp to which the intervention is applied.
         efficacy (float, optional): The efficacy of the Typhoid vaccine. Default is 0.82.
         mode (str, optional): The mode of the intervention. Default is "Shedding".
         constant_period (float, optional): The constant period of the waning effect in days. Default is 0.
         decay_constant (float, optional): The decay time constant for the waning effect. Default is 6935.0.
         expected_expiration (float, optional): The mean duration before efficacy becomes 0. If this is set to non-zero value, the constant_period and decay_constant are ignored. These are two different modes of waning.

     Returns:
         TyphoidVaccine: A fully configured instance of the TyphoidVaccine intervention with the specified parameters.
     """

    intervention = s2c.get_class_with_defaults( "TyphoidVaccine", camp.schema_path )
    intervention.Effect = efficacy
    intervention.Mode = mode
    intervention.Changing_Effect = _get_waning( constant_period=constant_period, decay_constant=decay_constant, expected_expiration=expected_expiration ) 
    intervention.Changing_Effect.Initial_Effect = efficacy

    return intervention

def new_vax( camp, efficacy=0.82, mode="Acquisition", constant_period=0, decay_constant=0, expected_expiration=0, deduplication_policy="replace" ):
    """
     Create a new 'SimpleVaccine' intervention with specified parameters. If you use this function directly, you'll need to distribute the intervention with a function like ScheduledCampaignEvent or TriggeredCampaignEvent from emod_api.interventions.common.

     Args:
         camp (Camp): The camp to which the intervention is applied.
         efficacy (float, optional): The efficacy of the Typhoid vaccine. Default is 0.82.
         mode (str, optional): The mode of the intervention. Default is "Acquisition" Can also be "Transmission" or "All".
         constant_period (float, optional): The constant period of the waning effect in days. Default is 0.
         decay_constant (float, optional): The decay time constant for the waning effect. Default is 6935.0.
         expected_expiration (float, optional): The mean duration before efficacy becomes 0. If this is set to non-zero value, the constant_period and decay_constant are ignored. These are two different modes of waning.
         deduplication_policy (string,optional): "replace" (default) or "combine". If giving vax to someone who already has one, based on Intervention_Name which defaults to intervention classname ("SimpleVaccine"), "replace" will purge the existing one, and "combine" will add the new one without replacement, and rely on code and configuration to calculate the combinatorix. If using "combine", make sure you _know_ the combinatorix.

     Returns:
         SimpleVaccine: A fully configured instance of the SimpleVaccine intervention with the specified parameters.
     """

    intervention = s2c.get_class_with_defaults( "SimpleVaccine", camp.schema_path )
    if mode == "Acquisition":
        intervention.Vaccine_Type = "AcquisitionBlocking"
    elif mode == "Transmission":
        intervention.Vaccine_Type = "TransmissionBlocking"
    elif mode == "All":
        intervention.Vaccine_Type = "General"
    else:
        raise ValueError( f"mode {mode} not recognized. Options are: 'Acquisition', 'Transmission', or 'All'." )

    # combine: DAD=0
    # replace: DAD=1, EIR=1
    # abort: DAD=1, EIR=0  -- not supported
    if deduplication_policy == "replace":
        intervention.Enable_Intervention_Replacement = 1 # D_A_D should be set implicitly
    elif deduplication_policy == "combine":
        intervention.Dont_Allow_Duplicates = 0
    else:
        raise ValueError( f"deduplication_policy needs to be 'replace' or 'combine', not '{deduplication_policy}'." )

    intervention.Waning_Config = _get_waning( constant_period=constant_period, decay_constant=decay_constant, expected_expiration=expected_expiration ) 
    intervention.Waning_Config.Initial_Effect = efficacy
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
         co_event (None, optional): The name of the event to be broadcast. This event name can be set in the Report_Event_Recorder_Events configuration parameter. It will be collected in ReportEventRecorder.csv with default event "VaccineDistributed".

     Returns:
         TriggeredCampaignEvent: An instance of a triggered campaign event with the TyphoidVaccine intervention.
    """
    iv = new_intervention( camp, efficacy=efficacy, mode=mode, constant_period=constant_period, decay_constant=decay_constant )
    if co_event:
        signal = common.BroadcastEvent(camp, co_event)
        iv = [iv, signal]
    else:
        iv = [iv]
    event = common.TriggeredCampaignEvent( camp, Start_Day=start_day, Triggers=triggers, Demographic_Coverage=coverage, Intervention_List=iv, Node_Ids=node_ids, Property_Restrictions=property_restrictions_list, Event_Name="Triggered Typhoid Vax" )

    return event

def new_routine_immunization( 
        camp, 
        efficacy=0.82,
        mode="Acquisition",
        constant_period=0,
        decay_constant=0,
        expected_expiration=0,
        start_day=1, 
        child_age=9*30,
        coverage=1.0, 
        node_ids=None,
        property_restrictions_list=[],
        co_event="VaccineDistributed" # expansion slot
    ):
    """
    Create a new delayed, birth-triggered SimpleVaccine intervention based on specified parameters. Does not add to campaign.

    Args:
         camp (Camp): The camp to which the intervention is applied.
         efficacy (float, optional): The efficacy of the Typhoid vaccine. Default is 0.82.
         mode (str, optional): The mode of the intervention. Default is "Shedding".
         constant_period (float, optional): The constant period of the waning effect in days. Default is 0.
         decay_constant (float, optional): The decay time constant for the waning effect. Default is 6935.0.
         expected_expiration (float, optional): The mean duration before efficacy becomes 0. If this is set to non-zero value, the constant_period and decay_constant are ignored. These are two different modes of waning.
         start_day (int, optional): The day on which the intervention starts. Default is 1.
         child_age (int, optional): The age of the person when they get the vaccine. Defaults to 9 months. Vaccines are actually distribute +/- 7 days.
         coverage (float, optional): Demographic coverage of the intervention. Default is 1.0.
         node_ids (list, optional): List of node IDs where the intervention is applied. Default is None.
         property_restrictions_list (list, optional): List of property restrictions for the intervention. Default is an empty list.
         co_event (str, optional): The name of the event to be broadcast. This event name can be set in the Report_Event_Recorder_Events configuration parameter. It will be collected in ReportEventRecorder.csv with default event "VaccineDistributed" if not set with other name.

     Returns:
         TriggeredCampaignEvent: An instance of a triggered campaign event with the TyphoidVaccine intervention.
    """
    iv = new_vax( camp, efficacy=efficacy, mode=mode, constant_period=constant_period, decay_constant=decay_constant, expected_expiration=expected_expiration )
    if co_event:
        signal = common.BroadcastEvent( camp, co_event )
        iv = [ iv, signal ]
    else:
        iv = [ iv ]
    age_min = max(0,child_age-7)
    delay = {
            "Delay_Period_Min": age_min,
            "Delay_Period_Max": child_age+7
            }

    #event = common.triggered_campaign_delay_event( camp, start_day=start_day, trigger="Births", delay=delay, intervention=iv, ip_targeting=property_restrictions_list, coverage=coverage )
    delay_iv = common.DelayedIntervention( camp, Configs=iv, Delay_Dict = delay )

    event = common.TriggeredCampaignEvent( camp, Start_Day=start_day, Event_Name="triggered_delayed_intervention", Triggers=[ "Births"], Intervention_List=[delay_iv], Property_Restrictions=property_restrictions_list, Demographic_Coverage=coverage )


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
         co_event (None, optional): The name of the event to be broadcast. This event name can be set in the Report_Event_Recorder_Events configuration parameter. It will be collected in ReportEventRecorder.csv if set not None or "".

     Returns:
         ScheduledCampaignEvent: An instance of a scheduled campaign event with the TyphoidVaccine intervention.
    
    """
    iv = new_intervention( camp, efficacy=efficacy, mode=mode, constant_period=constant_period, decay_constant=decay_constant )
    if co_event:
        signal = common.BroadcastEvent(camp, co_event)
        iv = [iv, signal]
    else:
        iv = [iv]
    event = common.ScheduledCampaignEvent( camp, Start_Day=start_day, Demographic_Coverage=coverage, Intervention_List=iv, Node_Ids=node_ids, Property_Restrictions=property_restrictions_list )
    return event

def new_intervention_as_file( camp, start_day, filename=None ):
    import emod_api.campaign as camp
    camp.add( new_triggered_intervention( camp, start_day=start_day ), first=True )
    if filename is None:
        filename = "TyphoidVaccine.json"
    camp.save( filename )
    return filename
