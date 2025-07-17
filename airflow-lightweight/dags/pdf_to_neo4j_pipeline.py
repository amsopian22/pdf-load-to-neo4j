from datetime import datetime, timedelta
import os
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Default arguments
default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_pdf_text(**context):
    """Extract text from PDF files in SK PNS and SK PPPK directories"""
    import PyPDF2
    import pdfplumber
    import os
    import json
    import re
    from datetime import datetime
    
    # Directories containing PDF files
    pns_dir = "/opt/airflow/data/SK PNS"
    pppk_dir = "/opt/airflow/data/SK PPPK"
    
    extracted_data = []
    
    def extract_sk_date_from_content(content):
        """Extract SK date from document content using various patterns"""
        import re
        
        # Indonesian month mapping
        months = {
            'januari': '01', 'februari': '02', 'maret': '03', 'april': '04',
            'mei': '05', 'juni': '06', 'juli': '07', 'agustus': '08',
            'september': '09', 'oktober': '10', 'november': '11', 'desember': '12'
        }
        
        date_patterns = [
            # Pattern: "12 Januari 2024" atau "12 januari 2024"
            r'(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})',
            # Pattern: "12-01-2024" atau "12/01/2024"
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            # Pattern: "2024-01-12"
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            # Pattern dalam teks SK: "tanggal 12 Januari 2024"
            r'tanggal\s+(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})',
            # Pattern: "ditetapkan pada tanggal 12 Januari 2024"
            r'ditetapkan.*tanggal\s+(\d{1,2})\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(\d{4})'
        ]
        
        content_lower = content.lower()
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            if matches:
                match = matches[0]
                
                if len(match) == 3:
                    if pattern.startswith(r'(\d{4})'):
                        # Format: YYYY-MM-DD
                        year, month, day = match
                        if month.isdigit():
                            return {
                                'raw_date': f"{day.zfill(2)}-{month.zfill(2)}-{year}",
                                'day': int(day) if day.isdigit() else int(month),
                                'month': int(month) if month.isdigit() else int(day),
                                'year': int(year),
                                'month_name': None,
                                'formatted_date': f"{year}-{month.zfill(2)}-{day.zfill(2) if day.isdigit() else month.zfill(2)}"
                            }
                    elif match[1].isdigit():
                        # Format: DD-MM-YYYY atau DD/MM/YYYY
                        day, month, year = match
                        return {
                            'raw_date': f"{day.zfill(2)}-{month.zfill(2)}-{year}",
                            'day': int(day),
                            'month': int(month),
                            'year': int(year),
                            'month_name': None,
                            'formatted_date': f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        }
                    else:
                        # Format dengan nama bulan: DD Month YYYY
                        day, month_name, year = match
                        month_num = months.get(month_name.lower(), '01')
                        return {
                            'raw_date': f"{day} {month_name.title()} {year}",
                            'day': int(day),
                            'month': int(month_num),
                            'year': int(year),
                            'month_name': month_name.title(),
                            'formatted_date': f"{year}-{month_num}-{day.zfill(2)}"
                        }
        
        return None
    
    def extract_employee_info_from_filename(filename, document_type):
        """Extract employee information from filename"""
        employee_info = {
            'document_type': document_type,
            'employee_number': None,
            'employee_name': None,
            'department': None
        }
        
        if document_type == 'PNS':
            # Format: "01 SABARUDDIN.pdf" or "49 ACHMAD SAFI_I.pdf"
            match = re.match(r'^(\d+)\s+(.+)\.pdf$', filename, re.IGNORECASE)
            if match:
                employee_info['employee_number'] = match.group(1)
                employee_info['employee_name'] = match.group(2).strip().replace('_', ' ')
        elif document_type == 'PPPK':
            # Format: "SK_24697130810000398_BAHARUDDIN.pdf"
            match = re.match(r'^SK_(\d+)_(.+)\.pdf$', filename, re.IGNORECASE)
            if match:
                employee_info['employee_number'] = match.group(1)
                employee_info['employee_name'] = match.group(2).strip().replace('_', ' ')
        
        return employee_info
    
    def process_directory(base_dir, document_type):
        """Process PDF files in a directory recursively"""
        if not os.path.exists(base_dir):
            logging.warning(f"Directory {base_dir} does not exist")
            return
        
        processed_count = 0
        
        # Process files recursively
        for root, dirs, files in os.walk(base_dir):
            department = os.path.basename(root) if root != base_dir else "Unknown"
            
            pdf_files = [f for f in files if f.lower().endswith('.pdf')]
            
            for pdf_file in pdf_files:
                file_path = os.path.join(root, pdf_file)
                relative_path = os.path.relpath(file_path, base_dir)
                
                logging.info(f"Processing {document_type} PDF: {relative_path}")
                
                # Extract employee info from filename
                employee_info = extract_employee_info_from_filename(pdf_file, document_type)
                employee_info['department'] = department
                
                try:
                    # Try using pdfplumber first (better for complex layouts)
                    with pdfplumber.open(file_path) as pdf:
                        text_content = ""
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += page_text + "\n"
                        
                        # Extract metadata
                        metadata = {
                            'pages': len(pdf.pages),
                            'file_size': os.path.getsize(file_path),
                            'extraction_method': 'pdfplumber',
                            'document_type': document_type,
                            'relative_path': relative_path,
                            'department': department
                        }
                        
                        if text_content.strip():
                            # Extract SK date from content
                            sk_date_info = extract_sk_date_from_content(text_content)
                            
                            extracted_data.append({
                                'filename': pdf_file,
                                'full_path': relative_path,
                                'content': text_content.strip(),
                                'metadata': metadata,
                                'employee_info': employee_info,
                                'sk_date': sk_date_info
                            })
                            processed_count += 1
                            logging.info(f"Successfully extracted {len(text_content)} characters from {relative_path}")
                        else:
                            logging.warning(f"No text content found in {relative_path}")
                            
                except Exception as e:
                    logging.error(f"Error processing {relative_path} with pdfplumber: {e}")
                    
                    # Fallback to PyPDF2
                    try:
                        with open(file_path, 'rb') as file:
                            pdf_reader = PyPDF2.PdfReader(file)
                            text_content = ""
                            
                            for page in pdf_reader.pages:
                                text_content += page.extract_text() + "\n"
                            
                            metadata = {
                                'pages': len(pdf_reader.pages),
                                'file_size': os.path.getsize(file_path),
                                'extraction_method': 'PyPDF2',
                                'document_type': document_type,
                                'relative_path': relative_path,
                                'department': department
                            }
                            
                            if text_content.strip():
                                # Extract SK date from content
                                sk_date_info = extract_sk_date_from_content(text_content)
                                
                                extracted_data.append({
                                    'filename': pdf_file,
                                    'full_path': relative_path,
                                    'content': text_content.strip(),
                                    'metadata': metadata,
                                    'employee_info': employee_info,
                                    'sk_date': sk_date_info
                                })
                                processed_count += 1
                                logging.info(f"Successfully extracted {len(text_content)} characters from {relative_path} using PyPDF2")
                            else:
                                logging.warning(f"No text content found in {relative_path} using PyPDF2")
                                
                    except Exception as e2:
                        logging.error(f"Error processing {relative_path} with PyPDF2: {e2}")
        
        logging.info(f"Processed {processed_count} {document_type} documents")
        return processed_count
    
    # Process both directories
    pns_count = process_directory(pns_dir, 'PNS')
    pppk_count = process_directory(pppk_dir, 'PPPK')
    
    total_processed = len(extracted_data)
    logging.info(f"Total documents processed: {total_processed} (PNS: {pns_count}, PPPK: {pppk_count})")
    
    if total_processed == 0:
        logging.warning("No PDF files found, creating sample data for testing")
        # Create sample data for testing
        sample_data = {
            'filename': 'sample_document.pdf',
            'full_path': 'sample/sample_document.pdf',
            'content': 'This is sample extracted text for testing the Neo4j pipeline.',
            'metadata': {
                'pages': 1,
                'file_size': 1024,
                'extraction_method': 'sample',
                'document_type': 'SAMPLE',
                'relative_path': 'sample/sample_document.pdf',
                'department': 'Sample Department'
            },
            'employee_info': {
                'document_type': 'SAMPLE',
                'employee_number': '999',
                'employee_name': 'SAMPLE EMPLOYEE',
                'department': 'Sample Department'
            },
            'sk_date': {
                'raw_date': '15 Januari 2024',
                'day': 15,
                'month': 1,
                'year': 2024,
                'month_name': 'Januari',
                'formatted_date': '2024-01-15'
            }
        }
        extracted_data.append(sample_data)
    
    return extracted_data

