from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import re
import logging
import json

# Import PDF and Neo4j libraries
import pdfplumber
from neo4j import GraphDatabase

# --- Dataclass-like Structures ---
# We will use dictionaries to represent these structures for easy XCom serialization.

def create_document_metadata(file_path, doc_type):
    """Factory function for DocumentMetadata dictionary."""
    return {
        "document_type": doc_type,
        "document_number": None,
        "issuing_authority": None,
        "issue_date": None,
        "subject": None,
        "legal_basis": [],
        "file_path": file_path,
        "processing_timestamp": datetime.now().isoformat()
    }

def create_person_info():
    """Factory function for PersonInfo dictionary."""
    return {
        "name": None,
        "employee_id": None,
        "birth_place": None,
        "birth_date": None,
        "gender": None,
        "education": None,
        "position": None,
        "grade": None,
        "salary": None,
        "work_unit": None,
        "institution": "Pemerintah Kota Samarinda", # Corrected Institution
        "appointment_start": None,
        "appointment_end": None
    }

# --- Agentic Extraction Logic ---

def extract_info_agent(text, file_path):
    """
    This is the core "AI" agent. It uses a series of targeted regular expressions
    and contextual analysis to extract structured data from the raw PDF text.
    """
    doc_type = 'PNS' if 'SK PNS' in file_path else 'PPPK'
    
    doc_metadata = create_document_metadata(file_path, doc_type)
    person_info = create_person_info()

    # --- Person Info Extraction (Enhanced) ---
    
    # Name
    name_match = re.search(r'Nama\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if name_match:
        person_info['name'] = name_match.group(1).strip()

    # Employee ID (NIP / NIPPPK) - More flexible patterns
    employee_id_patterns = [
        r'NIP\s*/\s*NIPPPK\s*:\s*([\d\s]+)',
        r'NIPPPK\s*:\s*([\d\s]+)',
        r'NIP\.\s*:\s*([\d\s]+)',
        r'NIP\s*:\s*([\d\s]+)'
    ]
    for pattern in employee_id_patterns:
        employee_id_match = re.search(pattern, text, re.IGNORECASE)
        if employee_id_match:
            person_info['employee_id'] = re.sub(r'\s+', '', employee_id_match.group(1).strip())
            break

    # Place and Date of Birth
    birth_match = re.search(r'Tempat\s*/\s*Tanggal Lahir\s*:\s*([^,]+),\s*([\d\s\w]+)', text, re.IGNORECASE)
    if birth_match:
        person_info['birth_place'] = birth_match.group(1).strip()
        person_info['birth_date'] = birth_match.group(2).strip()

    # Education
    education_match = re.search(r'Pendidikan Terakhir\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if education_match:
        person_info['education'] = education_match.group(1).strip()

    # Position
    position_match = re.search(r'Jabatan\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if position_match:
        person_info['position'] = position_match.group(1).strip()

    # Work Unit
    work_unit_match = re.search(r'Unit Kerja\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if work_unit_match:
        person_info['work_unit'] = work_unit_match.group(1).strip()

    # Appointment Start Date (TMT)
    start_date_match = re.search(r'Terhitung Mulai Tanggal\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if start_date_match:
        person_info['appointment_start'] = start_date_match.group(1).strip()

    # --- Document Metadata Extraction ---

    # Document Number
    doc_num_match = re.search(r'NOMOR\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if doc_num_match:
        doc_metadata['document_number'] = doc_num_match.group(1).strip()

    # Issue Date
    issue_date_match = re.search(r'Ditetapkan di Samarinda\s*pada tanggal\s*:\s*([^\n]+)', text, re.IGNORECASE)
    if issue_date_match:
        doc_metadata['issue_date'] = issue_date_match.group(1).strip()
        
    return {"metadata": doc_metadata, "person": person_info}


# --- Airflow Task Functions ---

def _scan_and_extract(**context):
    """
    Task 1: Scans directories, extracts raw text from PDFs, and passes
    the content to the next task via XComs.
    """
    pns_dir = "/opt/airflow/data/SK PNS"
    pppk_dir = "/opt/airflow/data/SK PPPK"
    
    all_docs_text = []
    
    def process_directory(directory_path):
        logging.info(f"Scanning directory: {directory_path}")
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    logging.info(f"Extracting text from: {file_path}")
                    try:
                        with pdfplumber.open(file_path) as pdf:
                            full_text = "".join(page.extract_text() or "" for page in pdf.pages)
                            if full_text.strip():
                                all_docs_text.append({"file_path": file_path, "text": full_text})
                            else:
                                logging.warning(f"No text could be extracted from {file_path}")
                    except Exception as e:
                        logging.error(f"Failed to process {file_path}: {e}")

    process_directory(pns_dir)
    process_directory(pppk_dir)
    
    logging.info(f"Successfully extracted text from {len(all_docs_text)} documents.")
    return all_docs_text

def _analyze_and_structure(**context):
    """
    Task 2: Receives raw text data and uses the agentic extraction logic
    to create structured data.
    """
    extracted_docs = context['task_instance'].xcom_pull(task_ids='scan_and_extract_task')
    if not extracted_docs:
        logging.warning("No documents were extracted. Skipping analysis.")
        return []

    structured_results = []
    for doc in extracted_docs:
        logging.info(f"Analyzing document: {doc['file_path']}")
        structured_data = extract_info_agent(doc['text'], doc['file_path'])
        structured_results.append(structured_data)
    
    logging.info(f"Successfully analyzed and structured {len(structured_results)} documents.")
    return structured_results

def _load_to_neo4j(**context):
    """
    Task 3: Connects to Neo4j and loads the structured data, creating
    Person and Document nodes and their relationships.
    Features:
    - Clears existing data before loading new data
    - Processes data in chunks of 100 records for better performance
    """
    structured_data = context['task_instance'].xcom_pull(task_ids='analyze_and_structure_task')
    if not structured_data:
        logging.warning("No structured data to load. Skipping Neo4j operation.")
        return

    uri = os.getenv('NEO4J_URI', 'neo4j://host.docker.internal:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', '12345!@#$%')
    database = os.getenv('NEO4J_DATABASE', 'damkar-sk')
    
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session(database=database) as session:
        # --- CLEAR EXISTING DATA ---
        logging.info("Clearing existing data from Neo4j...")
        session.run("MATCH (n) DETACH DELETE n")
        logging.info("Existing data cleared successfully.")
        
        # Create constraints for idempotency and performance
        session.run("CREATE CONSTRAINT person_employee_id IF NOT EXISTS FOR (p:Person) REQUIRE p.employee_id IS UNIQUE")
        session.run("CREATE CONSTRAINT document_file_path IF NOT EXISTS FOR (d:Document) REQUIRE d.file_path IS UNIQUE")
        
        # Filter out invalid data
        valid_data = []
        for data in structured_data:
            person = data['person']
            doc = data['metadata']
            
            # Validate that the employee_id exists before trying to load to Neo4j.
            if not person.get('employee_id'):
                logging.warning(f"Skipping load for document {doc.get('file_path')} because employee_id is missing.")
                continue
            
            valid_data.append(data)
        
        # --- CHUNK PROCESSING ---
        chunk_size = 100
        total_chunks = len(valid_data) // chunk_size + (1 if len(valid_data) % chunk_size > 0 else 0)
        
        logging.info(f"Processing {len(valid_data)} records in {total_chunks} chunks of {chunk_size} records each.")
        
        for i in range(0, len(valid_data), chunk_size):
            chunk = valid_data[i:i + chunk_size]
            chunk_number = i // chunk_size + 1
            
            logging.info(f"Processing chunk {chunk_number}/{total_chunks} ({len(chunk)} records)")
            
            # Process chunk in a single transaction
            with session.begin_transaction() as tx:
                for data in chunk:
                    person = data['person']
                    doc = data['metadata']
                    
                    logging.info(f"Loading data for {person.get('name')} from {doc.get('file_path')}")

                    # Use MERGE to create/update Person and Document nodes and the relationship
                    tx.run("""
                        // Create or find the Person node
                        MERGE (p:Person {employee_id: $person.employee_id})
                        ON CREATE SET p = $person, p.created_at = timestamp()
                        ON MATCH SET p += $person, p.updated_at = timestamp()

                        // Create or find the Document node
                        MERGE (d:Document {file_path: $doc.file_path})
                        ON CREATE SET d = $doc, d.created_at = timestamp()
                        ON MATCH SET d += $doc, d.updated_at = timestamp()

                        // Create the relationship between them
                        MERGE (p)-[r:HAS_DOCUMENT]->(d)
                    """, person=person, doc=doc)
                
                tx.commit()
            
            logging.info(f"Chunk {chunk_number}/{total_chunks} processed successfully.")

    driver.close()
    logging.info(f"Successfully loaded data for {len(valid_data)} documents into Neo4j using chunked processing.")


# --- DAG Definition ---

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 7, 16),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'agentic_pdf_processing_dag',
    default_args=default_args,
    description='An agentic pipeline to extract data from PDFs and load to Neo4j.',
    schedule_interval='@daily',
    catchup=False,
    tags=['agentic', 'pdf', 'neo4j'],
) as dag:

    scan_and_extract_task = PythonOperator(
        task_id='scan_and_extract_task',
        python_callable=_scan_and_extract,
    )

    analyze_and_structure_task = PythonOperator(
        task_id='analyze_and_structure_task',
        python_callable=_analyze_and_structure,
    )

    load_to_neo4j_task = PythonOperator(
        task_id='load_to_neo4j_task',
        python_callable=_load_to_neo4j,
    )

    # Define the agentic workflow
    scan_and_extract_task >> analyze_and_structure_task >> load_to_neo4j_task