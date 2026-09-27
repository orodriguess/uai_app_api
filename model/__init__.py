from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Entidades do modelo, importadas para registro no metadata
from model.base import Base
from model.evento_estoque import EventoEstoque
from model.taxa_consumo import TaxaConsumo

db_path = "database/"
# Cria o diretório do banco, caso não exista
if not os.path.exists(db_path):
   os.makedirs(db_path)

# URL de acesso ao banco SQLite local
db_url = 'sqlite:///%s/db.sqlite3' % db_path

# Engine de conexão com o banco
engine = create_engine(db_url, echo=False)

# Fábrica de sessões vinculada à engine
Session = sessionmaker(bind=engine)

# Cria o banco, caso não exista
if not database_exists(engine.url):
    create_database(engine.url)

# Cria as tabelas ausentes
Base.metadata.create_all(engine)
