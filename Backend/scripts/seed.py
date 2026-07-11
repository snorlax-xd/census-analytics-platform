from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Callable

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import SessionLocal
from app.models import District, FactValue, Locale, Measure, StateAdjacency


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "Database" / "india-districts-census-2011.csv"
YEAR = 2011


@dataclass(frozen=True)
class LocaleSeed:
    iso_code: str
    name: str
    source_name: str
    type: str
    centroid_lat: float | None = None
    centroid_lng: float | None = None
    area_sq_km: float | None = None


@dataclass(frozen=True)
class MeasureSeed:
    code: str
    name: str
    unit: str
    category: str
    higher_is_better: bool | None
    is_derived: bool
    compute: Callable[[pd.Series], float]


@dataclass(frozen=True)
class AdjacencySeed:
    state_code: str
    neighbor_code: str
    shared_border_length: float


LOCALES: tuple[LocaleSeed, ...] = (
    LocaleSeed("JK", "Jammu and Kashmir", "JAMMU AND KASHMIR", "state"),
    LocaleSeed("HP", "Himachal Pradesh", "HIMACHAL PRADESH", "state"),
    LocaleSeed("PB", "Punjab", "PUNJAB", "state"),
    LocaleSeed("CH", "Chandigarh", "CHANDIGARH", "ut"),
    LocaleSeed("UK", "Uttarakhand", "UTTARAKHAND", "state"),
    LocaleSeed("HR", "Haryana", "HARYANA", "state"),
    LocaleSeed("DL", "Delhi", "NCT OF DELHI", "ut"),
    LocaleSeed("RJ", "Rajasthan", "RAJASTHAN", "state"),
    LocaleSeed("UP", "Uttar Pradesh", "UTTAR PRADESH", "state"),
    LocaleSeed("BR", "Bihar", "BIHAR", "state"),
    LocaleSeed("SK", "Sikkim", "SIKKIM", "state"),
    LocaleSeed("AR", "Arunachal Pradesh", "ARUNACHAL PRADESH", "state"),
    LocaleSeed("NL", "Nagaland", "NAGALAND", "state"),
    LocaleSeed("MN", "Manipur", "MANIPUR", "state"),
    LocaleSeed("MZ", "Mizoram", "MIZORAM", "state"),
    LocaleSeed("TR", "Tripura", "TRIPURA", "state"),
    LocaleSeed("ML", "Meghalaya", "MEGHALAYA", "state"),
    LocaleSeed("AS", "Assam", "ASSAM", "state"),
    LocaleSeed("WB", "West Bengal", "WEST BENGAL", "state"),
    LocaleSeed("JH", "Jharkhand", "JHARKHAND", "state"),
    LocaleSeed("OD", "Odisha", "ORISSA", "state"),
    LocaleSeed("CT", "Chhattisgarh", "CHHATTISGARH", "state"),
    LocaleSeed("MP", "Madhya Pradesh", "MADHYA PRADESH", "state"),
    LocaleSeed("GJ", "Gujarat", "GUJARAT", "state"),
    LocaleSeed("DD", "Daman and Diu", "DAMAN AND DIU", "ut"),
    LocaleSeed("DN", "Dadra and Nagar Haveli", "DADRA AND NAGAR HAVELI", "ut"),
    LocaleSeed("MH", "Maharashtra", "MAHARASHTRA", "state"),
    LocaleSeed("AP", "Andhra Pradesh", "ANDHRA PRADESH", "state"),
    LocaleSeed("KA", "Karnataka", "KARNATAKA", "state"),
    LocaleSeed("GA", "Goa", "GOA", "state"),
    LocaleSeed("LD", "Lakshadweep", "LAKSHADWEEP", "ut"),
    LocaleSeed("KL", "Kerala", "KERALA", "state"),
    LocaleSeed("TN", "Tamil Nadu", "TAMIL NADU", "state"),
    LocaleSeed("PY", "Puducherry", "PONDICHERRY", "ut"),
    LocaleSeed("AN", "Andaman and Nicobar Islands", "ANDAMAN AND NICOBAR ISLANDS", "ut"),
)


