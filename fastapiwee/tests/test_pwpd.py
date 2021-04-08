import random
import string
from unittest import TestCase

import peewee as pw
import pydantic as pd
from playhouse.shortcuts import model_to_dict

from fastapiwee.pwpd import PwPdMeta, PwPdModel, PwPdModelFactory

DB = pw.SqliteDatabase(':memory:')


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


class PwPdMetaTestCase(TestCase):
    def test_creation(self):
        class TestModelSerializer(pd.BaseModel, metaclass=PwPdMeta):
            class Config:
                pw_model = TestModel
                pw_fields = {'id', 'text', 'number', 'related', 'childs'}
                pw_exclude = {'text'}
                pw_nest_fk = True
                pw_nest_backrefs = True

        for field_in_check in {'id', 'number', 'related', 'childs'}:
            self.assertIn(field_in_check, TestModelSerializer.__fields__)

        for field_not_in_check in {'is_test', 'text'}:
            self.assertNotIn(field_not_in_check, TestModelSerializer.__fields__)

        # FK field nested
        self.assertTrue(issubclass(TestModelSerializer.__fields__['related'].type_, PwPdModel))

        # Backref type is List[Serializer]
        self.assertIs(TestModelSerializer.__fields__['childs'].shape, pd.fields.SHAPE_LIST)
        self.assertTrue(issubclass(TestModelSerializer.__fields__['childs'].type_, PwPdModel))

        class TestModelSerializer(pd.BaseModel, metaclass=PwPdMeta):
            class Config:
                pw_model = TestModel
                pw_exclude_pk = True
                pw_nest_fk = False
                pw_nest_backrefs = False

        # All fields are in serializer by default
        model_fields = set(TestModel._meta.fields.keys())
        model_fields.remove('id')  # pw_exclude_pk = True
        model_fields.remove('related')  # pw_nest_fk = False
        model_fields.add('related_id')

        for field_in_check in model_fields:
            self.assertIn(field_in_check, TestModelSerializer.__fields__)

        # FK field not nested, just an ID
        self.assertIs(TestModelSerializer.__fields__['related_id'].type_, int)

        # Backref not included
        self.assertNotIn('childs', TestModelSerializer.__fields__)


class PwPdModelTestCase(TestCase):
    def setUp(self):
        self.tm_amount = 3
        self.child_tm_amount = 4
        create_dummy_data()

    def tearDown(self):
        DB.drop_tables((ParentTestModel, TestModel, ChildTestModel))

    def test_serialization(self):
        class TestModelSerializer(PwPdModel):
            class Config:
                pw_model = TestModel
                pw_nest_fk = True
                pw_nest_backrefs = True

        test_model = TestModel.select().order_by('?').first()
        test_model_dict = model_to_dict(test_model)
        serialized = TestModelSerializer.from_orm(test_model)
        serialized_dict = serialized.dict()

        # check values equal
        for field_check in TestModel._meta.fields.keys():
            self.assertEqual(test_model_dict[field_check], serialized_dict[field_check])

        # check backref
        self.assertEqual(test_model.childs.count(), len(serialized_dict['childs']))

    def test_make_serializer(self):
        serializer = PwPdModel.make_serializer(TestModel)
        test_model = TestModel.select().order_by('?').first()
        test_model_dict = model_to_dict(test_model)
        test_model_dict['related_id'] = test_model_dict.pop('related')['id']  # FK no nested, just ID
        serialized = serializer.from_orm(test_model)
        serialized_dict = serialized.dict()

        # check values equal
        for field_check in test_model_dict.keys():
            self.assertEqual(test_model_dict[field_check], serialized_dict[field_check])

        serializer = PwPdModel.make_serializer(TestModel, pw_fields={'id'})
        serialized = serializer.from_orm(test_model)

        self.assertListEqual(['id'], list(serialized.dict().keys()))

        with self.assertRaises(ValueError):
            PwPdModel.make_serializer(TestModel, pw_model=ParentTestModel)


class PwPdModelFactoryTestCase(TestCase):
    def setUp(self):
        create_dummy_data()
        self.test_model_pwpd = PwPdModelFactory(TestModel)

    def test_read_pd(self):
        test_model = TestModel.select().order_by('?').first()
        test_model_dict = model_to_dict(test_model)
        test_model_dict['related_id'] = test_model_dict.pop('related')['id']  # FK no nested, just ID
        serialized = self.test_model_pwpd.read_pd.from_orm(test_model)
        serialized_dict = serialized.dict()

        # check values equal
        for field_check in test_model_dict.keys():
            self.assertEqual(test_model_dict[field_check], serialized_dict[field_check])

    def test_write_pd(self):
        valid_data = {
            'text': 'Cucumber',
            'number': 300,
            'is_test': False,
            'related_id': ParentTestModel.select().first().id,
        }

        self.test_model_pwpd.write_pd(**valid_data)

        minimal_valid_data = {
            'text': 'Cucumber',
            'related_id': ParentTestModel.select().first().id,
        }
        expected_data = {
            'text': 'Cucumber',
            'number': None,
            'is_test': True,
            'related_id': ParentTestModel.select().first().id,
        }

        data = self.test_model_pwpd.write_pd(**minimal_valid_data)

        self.assertDictEqual(data.dict(), expected_data)

        invalid_data = {
            'id': 1,
            'text': 23,
            'is_test': None,
        }
        expected_errors = {
            'id': 'value_error.extra',
            'is_test': 'type_error.none.not_allowed',
            'related_id': 'value_error.missing',
        }

        with self.assertRaises(pd.ValidationError) as raised:
            self.test_model_pwpd.write_pd(**invalid_data)

        raised_errors = dict()
        for error in raised.exception.errors():
            raised_errors[error['loc'][0]] = error['type']

        self.assertDictEqual(raised_errors, expected_errors)
