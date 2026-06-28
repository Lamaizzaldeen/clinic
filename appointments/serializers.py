from rest_framework import serializers
from .models import Appointment, Schedule
from patients.models import Patient
from nutritionists.models import Nutritionist


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'app_id',
            'patient',
            'nutritionist',
            'date',
            'time',
            'status',
            'type',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['app_id', 'created_at', 'updated_at']


class AppointmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'app_id',
            'patient',
            'date',
            'start_time',
            'end_time',
            'status',
            'type',
            'notes',
            'created_at',
        ]
        read_only_fields = ['app_id', 'patient', 'end_time', 'created_at']


class AppointmentBookSerializer(serializers.Serializer):
    date = serializers.DateField()
    start_time = serializers.TimeField()
    type = serializers.ChoiceField(
        choices=[('online', 'أونلاين'), ('in-person', 'حضوري')],
        default='in-person',
        required=False,
    )


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'day_of_week', 'start_time', 'end_time']
        read_only_fields = ['id']


class AvailableSlotSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
