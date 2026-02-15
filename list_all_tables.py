import psycopg2
conn = psycopg2.connect(dbname='db_tds_new', user='tsdb_django_d4j7g9', password='DjangoTS2025TimeSeries', host='localhost', port=5442)
cursor = conn.cursor()
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;")
print("Todas as tabelas no banco:")
for t in cursor.fetchall():
    print(f"  - {t[0]}")
conn.close()
