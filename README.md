# crop-pdf-margins
Auto-crop blank margins from PDFs to improve readability using flexible cropping strategies.

## Motivation
Studies have shown that reading books, especially before sleep, helps improve attention and focus. 
Nowadays, tablets are widely used for reading, and besides EPUB, PDF is one of the most common formats. 
However, many PDFs contain large side margins, which reduce the effective text size on tablets, making reading less comfortable.

This application automatically removes unnecessary margins to better scale the text for tablet screens, 
providing a more pleasant reading experience. Users can also manually adjust the margins to ensure the text isn’t too tight.

## Project Installation
This project uses the [PDM](https://pdm-project.org/) package management tool. To set it up:

1. Install PDM by following the instructions on their website.
2. Install project dependencies by running the following command in the root directory:
```bash
    pdm init
```

### Dependencies
The project requires:
- [**PyMuPDF**](https://pymupdf.readthedocs.io/) – for manipulating a PDF document.
- [**pytesseract**](https://pypi.org/project/pytesseract/) – for recognizing the characters (OCR) in the PDF document. Use only by the [OCRBoundsExtractor](src/crop/box_cropper.py). You have to install the Google Tesseract OCR by following the guide on the aforementioned webpage.

## Usage
The program can be executed using Pixi with the following command:
```bash
    pdm run python src/main.py
```
You will get the output of the needed command line arguments.

Alternatively, you can use the predefined task `convert`, which includes example arguments and demonstrates how to call the program. You will have to just change the `<pdf-path>`:
```bash
    pdm run convert
```
### Command-Line Usage
For more control, you can run the program with specific options:
```bash
usage: main.py -i INPUT -d OUTPUT_DIR -be {page_bounds,text_page,dict_text,text_page_images,dict_text_images,ocr,histogram} -c {box,scale} [-n NAME] [-b BORDER [BORDER ...]]
```

### Command-Line Parameters
#### Parameters
- **`-i INPUT`**: Path to the input PDF file (required).
- **`-d OUTPUT_DIR`**: Directory where the cropped PDF will be saved to. (required).
- **`-n NAME`**: Optional output filename (without extension). Defaults to the input basename.
- **`-be BOUNDS-EXTRACTOR`**: Which heuristic to use for extracting the bounds. Defaults to `histogram`.
  - `page_bounds`: Extracts each page’s visible content bounds without analyzing content.
  - `text_page`: Extracts bounds by combining all text blocks from the textpage object.
  - `dict_text`: Extracts bounds using text blocks from the raw dictionary text layout.
  - `text_page_images`: Extends `text_page` extractor by including image positions on the page.
  - `dict_text_images`: Extends `dict_text` extractor by including image positions on the page.
  - `ocr`: Performs OCR on each page image to detect and bound visible text content..
  - `histogram`: Analyzes pixel color distribution to find content area by trimming dominant background.
- **`-b BORDER`**: Padding in pixels (e.g., 10.5) or percent (e.g., 5.3%). One or four values like CSS.
- **`-c CROPPER`**: Cropping strategy used to trim page content. Defaults to `scale`.
  - `box`: Crops each page by adjusting visible bounds without scaling or redrawing content.
  - `scale`: Crops each page to given bounds and scales content to full-page size.
- **`-h`**: Display the help message.

## Limitations
Currently, the `scale` cropper method does not preserve PDF annotations.
If preserving annotations is critical, consider using the `box` cropper instead.

## Considered Alternatives
* **[pdfcrop](https://pypi.org/project/pdf-crop/)**: Not suitable — limited control.
* **Online Croppers**: Some worked reasonably well, but they lacked the ability to specify padding or exact margins.

## Interim Testing Results
*All tests run with border padding set to 0.*

|   Bounds          | Cropping  | Summary |
| ----------------- | ----------- |------------- |
| `page_bounds`     | `box`       | No effect.
| `page_bounds`     | `scale`     | No effect. 
| `text_page`       | `box`       | Pages differ in size. On the first few pages containing images, the text is cut off. The back cover image has too much whitespace. There are issues with the images. Empty pages without text need to be fixed.
| `text_page`       | `scale`     | Missing images when they’re at the top (e.g. page 50).
| `dict_text`       | `box`       | Slightly wider side margins on first page. Otherwise similar to text_page.
| `dict_text`       | `scale`     | Same as above.
| `text_page_images`| `box`       | The first page has slightly more space on the left, while the second page remains unchanged. The image on page 50 is not displaying correctly.
| `text_page_images`| `scale`     | Similar to `text_page_images` and  `scale` cropper.
| `ocr`             | `box`       | It works surprisingly well. However, the image on page 2 is cut off on the right. This is likely because OCR didn't perform flawlessly—the word is not narrow and appears in an arch.
| `ocr`             | `scale`     | It works better than the `box` cropper and also preserves the images.
| `histogram`       | `box`       | Best of all methods—but the first page still has a thin black border ([see issue #1](https://github.com/tilenskr/crop-pdf-margins/issues/1)).
| `histogram`       | `scale`     | Only the first page is potentially problematic due to the thin borders mentioned above.

> **Note:** The `text_page` extractor is better than `dict_text`, and since they are similar, we performed tests on the former when adding the images.
