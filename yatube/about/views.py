from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    """About author."""
    template_name = 'about/about_author_page.html'


class AboutTechView(TemplateView):
    """About using technology."""
    template_name = 'about/about_tech_page.html'
