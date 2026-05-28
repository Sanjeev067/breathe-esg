from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet,
    DataSourceViewSet,
    EmissionRecordViewSet,
    AuditLogViewSet
)

# Instantiate the DRF DefaultRouter for clean REST mapping
router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'sources', DataSourceViewSet, basename='datasource')
router.register(r'records', EmissionRecordViewSet, basename='emissionrecord')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('', include(router.urls)),
]