import fitz  # PyMuPDF
import io
import sys
import os
from os import listdir
from PIL import Image
from ollama import chat
from ollama import ChatResponse
import base64
import time
import math
import json
import subprocess
from pathlib import Path

def are_numbers_close(num1, num2, rel_tol=1e-09, abs_tol=0.0):
    """
    Checks if two numbers are close to each other, considering floating-point precision.

    Args:
        num1 (float or int): The first number.
        num2 (float or int): The second number.
        rel_tol (float): The relative tolerance. This is the maximum allowed difference
                         relative to the larger absolute value of the two arguments.
                         Defaults to 1e-09.
        abs_tol (float): The absolute tolerance. This is the maximum allowed absolute
                         difference between the two numbers. Defaults to 0.0.

    Returns:
        bool: True if the numbers are considered close, False otherwise.
    """
    return math.isclose(num1, num2, rel_tol=rel_tol, abs_tol=abs_tol)

def min_image_size_check(image_path, min_width, min_height, output_path=None):
    """
    Ensures an image is at least a certain minimum width and height.
    If the image is smaller, it is scaled up while maintaining aspect ratio.

    Args:
        image_path (str): The path to the input image.
        min_width (int): The minimum required width.
        min_height (int): The minimum required height.
        output_path (str, optional): The path to save the resized image.
                                     If None, the original image is overwritten.
    """
    try:
        img = Image.open(image_path)
        width, height = img.size

        # Check if resizing is necessary
        if width < min_width or height < min_height:
            # Calculate scaling factor to meet minimum dimensions while preserving aspect ratio
            scale_w = min_width / width if width < min_width else 1
            scale_h = min_height / height if height < min_height else 1
            scale_factor = max(scale_w, scale_h) # Use max to ensure both dimensions meet minimum

            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            # Resize the image using LANCZOS for high-quality scaling
            img = img.resize((new_width, new_height), Image.LANCZOS)

        # Save the image
        if output_path:
            img.save(output_path)
        else:
            img.save(image_path)

    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def aspect_ratio_check(image_path, max_aspect_ratio, output_path=None):
    """
    Ensures an images has an aspect ratio less than a certain maximum aspect ratio.
    If the image does not, it is resized to fit the requirements.

    Args:
        image_path (str): The path to the input image.
        max_aspect_ratio (int): The maximum aspect ratio allowed.
        output_path (str, optional): The path to save the resized image.
                                     If None, the original image is overwritten.
    """
    try:
        img = Image.open(image_path)
        original_width, original_height = img.size
        original_aspect_ratio = original_width / original_height

        if original_aspect_ratio > max_aspect_ratio:
            new_width = int(original_height * max_aspect_ratio)
            img = img.resize((new_width, original_height), Image.LANCZOS)

        if output_path:
            img.save(output_path)
        else:
            img.save(image_path)
    
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_page_size_pymupdf(pdf_path, page_number=0):
    """
    Retrieves the dimensions (width, height) of a specific PDF page in points using PyMuPDF.

    Args:
        pdf_path (str): The path to the PDF file.
        page_number (int): The index of the page to retrieve (0-indexed).

    Returns:
        height of the page in points,
               or None if the file or page is not found.
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_number]
        height = page.rect.height
        doc.close()
        return height
    except Exception as e:
        print(f"Error getting page size with PyMuPDF: {e}")
        return None

#Initialize a start time variable to track how long processing the pdfs takes
start_time = time.time()

#Initialize the directory path which the pdfs are in and set it to the command line argument given
directory_path = sys.argv[1]

def process_pdfs_in_directory(directory_path):
    """
    The main function that takes in a directory path where tagged pdfs are stored and processes them to add alt text to the images.

    Args:
        directory_path (str): the path where the pdfs to be analyzed are stored.
    """
    path = Path(directory_path)
    
    for pdf_file in path.glob("**/*.pdf"):
        print(f"Processing PDF: {pdf_file}")
        add_alt_text(pdf_file)

def add_alt_text(file):
    """
    Function that adds GenAI alt text to a given pdf.

    Args:
        file (str): path to the pdf file to add alt text to.
    """

    print(file)
    # Define the path to the JavaScript file that finds the bboxes outlining the images
    js_file_path = f"./get-bbox.js"

    #Open the pdf file with PyMuPDF
    pdf_file = fitz.open(file)
    combined_page_text_dict = {}

    height = get_page_size_pymupdf(pdf_file)
    if height is not None:
        # Execute the JavaScript file using Node.js
        try:
            # Use subprocess.run for simple execution and capture output
            result = subprocess.run(["node", js_file_path, file, str(height)], capture_output=True, text=True, check=True)
            pageJsonString = result.stdout.split("|")[0]
            itemPageJsonString = result.stdout.split("|")[1]
            try:
                pagedata = json.loads(pageJsonString)
                pagedatadict = {item[0]: item[1] for item in pagedata}
                itemdata = json.loads(itemPageJsonString)
                itemdatadict = {item[0]: item[1] for item in itemdata}
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing JavaScript: {e}")
            print(f"Stderr: {e.stderr}")

    json_dict = {}

    #Initialize a folder to store the images in
    folder_path = r"./imagestest/"

    #Remove any previous files/images from that folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(filename, "is removed")

    def encode_image(image_path):
        """
        Function to base 64 encode an image.

        Args:
            image_path (str): path to the image to be encoded
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    #Iterate through the xrefs of the images in the pdf
    for xref in itemdatadict:
        itemarray = itemdatadict[xref]
        #Get the page index value of the item
        page_index = pagedatadict[itemarray[0]]
        #Get the page and extract the text from the page
        page = pdf_file.load_page(page_index)
        page_text = page.get_text("blocks", clip=None, flags=4, textpage=None, sort=False, delimiters=None)
        #Get a pixmap of the image based on the bbox found in the Javascript
        pix = page.get_pixmap(matrix=fitz.Matrix(4,4), clip=fitz.Rect(itemarray[1], itemarray[2], itemarray[3], itemarray[4]))
        combined_page_text = ""
        #Loop through each section of the page text and if it contains the image tag see if the bbox matches and mark the image accordingly in the text
        for section in page_text:
            if '<image:' in section[4]:
                if(are_numbers_close(section[0], itemarray[1], abs_tol=0.1) and are_numbers_close(section[1], itemarray[2], abs_tol=0.1) and are_numbers_close(section[2], itemarray[3], abs_tol=0.1) and are_numbers_close(section[3], itemarray[4], abs_tol=0.1)):
                    combined_page_text += '|IMAGE INTERESTED| '
                else:
                    combined_page_text += '|OTHER IMAGE| '
            else:
                combined_page_text += section[4] + " "
        #Make a dictionary of the xrefs of the images linked to the corresponding page text that will be used for context in the LLM
        combined_page_text_dict[xref] = combined_page_text
        #Save the pixmap of the image as a png
        pix.save(f"./imagestest/{xref}.png",output="png", jpg_quality=95)

    #Path to the system prompt of the LLM in Markdown format
    system_prompt_path = "./system-prompt.md"

    #Open the Markdown file and save the content as a string
    try:
        with open(system_prompt_path, "r", encoding="utf-8") as markdown_file:
            markdown_content = markdown_file.read()
        print("Markdown content loaded successfully")
    except FileNotFoundError:
        print(f"Error: The file '{system_prompt_path}' was not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

    #Iterate through all of the images
    for image in os.listdir("./imagestest"):
        if(image.endswith(".png")):
            testResponse = ""
            image_file = './imagestest/' + image
            #Make sure the image is larger than 28 pixels x 28 pixels
            min_image_size_check(image_file, 32, 32)
            #Make sure the image aspect ratio is less than 200
            aspect_ratio_check(image_file, 200)
            #Encode the image
            encoded_image = encode_image(image_file)
            xref = image.replace(".png","")
            while(testResponse == ""):                
                #Call the LLM with Ollama
                response: ChatResponse = chat(model='qwen3-vl:30b', messages=[
                    {
                        'role': 'system',
                        'content': f"""{markdown_content}"""
                    },
                    {
                        'role': 'user',
                        'content': f"""Image Context: {combined_page_text_dict[int(xref)]}""",
                        'images': [encoded_image],
                        'options': {'num_ctx': 32000}
                    },
                    ])
                #Print out the alt text generated
                testResponse = response['message']['content']
            print(xref + ":" + response['message']['content'])
            json_dict[xref] = {"alt": response['message']['content']}
    #Save the output text as a json file
    with open("output-alt-text.json", 'w') as f:
        json.dump(json_dict,f)

    # Define the path to your JavaScript file
    js_file_path2 = "./add-alt-text.js"

    # Execute the JavaScript file using Node.js
    try:
        # Use subprocess.run for simple execution and capture output
        result = subprocess.run(["node", js_file_path2, file], capture_output=True, text=True, check=True)
        JsonString = result.stdout
        print(JsonString)
    except subprocess.CalledProcessError as e:
        print(f"Error executing JavaScript: {e}")
        print(f"Stderr: {e.stderr}")

#Run the main process
process_pdfs_in_directory(directory_path)

#Set the end time and print out how long the script took
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Elapsed time: {elapsed_time:.4f} seconds")
