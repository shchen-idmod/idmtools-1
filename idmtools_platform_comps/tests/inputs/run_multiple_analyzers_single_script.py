"""
This script is to create AnalyzerManager and do analyzer.
If you want to run it locally, just run as "python run_analysis.py expid"
If you want to run it from ssmt, you will call this file from run_ssmt_analysis.py as example
"""
import os
import sys

from idmtools.core import ItemType
from idmtools.core.platform_factory import Platform
from idmtools.analysis.analyze_manager import AnalyzeManager

sys.path.append(os.path.dirname(__file__))
from custom_csv_analyzer import NodeCSVAnalyzer  # noqa
from custom_csv_analyzer import InfectiousnessCSVAnalyzer  # noqa

if __name__ == "__main__":
    platform = Platform('COMPS2')
    filenames = ['output/individual.csv']
    filenames_2 = ['output/node.csv']
    analyzers = [InfectiousnessCSVAnalyzer(filenames=filenames), NodeCSVAnalyzer(filenames=filenames_2)]

    if len(sys.argv) > 1:
        expid = [(sys.argv[1], ItemType.EXPERIMENT)]
    else:
        expid = [('a980f265-995e-ea11-a2bf-f0921c167862', ItemType.EXPERIMENT)]
    am = AnalyzeManager(ids=expid, analyzers=analyzers)
    am.analyze()
