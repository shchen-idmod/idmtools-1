import os
import sys

from idmtools.assets.file_list import FileList
from idmtools.core.platform_factory import Platform
from idmtools_platform_comps.ssmt_work_items.comps_workitems import SSMTWorkItem

# run command in comps's workitem
command = "python Assets/analyzer_file.py"
# load everything including analyzers from local 'analyzers' dir to comps's Assets dir in workitem
asset_files = FileList(root='analyzers')

if __name__ == "__main__":
    platform = Platform('BELEGOST')
    wi = SSMTWorkItem(item_name=os.path.split(sys.argv[0])[1], command=command, asset_files=asset_files)

    wi.run(True, platform=platform)

