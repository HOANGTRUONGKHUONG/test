from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.setting import DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, \
    DATABASE_CHARSET


# def ORMSession():
#     cs = f"mysql+mysqldb://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}" \
#         f"?charset={DATABASE_CHARSET}"
#     en = create_engine(cs, pool_pre_ping=True)
#     se = sessionmaker(bind=en)()
#     return se

    
def ORMSession_alter():
    cs = f"mysql+mysqldb://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}" \
         f"?charset={DATABASE_CHARSET}"
    en = create_engine(cs, pool_pre_ping=True)
    se = sessionmaker(bind=en)
    session= se()
    # return se
    return session,en