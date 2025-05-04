# import pymupdf


# def auto_crop_pdf(input_path:str, output_path:str, border_pt=20):

#     doc = pymupdf.open(input_path)
#     for page in doc:
#         # get tight bbox of all text and images
#         # These are rectangles of the page, same as page.rect
#         # Starts with 0, 0 and and goes to the end, not useful
#         rect = page.bound()
#         # expand it by border_pt (on each side)
#         rect = pymupdf.Rect(
#             rect.x0 + border_pt,
#             rect.y0 + border_pt,
#             rect.x1 - border_pt,
#             rect.y1 - border_pt
#         )
#         page.set_cropbox(rect)
#     doc.save(output_path)