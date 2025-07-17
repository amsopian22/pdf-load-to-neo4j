from datetime import datetime, timedelta
import os
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_and_load_to_neo4j(**context):
    """Extract sample PDF data and load to Neo4j"""
    from neo4j import GraphDatabase
    import os
    
    # Get Neo4j connection details from environment
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', '12345!@#$%')
    
    logging.info(f"Connecting to Neo4j at {neo4j_uri}")
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Test connection
            result = session.run("RETURN 'Connection successful' as message")
            record = result.single()
            logging.info(f"✅ Neo4j connection: {record['message']}")
            
            # Create sample document data (simulating PDF extraction)
            sample_documents = [
                {
                    'filename': 'SABARUDDIN_SK.pdf',
                    'content': 'KEPUTUSAN KEPALA DINAS PEMADAM KEBAKARAN Nomor: 01/2024 Tentang Pengangkatan SABARUDDIN sebagai Pegawai Negeri Sipil di Sub Bagian Umum dan Kepegawaian',
                    'pages': 2,
                    'file_size': 2048,
                    'extraction_method': 'sample_data'
                },
                {
                    'filename': 'YUDI_HARSOYO_SK.pdf', 
                    'content': 'SURAT KEPUTUSAN PENGANGKATAN YUDI HARSOYO Nomor: 02/2024 Sebagai Staf Sub Bagian Umum dan Kepegawaian Dinas Pemadam Kebakaran',
                    'pages': 1,
                    'file_size': 1536,
                    'extraction_method': 'sample_data'
                },
                {
                    'filename': 'RUSDIANA_SK.pdf',
                    'content': 'SURAT KEPUTUSAN PENETAPAN RUSDIANA Nomor: 03/2024 Sebagai Pegawai Negeri Sipil Sub Bagian Umum dan Kepegawaian Dinas Pemadam Kebakaran',
                    'pages': 1,
                    'file_size': 1792,
                    'extraction_method': 'sample_data'
                }
            ]
            
            # Create constraints and indexes
            session.run("""
                CREATE CONSTRAINT document_filename_unique IF NOT EXISTS 
                FOR (d:Document) REQUIRE d.filename IS UNIQUE
            """)
            
            session.run("""
                CREATE INDEX document_content_fulltext IF NOT EXISTS 
                FOR (d:Document) ON (d.content)
            """)
            
            # Load documents
            for doc_data in sample_documents:
                logging.info(f"Loading document: {doc_data['filename']}")
                
                # Create document node
                session.run("""
                    MERGE (d:Document {filename: $filename})
                    SET d.content = $content,
                        d.pages = $pages,
                        d.file_size = $file_size,
                        d.extraction_method = $extraction_method,
                        d.loaded_at = datetime(),
                        d.content_length = size($content)
                """, **doc_data)
                
                # Extract keywords (simple approach)
                words = doc_data['content'].lower().split()
                keywords = [word.strip('.,!?";()[]{}') for word in words if len(word) > 3]
                
                # Count word frequency
                keyword_freq = {}
                for keyword in keywords:
                    if keyword.isalpha():
                        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
                
                # Take top keywords
                for keyword, frequency in list(keyword_freq.items())[:10]:
                    session.run("""
                        MERGE (k:Keyword {word: $keyword})
                        MERGE (d:Document {filename: $filename})
                        MERGE (d)-[r:CONTAINS_KEYWORD]->(k)
                        SET r.frequency = $frequency
                    """, keyword=keyword, filename=doc_data['filename'], frequency=frequency)
            
            # Create employee nodes from document content
            employees = [
                {'name': 'SABARUDDIN', 'position': 'Sub Bagian Umum dan Kepegawaian', 'sk_number': '01/2024'},
                {'name': 'YUDI HARSOYO', 'position': 'Sub Bagian Umum dan Kepegawaian', 'sk_number': '02/2024'},
                {'name': 'RUSDIANA', 'position': 'Sub Bagian Umum dan Kepegawaian', 'sk_number': '03/2024'}
            ]
            
            for emp in employees:
                session.run("""
                    MERGE (e:Employee {name: $name})
                    SET e.position = $position,
                        e.sk_number = $sk_number,
                        e.department = 'Dinas Pemadam Kebakaran'
                """, **emp)
                
                # Link employee to their document
                doc_filename = f"{emp['name']}_SK.pdf"
                session.run("""
                    MATCH (e:Employee {name: $name})
                    MATCH (d:Document {filename: $filename})
                    MERGE (e)-[:HAS_DOCUMENT]->(d)
                """, name=emp['name'], filename=doc_filename)
            
            # Get statistics
            result = session.run("""
                MATCH (d:Document)
                RETURN count(d) as total_documents, 
                       sum(d.pages) as total_pages,
                       sum(d.file_size) as total_size
            """)
            
            stats = result.single()
            logging.info(f"Successfully loaded {stats['total_documents']} documents to Neo4j")
            logging.info(f"Total pages: {stats['total_pages']}, Total size: {stats['total_size']} bytes")
            
            # Verify employees
            result = session.run("MATCH (e:Employee) RETURN count(e) as employee_count")
            emp_count = result.single()['employee_count']
            logging.info(f"Created {emp_count} employee nodes")
            
        driver.close()
        return True
        
    except Exception as e:
        logging.error(f"Error: {e}")
        raise

def verify_neo4j_data(**context):
    """Verify data was loaded correctly to Neo4j"""
    from neo4j import GraphDatabase
    import os
    
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', '12345!@#$%')
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Check counts
            doc_result = session.run("MATCH (d:Document) RETURN count(d) as count")
            doc_count = doc_result.single()['count']
            
            emp_result = session.run("MATCH (e:Employee) RETURN count(e) as count")
            emp_count = emp_result.single()['count']
            
            kw_result = session.run("MATCH (k:Keyword) RETURN count(k) as count")
            kw_count = kw_result.single()['count']
            
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_result.single()['count']
            
            logging.info("=== Neo4j Data Verification ===")
            logging.info(f"Documents: {doc_count}")
            logging.info(f"Employees: {emp_count}")
            logging.info(f"Keywords: {kw_count}")
            logging.info(f"Relationships: {rel_count}")
            
            # Sample query
            result = session.run("""
                MATCH (e:Employee)-[:HAS_DOCUMENT]->(d:Document)
                RETURN e.name, e.position, d.filename, d.content_length
                LIMIT 3
            """)
            
            logging.info("Sample employee-document relationships:")
            for record in result:
                logging.info(f"  {record['e.name']} -> {record['d.filename']} ({record['d.content_length']} chars)")
        
        driver.close()
        
        if doc_count > 0 and emp_count > 0:
            logging.info("✅ Data verification successful!")
            return True
        else:
            logging.warning("⚠️ No data found in Neo4j")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error verifying Neo4j data: {e}")
        raise

# Create DAG
dag = DAG(
    'pdf_to_neo4j_simple',
    default_args=default_args,
    description='Simple PDF to Neo4j pipeline with sample data',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['pdf', 'neo4j', 'test'],
)

# Tasks
extract_load_task = PythonOperator(
    task_id='extract_and_load_to_neo4j',
    python_callable=extract_and_load_to_neo4j,
    dag=dag,
)

verify_task = PythonOperator(
    task_id='verify_neo4j_data',
    python_callable=verify_neo4j_data,
    dag=dag,
)

# Set dependencies
extract_load_task >> verify_task