# crop-pdf-margins
Auto-crop blank margins from PDFs while preserving original page size.

# Commands I have executed

`pdm init`
`pdm python install`
`pdm add pymupf`

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



The text_page is better alternative so we built on this.