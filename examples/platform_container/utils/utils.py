import tempfile
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader


def write_wrapper_script(packages: List[str]):
    env = Environment(loader=FileSystemLoader(Path(__file__).parent))
    template = env.get_template('package_script.sh.jinja2')
    f = tempfile.NamedTemporaryFile(suffix='.sh', mode='wb', delete=False)
    f.write(template.render(dict(packages=packages)).replace("\r", "").encode('utf-8'))
    f.flush()
    return f.name


def get_wrapper_script_as_string(packages: List[str]):
    env = Environment(loader=FileSystemLoader(Path(__file__).parent))
    # Load the template
    template = env.get_template('package_script.sh.jinja2')
    rendered_template = template.render(packages=packages)
    return rendered_template