#!/usr/bin/env python3
"""
Damkar SK Agentic AI System
===========================

An intelligent agent that can query and analyze SK (Surat Keputusan) data 
from Neo4j database using natural language interface.

Features:
- Natural language query processing
- Intelligent Cypher query generation
- Data analysis and insights
- Interactive conversation interface
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Data structure for query results"""
    query: str
    results: List[Dict[str, Any]]
    summary: str
    execution_time: float

class DamkarSKAgent:
    """
    Agentic AI system for interacting with Damkar SK database
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None, database: str = "damkar-sk"):
        """Initialize the agent with Neo4j connection"""
        self.uri = uri or os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', '12345!@#$%')
        self.database = database
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Test connection
        self._test_connection()
        
        # Initialize query templates
        self._init_query_templates()
        
        logger.info(f"Damkar SK Agent initialized and connected to database: {self.database}")
    
    def _test_connection(self):
        """Test Neo4j connection"""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
                logger.info("✅ Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    def _init_query_templates(self):
        """Initialize predefined query templates"""
        self.query_templates = {
            # Employee queries - using actual schema
            'find_employee': '''
                MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
                WHERE p.name CONTAINS UPPER($name)
                RETURN p.name as nama, p.employee_id as nip, p.institution as institusi,
                       p.work_unit as unit_kerja, d.file_path as file_sk,
                       d.document_type as jenis_sk
            ''',
            
            'list_employees': '''
                MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
                WHERE d.document_type = $doc_type
                RETURN p.name as nama, p.employee_id as nip, p.institution as institusi,
                       p.work_unit as unit_kerja, d.file_path as file_sk,
                       d.document_type as jenis_sk
                ORDER BY p.name
            ''',
            
            # Statistics queries
            'employee_stats': '''
                MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
                WITH d.document_type as jenis_sk, count(p) as jumlah
                RETURN jenis_sk, jumlah
                ORDER BY jumlah DESC
            ''',
            
            'unit_stats': '''
                MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
                WITH p.work_unit as unit_kerja, count(p) as jumlah_pegawai
                RETURN unit_kerja, jumlah_pegawai
                ORDER BY jumlah_pegawai DESC
            ''',
            
            # Search queries
            'search_by_unit': '''
                MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
                WHERE p.work_unit CONTAINS $unit
                RETURN p.name as nama, p.employee_id as nip, p.institution as institusi,
                       p.work_unit as unit_kerja, d.document_type as jenis_sk
                ORDER BY p.name
            ''',
            
            # Document queries
            'all_employees': '''
                MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
                RETURN p.name as nama, p.employee_id as nip, p.institution as institusi,
                       p.work_unit as unit_kerja, d.file_path as file_sk,
                       d.document_type as jenis_sk
                ORDER BY p.name
            ''',
            
            # Full database overview
            'database_overview': '''
                MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
                RETURN count(DISTINCT p) as total_pegawai,
                       count(DISTINCT d) as total_dokumen,
                       count(DISTINCT p.work_unit) as total_unit_kerja,
                       collect(DISTINCT d.document_type) as jenis_sk
            '''
        }
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> QueryResult:
        """Execute a Cypher query and return results"""
        start_time = datetime.now()
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                records = [record.data() for record in result]
                
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                return QueryResult(
                    query=query,
                    results=records,
                    summary=f"Found {len(records)} records",
                    execution_time=execution_time
                )
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                query=query,
                results=[],
                summary=f"Query failed: {str(e)}",
                execution_time=0
            )
    
    def process_natural_language_query(self, user_input: str) -> QueryResult:
        """Process natural language input and convert to appropriate query"""
        user_input = user_input.lower().strip()
        
        # Pattern matching for different query types
        if "cari" in user_input or "find" in user_input:
            return self._handle_search_query(user_input)
        elif "berapa" in user_input or "count" in user_input or "jumlah" in user_input:
            return self._handle_count_query(user_input)
        elif "list" in user_input or "daftar" in user_input or "semua" in user_input:
            return self._handle_list_query(user_input)
        elif "statistik" in user_input or "stats" in user_input or "analisis" in user_input:
            return self._handle_stats_query(user_input)
        elif "overview" in user_input or "ringkasan" in user_input or "gambaran" in user_input:
            return self._handle_overview_query()
        else:
            return self._handle_general_query(user_input)
    
    def _handle_search_query(self, user_input: str) -> QueryResult:
        """Handle search queries"""
        # Extract name from input
        name_match = re.search(r'cari\s+(.+)', user_input)
        if name_match:
            name = name_match.group(1).strip()
            return self.execute_query(
                self.query_templates['find_employee'],
                {'name': name.upper()}
            )
        
        return QueryResult("", [], "Could not understand search query", 0)
    
    def _handle_count_query(self, user_input: str) -> QueryResult:
        """Handle counting queries"""
        if "pegawai" in user_input or "karyawan" in user_input or "employee" in user_input:
            return self.execute_query(self.query_templates['employee_stats'])
        elif "unit" in user_input or "bagian" in user_input:
            return self.execute_query(self.query_templates['unit_stats'])
        else:
            return self.execute_query(self.query_templates['database_overview'])
    
    def _handle_list_query(self, user_input: str) -> QueryResult:
        """Handle list queries"""
        if "pns" in user_input:
            return self.execute_query(
                self.query_templates['list_employees'],
                {'doc_type': 'PNS'}
            )
        elif "pppk" in user_input:
            return self.execute_query(
                self.query_templates['list_employees'],
                {'doc_type': 'PPPK'}
            )
        elif "semua" in user_input or "all" in user_input:
            return self.execute_query(self.query_templates['all_employees'])
        else:
            return self.execute_query(
                self.query_templates['list_employees'],
                {'doc_type': 'PNS'}
            )
    
    def _handle_stats_query(self, user_input: str) -> QueryResult:
        """Handle statistics queries"""
        return self.execute_query(self.query_templates['employee_stats'])
    
    def _handle_overview_query(self) -> QueryResult:
        """Handle overview queries"""
        return self.execute_query(self.query_templates['database_overview'])
    
    def _handle_general_query(self, user_input: str) -> QueryResult:
        """Handle general queries"""
        # Default to overview
        return self.execute_query(self.query_templates['database_overview'])
    
    def format_results(self, query_result: QueryResult) -> str:
        """Format query results for display"""
        if not query_result.results:
            return f"❌ {query_result.summary}"
        
        output = []
        output.append(f"📊 {query_result.summary}")
        output.append(f"⏱️ Execution time: {query_result.execution_time:.2f}s")
        output.append("-" * 50)
        
        for i, record in enumerate(query_result.results, 1):
            output.append(f"\n{i}. {self._format_record(record)}")
        
        return "\n".join(output)
    
    def _format_record(self, record: Dict[str, Any]) -> str:
        """Format a single record for display"""
        formatted = []
        for key, value in record.items():
            if value is not None:
                formatted.append(f"{key}: {value}")
        return " | ".join(formatted)
    
    def interactive_mode(self):
        """Start interactive mode"""
        print("🤖 Damkar SK Agent - Interactive Mode")
        print("=" * 50)
        print("Ketik 'help' untuk melihat contoh query")
        print("Ketik 'exit' untuk keluar")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 Query: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'keluar']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                if not user_input:
                    continue
                
                result = self.process_natural_language_query(user_input)
                print(f"\n{self.format_results(result)}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
🔍 Contoh Query:
- "cari SABARUDDIN" - Mencari pegawai bernama SABARUDDIN  
- "berapa jumlah pegawai" - Menghitung jumlah pegawai
- "daftar pegawai PNS" - Menampilkan semua pegawai PNS
- "daftar pegawai PPPK" - Menampilkan semua pegawai PPPK
- "semua pegawai" - Menampilkan semua pegawai
- "statistik pegawai" - Menampilkan statistik pegawai
- "statistik unit kerja" - Menampilkan statistik per unit kerja
- "overview" - Menampilkan ringkasan database

📚 Query Templates Available:
- find_employee: Cari pegawai berdasarkan nama
- list_employees: Daftar pegawai berdasarkan jenis SK
- all_employees: Semua pegawai  
- employee_stats: Statistik pegawai berdasarkan jenis SK
- unit_stats: Statistik pegawai per unit kerja
- search_by_unit: Cari pegawai berdasarkan unit kerja
- database_overview: Ringkasan lengkap database

💡 Tips: Gunakan nama HURUF BESAR untuk pencarian yang lebih akurat.
        """
        print(help_text)
    
    def close(self):
        """Close database connection"""
        self.driver.close()
        logger.info("Connection closed")

def main():
    """Main function to run the agent"""
    try:
        # Initialize agent
        agent = DamkarSKAgent()
        
        # Start interactive mode
        agent.interactive_mode()
        
    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
    finally:
        if 'agent' in locals():
            agent.close()

if __name__ == "__main__":
    main()