def load_to_neo4j(**context):
    """Load extracted data to Neo4j with enhanced employee and department modeling"""
    from neo4j import GraphDatabase
    import os
    import json
    
    # Get Neo4j connection details from environment variables
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', '12345!@#$%')
    
    logging.info(f"Connecting to Neo4j at {neo4j_uri}")
    
    # Get extracted data from previous task
    extracted_data = context['task_instance'].xcom_pull(task_ids='extract_pdf_text')
    
    if not extracted_data:
        logging.warning("No data to load to Neo4j")
        return
    
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Create constraints and indexes
            logging.info("Creating database constraints and indexes...")
            
            session.run("""
                CREATE CONSTRAINT document_path_unique IF NOT EXISTS
                FOR (d:Document) REQUIRE d.full_path IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT employee_id_unique IF NOT EXISTS
                FOR (e:Employee) REQUIRE e.employee_id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT department_name_unique IF NOT EXISTS
                FOR (dept:Department) REQUIRE dept.name IS UNIQUE
            """)
            
            session.run("""
                CREATE INDEX document_content_fulltext IF NOT EXISTS
                FOR (d:Document) ON (d.content)
            """)
            
            session.run("""
                CREATE INDEX employee_name_index IF NOT EXISTS
                FOR (e:Employee) ON (e.name)
            """)
            
            session.run("""
                CREATE CONSTRAINT sk_date_unique IF NOT EXISTS
                FOR (sd:SKDate) REQUIRE sd.date_id IS UNIQUE
            """)
            
            session.run("""
                CREATE INDEX sk_date_formatted IF NOT EXISTS
                FOR (sd:SKDate) ON (sd.formatted_date)
            """)
            
            # Process each document
            for doc_data in extracted_data:
                logging.info(f"Loading document: {doc_data['full_path']}")
                
                # Create document node with enhanced metadata
                session.run("""
                    MERGE (d:Document {full_path: $full_path})
                    SET d.filename = $filename,
                        d.content = $content,
                        d.pages = $pages,
                        d.file_size = $file_size,
                        d.extraction_method = $extraction_method,
                        d.document_type = $document_type,
                        d.department = $department,
                        d.loaded_at = datetime(),
                        d.content_length = size($content)
                """, 
                full_path=doc_data['full_path'],
                filename=doc_data['filename'],
                content=doc_data['content'],
                pages=doc_data['metadata']['pages'],
                file_size=doc_data['metadata']['file_size'],
                extraction_method=doc_data['metadata']['extraction_method'],
                document_type=doc_data['metadata']['document_type'],
                department=doc_data['metadata']['department']
                )
                
                # Create SK Date node if date was extracted
                sk_date = doc_data.get('sk_date')
                if sk_date:
                    date_id = f"{sk_date['year']}-{sk_date['month']:02d}-{sk_date['day']:02d}"
                    
                    session.run("""
                        MERGE (sd:SKDate {date_id: $date_id})
                        SET sd.raw_date = $raw_date,
                            sd.day = $day,
                            sd.month = $month,
                            sd.year = $year,
                            sd.month_name = $month_name,
                            sd.formatted_date = $formatted_date,
                            sd.created_at = datetime()
                    """,
                    date_id=date_id,
                    raw_date=sk_date['raw_date'],
                    day=sk_date['day'],
                    month=sk_date['month'],
                    year=sk_date['year'],
                    month_name=sk_date.get('month_name'),
                    formatted_date=sk_date['formatted_date']
                    )
                    
                    # Link document to SK date
                    session.run("""
                        MATCH (d:Document {full_path: $full_path})
                        MATCH (sd:SKDate {date_id: $date_id})
                        MERGE (d)-[:ISSUED_ON]->(sd)
                    """,
                    full_path=doc_data['full_path'],
                    date_id=date_id
                    )
                
                # Create employee node if employee info is available
                emp_info = doc_data['employee_info']
                if emp_info['employee_name'] and emp_info['employee_number']:
                    employee_id = f"{emp_info['document_type']}_{emp_info['employee_number']}"
                    
                    session.run("""
                        MERGE (e:Employee {employee_id: $employee_id})
                        SET e.name = $name,
                            e.employee_number = $employee_number,
                            e.document_type = $document_type,
                            e.department = $department,
                            e.updated_at = datetime()
                    """,
                    employee_id=employee_id,
                    name=emp_info['employee_name'],
                    employee_number=emp_info['employee_number'],
                    document_type=emp_info['document_type'],
                    department=emp_info['department']
                    )
                    
                    # Create relationship between employee and document
                    session.run("""
                        MATCH (e:Employee {employee_id: $employee_id})
                        MATCH (d:Document {full_path: $full_path})
                        MERGE (e)-[:HAS_DOCUMENT]->(d)
                    """,
                    employee_id=employee_id,
                    full_path=doc_data['full_path']
                    )
                    
                    # Link employee to SK date if available
                    if sk_date:
                        date_id = f"{sk_date['year']}-{sk_date['month']:02d}-{sk_date['day']:02d}"
                        session.run("""
                            MATCH (e:Employee {employee_id: $employee_id})
                            MATCH (sd:SKDate {date_id: $date_id})
                            MERGE (e)-[:APPOINTED_ON]->(sd)
                        """,
                        employee_id=employee_id,
                        date_id=date_id
                        )
                
                # Create department node
                if doc_data['metadata']['department'] and doc_data['metadata']['department'] != 'Unknown':
                    session.run("""
                        MERGE (dept:Department {name: $department_name})
                        SET dept.document_type_source = $document_type,
                            dept.updated_at = datetime()
                    """,
                    department_name=doc_data['metadata']['department'],
                    document_type=doc_data['metadata']['document_type']
                    )
                    
                    # Link employee to department
                    if emp_info['employee_name'] and emp_info['employee_number']:
                        employee_id = f"{emp_info['document_type']}_{emp_info['employee_number']}"
                        session.run("""
                            MATCH (e:Employee {employee_id: $employee_id})
                            MATCH (dept:Department {name: $department_name})
                            MERGE (e)-[:WORKS_IN]->(dept)
                        """,
                        employee_id=employee_id,
                        department_name=doc_data['metadata']['department']
                        )
                    
                    # Link document to department
                    session.run("""
                        MATCH (d:Document {full_path: $full_path})
                        MATCH (dept:Department {name: $department_name})
                        MERGE (d)-[:BELONGS_TO]->(dept)
                    """,
                    full_path=doc_data['full_path'],
                    department_name=doc_data['metadata']['department']
                    )
                
                # Extract and create keyword nodes (enhanced keyword extraction)
                words = doc_data['content'].lower().split()
                # Filter significant words (longer than 3 characters, not common words)
                stopwords = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 
                           'this', 'that', 'these', 'those', 'from', 'into', 'during', 'including', 
                           'until', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 
                           'concerning', 'about', 'above', 'across', 'after', 'along', 'around', 
                           'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 
                           'down', 'inside', 'outside', 'over', 'through', 'under', 'within', 'without',
                           'yang', 'dan', 'atau', 'dengan', 'pada', 'untuk', 'dari', 'dalam', 'adalah',
                           'ini', 'itu', 'akan', 'telah', 'sudah', 'dapat', 'bisa', 'harus', 'juga',
                           'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'delapan', 'sembilan', 'sepuluh'}
                
                keywords = [word.strip('.,!?";()[]{}:-') for word in words 
                           if len(word) > 3 and word.lower() not in stopwords]
                
                # Get unique keywords and their frequency
                keyword_freq = {}
                for keyword in keywords:
                    if keyword.isalpha():  # Only alphabetic words
                        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
                
                # Take top 15 most frequent keywords
                top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:15]
                
                for keyword, frequency in top_keywords:
                    session.run("""
                        MERGE (k:Keyword {word: $keyword})
                        MERGE (d:Document {full_path: $full_path})
                        MERGE (d)-[r:CONTAINS_KEYWORD]->(k)
                        SET r.frequency = $frequency
                    """, 
                    keyword=keyword,
                    full_path=doc_data['full_path'],
                    frequency=frequency
                    )
            
            # Create summary statistics
            result = session.run("""
                MATCH (d:Document)
                OPTIONAL MATCH (e:Employee)
                OPTIONAL MATCH (dept:Department)
                OPTIONAL MATCH (k:Keyword)
                RETURN 
                    count(DISTINCT d) as total_documents, 
                    count(DISTINCT e) as total_employees,
                    count(DISTINCT dept) as total_departments,
                    count(DISTINCT k) as total_keywords,
                    sum(d.pages) as total_pages,
                    sum(d.file_size) as total_size,
                    avg(d.content_length) as avg_content_length
            """)
            
            stats = result.single()
            logging.info("=== Data Loading Summary ===")
            logging.info(f"Documents: {stats['total_documents']}")
            logging.info(f"Employees: {stats['total_employees']}")
            logging.info(f"Departments: {stats['total_departments']}")
            logging.info(f"Keywords: {stats['total_keywords']}")
            logging.info(f"Total pages: {stats['total_pages']}")
            logging.info(f"Total size: {stats['total_size']} bytes")
            logging.info(f"Average content length: {stats['avg_content_length']:.0f} characters")
            
            # Document type breakdown
            result = session.run("""
                MATCH (d:Document)
                RETURN d.document_type as doc_type, count(d) as count
                ORDER BY count DESC
            """)
            
            logging.info("Document types:")
            for record in result:
                logging.info(f"  {record['doc_type']}: {record['count']} documents")
            
            # SK Dates breakdown
            result = session.run("""
                MATCH (sd:SKDate)
                RETURN sd.year as year, count(sd) as count
                ORDER BY year DESC
            """)
            
            logging.info("SK Dates by year:")
            for record in result:
                logging.info(f"  {record['year']}: {record['count']} SK dates")
            
        driver.close()
        logging.info("Neo4j connection closed successfully")
        
    except Exception as e:
        logging.error(f"Error loading data to Neo4j: {e}")
        raise

