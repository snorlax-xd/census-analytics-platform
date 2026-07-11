from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import FactValue, Locale, Measure, StateAdjacency
from app.schemas import ClosestPresetResponse, NeighborPresetResponse

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("/closest", response_model=ClosestPresetResponse)
def get_closest_preset(
    anchor: str,
    metric: str,
    year: int = 2011,
    db: Session = Depends(get_db),
) -> ClosestPresetResponse:
    anchor_code = anchor.upper()
    metric_code = metric.strip()

    anchor_locale = db.execute(select(Locale).where(Locale.iso_code == anchor_code)).scalar_one_or_none()
    if anchor_locale is None:
        raise HTTPException(status_code=404, detail=f"Unknown anchor state code: {anchor_code}")

    measure = db.execute(select(Measure).where(Measure.code == metric_code)).scalar_one_or_none()
    if measure is None:
        raise HTTPException(status_code=404, detail=f"Unknown measure code: {metric_code}")

    anchor_value = db.execute(
        select(FactValue.value).where(
            FactValue.locale_id == anchor_locale.id,
            FactValue.measure_id == measure.id,
            FactValue.year == year,
        )
    ).scalar_one_or_none()
    if anchor_value is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data for {anchor_code}, measure {metric_code}, year {year}.",
        )

    row = db.execute(
        select(Locale.iso_code, Locale.name, FactValue.value)
        .join(FactValue, FactValue.locale_id == Locale.id)
        .where(
            Locale.id != anchor_locale.id,
            FactValue.measure_id == measure.id,
            FactValue.year == year,
        )
        .order_by(func.abs(FactValue.value - anchor_value).asc(), Locale.name.asc())
        .limit(1)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No comparison state available for measure {metric_code}.")

    state_code, state_name, value = row
    return ClosestPresetResponse(state_code=state_code, state_name=state_name, value=value)


@router.get("/neighbor", response_model=NeighborPresetResponse)
def get_neighbor_preset(anchor: str, db: Session = Depends(get_db)) -> NeighborPresetResponse:
    anchor_code = anchor.upper()
    anchor_locale = db.execute(select(Locale).where(Locale.iso_code == anchor_code)).scalar_one_or_none()
    if anchor_locale is None:
        raise HTTPException(status_code=404, detail=f"Unknown anchor state code: {anchor_code}")

    row = db.execute(
        select(Locale.iso_code, Locale.name)
        .join(StateAdjacency, StateAdjacency.neighbor_code == Locale.iso_code)
        .where(StateAdjacency.state_code == anchor_code)
        .order_by(StateAdjacency.shared_border_length.desc(), Locale.name.asc())
        .limit(1)
    ).one_or_none()
    if row is None:
        return NeighborPresetResponse(state_code=None)

    state_code, state_name = row
    return NeighborPresetResponse(state_code=state_code, state_name=state_name)
