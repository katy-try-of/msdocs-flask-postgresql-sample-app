from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import validates
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app import db


class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    street_address = Column(String(50))
    description = Column(String(250))

    def __str__(self):
        return self.name

class Review(db.Model):
    __tablename__ = 'review'
    id = Column(Integer, primary_key=True)
    restaurant = Column(Integer, ForeignKey('restaurant.id', ondelete="CASCADE"))
    user_name = Column(String(30))
    rating = Column(Integer)
    review_text = Column(String(500))
    review_date = Column(DateTime)

    @validates('rating')
    def validate_rating(self, key, value):
        assert value is None or (1 <= value <= 5)
        return value

    def __str__(self):
        return f"{self.user_name}: {self.review_date:%x}"


class PixelCount(db.Model):
    __tablename__ = "pixel_counts"

    id        = db.Column(db.Integer, primary_key=True)
    usuario   = db.Column(db.String(128), nullable=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Fecha y hora en UTC en que se subieron los datos"
    )
    fichero   = db.Column(db.String(256), nullable=False)
    pixeles   = db.Column(
        JSONB,
        nullable=False,
        doc="""
        Mapa de conteos por color,
        p. ej. {"rojo": 1234, "verde": 567, "azul": 890}
        """
    )

    def __repr__(self):
        return (
            f"<PixelCount id={self.id} usuario={self.usuario!r} "
            f"timestamp={self.timestamp.isoformat()} fichero={self.fichero!r} "
            f"pixeles={self.pixeles}>"
        )
