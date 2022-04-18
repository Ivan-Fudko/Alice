import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Station(SqlAlchemyBase):
    __tablename__ = 'stations'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    system_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('systems.id'))
    mart = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    refueling = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    reload = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    repair = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
    range_to_system = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    system = orm.relation("System")

