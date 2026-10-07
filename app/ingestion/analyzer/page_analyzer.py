from pathlib import Path

import pymupdf

from app.ingestion.models import PageAnalysis


class PDFPageAnalyzer:

    def analyze(self, file_path: Path) -> list[PageAnalysis]:
        analyses = []

        document = pymupdf.open(file_path)

        try:
            for page_number, page in enumerate(document, start=1):
                analyses.append(
                    self._analyze_page(
                        page,
                        page_number,
                    )
                )
        finally:
            document.close()

        return analyses

    def _analyze_page(
        self,
        page,
        page_number: int,
    ) -> PageAnalysis:

        text = page.get_text("text").strip()
        text_blocks = page.get_text("blocks")

        images = page.get_images(full=True)
        drawings = page.get_drawings()

        page_rect = page.rect
        page_area = page_rect.width * page_rect.height

        image_area = self._calculate_image_area(
            page,
            images,
        )

        drawing_area = self._calculate_drawing_area(
            drawings,
        )

        image_area_ratio = (
            image_area / page_area
            if page_area
            else 0.0
        )

        drawing_area_ratio = (
            min(drawing_area / page_area, 1.0)
            if page_area
            else 0.0
        )

        has_text = bool(text)
        has_images = bool(images)
        has_vector_graphics = bool(drawings)

        is_visual_heavy = (
            image_area_ratio >= 0.15
            or drawing_area_ratio >= 0.25
            or (
                has_images
                and len(text) < 200
            )
            or (
                has_vector_graphics
                and len(text) < 500
            )
        )

        return PageAnalysis(
            page_number=page_number,
            text_length=len(text),
            text_blocks=len(text_blocks),
            image_count=len(images),
            image_area_ratio=round(
                image_area_ratio,
                4,
            ),
            drawing_count=len(drawings),
            drawing_area_ratio=round(
                drawing_area_ratio,
                4,
            ),
            has_text=has_text,
            has_images=has_images,
            has_vector_graphics=has_vector_graphics,
            is_visual_heavy=is_visual_heavy,
        )

    def _calculate_image_area(
        self,
        page,
        images,
    ) -> float:

        image_area = 0.0

        for image in images:
            try:
                rects = page.get_image_rects(image)

                for rect in rects:
                    image_area += (
                        rect.width * rect.height
                    )

            except Exception:
                continue

        return image_area

    def _calculate_drawing_area(
        self,
        drawings,
    ) -> float:

        rectangles = []

        for drawing in drawings:
            rect = drawing.get("rect")

            if rect is None:
                continue

            if rect.width <= 0 or rect.height <= 0:
                continue

            rectangles.append(
                (
                    rect.x0,
                    rect.y0,
                    rect.x1,
                    rect.y1,
                )
            )

        if not rectangles:
            return 0.0

        return self._calculate_union_area(rectangles)


    def _calculate_union_area(
        self,
        rectangles,
    ) -> float:

        events = []

        for x0, y0, x1, y1 in rectangles:
            events.append((x0, 1, y0, y1))
            events.append((x1, -1, y0, y1))

        events.sort()

        active = []
        previous_x = events[0][0]
        area = 0.0

        for x, event_type, y0, y1 in events:

            width = x - previous_x

            if width > 0 and active:
                y_intervals = sorted(active)

                covered_y = 0.0
                current_start = None
                current_end = None

                for start, end in y_intervals:

                    if current_start is None:
                        current_start = start
                        current_end = end
                        continue

                    if start <= current_end:
                        current_end = max(
                            current_end,
                            end,
                        )
                    else:
                        covered_y += (
                            current_end - current_start
                        )

                        current_start = start
                        current_end = end

                if current_start is not None:
                    covered_y += (
                        current_end - current_start
                    )

                area += width * covered_y

            if event_type == 1:
                active.append((y0, y1))
            else:
                active.remove((y0, y1))

            previous_x = x

        return area