#!/usr/bin/env python3
"""
Test Script for Damkar SK Agent
===============================

This script demonstrates how to use the Damkar SK Agent with various examples.
"""

import sys
import os
from damkar_sk_agent import DamkarSKAgent

def test_basic_queries():
    """Test basic query functionality"""
    print("🧪 Testing Basic Queries")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = DamkarSKAgent()
        
        # Test 1: Database overview
        print("\n1️⃣ Testing Database Overview:")
        result = agent.process_natural_language_query("overview")
        print(agent.format_results(result))
        
        # Test 2: Employee statistics
        print("\n2️⃣ Testing Employee Statistics:")
        result = agent.process_natural_language_query("berapa jumlah pegawai")
        print(agent.format_results(result))
        
        # Test 3: List PNS employees
        print("\n3️⃣ Testing List PNS Employees:")
        result = agent.process_natural_language_query("daftar pegawai PNS")
        print(agent.format_results(result))
        
        # Test 4: Search specific employee
        print("\n4️⃣ Testing Search Employee:")
        result = agent.process_natural_language_query("cari SABARUDDIN")
        print(agent.format_results(result))
        
        # Test 5: Unit statistics
        print("\n5️⃣ Testing Unit Statistics:")
        result = agent.process_natural_language_query("statistik unit kerja")
        print(agent.format_results(result))
        
        agent.close()
        print("\n✅ All basic tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_advanced_queries():
    """Test advanced query functionality"""
    print("\n🚀 Testing Advanced Queries")
    print("=" * 50)
    
    try:
        agent = DamkarSKAgent()
        
        # Test custom Cypher query
        print("\n1️⃣ Testing Custom Cypher Query:")
        custom_query = '''
            MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
            WHERE d.document_type = 'PNS'
            RETURN p.name as nama, p.work_unit as unit_kerja
            ORDER BY p.name
            LIMIT 5
        '''
        result = agent.execute_query(custom_query)
        print(agent.format_results(result))
        
        # Test query with parameters
        print("\n2️⃣ Testing Query with Parameters:")
        parametrized_query = '''
            MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
            WHERE p.work_unit CONTAINS $unit
            RETURN p.name as nama, p.employee_id as nip, p.position as jabatan
            ORDER BY p.name
        '''
        result = agent.execute_query(parametrized_query, {'unit': 'UMUM'})
        print(agent.format_results(result))
        
        agent.close()
        print("\n✅ Advanced tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Advanced test failed: {e}")

def demo_interactive_examples():
    """Show examples of interactive queries"""
    print("\n🎯 Interactive Query Examples")
    print("=" * 50)
    
    examples = [
        "cari SABARUDDIN",
        "berapa jumlah pegawai",
        "daftar pegawai PNS",
        "daftar pegawai PPPK", 
        "statistik pegawai",
        "overview",
        "help"
    ]
    
    print("💡 Contoh query yang bisa Anda gunakan:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    
    print("\n📝 Untuk menjalankan interactive mode:")
    print("python damkar_sk_agent.py")

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking Prerequisites")
    print("=" * 50)
    
    # Check if Neo4j is running
    try:
        from neo4j import GraphDatabase
        print("✅ Neo4j driver available")
    except ImportError:
        print("❌ Neo4j driver not installed. Run: pip install neo4j")
        return False
    
    # Check environment variables
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', '12345!@#$%')
    
    print(f"📍 Neo4j URI: {neo4j_uri}")
    print(f"👤 Neo4j User: {neo4j_user}")
    print(f"🔑 Neo4j Password: {'*' * len(neo4j_password)}")
    
    # Test connection
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        with driver.session(database="damkar-sk") as session:
            result = session.run("RETURN 1 as test")
            result.single()
        driver.close()
        print("✅ Neo4j connection successful")
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

def main():
    """Main function"""
    print("🤖 Damkar SK Agent Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please check your Neo4j setup.")
        return
    
    # Run tests
    test_basic_queries()
    test_advanced_queries()
    demo_interactive_examples()
    
    print("\n🎉 Test suite completed!")
    print("\n📚 Next steps:")
    print("1. Run: python damkar_sk_agent.py")
    print("2. Try the interactive mode")
    print("3. Explore different query types")

if __name__ == "__main__":
    main()