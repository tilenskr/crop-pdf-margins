import pymupdf


class CoordinateTransformer:
    def __init__(self, source_rect: pymupdf.Rect, destination_rect: pymupdf.Rect) -> None:
        self._source_rect = source_rect
        self._destination_rect = destination_rect
        if (
            source_rect.width <= 0
            or source_rect.height <= 0
            or destination_rect.width <= 0
            or destination_rect.height <= 0
        ):
            self._scale_x = 0.0
            self._scale_y = 0.0
            self._dx = destination_rect.x0
            self._dy = destination_rect.y0
            return

        self._scale_x = destination_rect.width / source_rect.width
        self._scale_y = destination_rect.height / source_rect.height

        # MuPDF scales uniformly with the *smaller* factor
        s = min(self._scale_x, self._scale_y)
        self._scale_x = self._scale_y = s
        # centred letter-box margins
        self._dx = destination_rect.x0 + (
            destination_rect.width - source_rect.width * s
        ) / 2
        self._dy = destination_rect.y0 + (
            destination_rect.height - source_rect.height * s
        ) / 2

    # -----------------------------------------------------------------
    # public helpers ---------------------------------------------------
    # -----------------------------------------------------------------
    def transform_point(self, x: float, y: float) -> tuple[float, float]:
        """
        Map (x, y) from the *source* coordinate space into the destination.
        """
        return (
            self._dx + (x - self._source_rect.x0) * self._scale_x,
            self._dy + (y - self._source_rect.y0) * self._scale_y,
        )

    def transform_rect(self, rect: pymupdf.Rect) -> pymupdf.Rect:
        p0 = self.transform_point(rect.x0, rect.y0)
        p1 = self.transform_point(rect.x1, rect.y1)
        return pymupdf.Rect(p0, p1)

    def transform_vertices(self, vertices):
        if vertices is None:
            return None
        if not vertices:
            return []

        # list of Quads (text markup: highlight/underline/strikeout/squiggly)
        if isinstance(vertices[0], pymupdf.Quad):
            out = []
            for q in vertices:
                ul = self.transform_point(q.ul.x, q.ul.y)
                ur = self.transform_point(q.ur.x, q.ur.y)
                ll = self.transform_point(q.ll.x, q.ll.y)
                lr = self.transform_point(q.lr.x, q.lr.y)
                out.append(pymupdf.Quad([ul, ur, ll, lr]))
            return out

        # nested strokes (ink): [ [(x,y),...], [(x,y),...], ... ]
        if isinstance(vertices[0], (list, tuple)) and vertices and isinstance(vertices[0][0], (list, tuple)):
            return [self.transform_vertices(stroke) for stroke in vertices]

        # list of points: [(x,y), (x,y), ...]
        return [self.transform_point(float(x), float(y)) for (x, y) in vertices]
