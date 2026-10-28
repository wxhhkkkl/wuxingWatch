"""Chart endpoints: predict (排盘) and long-image generation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.schemas import BirthInput, Dayun2Request, LiuShiLevel, LiuShiRequest
from services import chart_service, share_service
from services.bazi import liushi

router = APIRouter()


@router.post("/predict")
def predict(payload: BirthInput):
    try:
        result, _ = chart_service.compute(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return result


@router.post("/liushi")
def liushi_detail(payload: LiuShiRequest):
    """流月/流日/流时下钻：按 level 返回所选流年的月/日/时数据。"""
    ctx = payload.context.model_dump()
    try:
        if payload.level == LiuShiLevel.MONTH:
            return liushi.liu_yue_list(payload.year, ctx)
        if payload.level == LiuShiLevel.DAY:
            return liushi.liu_ri_list(payload.year, payload.month_branch, ctx)
        return liushi.liu_shi_list(
            payload.year, payload.month_branch, payload.date, ctx
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/image")
def chart_image(payload: BirthInput):
    result, _ = chart_service.compute(payload)
    try:
        png = share_service.render_long_image(result, person_name=payload.name)
    except Exception as exc:  # font / rendering failure
        raise HTTPException(status_code=500, detail="命盘图片生成失败") from exc
    headers = {"X-Privacy-Notice": "image-contains-personal-info"} if payload.name else {}
    return Response(content=png, media_type="image/png", headers=headers)

@router.post("/dayun2")
def dayun2(payload: Dayun2Request):
    """**大运引擎2**（014 期 T024）——按教师八步流程（R30 起含天干五合）独立算出的另一套大运旺度。

    这是当前**唯一**的大运旺度计算（`engine: "dayun-engine2"`）。
    **按需实时计算、不落库**（FR-008）。

    `dayun_ganzhi` 可选——不给则返回该盘全部大运步；给了则只算那一步。
    """
    try:
        return chart_service.dayun2_conclusion(payload, payload.dayun_ganzhi)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
