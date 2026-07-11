from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, null, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import FactValue, Locale, Measure
from app.schemas import AnalyticsResponse, LocaleAnalytics, MeasureValue

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    states: str = Query(..., description="Comma-separated state/UT ISO codes, e.g. MH,GJ"),
    year: int = 2011,
    include_rank: bool = False,
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    state_codes = [code.strip().upper() for code in states.split(",") if code.strip()]
    if not state_codes:
        raise HTTPException(status_code=404, detail="No state codes were provided.")

    locales = db.execute(select(Locale).where(Locale.iso_code.in_(state_codes))).scalars().all()
    locales_by_code = {locale.iso_code: locale for locale in locales}
    missing_codes = sorted(set(state_codes) - set(locales_by_code))
    if missing_codes:
        raise HTTPException(status_code=404, detail=f"Unknown state code(s): {', '.join(missing_codes)}")

    rank_subquery = None
    if include_rank:
        order_value = case(
            (Measure.higher_is_better.is_(False), FactValue.value),
            else_=-FactValue.value,
        )
        rank_subquery = (
            select(
                FactValue.locale_id.label("locale_id"),
                FactValue.measure_id.label("measure_id"),
                func.rank()
                .over(
                    partition_by=(FactValue.measure_id, FactValue.year),
                    order_by=order_value.asc(),
                )
                .label("rank"),
            )
            .join(Measure, Measure.id == FactValue.measure_id)
            .where(FactValue.year == year)
            .subquery()
        )

    stmt = (
        select(Locale, Measure, FactValue.value, rank_subquery.c.rank if rank_subquery is not None else null().label("rank"))
        .join(FactValue, FactValue.locale_id == Locale.id)
        .join(Measure, Measure.id == FactValue.measure_id)
        .where(Locale.iso_code.in_(state_codes), FactValue.year == year)
        .order_by(Locale.name, Measure.category, Measure.name)
    )

    if rank_subquery is not None:
        stmt = stmt.outerjoin(
            rank_subquery,
            (rank_subquery.c.locale_id == FactValue.locale_id)
            & (rank_subquery.c.measure_id == FactValue.measure_id),
        )

    rows = db.execute(stmt).all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No analytics data available for year {year}.")

    response_by_code: dict[str, LocaleAnalytics] = {
        code: LocaleAnalytics(locale_code=locale.iso_code, locale_name=locale.name, year=year, measures=[])
        for code, locale in locales_by_code.items()
    }

    for locale, measure, value, rank in rows:
        response_by_code[locale.iso_code].measures.append(
            MeasureValue(
                measure_code=measure.code,
                measure_name=measure.name,
                category=measure.category,
                unit=measure.unit,
                value=value,
                higher_is_better=measure.higher_is_better,
                rank=rank if include_rank else None,
            )
        )

    return AnalyticsResponse(data=[response_by_code[code] for code in state_codes])
