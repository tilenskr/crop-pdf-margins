# crop-pdf-margins
Auto-crop blank margins from PDFs while preserving original page size.

# Commands I have executed

`pdm init`
`pdm python install`
`pdm add pymupf`
`pdm add pytesseract`

`Install tesseract OCR on your computer for the ocr detector. See docs for more.`

# what i have tried

pdfcrop is not okay
some internet cropper, which was okay but the problem was i could not set margins from which it cut off the thingy


## Comparison of the current solution (borders set to 0)
The scale method has currently problems of not saving the metadata, so we lose everything: chapters, annotations, ....
|   Bounds      | Cropping  | Summary |
| ------------- | ----------|------------- |
| page_bounds   | box       | No effect.
| page_bounds   | scale     | No effect. 
| text_page     | box       | The problem is pages have different dimensions. Additionally on the first images the text, which is image is cut off. Also back cover is not okay too much space. Images not okay. Empty screen without text need to be fixed.
| text_page     | scale     | Missing images if they are on the top like page 50.
| dict_text     | box       | Has more white on the left and right than text page (first page). Otherwise similar on the text_page.
| dict_text     | scale     | Has more white on the left and right than text page (first page). Otherwise similar on the text_page.
text_page_images| box       | First page has a little more left and second stays the same. There is image on 50 page.
text_page_images| scale     | The similar than text_page_images and text_page scale method.
| ocr           | box       | Works surprisingly well. But the image in page 2 is cut of on the right. This is that, ocr probably did not work flawlessly, because the word is not narrow and it is in arch.
| ocr           | scale     | Works better than box and also images are preserved.
| histogram     | box       | Works the best. But the first page has black border around so it is not ideally trimmed. A github issue was created on this.
| histogram     | scale     | Only the first page is potentially problematic.


The text_page is better alternative so we built on this (for the images).