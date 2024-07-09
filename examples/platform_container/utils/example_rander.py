from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Setup Jinja2 environment
env = Environment(loader=FileSystemLoader(Path(__file__).parent))

# Load the template
template = env.get_template('package_script.sh.jinja2')

# Example list of packages
packages = ['numpy', 'pandas', 'scipy']

# Render the template with the packages variable
rendered_template = template.render(packages=packages)

# Print or return the rendered template
print(rendered_template)
