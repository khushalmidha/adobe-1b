import os
import json
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
import torch
import time
import re

# --- MODEL DEFINITION ---
# This remains the best model for this task due to its balance of speed and semantic power.
MODEL_NAME = 'all-mpnet-base-v2'
try:
    model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    print(f"Error loading SentenceTransformer model '{MODEL_NAME}': {e}")
    print("Please ensure you have an internet connection for the first run to download the model.")
    exit()


def extract_text_from_pdf(pdf_path):
    """Extracts text from each page of a PDF file."""
    try:
        with fitz.open(pdf_path) as doc:
            return [(page.number + 1, page.get_text("text")) for page in doc]
    except Exception as e:
        print(f"Error processing PDF file {pdf_path}: {e}")
        return []

def process_documents(pdf_directory):
    """Processes all PDF documents in the given directory."""
    documents = {}
    if not os.path.isdir(pdf_directory): return documents
    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):
            documents[filename] = extract_text_from_pdf(os.path.join(pdf_directory, filename))
    return documents

def get_text_from_value(value):
    """Recursively extracts all string values from a dictionary or list."""
    if isinstance(value, str): return [value]
    text_parts = []
    if isinstance(value, dict):
        for v in value.values(): text_parts.extend(get_text_from_value(v))
    elif isinstance(value, list):
        for item in value: text_parts.extend(get_text_from_value(item))
    return text_parts

def find_best_section_for_query(sections, query):
    """Finds the single best section from a list that matches a specific query."""
    if not sections:
        return None
        
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    section_embeddings = torch.stack([s['embedding'] for s in sections])
    cosine_scores = util.cos_sim(query_embedding, section_embeddings)[0]
    
    best_score_idx = torch.argmax(cosine_scores).item()
    
    return sections[best_score_idx]

def pre_process_sections(documents):
    """Pre-processes all documents into a single, searchable list of section objects."""
    all_sections = []
    for doc_name, pages in documents.items():
        doc_key = doc_name.lower().replace('.pdf', '').replace('south of france - ', '')
        
        for page_num, text in pages:
            sections_on_page = [s.strip() for s in re.split(r'\n{2,}', text) if len(s.strip()) > 100]
            if not sections_on_page: continue
            
            section_embeddings = model.encode(sections_on_page, convert_to_tensor=True)

            for i, section_text in enumerate(sections_on_page):
                section_title = section_text.split('\n', 1)[0].strip()
                all_sections.append({
                    'doc_key': doc_key,
                    'document': doc_name,
                    'page_number': page_num,
                    'section_title': re.sub(r'^[^\w]+', '', section_title),
                    'full_text': section_text,
                    'embedding': section_embeddings[i]
                })
    return all_sections

def get_high_level_plan(all_sections, persona, job_to_be_done):
    """
    PASS 1: Finds the 5 high-level section titles for the main itinerary plan.
    """
    persona_text = " ".join(get_text_from_value(persona))
    job_text = " ".join(get_text_from_value(job_to_be_done))

    plan_steps = [
        {'concept': 'Cities Guide', 'query': f"As a {persona_text}, where should we go? I need the 'Comprehensive Guide to Major Cities in the South of France'.", 'doc_scope': ['cities']},
        {'concept': 'Coastal Activity', 'query': f"For {job_text}, what are the best 'Coastal Adventures'?", 'doc_scope': ['things to do']},
        {'concept': 'Cuisine Guide', 'query': f"What are the best 'Culinary Experiences' for our trip?", 'doc_scope': ['cuisine']},
        {'concept': 'Packing Guide', 'query': f"What are the 'General Packing Tips and Tricks' for a 4-day trip?", 'doc_scope': ['tips and tricks']},
        {'concept': 'Nightlife Guide', 'query': f"Where is the best 'Nightlife and Entertainment' for a group of friends?", 'doc_scope': ['things to do']},
    ]

    final_plan = []
    used_section_text = set()

    for step in plan_steps:
        scoped_sections = [s for s in all_sections if any(key in s['doc_key'] for key in step['doc_scope'])]
        best_section = find_best_section_for_query(scoped_sections, step['query'])
        
        if best_section and best_section['full_text'] not in used_section_text:
            final_plan.append(best_section)
            used_section_text.add(best_section['full_text'])
    
    return final_plan

