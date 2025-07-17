#!/usr/bin/env python3
"""
Example Usage: Damkar SK Agent
==============================

Contoh penggunaan praktis Damkar SK Agent untuk berbagai skenario.
"""

import time
from damkar_sk_agent import DamkarSKAgent

def example_basic_usage():
    """Contoh penggunaan dasar"""
    print("🔥 Contoh Penggunaan Dasar")
    print("=" * 50)
    
    # Initialize agent
    agent = DamkarSKAgent()
    
    # 1. Dapatkan overview database
    print("\n1. Overview Database:")
    result = agent.process_natural_language_query("overview")
    print(agent.format_results(result))
    
    # 2. Cari pegawai spesifik
    print("\n2. Cari Pegawai:")
    result = agent.process_natural_language_query("cari SABARUDDIN")
    print(agent.format_results(result))
    
    # 3. Statistik pegawai
    print("\n3. Statistik Pegawai:")
    result = agent.process_natural_language_query("berapa jumlah pegawai")
    print(agent.format_results(result))
    
    agent.close()

def example_advanced_queries():
    """Contoh query advanced"""
    print("\n🚀 Contoh Query Advanced")
    print("=" * 50)
    
    agent = DamkarSKAgent()
    
    # 1. Query dengan custom Cypher
    print("\n1. Custom Cypher Query:")
    custom_query = '''
        MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
        WHERE d.document_type = $doc_type
        RETURN p.name as nama, 
               p.employee_id as nip,
               p.position as jabatan,
               p.work_unit as unit_kerja
        ORDER BY p.name
        LIMIT 10
    '''
    
    result = agent.execute_query(custom_query, {'doc_type': 'PNS'})
    print(agent.format_results(result))
    
    # 2. Query dengan filtering
    print("\n2. Query dengan Filtering:")
    filter_query = '''
        MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
        WHERE p.work_unit CONTAINS $unit_keyword
        RETURN p.name as nama,
               p.employee_id as nip,
               p.work_unit as unit_kerja
        ORDER BY p.name
    '''
    
    result = agent.execute_query(filter_query, {'unit_keyword': 'UMUM'})
    print(agent.format_results(result))
    
    agent.close()

def example_batch_processing():
    """Contoh batch processing"""
    print("\n📊 Contoh Batch Processing")
    print("=" * 50)
    
    agent = DamkarSKAgent()
    
    # Daftar query yang akan diproses
    queries = [
        "overview",
        "berapa jumlah pegawai",
        "daftar pegawai PNS",
        "statistik pegawai"
    ]
    
    print("Processing multiple queries...")
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 30)
        
        result = agent.process_natural_language_query(query)
        print(agent.format_results(result))
        
        # Small delay between queries
        time.sleep(0.5)
    
    agent.close()

def example_error_handling():
    """Contoh error handling"""
    print("\n⚠️ Contoh Error Handling")
    print("=" * 50)
    
    try:
        agent = DamkarSKAgent()
        
        # Test query yang mungkin error
        print("Testing invalid query...")
        result = agent.process_natural_language_query("invalid nonsense query")
        print(agent.format_results(result))
        
        # Test query yang valid
        print("\nTesting valid query...")
        result = agent.process_natural_language_query("overview")
        print(agent.format_results(result))
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
    finally:
        if 'agent' in locals():
            agent.close()

def example_search_scenarios():
    """Contoh skenario pencarian"""
    print("\n🔍 Contoh Skenario Pencarian")
    print("=" * 50)
    
    agent = DamkarSKAgent()
    
    # Skenario 1: Cari pegawai berdasarkan nama
    print("\n1. Cari Pegawai Berdasarkan Nama:")
    search_queries = [
        "cari SABARUDDIN",
        "cari YUDI",
        "cari RUSDIANA"
    ]
    
    for query in search_queries:
        print(f"\n   {query}:")
        result = agent.process_natural_language_query(query)
        if result.results:
            print(f"   ✅ Found: {result.results[0].get('nama', 'Unknown')}")
        else:
            print("   ❌ Not found")
    
    # Skenario 2: Analisis berdasarkan unit kerja
    print("\n2. Analisis Unit Kerja:")
    result = agent.process_natural_language_query("statistik unit kerja")
    print(agent.format_results(result))
    
    agent.close()

def example_reporting():
    """Contoh untuk reporting"""
    print("\n📈 Contoh Reporting")
    print("=" * 50)
    
    agent = DamkarSKAgent()
    
    # Generate comprehensive report
    report_queries = [
        ("Database Overview", "overview"),
        ("Employee Statistics", "berapa jumlah pegawai"),
        ("Unit Statistics", "statistik unit kerja"),
        ("PNS List", "daftar pegawai PNS"),
        ("PPPK List", "daftar pegawai PPPK")
    ]
    
    print("📋 LAPORAN KOMPREHENSIF DAMKAR SK")
    print("=" * 60)
    print(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    for title, query in report_queries:
        print(f"\n📊 {title.upper()}")
        print("-" * 40)
        
        result = agent.process_natural_language_query(query)
        print(agent.format_results(result))
        
        time.sleep(0.3)
    
    agent.close()

def main():
    """Main function dengan menu"""
    print("🤖 Damkar SK Agent - Example Usage")
    print("=" * 50)
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Advanced Queries", example_advanced_queries),
        ("Batch Processing", example_batch_processing),
        ("Error Handling", example_error_handling),
        ("Search Scenarios", example_search_scenarios),
        ("Reporting", example_reporting)
    ]
    
    print("📚 Available Examples:")
    for i, (title, _) in enumerate(examples, 1):
        print(f"{i}. {title}")
    
    print("\n🎯 Select an example to run:")
    print("Enter number (1-6) or 'all' to run all examples")
    
    try:
        choice = input("Choice: ").strip().lower()
        
        if choice == 'all':
            for title, func in examples:
                print(f"\n🚀 Running: {title}")
                func()
                print("\n" + "="*50)
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            idx = int(choice) - 1
            title, func = examples[idx]
            print(f"\n🚀 Running: {title}")
            func()
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()