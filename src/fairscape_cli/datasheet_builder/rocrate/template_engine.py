import os
from jinja2 import Environment, FileSystemLoader


class TemplateEngine:
    """Template engine for rendering HTML templates"""
    
    def __init__(self, template_dir=None):
        """Initialize the template engine with a template directory"""
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
        
        os.makedirs(template_dir, exist_ok=True)
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(self, template_name, **context):
        """Render a template with the given context"""
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def render_string(self, template_string, **context):
        """Render a template string with the given context"""
        template = self.env.from_string(template_string)
        return template.render(**context)