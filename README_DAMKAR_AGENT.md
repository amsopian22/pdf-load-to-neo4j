# Damkar SK Agentic AI System

Sistem AI yang dapat berinteraksi dengan database Neo4j "damkar-sk" untuk menganalisis data Surat Keputusan (SK) Dinas Pemadam Kebakaran Kota Samarinda.

## 🎯 Fitur Utama

- **Natural Language Interface**: Query menggunakan bahasa Indonesia
- **Intelligent Query Processing**: Konversi otomatis ke Cypher query
- **Interactive Mode**: Mode interaktif dengan prompt yang user-friendly
- **Pre-built Templates**: Template query siap pakai untuk berbagai keperluan
- **Real-time Analysis**: Analisis data secara real-time
- **Comprehensive Statistics**: Statistik lengkap pegawai dan dokumen SK

## 🚀 Quick Start

### 1. Persiapan Environment

```bash
# Pastikan Neo4j sudah running
# Set environment variables (optional)
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="12345!@#$%"
export NEO4J_DATABASE="damkar-sk"
```

### 2. Install Dependencies

```bash
pip install neo4j
```

### 3. Test Connection

```bash
python test_damkar_agent.py
```

### 4. Run Interactive Mode

```bash
python damkar_sk_agent.py
```

## 💬 Contoh Query

### Natural Language Queries

```
cari SABARUDDIN                    # Mencari pegawai bernama SABARUDDIN
berapa jumlah pegawai              # Menghitung jumlah pegawai
daftar pegawai PNS                 # Menampilkan semua pegawai PNS
daftar pegawai PPPK                # Menampilkan semua pegawai PPPK
statistik pegawai                  # Menampilkan statistik pegawai
overview                           # Menampilkan ringkasan database
help                               # Menampilkan bantuan
```

### Programmatic Usage

```python
from damkar_sk_agent import DamkarSKAgent

# Initialize agent
agent = DamkarSKAgent()

# Process natural language query
result = agent.process_natural_language_query("cari SABARUDDIN")
print(agent.format_results(result))

# Execute custom Cypher query
custom_query = '''
    MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
    WHERE p.work_unit CONTAINS $unit
    RETURN p.name as nama, p.employee_id as nip
'''
result = agent.execute_query(custom_query, {'unit': 'UMUM'})
print(agent.format_results(result))

# Close connection
agent.close()
```

## 📊 Query Templates

### Employee Queries
- `find_employee`: Mencari pegawai berdasarkan nama
- `list_employees`: Menampilkan daftar pegawai berdasarkan jenis SK
- `search_by_position`: Mencari pegawai berdasarkan jabatan
- `search_by_unit`: Mencari pegawai berdasarkan unit kerja

### Statistics Queries
- `employee_stats`: Statistik pegawai berdasarkan jenis SK
- `unit_stats`: Statistik pegawai per unit kerja
- `database_overview`: Ringkasan lengkap database

### Document Queries
- `document_info`: Informasi dokumen berdasarkan nomor SK

## 🔧 Configuration

### Environment Variables

```bash
NEO4J_URI=neo4j://localhost:7687      # Neo4j connection URI
NEO4J_USER=neo4j                      # Neo4j username
NEO4J_PASSWORD=12345!@#$%             # Neo4j password
NEO4J_DATABASE=damkar-sk              # Target database name
```

### Database Schema

```
Nodes:
- Person: {name, employee_id, position, work_unit, institution, ...}
- Document: {document_type, document_number, issue_date, file_path, ...}

Relationships:
- Person-[:HAS_DOCUMENT]->Document
```

## 🎮 Interactive Mode

```bash
$ python damkar_sk_agent.py

🤖 Damkar SK Agent - Interactive Mode
==================================================
Ketik 'help' untuk melihat contoh query
Ketik 'exit' untuk keluar
==================================================

💬 Query: cari SABARUDDIN

📊 Found 1 records
⏱️ Execution time: 0.05s
--------------------------------------------------

1. nama: SABARUDDIN | nip: 196801011990031005 | jabatan: Kepala Sub Bagian Umum dan Kepegawaian | unit_kerja: SUB BAG UMUM DAN KEPEGAWAIAN | file_sk: /opt/airflow/data/SK PNS/SUB BAG UMUM DAN KEPEGAWAIAN/01 SABARUDDIN.pdf
```

## 🧪 Testing

### Basic Test
```bash
python test_damkar_agent.py
```

### Custom Testing
```python
from damkar_sk_agent import DamkarSKAgent

# Test connection
agent = DamkarSKAgent()
result = agent.process_natural_language_query("overview")
print(agent.format_results(result))
agent.close()
```

## 📈 Advanced Usage

### Custom Query Templates

```python
# Add custom query template
agent.query_templates['custom_query'] = '''
    MATCH (p:Person)-[:HAS_DOCUMENT]->(d:Document)
    WHERE d.issue_date > $date
    RETURN p.name, d.document_number, d.issue_date
'''

# Execute custom template
result = agent.execute_query(
    agent.query_templates['custom_query'],
    {'date': '2024-01-01'}
)
```

### Batch Processing

```python
queries = [
    "berapa jumlah pegawai",
    "daftar pegawai PNS",
    "statistik unit kerja"
]

for query in queries:
    result = agent.process_natural_language_query(query)
    print(f"Query: {query}")
    print(agent.format_results(result))
    print("-" * 50)
```

## 🚨 Error Handling

```python
try:
    agent = DamkarSKAgent()
    result = agent.process_natural_language_query("invalid query")
    print(agent.format_results(result))
except Exception as e:
    print(f"Error: {e}")
finally:
    agent.close()
```

## 📚 Dependencies

- **neo4j**: Neo4j Python driver
- **dataclasses**: For data structures (built-in Python 3.7+)
- **logging**: For logging (built-in)
- **re**: For regular expressions (built-in)
- **json**: For JSON handling (built-in)
- **datetime**: For timestamps (built-in)

## 🔮 Future Enhancements

- [ ] Machine Learning untuk query prediction
- [ ] Voice interface dengan speech-to-text
- [ ] Export results ke Excel/PDF
- [ ] Dashboard web interface
- [ ] Real-time notifications
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

Jika ada pertanyaan atau masalah:
1. Check troubleshooting section
2. Review logs untuk error details
3. Verify Neo4j connection dan database setup
4. Contact system administrator

---

**Damkar SK Agent** - Intelligent database querying for Samarinda Fire Department SK documents.