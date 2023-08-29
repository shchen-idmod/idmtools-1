"""idmtools local platform api tools.

Copyright 2021, Bill & Melinda Gates Foundation. All rights reserved.
"""
import re
import urllib

from webargs.flaskparser import FlaskParser
import six
from flask_restful import abort
from flask_restful.reqparse import Argument
from werkzeug.datastructures import MultiDict


class dotdict(dict):
    """dot.notation access to dictionary attributes."""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def validate_tags(tags):
    """
    Ensure tags are valid.

    Args:
        tags: Tags to validate

    Returns:
        None
    """
    # validate the tags
    if tags is not None:
        for i in range(len(tags)):
            if ',' in tags[i]:
                tags[i] = tags[i].split(',')

            if type(tags[i]) not in [list, tuple] or len(tags[i]) > 2:
                abort(400, message='Tags needs to be in the format "name,value"')


class LocalArgument(Argument):
    """Wraps the Argument class from Flask Restful to not error when fetching the json object on non-json requests."""

    def source(self, request):
        """Pulls values off the request in the provided location.

        :param request: The flask request object to parse arguments from
        """
        if isinstance(self.location, six.string_types):
            super().source(request)
        else:
            values = MultiDict()
            for location in self.location:
                if location == "json" and not request.is_json:
                    value = None
                else:
                    value = getattr(request, location, None)
                if callable(value):
                    value = value()
                if value is not None:
                    values.update(value)
            return values

        return MultiDict()


class TagsParser(FlaskParser):
    """Parses tags arguments

    This parser handles nested query args. It expects nested levels
    delimited by a period and then deserializes the query args into a
    nested dict.

    For example, the URL query params `?tags=a,b&tags=c,d`
    will yield the following dict:

        {
            'tags': [
                ['a, b'],
                ['c, d']]
        }
    """

    def load_querystring(self, req, schema):
        return _structure_tags(req.args)


def _structure_tags(byte_string):
    input_string = byte_string.decode('utf-8')

    # Parse the string into a dictionary using urllib.parse.parse_qs
    parsed_data = urllib.parse.parse_qs(input_string)

    for key, values in parsed_data.items():
        if 'tags' in key and values is not None:
            validate_tags(values)
            return {key: values}
    return {}
