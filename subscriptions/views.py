from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from utils.permissions import IsPatientUser
from django.db.models import Count

from .models import Package, Workshop, PatientWorkshop, WorkshopAttendance
from .serializers import PackageSerializer, WorkshopListSerializer, WorkshopSerializer, WorkshopAttendanceSerializer
from utils.pagination import StandardPagination

class PackageViewSet(ModelViewSet):
    queryset = Package.objects.all().order_by('-created_at')
    serializer_class = PackageSerializer
    pagination_class = PageNumberPagination
    pagination_class.page_size = 10
    @action(detail=False, methods=['get'])
    def stats(self, request):
        # احصاء عدد الاشتراكات لكل باقة
        stats = Package.objects.annotate(
            subscribers_count=Count('payments')
        ).values('package_id', 'name', 'subscribers_count')

        # إجمالي الاشتراكات
        total = sum(item['subscribers_count'] for item in stats)

        # تجهيز النسب المئوية
        for item in stats:
            item['percentage'] = (
                round((item['subscribers_count'] / total) * 100, 2)
                if total > 0 else 0
            )

        # الباقة الأكثر مبيعًا
        most_sold = max(stats, key=lambda x: x['subscribers_count']) if stats else None

        # الباقة الأقل مبيعًا
        least_sold = min(stats, key=lambda x: x['subscribers_count']) if stats else None

        # بيانات الرسم البياني
        chart_data = [
            {
                "label": item['name'],
                "value": item['subscribers_count'],
                "percentage": item['percentage']
            }
            for item in stats
        ]

        return Response({
            "total_subscribers": total,
            "packages": stats,
            "most_sold": most_sold,
            "least_sold": least_sold,
            "chart_data": chart_data,
        })


class WorkshopViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = StandardPagination

    def get_serializer_class(self):
        return WorkshopSerializer

    def get_queryset(self):
        return Workshop.objects.filter(
            status__in=['upcoming', 'ongoing']
        ).order_by('date', 'time')

    def get_permissions(self):
        if self.action == 'register':
            return [AllowAny()]
        return [AllowAny()]

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        workshop = self.get_object()

        email = request.data.get('email', '').strip()
        if not email:
            return Response(
                {'error': 'البريد الإلكتروني مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if workshop.is_full:
            return Response(
                {'error': 'Workshop is full'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if WorkshopAttendance.objects.filter(email=email, workshop=workshop).exists():
            return Response(
                {'error': 'هذا البريد الإلكتروني مسجّل بالفعل في هذه الورشة'},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendance = WorkshopAttendance.objects.create(email=email, workshop=workshop)

        if request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
            patient = request.user.patient_profile
            PatientWorkshop.objects.get_or_create(patient=patient, workshop=workshop)

        return Response(
            WorkshopAttendanceSerializer(attendance).data,
            status=status.HTTP_201_CREATED
        )