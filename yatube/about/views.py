from django.views.generic.base import TemplateView


class AboutAuthorView(TemplateView):
    template_name = 'about/about_author_page.html'


class AboutTechView(TemplateView):
    template_name = 'about/about_tech_page.html'
