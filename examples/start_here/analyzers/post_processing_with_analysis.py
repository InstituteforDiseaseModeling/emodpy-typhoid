from idmtools.analysis.analyze_manager import AnalyzeManager
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from population_analyzer import PopulationAnalyzer




def post_processing_with_analysis(experiment_id):
    platform = Platform("Calculon")

    filenames = ['output/population.json']
    # Initialize the analyser class with the path of the output files to download
    analyzers = [PopulationAnalyzer(filenames=filenames, output_path='../output')]
    # Specify the id Type, in this case an Experiment
    manager = AnalyzeManager(platform, ids=[(experiment_id, ItemType.EXPERIMENT)],
                             analyzers=analyzers, max_workers=1)
    manager.analyze()

if __name__ == '__main__':
    experiment_id = '0352f566955ef011aa23b88303911bc1'
    post_processing_with_analysis(experiment_id)