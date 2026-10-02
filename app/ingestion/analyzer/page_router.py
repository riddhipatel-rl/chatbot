from app.ingestion.models import PageAnalysis


class PageRouter:

    def route(self, page: PageAnalysis) -> str:

        if page.is_visual_heavy:
            return "vision"

        return "native"