from datetime import timedelta, datetime, date as date_type
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from utils.permissions import IsPatientUser, IsNutritionistUser
from utils.pagination import StandardPagination
from .models import Appointment, Schedule
from .serializers import (
    ScheduleSerializer,
    AppointmentBookSerializer,
    AppointmentDetailSerializer,
)


class ScheduleViewSet(ModelViewSet):
    queryset = Schedule.objects.all().order_by('day_of_week')
    serializer_class = ScheduleSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsNutritionistUser()]
        return [AllowAny()]


class AvailableSlotsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'date parameter is required (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        day_name = target_date.strftime('%A').lower()

        try:
            schedule = Schedule.objects.get(day_of_week=day_name)
        except Schedule.DoesNotExist:
            return Response(
                {'error': 'لا يوجد دوام في هذا اليوم'},
                status=status.HTTP_404_NOT_FOUND
            )

        slots = []
        current = datetime.combine(target_date, schedule.start_time)
        end = datetime.combine(target_date, schedule.end_time)
        while current + timedelta(minutes=30) <= end:
            slots.append({
                'start_time': current.time(),
                'end_time': (current + timedelta(minutes=30)).time()
            })
            current += timedelta(minutes=30)

        booked_times = set(
            Appointment.objects.filter(
                date=target_date,
                status__in=['pending', 'confirmed'],
                start_time__isnull=False,
            ).values_list('start_time', flat=True)
        )

        from subscriptions.models import Workshop
        workshop_times = set(
            Workshop.objects.filter(
                date=target_date,
                status__in=['upcoming', 'ongoing']
            ).values_list('time', flat=True)
        )

        available = [
            slot for slot in slots
            if slot['start_time'] not in booked_times
            and slot['start_time'] not in workshop_times
        ]

        return Response(available)


class BookAppointmentView(APIView):
    permission_classes = [IsPatientUser]

    def post(self, request):
        serializer = AppointmentBookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        target_date = serializer.validated_data['date']
        start_time = serializer.validated_data['start_time']

        if target_date < date_type.today():
            return Response(
                {'error': 'لا يمكن حجز موعد في تاريخ ماضٍ'},
                status=status.HTTP_400_BAD_REQUEST
            )

        day_name = target_date.strftime('%A').lower()

        try:
            schedule = Schedule.objects.get(day_of_week=day_name)
        except Schedule.DoesNotExist:
            return Response(
                {'error': 'لا يوجد دوام في هذا اليوم'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not (schedule.start_time <= start_time < schedule.end_time):
            return Response(
                {'error': 'الوقت المطلوب خارج أوقات الدوام'},
                status=status.HTTP_400_BAD_REQUEST
            )

        end_time = (
            datetime.combine(target_date, start_time) + timedelta(minutes=30)
        ).time()

        if end_time > schedule.end_time:
            return Response(
                {'error': 'الوقت المطلوب خارج أوقات الدوام'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Appointment.objects.filter(
            date=target_date,
            start_time=start_time,
            status__in=['pending', 'confirmed'],
        ).exists():
            return Response(
                {'error': 'هذا الموعد محجوز مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from subscriptions.models import Workshop
        if Workshop.objects.filter(
            date=target_date,
            time=start_time,
            status__in=['upcoming', 'ongoing'],
        ).exists():
            return Response(
                {'error': 'يوجد ورشة في هذا الوقت'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from nutritionists.models import Nutritionist
        try:
            nutritionist = Nutritionist.objects.get()
        except Nutritionist.DoesNotExist:
            return Response(
                {"error": "لا يوجد أخصائي تغذية مسجل في النظام"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Nutritionist.MultipleObjectsReturned:
            return Response(
                {"error": "يوجد أكثر من أخصائي — يرجى مراجعة الإعدادات"},
                status=status.HTTP_400_BAD_REQUEST
            )

        patient = request.user.patient_profile
        try:
            appointment = Appointment.objects.create(
                patient=patient,
                nutritionist=nutritionist,
                date=target_date,
                time=start_time,
                start_time=start_time,
                end_time=end_time,
                status='pending',
                type=serializer.validated_data.get('type', 'in-person'),
            )
        except IntegrityError:
            return Response(
                {'error': 'هذا الموعد محجوز مسبقاً'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from payments.models import Cart, CartItem
        cart, _ = Cart.objects.get_or_create(patient=patient)
        CartItem.objects.get_or_create(
            cart=cart,
            appointment=appointment,
            defaults={'quantity': 1},
        )

        return Response(
            AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_201_CREATED
        )


class AppointmentListView(APIView):
    permission_classes = [IsPatientUser]

    def get(self, request):
        patient = request.user.patient_profile
        appointments = Appointment.objects.filter(
            patient=patient
        ).order_by('date', 'start_time')

        paginator = StandardPagination()
        page = paginator.paginate_queryset(appointments, request)
        serializer = AppointmentDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