# Static 2011-era state/UT land adjacencies. The numeric value is the
# deterministic preset priority for "longest shared border"; higher wins.
ADJACENCIES: tuple[AdjacencySeed, ...] = (
    AdjacencySeed("JK", "HP", 2),
    AdjacencySeed("JK", "PB", 1),
    AdjacencySeed("HP", "JK", 3),
    AdjacencySeed("HP", "PB", 2),
    AdjacencySeed("HP", "HR", 1),
    AdjacencySeed("HP", "UK", 4),
    AdjacencySeed("PB", "JK", 3),
    AdjacencySeed("PB", "HP", 2),
    AdjacencySeed("PB", "HR", 4),
    AdjacencySeed("PB", "RJ", 1),
    AdjacencySeed("PB", "CH", 5),
    AdjacencySeed("CH", "PB", 2),
    AdjacencySeed("CH", "HR", 1),
    AdjacencySeed("UK", "HP", 1),
    AdjacencySeed("UK", "HR", 2),
    AdjacencySeed("UK", "UP", 3),
    AdjacencySeed("HR", "PB", 3),
    AdjacencySeed("HR", "HP", 2),
    AdjacencySeed("HR", "UK", 1),
    AdjacencySeed("HR", "UP", 4),
    AdjacencySeed("HR", "RJ", 5),
    AdjacencySeed("HR", "DL", 6),
    AdjacencySeed("HR", "CH", 7),
    AdjacencySeed("DL", "HR", 2),
    AdjacencySeed("DL", "UP", 1),
    AdjacencySeed("RJ", "PB", 3),
    AdjacencySeed("RJ", "HR", 4),
    AdjacencySeed("RJ", "UP", 2),
    AdjacencySeed("RJ", "MP", 5),
    AdjacencySeed("RJ", "GJ", 1),
    AdjacencySeed("UP", "UK", 2),
    AdjacencySeed("UP", "HR", 3),
    AdjacencySeed("UP", "DL", 6),
    AdjacencySeed("UP", "RJ", 1),
    AdjacencySeed("UP", "MP", 5),
    AdjacencySeed("UP", "CT", 7),
    AdjacencySeed("UP", "JH", 4),
    AdjacencySeed("UP", "BR", 8),
    AdjacencySeed("BR", "UP", 3),
    AdjacencySeed("BR", "JH", 2),
    AdjacencySeed("BR", "WB", 1),
    AdjacencySeed("SK", "WB", 1),
    AdjacencySeed("AR", "AS", 4),
    AdjacencySeed("AR", "NL", 1),
    AdjacencySeed("NL", "AR", 1),
    AdjacencySeed("NL", "AS", 3),
    AdjacencySeed("NL", "MN", 2),
    AdjacencySeed("MN", "NL", 2),
    AdjacencySeed("MN", "AS", 1),
    AdjacencySeed("MN", "MZ", 3),
    AdjacencySeed("MZ", "AS", 1),
    AdjacencySeed("MZ", "MN", 3),
    AdjacencySeed("MZ", "TR", 2),
    AdjacencySeed("TR", "AS", 1),
    AdjacencySeed("TR", "MZ", 2),
    AdjacencySeed("ML", "AS", 1),
    AdjacencySeed("AS", "AR", 7),
    AdjacencySeed("AS", "NL", 5),
    AdjacencySeed("AS", "MN", 3),
    AdjacencySeed("AS", "MZ", 2),
    AdjacencySeed("AS", "TR", 4),
    AdjacencySeed("AS", "ML", 6),
    AdjacencySeed("AS", "WB", 1),
    AdjacencySeed("WB", "BR", 3),
    AdjacencySeed("WB", "JH", 2),
    AdjacencySeed("WB", "OD", 1),
    AdjacencySeed("WB", "SK", 4),
    AdjacencySeed("WB", "AS", 5),
    AdjacencySeed("JH", "BR", 4),
    AdjacencySeed("JH", "UP", 1),
    AdjacencySeed("JH", "CT", 2),
    AdjacencySeed("JH", "OD", 3),
    AdjacencySeed("JH", "WB", 5),
    AdjacencySeed("OD", "WB", 3),
    AdjacencySeed("OD", "JH", 2),
    AdjacencySeed("OD", "CT", 4),
    AdjacencySeed("OD", "AP", 1),
    AdjacencySeed("CT", "UP", 4),
    AdjacencySeed("CT", "MP", 3),
    AdjacencySeed("CT", "MH", 2),
    AdjacencySeed("CT", "AP", 1),
    AdjacencySeed("CT", "OD", 6),
    AdjacencySeed("CT", "JH", 5),
    AdjacencySeed("MP", "RJ", 5),
    AdjacencySeed("MP", "UP", 6),
    AdjacencySeed("MP", "CT", 3),
    AdjacencySeed("MP", "MH", 4),
    AdjacencySeed("MP", "GJ", 2),
    AdjacencySeed("GJ", "RJ", 3),
    AdjacencySeed("GJ", "MP", 2),
    AdjacencySeed("GJ", "MH", 4),
    AdjacencySeed("GJ", "DN", 1),
    AdjacencySeed("GJ", "DD", 5),
    AdjacencySeed("DD", "GJ", 1),
    AdjacencySeed("DN", "GJ", 2),
    AdjacencySeed("DN", "MH", 1),
    AdjacencySeed("MH", "GJ", 4),
    AdjacencySeed("MH", "MP", 6),
    AdjacencySeed("MH", "CT", 2),
    AdjacencySeed("MH", "AP", 5),
    AdjacencySeed("MH", "KA", 3),
    AdjacencySeed("MH", "GA", 1),
    AdjacencySeed("MH", "DN", 7),
    AdjacencySeed("AP", "OD", 2),
    AdjacencySeed("AP", "CT", 3),
    AdjacencySeed("AP", "MH", 4),
    AdjacencySeed("AP", "KA", 5),
    AdjacencySeed("AP", "TN", 1),
    AdjacencySeed("AP", "PY", 6),
    AdjacencySeed("KA", "AP", 5),
    AdjacencySeed("KA", "MH", 4),
    AdjacencySeed("KA", "GA", 2),
    AdjacencySeed("KA", "KL", 1),
    AdjacencySeed("KA", "TN", 3),
    AdjacencySeed("GA", "MH", 2),
    AdjacencySeed("GA", "KA", 1),
    AdjacencySeed("KL", "KA", 1),
    AdjacencySeed("KL", "TN", 2),
    AdjacencySeed("KL", "PY", 3),
    AdjacencySeed("TN", "AP", 3),
    AdjacencySeed("TN", "KA", 4),
    AdjacencySeed("TN", "KL", 2),
    AdjacencySeed("TN", "PY", 1),
    AdjacencySeed("PY", "TN", 3),
    AdjacencySeed("PY", "KL", 1),
    AdjacencySeed("PY", "AP", 2),
)


