"""Chart endpoints: predict (排盘) and long-image generation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.schemas import BirthInput
from services import chart_service, share_service

router = APIRouter()


@router.post("/predict")
def predict(payload: BirthInput):
    result, _ = chart_service.compute(payload)
    return result


@router.post("/image")
def chart_image(payload: BirthInput):
    result, _ = chart_service.compute(payload)
    try:
        png = share_service.render_long_image(result, person_name=payload.name)
    except Exception as exc:  # font / rendering failure
        raise HTTPException(status_code=500, detail="命盘图片生成失败") from exc
    headers = {"X-Privacy-Notice": "image-contains-personal-info"} if payload.name else {}
    return Response(content=png, media_type="image/png", headers=headers)
