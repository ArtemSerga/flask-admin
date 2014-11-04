import warnings

from flask.ext.admin.babel import lazy_gettext
from flask.ext.admin.model import filters
from flask.ext.admin.contrib.sqla import tools


class BaseSQLAFilter(filters.BaseFilter):
    """
        Base SQLAlchemy filter.
    """
    def __init__(self, column, name, options=None, data_type=None):
        """
            Constructor.

            :param column:
                Model field
            :param name:
                Display name
            :param options:
                Fixed set of options
            :param data_type:
                Client data type
        """
        super(BaseSQLAFilter, self).__init__(name, options, data_type)

        self.column = column


# Common filters
class FilterEqual(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column == value)

    def operation(self):
        return lazy_gettext('equals')


class FilterNotEqual(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column != value)

    def operation(self):
        return lazy_gettext('not equal')


class FilterLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(self.column.ilike(stmt))

    def operation(self):
        return lazy_gettext('contains')


class FilterNotLike(BaseSQLAFilter):
    def apply(self, query, value):
        stmt = tools.parse_like_term(value)
        return query.filter(~self.column.ilike(stmt))

    def operation(self):
        return lazy_gettext('not contains')


class FilterGreater(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column > value)

    def operation(self):
        return lazy_gettext('greater than')


class FilterSmaller(BaseSQLAFilter):
    def apply(self, query, value):
        return query.filter(self.column < value)

    def operation(self):
        return lazy_gettext('smaller than')


# Customized type filters
class BooleanEqualFilter(FilterEqual, filters.BaseBooleanFilter):
    pass


class BooleanNotEqualFilter(FilterNotEqual, filters.BaseBooleanFilter):
    pass


class FilterManyToOne(BaseSQLAFilter):

    _filter_joins = []

    cache_enabled = False

    def __init__(self, column, name=None, options=None, data_type=None, model=None, display_field=None):
        """
        Create Select box by foreign key

        :param column:
            SA relational field represented as string
        :param name:
            Filter name
        :param model:
            SA current model class
        :param display_field:
            SA Field represented as string to use in choices displaying
        :return:
        """
        super(FilterManyToOne, self).__init__(column, name, options, data_type)
        if not model:
            raise Exception('Pass `model` keyword argument')
        if not name:
            raise Exception('Pass `name` keyword argument')

        self.model = model
        self.display_field = display_field
        if isinstance(column, basestring):
            parent_attrs = column.split('.')
            self.column = getattr(self.model, parent_attrs[0]).property
            if '.' in column:
                for i, attribute in enumerate(parent_attrs):
                    self.parent_property = getattr(model, attribute).property
                    model = self.parent_property.mapper.class_
                    if i != (len(parent_attrs) - 1):
                        self._filter_joins.append(model.__table__)
                self.parent_model = model
        if not hasattr(self, 'parent_model'):
            self.parent_model = getattr(self.model, column).property.mapper.class_
            self.parent_property = getattr(self.model, column).property

    def operation(self):
        return lazy_gettext('equals')

    def validate(self, value):
        return True

    def get_query(self):
        return self.parent_model.query

    def get_options(self, view):
        query = self.get_query()
        for table in self._filter_joins:
            if (
                table.name != view.model.__tablename__
                and table.name not in view._filter_joins
            ):
                view._filter_joins[table.name] = [table]
        display_field = getattr(self, 'display_field', None)
        if display_field:
            return [
                (id, label)
                for id, label in query.values('id', display_field)
            ]
        else:
            return [
                (obj.id, unicode(obj))
                for obj in query
            ]

    def apply(self, query, value):
        field = self.parent_property.local_remote_pairs[0][0]
        query = query.filter(field == value)
        return query


# Base SQLA filter field converter
class FilterConverter(filters.BaseFilterConverter):
    strings = (FilterEqual, FilterNotEqual, FilterLike, FilterNotLike)
    numeric = (FilterEqual, FilterNotEqual, FilterGreater, FilterSmaller)
    bool = (BooleanEqualFilter, BooleanNotEqualFilter)
    enum = (FilterEqual, FilterNotEqual)

    def convert(self, type_name, column, name, **kwargs):
        if type_name.lower() in self.converters:
            return self.converters[type_name.lower()](column, name, **kwargs)

        return None

    @filters.convert('string', 'unicode', 'text', 'unicodetext', 'varchar')
    def conv_string(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.strings]

    @filters.convert('boolean', 'tinyint')
    def conv_bool(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.bool]

    @filters.convert('integer', 'smallinteger', 'numeric', 'float', 'biginteger')
    def conv_int(self, column, name, **kwargs):
        return [f(column, name, **kwargs) for f in self.numeric]

    @filters.convert('date')
    def conv_date(self, column, name, **kwargs):
        return [f(column, name, data_type='datepicker', **kwargs) for f in self.numeric]

    @filters.convert('datetime')
    def conv_datetime(self, column, name, **kwargs):
        return [f(column, name, data_type='datetimepicker', **kwargs) for f in self.numeric]

    @filters.convert('enum')
    def conv_enum(self, column, name, options=None, **kwargs):
        if not options:
            options = [
                (v, v)
                for v in column.type.enums
            ]
        return [f(column, name, options, **kwargs) for f in self.enum]
