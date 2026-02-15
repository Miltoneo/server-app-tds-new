import psycopg2
conn = psycopg2.connect(dbname='db_tds_new', user='tsdb_django_d4j7g9', password='DjangoTS2025TimeSeries', host='localhost', port=5442)
cursor = conn.cursor()
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND (tablename LIKE '%gateway%' OR tablename LIKE '%empresa%' OR tablename = 'pessoa') ORDER BY tablename;")
tables = cursor.fetchall()
if tables:
    print("Tabelas encontradas:")
    for t in tables:
        print(f"  - {t[0]}")
else:
    print("Nenhuma tabela gateway, empresa ou pessoa encontrada.")
    print("\nVerificando se há uma tabela 'tds_new_gateway'...")
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'tds_%';")
    print("\nTabelas tds_*:")
    for t in cursor.fetchall():
        print(f"  - {t[0]}")
conn.close()
