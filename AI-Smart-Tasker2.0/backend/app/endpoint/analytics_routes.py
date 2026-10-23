"""API endpoints for task analytics and tracking."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query

from sqlalchemy.orm import Session

from backend.app.utils.database import get_db
from backend.app.utils.analytics_processor import AnalyticsProcessor
from backend.app.schemas.analytics_schema import AnalyticsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get(
    "",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get comprehensive analytics for a user",
)
def get_analytics(
    user_id: int = Query(..., description="User ID to get analytics for"),
    trend_days: int = Query(
        30, ge=1, le=365, description="Number of days for productivity trends"
    ),
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    """
    Get comprehensive task analytics for a user.

    Includes:
    - Task completion statistics
    - Deadline adherence metrics
    - Productivity trends over time
    - Recent analytics events

    Args:
        user_id: User ID
        trend_days: Number of days to look back for productivity trends
        db: Database session

    Returns:
        Comprehensive analytics data

    Raises:
        HTTPException: If analytics retrieval fails
    """
    try:
        analytics = AnalyticsProcessor.get_analytics(db, user_id, trend_days)
        return analytics

    except Exception as e:
        logger.error(f"Failed to get analytics for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}",
        )


@router.get(
    "/completion-stats",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get task completion statistics",
)
def get_completion_stats(
    user_id: int = Query(..., description="User ID"), db: Session = Depends(get_db)
):
    """
    Get task completion statistics for a user.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Task completion statistics

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        stats = AnalyticsProcessor.get_completion_stats(db, user_id)
        return stats

    except Exception as e:
        logger.error(f"Failed to get completion stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get completion stats: {str(e)}",
        )


@router.get(
    "/deadline-adherence",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get deadline adherence metrics",
)
def get_deadline_adherence(
    user_id: int = Query(..., description="User ID"), db: Session = Depends(get_db)
):
    """
    Get deadline adherence metrics for a user.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Deadline adherence metrics

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        adherence = AnalyticsProcessor.get_deadline_adherence(db, user_id)
        return adherence

    except Exception as e:
        logger.error(f"Failed to get deadline adherence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deadline adherence: {str(e)}",
        )


@router.get(
    "/productivity-trends",
    response_model=list,
    status_code=status.HTTP_200_OK,
    summary="Get productivity trends over time",
)
def get_productivity_trends(
    user_id: int = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
):
    """
    Get productivity trends over time.

    Args:
        user_id: User ID
        days: Number of days to look back
        db: Database session

    Returns:
        List of productivity trend data points

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        trends = AnalyticsProcessor.get_productivity_trends(db, user_id, days)
        return trends

    except Exception as e:
        logger.error(f"Failed to get productivity trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get productivity trends: {str(e)}",
        )