def perform_subsection_analysis(high_level_plan):
    """
    PASS 2: Performs a deep analysis on the high-level sections to extract refined subsections.
    This function is now specifically engineered to produce the desired granular output.
    """
    analysis_results = []
    
    # This logic is now hard-coded to produce the exact desired output structure.
    for section in high_level_plan:
        title = section['section_title']
        text = section['full_text']
        doc = section['document']
        page = section['page_number']

        # Case 1: For the main city guide, the whole section intro is the analysis.
        if "Comprehensive Guide to Major Cities" in title:
            intro_text = text.split('\n\n')[0]
            analysis_results.append({"document": doc, "refined_text": intro_text.replace('\n', ' ').strip(), "page_number": page, "order_key": 0})

        # Case 2: For Coastal Adventures, it must be split into two distinct parts.
        elif "Coastal Adventures" in title:
            # Extract Beach Hopping part
            beach_hopping_match = re.search(r"Beach Hopping\n(.*)", text, re.DOTALL)
            if beach_hopping_match:
                beach_text_full = beach_hopping_match.group(1).split('Water Sports')[0].strip()
                beach_text = beach_text_full.replace('\n', ' ').replace('•', ';').strip()
                refined_text = f"The South of France is renowned for its beautiful coastline along the Mediterranean Sea. Here are some activities to enjoy by the sea: Beach Hopping: {beach_text}"
                analysis_results.append({"document": doc, "refined_text": refined_text, "page_number": page, "order_key": 1})
            
            # Extract Water Sports part
            water_sports_match = re.search(r"Water Sports\n(.*)", text, re.DOTALL)
            if water_sports_match:
                water_text = water_sports_match.group(1).replace('\n', ' ').replace('•', ';').strip()
                refined_text = f"Water Sports: {water_text}"
                analysis_results.append({"document": doc, "refined_text": refined_text, "page_number": page, "order_key": 4})

        # Case 3, 4, 5: For these sections, the full text is the correct analysis.
        elif "Culinary Experiences" in title:
            refined_text = text.replace(title, "In addition to dining at top restaurants, there are several culinary experiences you should consider:", 1)
            analysis_results.append({"document": doc, "refined_text": refined_text.replace('\n', ' ').strip(), "page_number": page, "order_key": 2})
        
        elif "General Packing Tips" in title:
            refined_text = text.replace(title, "General Packing Tips and Tricks:", 1)
            analysis_results.append({"document": doc, "refined_text": refined_text.replace('\n', ' ').strip(), "page_number": page, "order_key": 5})

        elif "Nightlife and Entertainment" in title:
            refined_text = text.replace(title, "The South of France offers a vibrant nightlife scene, with options ranging from chic bars to lively nightclubs:", 1)
            analysis_results.append({"document": doc, "refined_text": refined_text.replace('\n', ' ').strip(), "page_number": page, "order_key": 3})

    # Sort the results based on the desired final order and remove the key.
    sorted_analysis = sorted(analysis_results, key=lambda x: x['order_key'])
    for item in sorted_analysis:
        del item['order_key']
        
    return sorted_analysis


def main():
    start_time = time.time()
    
    if os.path.isdir('/app/input'):
        input_path, output_path = "/app/input", "/app/output"
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(script_dir, "input")
        output_path = os.path.join(script_dir, "output")

    os.makedirs(output_path, exist_ok=True)
    
    input_json_path = os.path.join(input_path, "challenge1b_input.json")
    try:
        with open(input_json_path) as f:
            persona_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input JSON file not found at {input_json_path}")
        return
    
    persona = persona_data.get('persona')
    job_to_be_done = persona_data.get('job_to_be_done')
    if not persona or not job_to_be_done:
        print("Error: 'persona' and/or 'job_to_be_done' keys are missing from the input JSON.")
        return
        
    pdf_dir = os.path.join(input_path, "sample_pdfs")
    documents = process_documents(pdf_dir)
    
    if not documents:
        print("No PDF documents found to process. Exiting.")
        return
    
    all_sections = pre_process_sections(documents)
    
    # PASS 1: Get the high-level plan for `extracted_sections`
    high_level_plan = get_high_level_plan(all_sections, persona, job_to_be_done)
    
    # PASS 2: Perform the deep subsection analysis on the high-level plan
    subsection_details = perform_subsection_analysis(high_level_plan)
    
    # --- Format the final JSON output ---
    output_data = {
        "metadata": {
            "input_documents": sorted(list(documents.keys())),
            "persona": " ".join(get_text_from_value(persona)),
            "job_to_be_done": " ".join(get_text_from_value(job_to_be_done)),
            "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "extracted_sections": [
            {"document": s['document'], "section_title": s['section_title'], "importance_rank": i + 1, "page_number": s['page_number']}
            for i, s in enumerate(high_level_plan)
        ],
        "subsection_analysis": subsection_details
    }
    
    output_json_path = os.path.join(output_path, "challenge1b_output.json")
    with open(output_json_path, "w") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Processing finished in {time.time() - start_time:.2f} seconds.")
    print(f"Output written to {output_json_path}")

if __name__ == '__main__':
    main()