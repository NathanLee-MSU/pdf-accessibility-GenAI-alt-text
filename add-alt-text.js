const fs = require('fs').promises;
const fs_1 = require('fs');
//Import pdfLib library
const pdfLib = require('./pdfLib.js');

const { PDFDocument, PDFName, PDFDict, PDFString, PDFDocumentFactory, PDFRawStream} = require('./pdfLib.js');

const args = process.argv;

async function modifyPdf() {
    //Read in document and set variables read in as arguments
    const url = args[2];
    const pdfBytes = fs_1.readFileSync(url);
    const pdfDoc = await PDFDocument.load(pdfBytes);
    //Read in the json document containing the alt text
    const data = require('./output-alt-text.json');
    //Iterate through each xref of images in the document
    for (const xref in data) {
      //Iterate through every object in the pdf
      pdfDoc.context.enumerateIndirectObjects().forEach(([pdfRef, pdfObject]) => {
            //See if the object is a PDFDict object
            if (pdfObject instanceof PDFDict) {
                //If it is see if the structure type is a figure
                const structType = pdfObject.lookup(PDFName.of('S'))?.encodedName;

                if (structType === '/Figure') {
                  //If it is a figure, see if it is the figure referenced by the xref in the json document
                  if(pdfRef.objectNumber == xref){
                    //If so, add the alt text found in the json
                    let newAltText = data[xref]['alt'];
                    pdfObject.set(PDFName.of('Alt'), PDFString.of(newAltText));
                    pdfObject.set(PDFName.of('Contents'), PDFString.of(newAltText));
                  }
                }
                
            }
      });
    }
    //Save the PDF as a new PDF with _alt_text_added to the name
    const newPdfBytes = await pdfDoc.save();
    filepath = url.replace(".pdf", "") + "_alt_text_added.pdf";
    fs.writeFile(filepath, newPdfBytes, (err) => {
      if (err){
        console.error('Error writing file:', err);
        return;
      }
      console.log('Bytes successfully written to', filePath);
    });
}

modifyPdf()