"""initial schema

Revision ID: 20260710_0001
Revises:
Create Date: 2026-07-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260710_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "locales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("iso_code", sa.String(length=4), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=True),
        sa.Column("centroid_lng", sa.Float(), nullable=True),
        sa.Column("area_sq_km", sa.Float(), nullable=True),
        sa.UniqueConstraint("iso_code"),
        sa.UniqueConstraint("source_name"),
    )
    op.create_index("ix_locales_iso_code", "locales", ["iso_code"])

    op.create_table(
        "measures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("higher_is_better", sa.Boolean(), nullable=True),
        sa.Column("is_derived", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_measures_code", "measures", ["code"])

    op.create_table(
        "districts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_district_code", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("locale_id", sa.Integer(), sa.ForeignKey("locales.id"), nullable=False),
        sa.UniqueConstraint("source_district_code"),
    )
    op.create_index("ix_districts_source_district_code", "districts", ["source_district_code"])

    op.create_table(
        "fact_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("locale_id", sa.Integer(), sa.ForeignKey("locales.id"), nullable=False),
        sa.Column("measure_id", sa.Integer(), sa.ForeignKey("measures.id"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.UniqueConstraint("locale_id", "measure_id", "year", name="uq_fact_values_locale_measure_year"),
    )
    op.create_index("ix_fact_values_locale_id", "fact_values", ["locale_id"])
    op.create_index("ix_fact_values_measure_id", "fact_values", ["measure_id"])
    op.create_index("ix_fact_values_year", "fact_values", ["year"])
    op.create_index("ix_fact_values_measure_year_value", "fact_values", ["measure_id", "year", "value"])

    op.create_table(
        "state_adjacency",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state_code", sa.String(length=4), nullable=False),
        sa.Column("neighbor_code", sa.String(length=4), nullable=False),
        sa.Column("shared_border_length", sa.Float(), nullable=False),
    )
    op.create_index("ix_state_adjacency_state_code", "state_adjacency", ["state_code"])


def downgrade() -> None:
    op.drop_index("ix_state_adjacency_state_code", table_name="state_adjacency")
    op.drop_table("state_adjacency")
    op.drop_index("ix_fact_values_measure_year_value", table_name="fact_values")
    op.drop_index("ix_fact_values_year", table_name="fact_values")
    op.drop_index("ix_fact_values_measure_id", table_name="fact_values")
    op.drop_index("ix_fact_values_locale_id", table_name="fact_values")
    op.drop_table("fact_values")
    op.drop_index("ix_districts_source_district_code", table_name="districts")
    op.drop_table("districts")
    op.drop_index("ix_measures_code", table_name="measures")
    op.drop_table("measures")
    op.drop_index("ix_locales_iso_code", table_name="locales")
    op.drop_table("locales")

