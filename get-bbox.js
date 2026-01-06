const fs = require('fs');

//Import pdfLib library
const pdfLib = require('./pdfLib.js');

const { PDFDocument, PDFName, PDFDict, PDFString, PDFDocumentFactory, PDFRawStream} = require('./pdfLib.js');

const args = process.argv;

async function modifyPdf() {
        //Read in document and set variables read in as arguments
        const url = args[2];
        const height = parseFloat(args[3]);
        const pdfBytes = fs.readFileSync(url);
        const pdfDoc = await PDFDocument.load(pdfBytes);
        let pages = pdfDoc.getPages();
        const pageDict = new Map();
        for (page in pages) {
            //Set a map of the xref number of the page with it's page number
            pageDict.set(pages[page].ref.objectNumber, parseInt(page));
        }
        //Turn the map into a json object
        const pageArray = [...pageDict.entries()];
        const pageJson = JSON.stringify(pageArray);
        const refPageDict = new Map()
        //Iterate through every object in the pdf
        pdfDoc.context.enumerateIndirectObjects().forEach(([pdfRef, pdfObject]) => {
            //See if the object is a PDFDict object
            if (pdfObject instanceof PDFDict) {
                //If it is see if the structure type is a figure
                const structType = pdfObject.lookup(PDFName.of('S'))?.encodedName;

                if (structType === '/Figure') {
                    //If it is a figure, get the bounding box information and set it in the diction with the xref number and manipulated to be the right format for python bounding boxes
                    var bbox_array = pdfObject.lookup(PDFName.of('A')).lookup(PDFName.of('BBox'));
                    refPageDict.set(pdfRef.objectNumber, [pdfObject.get(PDFName.of('Pg')).objectNumber, bbox_array.array[0].numberValue, height-bbox_array.array[3].numberValue, bbox_array.array[2].numberValue, height-bbox_array.array[1].numberValue]);
                }
            }
        });
        const refPageArray = [...refPageDict.entries()];
        const refPageJson = JSON.stringify(refPageArray);
        //return the formated pages/xref and figure/xref/bounding box json objects
        console.log(`${pageJson}|${refPageJson}`);
    }

modifyPdf()