# Preferred neighbor per 2011-era locale for Tab 2's single-result preset.
# These values prevent tiny enclaves from outranking major land borders while
# preserving all adjacency rows for future UI uses.
PRIMARY_NEIGHBOR_OVERRIDES: dict[tuple[str, str], float] = {
    ("JK", "HP"): 1000,
    ("HP", "UK"): 1000,
    ("PB", "HR"): 1000,
    ("CH", "PB"): 1000,
    ("UK", "UP"): 1000,
    ("HR", "RJ"): 1000,
    ("DL", "HR"): 1000,
    ("RJ", "MP"): 1000,
    ("UP", "MP"): 1000,
    ("BR", "JH"): 1000,
    ("SK", "WB"): 1000,
    ("AR", "AS"): 1000,
    ("NL", "AS"): 1000,
    ("MN", "MZ"): 1000,
    ("MZ", "MN"): 1000,
    ("TR", "MZ"): 1000,
    ("ML", "AS"): 1000,
    ("AS", "AR"): 1000,
    ("WB", "JH"): 1000,
    ("JH", "BR"): 1000,
    ("OD", "CT"): 1000,
    ("CT", "OD"): 1000,
    ("MP", "UP"): 1000,
    ("GJ", "RJ"): 1000,
    ("DD", "GJ"): 1000,
    ("DN", "GJ"): 1000,
    ("MH", "MP"): 1000,
    ("AP", "KA"): 1000,
    ("KA", "AP"): 1000,
    ("GA", "KA"): 1000,
    ("KL", "TN"): 1000,
    ("TN", "KA"): 1000,
    ("PY", "TN"): 1000,
}


