from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres:Remaks124421@db.ovogzuuhnqttehzgjkzj.supabase.co:5432/postgres"
    
engine = create_engine(DATABASE_URL)
