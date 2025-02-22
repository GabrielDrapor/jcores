from models import Base
from db import engine
from sqlalchemy.schema import CreateTable

# Generate DDL
ddl = []
for table in Base.metadata.sorted_tables:
    ddl.extend(str(CreateTable(table).compile(engine)).split(';'))

# Print PostgreSQL-compatible DDL
for statement in ddl:
    if statement.strip():
        print(f"{statement.strip()};")
