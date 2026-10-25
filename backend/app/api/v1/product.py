from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.deps import get_current_user
from app.repositories.product import ProductAlreadyExistsError
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import ProductNotFoundError, ProductService, get_product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductResponse])
async def list_products(service: ProductService = Depends(get_product_service)):
    return await service.list_products()


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
async def create_product(
    payload: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    try:
        return await service.add_product(payload)
    except ProductAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(get_current_user)],
)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    try:
        return await service.update_product(product_id, payload)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProductAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{product_id}",
    status_code=204,
    dependencies=[Depends(get_current_user)],
)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    try:
        await service.delete_product(product_id)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(status_code=204)
