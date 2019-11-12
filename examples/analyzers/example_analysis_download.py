from idmtools.analysis.analyze_manager import AnalyzeManager
from idmtools.analysis.download_analyzer import DownloadAnalyzer
from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform

if __name__ == '__main__':

    platform = Platform('COMPS')

    filenames = ['StdOut.txt']
    analyzers = [DownloadAnalyzer(filenames=filenames, output_path='download')]

    experiment_id = '11052582-83da-e911-a2be-f0921c167861'

    manager = AnalyzeManager(configuration={}, platform=platform, ids=[(experiment_id, ItemType.EXPERIMENT)], analyzers=analyzers)
    manager.analyze()
