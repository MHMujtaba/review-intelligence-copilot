from fastapi import APIRouter, Depends

from app.core.dependencies import get_app_services
from app.core.services import ApplicationServices
from app.schemas.contracts import (
    AskRequest,
    AskResponse,
    EmbedRequest,
    EmbedResponse,
    LoadCsvRequest,
    LoadCsvResponse,
    ProductInsightsResponse,
    ProductSummaryResponse,
    SearchRequest,
    SearchResponse,
)


router = APIRouter()


@router.post("/load_csv", response_model=LoadCsvResponse)
async def load_csv(payload: LoadCsvRequest, services: ApplicationServices = Depends(get_app_services)) -> LoadCsvResponse:
    return await services.load_csv(payload)


@router.post("/embed", response_model=EmbedResponse)
async def embed(payload: EmbedRequest, services: ApplicationServices = Depends(get_app_services)) -> EmbedResponse:
    return await services.embed_reviews(payload)


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, services: ApplicationServices = Depends(get_app_services)) -> AskResponse:
    return await services.ask(payload)


@router.get("/summary/{asin}", response_model=ProductSummaryResponse)
async def summary(asin: str, services: ApplicationServices = Depends(get_app_services)) -> ProductSummaryResponse:
    return await services.get_summary(asin)


@router.get("/insights/{asin}", response_model=ProductInsightsResponse)
async def insights(asin: str, services: ApplicationServices = Depends(get_app_services)) -> ProductInsightsResponse:
    return await services.get_insights(asin)


@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest, services: ApplicationServices = Depends(get_app_services)) -> SearchResponse:
    return await services.search(payload)
