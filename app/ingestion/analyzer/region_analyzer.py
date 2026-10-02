from uuid import uuid4

import pymupdf

from app.ingestion.models import VisualRegion


class PDFRegionAnalyzer:

    def analyze_page(
        self,
        page,
    ) -> list[VisualRegion]:

        regions = []

        regions.extend(
            self._extract_image_regions(page)
        )

        regions.extend(
            self._extract_drawing_regions(page)
        )

        return self._merge_regions(
            regions
        )

    def _extract_image_regions(
        self,
        page,
    ) -> list[VisualRegion]:

        regions = []

        page_area = (
            page.rect.width
            * page.rect.height
        )

        images = page.get_images(
            full=True
        )

        for image in images:

            try:
                rects = page.get_image_rects(
                    image
                )
            except Exception:
                continue

            for rect in rects:

                if rect.width <= 0 or rect.height <= 0:
                    continue

                area = (
                    rect.width
                    * rect.height
                )

                regions.append(
                    VisualRegion(
                        region_id=str(uuid4()),
                        page_number=page.number + 1,
                        bbox=self._bbox(rect),
                        region_type="unknown",
                        source="image",
                        area_ratio=(
                            area / page_area
                            if page_area
                            else 0.0
                        ),
                    )
                )

        return regions

    def _extract_drawing_regions(
        self,
        page,
    ) -> list[VisualRegion]:

        regions = []

        drawings = page.get_drawings()

        for drawing in drawings:

            rect = drawing.get("rect")

            if rect is None:
                continue

            if rect.width <= 0 or rect.height <= 0:
                continue

            page_area = (
                page.rect.width
                * page.rect.height
            )

            area = (
                rect.width
                * rect.height
            )

            regions.append(
                VisualRegion(
                    region_id=str(uuid4()),
                    page_number=page.number + 1,
                    bbox=self._bbox(rect),
                    region_type="unknown",
                    source="vector",
                    area_ratio=(
                        area / page_area
                        if page_area
                        else 0.0
                    ),
                )
            )

        return regions

    def _merge_regions(
        self,
        regions: list[VisualRegion],
    ) -> list[VisualRegion]:

        if not regions:
            return []

        regions = sorted(
            regions,
            key=lambda region: (
                region.bbox["top"],
                region.bbox["left"],
            ),
        )

        merged = []

        for region in regions:

            merged_into_existing = False

            for existing in merged:

                if self._overlaps(
                    existing,
                    region,
                ):

                    existing.bbox = self._union_bbox(
                        existing.bbox,
                        region.bbox,
                    )

                    existing.area_ratio = max(
                        existing.area_ratio,
                        region.area_ratio,
                    )

                    if (
                        existing.source
                        != region.source
                    ):
                        existing.source = "mixed"

                    merged_into_existing = True
                    break

            if not merged_into_existing:
                merged.append(region)

        return merged

    @staticmethod
    def _overlaps(
        first: VisualRegion,
        second: VisualRegion,
    ) -> bool:

        a = first.bbox
        b = second.bbox

        return not (
            a["right"] <= b["left"]
            or b["right"] <= a["left"]
            or a["bottom"] <= b["top"]
            or b["bottom"] <= a["top"]
        )

    @staticmethod
    def _union_bbox(
        first: dict[str, float],
        second: dict[str, float],
    ) -> dict[str, float]:

        return {
            "left": min(
                first["left"],
                second["left"],
            ),
            "top": min(
                first["top"],
                second["top"],
            ),
            "right": max(
                first["right"],
                second["right"],
            ),
            "bottom": max(
                first["bottom"],
                second["bottom"],
            ),
        }

    @staticmethod
    def _bbox(
        rect,
    ) -> dict[str, float]:

        return {
            "left": rect.x0,
            "top": rect.y0,
            "right": rect.x1,
            "bottom": rect.y1,
        }