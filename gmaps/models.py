import json_fix
from datetime import datetime
from django.db.models import Model, IntegerField, CharField, ForeignKey, DateTimeField, FloatField, DO_NOTHING, DateField
from rest_framework.reverse import reverse
from status.SUB_TASK_STATUSES import *
from google_maps_parser_api.settings import URL

STATUS_URL = {
    RUNNING: 'start',
    STOPPED: 'stop',
    CANCELED: 'cancel',
}

POSSIBLE_STATUSES = {
    WAITING: [CANCELED, SENT],
    SENT: [RUNNING, STOPPED],
    RUNNING: [ERROR, STOPPED, DONE],
    DONE: [],
    ERROR: [WAITING],
    STOPPED: [],
    CANCELED: []
}


IS_FINISH_DATE_UPDATE_REQUIRED = {
    WAITING: False,
    RUNNING: False,
    DONE: True,
    ERROR: True,
    STOPPED: True,
    CANCELED: True,
    SENT: False
}

IS_START_DATE_UPDATE_REQUIRED = {
    WAITING: False,
    RUNNING: True,
    DONE: False,
    ERROR: False,
    STOPPED: False,
    CANCELED: False,
    SENT: False
}


class Credential(Model):
    token = CharField(max_length=560)
    name = CharField(max_length=500)

    def __json__(self):
        return self.token

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class PlaceType(Model):
    value = CharField(max_length=250, unique=True)

    def __json__(self):
        return self.value

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class Coordinate(Model):
    name = CharField(max_length=250)
    lon = FloatField()
    lat = FloatField()
    radius = IntegerField(default=10000)

    def __json__(self):
        return {'name': self.name,
                'lon': self.lon,
                'lat': self.lat,
                'radius': self.radius}

    class Meta:
        unique_together = ('name', 'lon', 'lat', 'radius', )

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class TaskTemplate(Model):
    credentials = ForeignKey(Credential, on_delete=DO_NOTHING)
    coordinates = ForeignKey(Coordinate, on_delete=DO_NOTHING)
    place = ForeignKey(PlaceType, on_delete=DO_NOTHING)

    def __json__(self):
        return {'place': self.place,
                'coordinates': self.coordinates,
                'token': self.credentials
                }

    def __repr__(self):
        return f"{self.place.value}-{self.coordinates.name}-{self.credentials.name}"

    def __str__(self):
        return f"{self.place.value}-{self.coordinates.name}-{self.credentials.name}"


class Task(Model):
    class InvalidStatusChange(Exception):
        pass

    class InvalidStatusForProgressTrack(Exception):
        pass

    class InvalidProgressValue(Exception):
        pass

    template = ForeignKey(TaskTemplate, on_delete=DO_NOTHING)
    start = DateTimeField(null=True, default=None, blank=True)
    finish = DateTimeField(null=True, default=None, blank=True)
    items_collected = IntegerField(default=0)
    status = CharField(choices=STATUS_CHOICES, default=WAITING, max_length=20)
    planned_exec_date = DateField(default=datetime.now, blank=True)

    class Meta:
        unique_together = ('template', 'status', 'planned_exec_date',)

    def __json__(self):
        return {
            'template': self.template,
            'id': self.pk,
        }

    @property
    def actions(self):
        res = {}
        for possible_status in POSSIBLE_STATUSES.get(self.status):
            if STATUS_URL.get(possible_status):
                res[STATUS_URL.get(possible_status)] = URL + reverse('subtask') + str(self.pk) + "/" + STATUS_URL.get(possible_status)
        return res

    def change_status(self, target_status):
        if target_status in POSSIBLE_STATUSES.get(self.status):
            self.status = target_status
        else:
            raise self.InvalidStatusChange(f"Cant change status to {target_status} for task with status {self.status}, start: {self.start}, finish: {self.finish}")
        if IS_FINISH_DATE_UPDATE_REQUIRED.get(target_status, False):
            self.finish = datetime.now()
        if IS_START_DATE_UPDATE_REQUIRED.get(target_status, False):
            self.start = datetime.now()

    def change_status_to_stopped(self):
        self.change_status(STOPPED)

    def change_status_to_error(self):
        self.change_status(ERROR)

    def change_status_to_running(self):
        self.change_status(RUNNING)

    def change_status_to_done(self):
        self.change_status(DONE)

    def change_status_to_canceled(self):
        self.change_status(CANCELED)

    def change_status_to_sent(self):
        self.change_status(SENT)


    def update_progress(self, progress):
        try:
            progress = int(progress)
        except ValueError:
            raise self.InvalidProgressValue(f"{progress} cant be converted to int")
        if self.status == RUNNING:
            self.items_collected += int(progress)
            self.save()
        else:
            raise self.InvalidStatusForProgressTrack(f"Cant increment progress for status {self.status}")
