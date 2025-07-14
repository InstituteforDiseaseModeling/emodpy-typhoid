from idmtools.analysis.platform_anaylsis import PlatformAnalysis
from idmtools.core import ItemType

from population_analyzer import PopulationAnalyzer
from idmtools.core.platform_factory import Platform


def _post_run(analysis, param):
    pass


def ssmt_analysis(experiment_id):
    platform = Platform("Calculon")

    filenames = ['output/population.json']
    # Initialize the analyser class with the path of the output files to download
    # Specify the id Type, in this case an Experiment
    analysis = PlatformAnalysis(platform=platform, experiment_ids=[experiment_id],
                                analyzers=[PopulationAnalyzer],
                                analyzers_args=[{'filenames': filenames}],
                                analysis_name='test platformanalysis with experiment',
                                tags={'idmtools': 'test_ssmt'},
                                extra_args={"max_workers": 8})

    analysis.analyze(check_status=True)
    wi = analysis.get_work_item()
    # verify workitem result
    local_output_path = "output_ssmt"
    out_filenames = [f"output/{experiment_id}/total_population.csv", f"output/{experiment_id}/total_population.json", "population_vs_time_by_run.png"]
    platform.get_files_by_id(wi.id, ItemType.WORKFLOW_ITEM, out_filenames, local_output_path)

if __name__ == '__main__':
    experiment_id = '0352f566-955e-f011-aa23-b88303911bc1'
    ssmt_analysis(experiment_id)
