"""
# New-ContextMenu Helper Script
> Generate a Windows File Explorer Context-Menu Items for Command-Line Tool

Usage:
  python scripts/New-ContextMenu.py -Exe "C:\\Path\\tool.exe"
  python scripts/New-ContextMenu.py -Exe "C:\\Path\\tool.exe" -TemplatesPath "C:\\Path\\templates"
  python scripts/New-ContextMenu.py -Exe "C:\\Path\\tool.exe" -Template "C:\\Path\\templates\\Custom.jinja.reg"

Overview:
  Renders a registry template with named variables and writes the rendered .reg file
  to the current working directory.

Arguments:
  -Exe, --exe: Executable path string injected into the template.
  -TemplatesPath, --templates-path: Directory that contains templates.
  -Template, --template: Full path to a specific template file; overrides template directory/default name.
"""

from argparse import ArgumentParser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


arguments = ArgumentParser()
arguments.add_argument("-Exe", "--exe", required=True)
arguments.add_argument("-TemplatesPath", "--templates-path", default=Path(__file__).resolve().parent)
arguments.add_argument("-Template", "--template")
parsed_arguments = arguments.parse_args()

default_template_name = "Faceless.jinja.reg"
template_path = Path(parsed_arguments.template) if parsed_arguments.template else Path(parsed_arguments.templates_path) / default_template_name
template_directory = template_path.parent
template_name = template_path.name
template_environment = Environment(loader=FileSystemLoader(template_directory))
template_variables = {"faceless_exe_path": parsed_arguments.exe}
rendered_registry = template_environment.get_template(template_name).render(**template_variables)

output_name = "Install-FacelessContextMenu.reg"
output_path = Path.cwd() / output_name
output_path.write_text(rendered_registry, encoding="utf-8")
