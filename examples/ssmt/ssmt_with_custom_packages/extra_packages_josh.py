
import tempfile
from pathlib import Path
from typing import List
from jinja2 import Environment, FileSystemLoader

from examples.ssmt.simple_analysis.analyzers.JoshAnalyzer import JoshAnalyzer
from idmtools.core.platform_factory import Platform
from idmtools.analysis.platform_anaylsis import PlatformAnalysis


def write_wrapper_script(list_of_packages: List[str]):
    env = Environment(loader=FileSystemLoader(Path(__file__).parent))
    template = env.get_template('package_script.sh.jinja2')
    f = tempfile.NamedTemporaryFile(suffix='.sh', mode='wb', delete=False)
    f.write(template.render(dict(packages=list_of_packages)).replace("\r", "").encode('utf-8'))
    f.flush()
    return f.name


if __name__ == "__main__":
    platform = Platform('Calculon')
    analysis = PlatformAnalysis(
        # platform=platform, experiment_ids=["440c1fe5-2229-ef11-aa14-b88303911bc1"],
        # analyzers=[JoshAnalyzer], analyzers_args=[{'filenames': ['output/example.db']}],
        platform=platform, experiment_ids=["5b21cba5-0713-ef11-aa13-b88303911bc1"],
        analyzers=[JoshAnalyzer], analyzers_args=[{'filenames': ['output/SqlReportMalaria.db']}],
        analysis_name="Example to use extra packages",
        wrapper_shell_script=write_wrapper_script(['apsw']),
        # You can pass any additional arguments needed to AnalyzerManager through the extra_args parameter
        extra_args=dict(max_items=1)
    )

    analysis.analyze(check_status=True)
    wi = analysis.get_work_item()
    print(wi)