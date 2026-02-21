import logging
from collections.abc import Sequence
from typing import Any, Optional

import pymupdf

from .coordinate_transformer import CoordinateTransformer
from .internal_destinations import Converted, Invalid, InternalDestinationResolver


def copy_links(
    src: pymupdf.Document, page_bounds: Sequence[pymupdf.Rect], dst: pymupdf.Document
) -> None:
    """
    Preserve links for the ScaleCropper method:
    - transforms link hot areas ("from") from src coords -> dst coords
    - transforms internal goto destinations ("to") using the destination page's bounds
    """
    resolver = InternalDestinationResolver(dst.page_count)
    for page_num in range(dst.page_count):
        src_page = src[page_num]
        dst_page = dst[page_num]

        dst_width = dst_page.rect.width
        dst_height = dst_page.rect.height
        page_bound = page_bounds[page_num]

        coordinate_transformer = CoordinateTransformer(
            page_bound, dst_width, dst_height
        )
        for link in src_page.get_links():
            transformed_link = transform_link_destination(
                link, dst, page_bounds, page_num, resolver
            )
            if transformed_link is None:

                continue

            new_from = coordinate_transformer.transform_rect(transformed_link["from"])

            if new_from.is_empty:
                continue

            transformed_link["from"] = new_from
            dst_page.insert_link(transformed_link)


def transform_link_destination(
    link: dict[str, Any],
    dst_doc: pymupdf.Document,
    page_bounds: Sequence[pymupdf.Rect],
    page_num: int,
    resolver: InternalDestinationResolver,
) -> Optional[dict[str, Any]]:
    """
    Transforms a link destination (LINK_GOTO or LINK_NAMED resolved to GOTO).
    Returns a new dict with transformed 'to' point, or None if invalid.
    """
    link_kind = link.get("kind")
    converted_result = resolver.resolve(link)

    if isinstance(converted_result, Invalid):
        logging.warning(
            "Cannot convert LINK_NAMED to LINK GO TO " "Page: %r, link dict: %r",
            page_num,
            link,
        )
        return None
    elif isinstance(converted_result, Converted):
        link = converted_result.link
        link_kind = pymupdf.LINK_GOTO

    if link_kind != pymupdf.LINK_GOTO:
        return dict(link)

    new_link = dict(link)
    link_dest_page = new_link.get("page", -1)
    link_dest_to = new_link.get("to")

    if not isinstance(link_dest_page, int):
        logging.warning(
            "Invalid LINK_GOTO destination. "
            "Expected page:int, got page=%r (%s). "
            "Full link dict: %r",
            link_dest_page,
            type(link_dest_page).__name__,
            new_link,
        )
        return None

    if isinstance(link_dest_to, pymupdf.Point):
        link_dest_to_width = dst_doc[link_dest_page].rect.width
        link_dest_to_height = dst_doc[link_dest_page].rect.height
        link_dest_page_bound = page_bounds[link_dest_page]
        link_coord_transformer = CoordinateTransformer(
            link_dest_page_bound, link_dest_to_width, link_dest_to_height
        )
        transformed_to_point = link_coord_transformer.transform_point(
            link_dest_to.x, link_dest_to.y
        )

        new_link["to"] = pymupdf.Point(transformed_to_point[0], transformed_to_point[1])

    return new_link
