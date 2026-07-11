from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Locale(Base):
    __tablename__ = "locales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iso_code: Mapped[str] = mapped_column(String(4), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    centroid_lat: Mapped[float | None] = mapped_column(Float)
    centroid_lng: Mapped[float | None] = mapped_column(Float)
    area_sq_km: Mapped[float | None] = mapped_column(Float)

    districts: Mapped[list["District"]] = relationship(back_populates="locale")


class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_district_code: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    locale_id: Mapped[int] = mapped_column(ForeignKey("locales.id"), nullable=False)

    locale: Mapped[Locale] = relationship(back_populates="districts")


class Measure(Base):
    __tablename__ = "measures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    higher_is_better: Mapped[bool | None] = mapped_column(Boolean)
    is_derived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class FactValue(Base):
    __tablename__ = "fact_values"
    __table_args__ = (
        UniqueConstraint("locale_id", "measure_id", "year", name="uq_fact_values_locale_measure_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    locale_id: Mapped[int] = mapped_column(ForeignKey("locales.id"), nullable=False, index=True)
    measure_id: Mapped[int] = mapped_column(ForeignKey("measures.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)


class StateAdjacency(Base):
    __tablename__ = "state_adjacency"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_code: Mapped[str] = mapped_column(String(4), index=True, nullable=False)
    neighbor_code: Mapped[str] = mapped_column(String(4), nullable=False)
    shared_border_length: Mapped[float] = mapped_column(Float, nullable=False)

