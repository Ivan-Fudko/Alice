import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class System(SqlAlchemyBase):
    __tablename__ = 'systems'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    cord_x = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    cord_y = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    cord_z = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    range_to_system = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    stations = orm.relation("Station", back_populates='system')
