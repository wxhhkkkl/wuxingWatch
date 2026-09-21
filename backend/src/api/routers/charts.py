"""Chart endpoints: predict (排盘) and long-image generation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.schemas import BirthInput, LiuShiLevel, LiuShiRequest, SuiyunRequest
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

@router.post("/suiyun")
def suiyun(payload: SuiyunRequest):
    """**岁运推导**（013 期 T034；FR-021a）——阶段 2（加入大运）或阶段 3（加入流年）。

    **按需实时计算、不落库**（FR-026）：不写记录，也不读记录里的岁运结论。
    「加入流年」时另返回 `pairs`——两阶段的同名判断**成对**列出，**引擎不合成吉凶**
    （FR-016a/016c），判断由使用者做。
    """
    try:
        return chart_service.suiyun_conclusion(payload, payload.dayun_ganzhi,
                                               payload.liunian_year)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

