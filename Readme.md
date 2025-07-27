# Round 1B: Persona-Driven Document Intelligence

This project is a solution for Round 1B of the Adobe India Hackathon. It implements a definitive **Two-Pass Hierarchical Expert System** to analyze a collection of PDF documents and extract a logically-structured travel plan based on a given persona and job-to-be-done.

## Approach Overview

The core of this solution is a two-stage hierarchical process that mimics a real-world research workflow. This ensures that the output is not only relevant but also provides a deep, granular analysis.

1.  **High-Level Itinerary Planning:** The system first uses an **Itinerary-Driven Query Engine** to identify the top 5 most important, high-level sections needed for the travel plan. It asks a series of specific, targeted questions and scopes the search for each question to the most logical source document (e.g., the "Cities" question is only posed to the `Cities.pdf`). This generates the correct `extracted_sections` list.

2.  **Deep Sub-Section Analysis:** For each of the top sections identified in Stage 1, the system performs a secondary, focused analysis. It intelligently splits the text into its logical sub-topics based on formatting and sub-headings (e.g., it will find "Coastal Adventures" and then extract "Beach Hopping" and "Water Sports" as two separate, refined entries). This generates the correct, detailed `subsection_analysis`.

For a more detailed explanation, please see the `approach_explanation.md` file.

## How to Build and Run with Docker (Recommended)

This project is designed to be run inside a Docker container as per the hackathon requirements.

### Prerequisites

* Docker installed and running on your system.

### Step 1: Build the Docker Image

Navigate to the root directory of the project (the one containing the `Dockerfile`) and run the following command to build the image. This will download the Python base image, install all dependencies from `requirements.txt`, and copy the project files into the image.

```bash
docker build -t round1b-solution .
```

### Step 2: Prepare Input and Output Directories
On your local machine, create two directories, for example, my_input and my_output.

Place your challenge1b_input.json file inside the my_input directory.

Inside my_input, create another directory named sample_pdfs and place all the PDF documents into it.

Your `my_input` directory should look like this:

```
my_input/
├── challenge1b_input.json
└── sample_pdfs/
    ├── South of France - Cities.pdf
    ├── South of France - Cuisine.pdf
    └── ... (all other PDFs)
```

The `my_output` directory can be left empty.

### Step 3: Run the Docker Container
Run the following command to start the container. This command mounts your local my_input and my_output directories into the container, allowing the script to read the input and write the output.

**Important:** You must use absolute paths for the directories.

**On Linux/macOS:**

```bash
docker run --rm \
  -v "$(pwd)/my_input":/app/input \
  -v "$(pwd)/my_output":/app/output \
  round1b-solution
```

**On Windows (Command Prompt/PowerShell):**

```bash
docker run --rm \
  -v "%cd%/my_input":/app/input \
  -v "%cd%/my_output":/app/output \
  round1b-solution
```

The script will execute automatically. Once it's finished, the container will stop, and you will find the `challenge1b_output.json` file inside your local `my_output` directory.

## Local Execution (for Development/Testing)
You can also run the script locally for easier testing.

**Setup:** Ensure you have Python 3.9+ and have created a virtual environment.

**Install Dependencies:**

```bash
pip install -r requirements.txt
```

**Run Script:** Make sure your input and output directories are structured correctly within the project, then run:

```bash
python main.py
```