def safe_pct(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else round((numerator / denominator) * 100, 4)


def sex_ratio(row: pd.Series) -> float:
    return 0.0 if row["Male"] == 0 else round((row["Female"] / row["Male"]) * 1000, 4)


def raw(column: str) -> Callable[[pd.Series], float]:
    return lambda row: float(row[column])


MEASURES: tuple[MeasureSeed, ...] = (
    MeasureSeed("population", "Population", "people", "demographics", None, False, raw("Population")),
    MeasureSeed("male_population", "Male Population", "people", "demographics", None, False, raw("Male")),
    MeasureSeed("female_population", "Female Population", "people", "demographics", None, False, raw("Female")),
    MeasureSeed("sex_ratio", "Sex Ratio", "females per 1000 males", "demographics", None, True, sex_ratio),
    MeasureSeed("sc_population_pct", "SC Population Share", "%", "demographics", None, True, lambda row: safe_pct(row["SC"], row["Population"])),
    MeasureSeed("st_population_pct", "ST Population Share", "%", "demographics", None, True, lambda row: safe_pct(row["ST"], row["Population"])),
    MeasureSeed("age_0_29_pct", "Age 0-29 Share", "%", "demographics", None, True, lambda row: safe_pct(row["Age_Group_0_29"], row["Population"])),
    MeasureSeed("age_30_49_pct", "Age 30-49 Share", "%", "demographics", None, True, lambda row: safe_pct(row["Age_Group_30_49"], row["Population"])),
    MeasureSeed("age_50_plus_pct", "Age 50+ Share", "%", "demographics", None, True, lambda row: safe_pct(row["Age_Group_50"], row["Population"])),
    MeasureSeed("literacy_rate", "Literacy Rate", "%", "literacy", True, True, lambda row: safe_pct(row["Literate"], row["Population"])),
    MeasureSeed("male_literacy_rate", "Male Literacy Rate", "%", "literacy", True, True, lambda row: safe_pct(row["Male_Literate"], row["Male"])),
    MeasureSeed("female_literacy_rate", "Female Literacy Rate", "%", "literacy", True, True, lambda row: safe_pct(row["Female_Literate"], row["Female"])),
    MeasureSeed("graduate_education_count", "Graduate Education Count", "people", "literacy", None, False, raw("Graduate_Education")),
    MeasureSeed("workers", "Workers", "people", "economy", None, False, raw("Workers")),
    MeasureSeed("worker_participation_rate", "Worker Participation Rate", "%", "economy", True, True, lambda row: safe_pct(row["Workers"], row["Population"])),
    MeasureSeed("cultivator_workers_pct", "Cultivator Workers Share", "%", "economy", None, True, lambda row: safe_pct(row["Cultivator_Workers"], row["Workers"])),
    MeasureSeed("agricultural_workers_pct", "Agricultural Workers Share", "%", "economy", None, True, lambda row: safe_pct(row["Agricultural_Workers"], row["Workers"])),
    MeasureSeed("household_workers_pct", "Household Workers Share", "%", "economy", None, True, lambda row: safe_pct(row["Household_Workers"], row["Workers"])),
    MeasureSeed("other_workers_pct", "Other Workers Share", "%", "economy", None, True, lambda row: safe_pct(row["Other_Workers"], row["Workers"])),
    MeasureSeed("households", "Households", "households", "infrastructure", None, False, raw("Households")),
    MeasureSeed("electric_lighting_households_pct", "Households With Electric Lighting", "%", "infrastructure", True, True, lambda row: safe_pct(row["Housholds_with_Electric_Lighting"], row["Households"])),
    MeasureSeed("lpg_png_households_pct", "Households With LPG or PNG", "%", "infrastructure", True, True, lambda row: safe_pct(row["LPG_or_PNG_Households"], row["Households"])),
    MeasureSeed("internet_households_pct", "Households With Internet", "%", "infrastructure", True, True, lambda row: safe_pct(row["Households_with_Internet"], row["Households"])),
    MeasureSeed("computer_households_pct", "Households With Computer", "%", "infrastructure", True, True, lambda row: safe_pct(row["Households_with_Computer"], row["Households"])),
    MeasureSeed("television_households_pct", "Households With Television", "%", "infrastructure", True, True, lambda row: safe_pct(row["Households_with_Television"], row["Households"])),
    MeasureSeed("latrine_facility_households_pct", "Households With Latrine Facility", "%", "sanitation", True, True, lambda row: safe_pct(row["Having_latrine_facility_within_the_premises_Total_Households"], row["Households"])),
    MeasureSeed("bathing_facility_households_pct", "Households With Bathing Facility", "%", "sanitation", True, True, lambda row: safe_pct(row["Having_bathing_facility_Total_Households"], row["Households"])),
    MeasureSeed("open_latrine_households_pct", "Households Without Latrine Using Open Alternative", "%", "sanitation", False, True, lambda row: safe_pct(row["Not_having_latrine_facility_within_the_premises_Alternative_source_Open_Households"], row["Households"])),
    MeasureSeed("dilapidated_households_pct", "Dilapidated Occupied Census Houses", "%", "sanitation", False, True, lambda row: safe_pct(row["Condition_of_occupied_census_houses_Dilapidated_Households"], row["Households"])),
    MeasureSeed("tapwater_households_pct", "Households Using Tapwater", "%", "drinking_water", True, True, lambda row: safe_pct(row["Main_source_of_drinking_water_Tapwater_Households"], row["Households"])),
    MeasureSeed("water_within_premises_pct", "Drinking Water Within Premises", "%", "drinking_water", True, True, lambda row: safe_pct(row["Location_of_drinking_water_source_Within_the_premises_Households"], row["Households"])),
    MeasureSeed("water_away_pct", "Drinking Water Away From Premises", "%", "drinking_water", False, True, lambda row: safe_pct(row["Location_of_drinking_water_source_Away_Households"], row["Households"])),
)


def load_source_csv() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Primary dataset not found: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    expected_states = {locale.source_name for locale in LOCALES}
    actual_states = set(df["State name"].unique())
    missing = expected_states - actual_states
    unexpected = actual_states - expected_states
    if missing or unexpected:
        raise ValueError(f"State mapping mismatch. Missing={sorted(missing)} Unexpected={sorted(unexpected)}")
    return df


def clear_seeded_data(db: Session) -> None:
    db.execute(delete(FactValue))
    db.execute(delete(District))
    db.execute(delete(StateAdjacency))
    db.execute(delete(Measure))
    db.execute(delete(Locale))
    db.commit()


def seed_locales(db: Session) -> dict[str, Locale]:
    locales_by_source: dict[str, Locale] = {}
    for item in LOCALES:
        locale = Locale(
            iso_code=item.iso_code,
            name=item.name,
            source_name=item.source_name,
            type=item.type,
            centroid_lat=item.centroid_lat,
            centroid_lng=item.centroid_lng,
            area_sq_km=item.area_sq_km,
        )
        db.add(locale)
        locales_by_source[item.source_name] = locale
    db.flush()
    return locales_by_source


def seed_districts(db: Session, df: pd.DataFrame, locales_by_source: dict[str, Locale]) -> None:
    for row in df.to_dict(orient="records"):
        db.add(
            District(
                source_district_code=int(row["District code"]),
                name=row["District name"],
                locale_id=locales_by_source[row["State name"]].id,
            )
        )
    db.flush()


def seed_measures(db: Session) -> dict[str, Measure]:
    measures_by_code: dict[str, Measure] = {}
    for item in MEASURES:
        measure = Measure(
            code=item.code,
            name=item.name,
            unit=item.unit,
            category=item.category,
            higher_is_better=item.higher_is_better,
            is_derived=item.is_derived,
        )
        db.add(measure)
        measures_by_code[item.code] = measure
    db.flush()
    return measures_by_code


def seed_facts(db: Session, df: pd.DataFrame, locales_by_source: dict[str, Locale], measures_by_code: dict[str, Measure]) -> None:
    numeric_columns = df.select_dtypes(include=["number"]).columns
    state_totals = df.groupby("State name", as_index=True)[numeric_columns].sum()
    for source_name, row in state_totals.iterrows():
        locale = locales_by_source[source_name]
        for item in MEASURES:
            db.add(
                FactValue(
                    locale_id=locale.id,
                    measure_id=measures_by_code[item.code].id,
                    year=YEAR,
                    value=item.compute(row),
                )
            )
    db.flush()


def seed_adjacencies(db: Session) -> None:
    for item in ADJACENCIES:
        shared_border_length = PRIMARY_NEIGHBOR_OVERRIDES.get(
            (item.state_code, item.neighbor_code),
            item.shared_border_length,
        )
        db.add(
            StateAdjacency(
                state_code=item.state_code,
                neighbor_code=item.neighbor_code,
                shared_border_length=shared_border_length,
            )
        )
    db.flush()


def main() -> None:
    df = load_source_csv()
    with SessionLocal() as db:
        clear_seeded_data(db)
        locales_by_source = seed_locales(db)
        seed_districts(db, df, locales_by_source)
        measures_by_code = seed_measures(db)
        seed_facts(db, df, locales_by_source, measures_by_code)
        seed_adjacencies(db)
        db.commit()

    print(f"Seeded {len(LOCALES)} locales, {len(df)} districts, {len(MEASURES)} measures, {len(ADJACENCIES)} adjacency rows for {YEAR}.")


if __name__ == "__main__":
    main()
