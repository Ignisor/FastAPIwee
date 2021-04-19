import os
import random
import string

import peewee as pw
from fastapi import FastAPI

from fastapiwee.crud.viewsets import AutoFastAPIViewSet

DB = pw.SqliteDatabase('/tmp/fastapiwee_example.db')


class ParentTestModel(pw.Model):
    id = pw.AutoField()
    text = pw.TextField()

    class Meta:
        database = DB


class TestModel(pw.Model):
    id = pw.AutoField()
    text = pw.TextField()
    number = pw.IntegerField(null=True)
    is_test = pw.BooleanField(default=True)
    related = pw.ForeignKeyField(ParentTestModel, backref='test_models')

    class Meta:
        database = DB


class ChildTestModel(pw.Model):
    id = pw.AutoField()
    test = pw.ForeignKeyField(TestModel, backref='childs')

    class Meta:
        database = DB


def create_dummy_data(amount=10, childs=5):
    DB.create_tables((ParentTestModel, TestModel, ChildTestModel))

    rel_tm = ParentTestModel.create(
        text='Parent Test',
    )

    for _ in range(amount):
        tm = TestModel.create(
            text=f'Test {"".join(random.choices(string.ascii_letters, k=8))}',
            number=random.randint(0, 1e10),
            is_test=bool(random.getrandbits(1)),
            related=rel_tm,
        )

        for _ in range(childs):
            ChildTestModel.create(
                test=tm,
            )


def drop_dummy_data():
    DB.drop_tables((ParentTestModel, TestModel, ChildTestModel))
    DB.close()
    os.remove(DB.database)


app = FastAPI(on_startup=(create_dummy_data,), on_shutdown=(drop_dummy_data,))

AutoFastAPIViewSet(TestModel, app)
AutoFastAPIViewSet(ParentTestModel, app)
AutoFastAPIViewSet(ChildTestModel, app)
