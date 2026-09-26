"""
backend/routers/reports.py — Reports & Analytics API Endpoints
=============================================================================
This router provides administrative management and business intelligence reports:
- GET /api/reports/parcels: Parcel count, total charges, weight grouped by status.
- GET /api/reports/payments: Payment metrics, cash flow, and status breakdown.
- GET /api/reports/deliveries: Delivery agent workloads, completed tasks, completion %.
- GET /api/reports/monthly: Monthly summary integrating MySQL stored procedure.

Restricted exclusively to Administrator accounts (require_admin).
=============================================================================
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text

from backend.database import get_db
from backend.models.user import User
from backend.models.parcel import Parcel
from backend.models.parcel_status import ParcelStatus
from backend.models.payment import Payment
from backend.models.delivery import Delivery
from backend.models.delivery_person import DeliveryPerson
from backend.security import require_admin
from backend.schemas.report import (
    ParcelStatusSummary,
    ParcelReportResponse,
    PaymentStatusSummary,
    PaymentReportResponse,
    DeliveryAgentWorkload,
    DeliveryReportResponse,
    MonthlyReportResponse
)

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"], dependencies=[Depends(require_admin)])


# -----------------------------------------------------------------------------
# 1. PARCELS REPORT (GET /api/reports/parcels)
# -----------------------------------------------------------------------------
@router.get(
    "/parcels",
    response_model=ParcelReportResponse,
    summary="Get parcel statistics grouped by status (Admin only)"
)
def get_parcels_report(db: Session = Depends(get_db)):
    """
    Returns aggregated parcel statistics:
    - Total parcels count, total revenue booked, average parcel weight.
    - Status-wise breakdown (count, percentage, charges, weight).
    """
    total_parcels = db.scalar(select(func.count(Parcel.parcel_id))) or 0
    total_revenue = db.scalar(select(func.coalesce(func.sum(Parcel.charge), 0.0))) or 0.0
    avg_weight = db.scalar(select(func.coalesce(func.avg(Parcel.weight_kg), 0.0))) or 0.0

    # Group by parcel status
    status_query = (
        select(
            ParcelStatus.status,
            func.count(Parcel.parcel_id).label("status_count"),
            func.coalesce(func.sum(Parcel.charge), 0.0).label("status_charges"),
            func.coalesce(func.sum(Parcel.weight_kg), 0.0).label("status_weight")
        )
        .join(Parcel.status)
        .group_by(ParcelStatus.status)
        .order_by(func.count(Parcel.parcel_id).desc())
    )
    status_rows = db.execute(status_query).fetchall()

    by_status: List[ParcelStatusSummary] = []
    for row in status_rows:
        count = int(row.status_count)
        pct = round((count / total_parcels * 100), 2) if total_parcels > 0 else 0.0
        by_status.append(
            ParcelStatusSummary(
                status=str(row.status),
                count=count,
                percentage=pct,
                total_charges=round(float(row.status_charges), 2),
                total_weight_kg=round(float(row.status_weight), 2)
            )
        )

    return ParcelReportResponse(
        total_parcels=total_parcels,
        total_revenue=round(float(total_revenue), 2),
        average_weight_kg=round(float(avg_weight), 2),
        by_status=by_status
    )


# -----------------------------------------------------------------------------
# 2. PAYMENTS REPORT (GET /api/reports/payments)
# -----------------------------------------------------------------------------
@router.get(
    "/payments",
    response_model=PaymentReportResponse,
    summary="Get payment statistics and cash flow metrics (Admin only)"
)
def get_payments_report(db: Session = Depends(get_db)):
    """
    Returns aggregated payment statistics:
    - Total payments count, gross amount.
    - Collected amount ('Paid') vs Pending settlement.
    - Breakdown by payment status and by payment method.
    """
    total_payments = db.scalar(select(func.count(Payment.payment_id))) or 0
    total_amount = db.scalar(select(func.coalesce(func.sum(Payment.amount), 0.0))) or 0.0

    collected = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0.0))
        .where(Payment.payment_status == "Paid")
    ) or 0.0

    pending = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0.0))
        .where(Payment.payment_status == "Pending")
    ) or 0.0

    # Group by status
    status_rows = db.execute(
        select(
            Payment.payment_status,
            func.count(Payment.payment_id).label("status_count"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("status_amount")
        )
        .group_by(Payment.payment_status)
        .order_by(func.count(Payment.payment_id).desc())
    ).fetchall()

    by_status: List[PaymentStatusSummary] = []
    for r in status_rows:
        count = int(r.status_count)
        pct = round((count / total_payments * 100), 2) if total_payments > 0 else 0.0
        by_status.append(
            PaymentStatusSummary(
                payment_status=str(r.payment_status),
                count=count,
                total_amount=round(float(r.status_amount), 2),
                percentage=pct
            )
        )

    # Group by payment method
    method_rows = db.execute(
        select(
            func.coalesce(Payment.payment_method, "Unspecified").label("method"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("method_amount")
        )
        .group_by(Payment.payment_method)
    ).fetchall()

    by_method: Dict[str, float] = {
        str(r.method): round(float(r.method_amount), 2) for r in method_rows
    }

    return PaymentReportResponse(
        total_payments=total_payments,
        total_amount=round(float(total_amount), 2),
        collected_amount=round(float(collected), 2),
        pending_amount=round(float(pending), 2),
        by_status=by_status,
        by_method=by_method
    )


# -----------------------------------------------------------------------------
# 3. DELIVERIES REPORT (GET /api/reports/deliveries)
# -----------------------------------------------------------------------------
@router.get(
    "/deliveries",
    response_model=DeliveryReportResponse,
    summary="Get delivery workloads and agent performance metrics (Admin only)"
)
def get_deliveries_report(db: Session = Depends(get_db)):
    """
    Returns courier workforce metrics:
    - Total assignments, completed deliveries, overall completion rate.
    - Per-agent workload: assigned, delivered, pending, and completion percentage.
    """
    total_deliveries = db.scalar(select(func.count(Delivery.delivery_id))) or 0
    total_delivered = db.scalar(
        select(func.count(Delivery.delivery_id)).where(Delivery.delivered_at.isnot(None))
    ) or 0
    overall_rate = round((total_delivered / total_deliveries * 100), 2) if total_deliveries > 0 else 0.0

    agents = db.scalars(select(DeliveryPerson).order_by(DeliveryPerson.full_name)).all()

    agent_workloads: List[DeliveryAgentWorkload] = []
    for ag in agents:
        assigned = len(ag.deliveries)
        delivered = sum(1 for d in ag.deliveries if d.delivered_at is not None)
        pending = assigned - delivered
        comp_rate = round((delivered / assigned * 100), 2) if assigned > 0 else 0.0

        agent_workloads.append(
            DeliveryAgentWorkload(
                delivery_person_id=ag.delivery_person_id,
                full_name=ag.full_name,
                phone=ag.phone,
                vehicle_number=ag.vehicle_number,
                assigned_count=assigned,
                delivered_count=delivered,
                pending_count=pending,
                completion_rate=comp_rate
            )
        )

    return DeliveryReportResponse(
        total_deliveries=total_deliveries,
        total_delivered=total_delivered,
        overall_completion_rate=overall_rate,
        agents=agent_workloads
    )


# -----------------------------------------------------------------------------
# 4. MONTHLY EXECUTIVE REPORT (GET /api/reports/monthly)
# -----------------------------------------------------------------------------
@router.get(
    "/monthly",
    response_model=MonthlyReportResponse,
    summary="Monthly executive summary using MySQL Stored Procedure (Admin only)"
)
def get_monthly_report_endpoint(
    year: int = Query(..., ge=2000, le=2100, description="Calendar year"),
    month: int = Query(..., ge=1, le=12, description="Month of year (1-12)"),
    db: Session = Depends(get_db)
):
    """
    Executes the PL/SQL stored procedure `get_monthly_report(p_year, p_month)`
    created in Phase 6:
    - Overview metrics: booked count, revenue, average weight.
    - Status breakdown.
    - Destination city breakdown.
    """
    # Overview metrics
    overview_row = db.execute(
        text(
            "SELECT "
            "  COUNT(p.parcel_id) AS total_parcels_booked, "
            "  COALESCE(SUM(p.charge), 0.00) AS total_revenue, "
            "  COALESCE(ROUND(AVG(p.weight_kg), 2), 0.00) AS average_weight_kg "
            "FROM parcel p "
            "WHERE YEAR(p.booked_at) = :yr AND MONTH(p.booked_at) = :mo"
        ),
        {"yr": year, "mo": month}
    ).fetchone()

    # Status breakdown
    status_rows = db.execute(
        text(
            "SELECT "
            "  ps.status AS parcel_status, "
            "  COUNT(*) AS count_in_status, "
            "  ROUND(COALESCE(SUM(p.charge), 0), 2) AS revenue_for_status "
            "FROM parcel p "
            "INNER JOIN parcel_status ps ON p.parcel_id = ps.parcel_id "
            "WHERE YEAR(p.booked_at) = :yr AND MONTH(p.booked_at) = :mo "
            "GROUP BY ps.status "
            "ORDER BY count_in_status DESC"
        ),
        {"yr": year, "mo": month}
    ).fetchall()

    # Destination city breakdown
    city_rows = db.execute(
        text(
            "SELECT "
            "  p.destination_city, "
            "  COUNT(*) AS parcel_count, "
            "  ROUND(SUM(p.charge), 2) AS city_revenue "
            "FROM parcel p "
            "WHERE YEAR(p.booked_at) = :yr AND MONTH(p.booked_at) = :mo "
            "GROUP BY p.destination_city "
            "ORDER BY parcel_count DESC"
        ),
        {"yr": year, "mo": month}
    ).fetchall()

    return MonthlyReportResponse(
        year=year,
        month=month,
        total_parcels_booked=int(overview_row.total_parcels_booked) if overview_row else 0,
        total_revenue=float(overview_row.total_revenue) if overview_row else 0.0,
        average_weight_kg=float(overview_row.average_weight_kg) if overview_row else 0.0,
        by_status=[
            {"status": str(r.parcel_status), "count": int(r.count_in_status), "revenue": float(r.revenue_for_status)}
            for r in status_rows
        ],
        by_destination=[
            {"city": str(r.destination_city), "count": int(r.parcel_count), "revenue": float(r.city_revenue)}
            for r in city_rows
        ]
    )