def verify_neo4j_data(**context):
    """Verify data was loaded correctly to Neo4j with comprehensive analysis"""
    from neo4j import GraphDatabase
    import os
    
    # Get Neo4j connection details from environment variables
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', '12345!@#$%')
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Overall statistics
            result = session.run("""
                MATCH (d:Document)
                OPTIONAL MATCH (e:Employee)
                OPTIONAL MATCH (dept:Department)
                OPTIONAL MATCH (k:Keyword)
                OPTIONAL MATCH (sd:SKDate)
                RETURN 
                    count(DISTINCT d) as doc_count,
                    count(DISTINCT e) as emp_count,
                    count(DISTINCT dept) as dept_count,
                    count(DISTINCT k) as keyword_count,
                    count(DISTINCT sd) as sk_date_count
            """)
            
            stats = result.single()
            
            logging.info("=== Comprehensive Neo4j Data Verification ===")
            logging.info(f"Documents: {stats['doc_count']}")
            logging.info(f"Employees: {stats['emp_count']}")
            logging.info(f"Departments: {stats['dept_count']}")
            logging.info(f"Keywords: {stats['keyword_count']}")
            logging.info(f"SK Dates: {stats['sk_date_count']}")
            
            # Document type breakdown
            result = session.run("""
                MATCH (d:Document)
                RETURN d.document_type as doc_type, count(d) as count
                ORDER BY count DESC
            """)
            
            logging.info("Document types:")
            for record in result:
                logging.info(f"  {record['doc_type']}: {record['count']} documents")
            
            # Department analysis
            result = session.run("""
                MATCH (dept:Department)
                OPTIONAL MATCH (e:Employee)-[:WORKS_IN]->(dept)
                OPTIONAL MATCH (d:Document)-[:BELONGS_TO]->(dept)
                RETURN dept.name as dept_name, 
                       count(DISTINCT e) as employee_count,
                       count(DISTINCT d) as document_count
                ORDER BY employee_count DESC
                LIMIT 10
            """)
            
            logging.info("Top departments by employee count:")
            for record in result:
                logging.info(f"  {record['dept_name']}: {record['employee_count']} employees, {record['document_count']} documents")
            
            # Employee-Document relationships
            result = session.run("""
                MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
                RETURN count(*) as emp_doc_relations
            """)
            
            emp_doc_relations = result.single()['emp_doc_relations']
            logging.info(f"Employee-Document relationships: {emp_doc_relations}")
            
            # Sample employee data with SK dates
            result = session.run("""
                MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
                OPTIONAL MATCH (e)-[:APPOINTED_ON]->(sd:SKDate)
                RETURN e.name, e.document_type, e.department, d.filename, sd.formatted_date as sk_date
                LIMIT 5
            """)
            
            logging.info("Sample employee-document relationships with SK dates:")
            for record in result:
                sk_date = record['sk_date'] if record['sk_date'] else 'No date found'
                logging.info(f"  {record['e.name']} ({record['e.document_type']}) in {record['e.department']} -> {record['d.filename']} [SK: {sk_date}]")
            
            # SK Dates analysis
            result = session.run("""
                MATCH (sd:SKDate)
                OPTIONAL MATCH (e:Employee)-[:APPOINTED_ON]->(sd)
                OPTIONAL MATCH (d:Document)-[:ISSUED_ON]->(sd)
                RETURN sd.formatted_date, sd.raw_date, count(DISTINCT e) as employee_count, count(DISTINCT d) as document_count
                ORDER BY sd.formatted_date DESC
                LIMIT 10
            """)
            
            logging.info("Recent SK dates with associated documents and employees:")
            for record in result:
                logging.info(f"  {record['sd.formatted_date']} ({record['sd.raw_date']}): {record['employee_count']} employees, {record['document_count']} documents")
            
            # Top keywords analysis
            result = session.run("""
                MATCH (k:Keyword)<-[r:CONTAINS_KEYWORD]-(d:Document)
                RETURN k.word, count(d) as doc_count, sum(r.frequency) as total_frequency
                ORDER BY total_frequency DESC
                LIMIT 8
            """)
            
            logging.info("Top keywords across all documents:")
            for record in result:
                logging.info(f"  '{record['k.word']}': appears {record['total_frequency']} times in {record['doc_count']} documents")
            
            # Document extraction methods
            result = session.run("""
                MATCH (d:Document)
                RETURN d.extraction_method as method, count(d) as count
                ORDER BY count DESC
            """)
            
            logging.info("Extraction methods used:")
            for record in result:
                logging.info(f"  {record['method']}: {record['count']} documents")
            
            # Check for any processing errors
            result = session.run("""
                MATCH (d:Document)
                WHERE d.content_length < 50
                RETURN count(d) as short_content_docs
            """)
            
            short_docs = result.single()['short_content_docs']
            if short_docs > 0:
                logging.warning(f"Found {short_docs} documents with very short content (< 50 chars)")
            
            # Relationship summary (using fallback since APOC is not available)
            logging.info("Relationship counts:")
            result = session.run("MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count ORDER BY count DESC")
            for record in result:
                logging.info(f"  {record['rel_type']}: {record['count']} relationships")
        
        driver.close()
        
        if stats['doc_count'] > 0:
            logging.info("✅ Comprehensive data verification successful!")
            logging.info(f"Total graph elements: {stats['doc_count'] + stats['emp_count'] + stats['dept_count'] + stats['keyword_count'] + stats['sk_date_count']} nodes")
            return True
        else:
            logging.warning("⚠️ No documents found in Neo4j")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error verifying Neo4j data: {e}")
        raise

# Create DAG
dag = DAG(
    'pdf_to_neo4j_pipeline',
    default_args=default_args,
    description='Pipeline to extract text from PDFs and load to Neo4j',
    schedule_interval=timedelta(hours=6),  # Run every 6 hours
    catchup=False,
    tags=['pdf', 'neo4j', 'etl'],
)

# Test Neo4j connection
test_connection = PythonOperator(
    task_id='test_neo4j_connection',
    python_callable=lambda: logging.info("Testing Neo4j connection..."),
    dag=dag,
)

# Extract text from PDFs
extract_task = PythonOperator(
    task_id='extract_pdf_text',
    python_callable=extract_pdf_text,
    dag=dag,
)

# Load data to Neo4j
load_task = PythonOperator(
    task_id='load_to_neo4j',
    python_callable=load_to_neo4j,
    dag=dag,
)

# Verify loaded data
verify_task = PythonOperator(
    task_id='verify_neo4j_data',
    python_callable=verify_neo4j_data,
    dag=dag,
)

# Set task dependencies
test_connection >> extract_task >> load_task >> verify_task