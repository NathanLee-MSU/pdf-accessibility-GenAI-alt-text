# Creating Accessible PDFs with Open-Source Generative AI

This python script takes a directory of tagged pdf files and adds open source GenAI text to the images contained in them. The runtime will depend on the number of images contained in the pdfs as well as what machine the script is run on. It is recommended to be run on a machine with a dedicated gpu. Tests were run on a PC with an Intel Core Ultra 9 285 (2.5 GHz) processor, 192 GB of DDR5-5200 RAM, and an Nvidia GeForce RTX 5070 TI.

# Usage

- The first thing is to copy all of the files in this repository to a location where you can run python.
- You must have a directory with already tagged pdf files. The easiest way to tag (albeit error prone) is by using Adobe Pro auto-tagging batch feature.
- Setup Ollama to run the LLM locally using the instructions below
- Optionally tweak the Markdown if you wish to have a different system prompt
- Make sure the Javascript files are saved in the correct place
- Utilize the instructions in the Python section to run the script

## Ollama

You will need Ollama to run the LLM used to generate the alt-text. You can download it at: https://ollama.com/download.

Once downloaded you will need to run:

```shell
ollama pull qwen3-vl:30b
```

If you choose to use a different LLM, you will have to pull that model using a similar command. Ollama must either be running in the background or close the background instance and run:

```shell
ollama serve
```

Which allows you to be able to see when requests are made and their status. Make sure that http://localhost:11434 in your web browser returns: "Ollama is running" before running the Python script.

## Markdown

Markdown is used as the format for the system prompt sent to the LLM using the file system-prompt.md. This system prompt is tuned for PDFs containing scholarly articles so some of the language may need to be tweaked or removed based on your specific use case.

## Javascript

You will need all three Javascript files, add-alt-text.js, get-bbox.js, and pdfLib.js, in the same directory as directory-add-alt-text.py. The file get-bbox.js is used to get the page xref and bounding box information of the images, it should not be changed. The file add-alt-text.js is used to actually add the alt text back into the images after it has been generated, it should not be changed other than editing  "_alt_text_added.pdf" if you wish to have different file names saved. The file pdfLib.js contains the Javascript library pdfLib and is required and used by both other Javascript files, it also should not be changed.

## Python

First, install all the packages you will need:

```shell
pip install PyMuPDF PIL ollama
```

Double check if you already have a directory folder that contains tagged pdf files. This example assumes the directory is named pdfs-tagged/ and is saved at the same place as directory-add-alt-text.py

Then run:

```shell
python directory-add-alt-text.py ./pdfs-tagged
```

This will save the versions of the pdfs with alt-text added to ./pdfs-tagged with the original name +  "_alt_text_added.pdf" added to the end of the filename.