from __future__ import absolute_import, division, print_function

import datetime
import os
import random
import string
import sys
import unittest2

from distutils.version import StrictVersion
from mock import patch, Mock, ANY

import stripe
from stripe import six
from stripe.six.moves.urllib.request import urlopen
from stripe.six.moves.urllib.error import HTTPError


MOCK_MINIMUM_VERSION = '0.4.0'
MOCK_PORT = os.environ.get('STRIPE_MOCK_PORT', 12111)


try:
    resp = urlopen('http://localhost:%s/' % MOCK_PORT)
    info = resp.info()
except HTTPError as e:
    info = e.info()
except Exception:
    sys.exit("Couldn't reach stripe-mock at `localhost:%s`. Is "
             "it running? Please see README for setup instructions." %
             MOCK_PORT)

version = info.get('Stripe-Mock-Version')
if version != 'master' \
        and StrictVersion(version) < StrictVersion(MOCK_MINIMUM_VERSION):
    sys.exit("Your version of stripe-mock (%s) is too old. The minimum "
             "version to run this test suite is %s. Please "
             "see its repository for upgrade instructions." %
             (version, MOCK_MINIMUM_VERSION))


class StripeMockTestCase(unittest2.TestCase):
    RESTORE_ATTRIBUTES = ('api_base', 'api_key', 'client_id')

    def setUp(self):
        super(StripeMockTestCase, self).setUp()

        self._stripe_original_attributes = {}

        for attr in self.RESTORE_ATTRIBUTES:
            self._stripe_original_attributes[attr] = getattr(stripe, attr)

        stripe.api_base = 'http://localhost:%s' % MOCK_PORT
        stripe.api_key = 'sk_test_123'
        stripe.client_id = 'ca_123'

        self._real_request = stripe.api_requestor.APIRequestor.request
        self._stubbed_requests = {}

        self.request_patcher = patch(
            'stripe.api_requestor.APIRequestor.request',
            side_effect=self._patched_request,
            autospec=True)
        self.request_spy = self.request_patcher.start()

    def tearDown(self):
        super(StripeMockTestCase, self).tearDown()

        self.request_patcher.stop()

        for attr in self.RESTORE_ATTRIBUTES:
            setattr(stripe, attr, self._stripe_original_attributes[attr])

    def _patched_request(self, requestor, method, url, *args, **kwargs):
        if (method, url) in self._stubbed_requests:
            response_body = self._stubbed_requests.pop((method, url))
            return response_body, stripe.api_key
        return self._real_request(requestor, method, url, *args, **kwargs)

    def stub_request(self, method, url, response_body={}):
        self._stubbed_requests[(method, url)] = response_body

    def assert_requested(self, method, url, params=ANY, headers=ANY):
        called = False
        exception = None

        # Sadly, ANY does not match a missing optional argument, so we
        # check all the possible signatures of the request method
        possible_called_args = []
        possible_called_args.append((ANY, method, url))
        possible_called_args.append((ANY, method, url, params))
        possible_called_args.append((ANY, method, url, params, headers))

        for args in possible_called_args:
            try:
                self.request_spy.assert_called_with(*args)
            except AssertionError as e:
                exception = e
            else:
                called = True
                break

        if not called:
            raise exception


NOW = datetime.datetime.now()

DUMMY_CHARGE = {
    'amount': 100,
    'currency': 'usd',
    'source': 'tok_visa'
}

DUMMY_PLAN = {
    'amount': 2000,
    'interval': 'month',
    'name': 'Amazing Gold Plan',
    'currency': 'usd',
    'id': ('stripe-test-gold-' +
           ''.join(random.choice(string.ascii_lowercase) for x in range(10)))
}


class StripeTestCase(unittest2.TestCase):
    RESTORE_ATTRIBUTES = ('api_version', 'api_key', 'client_id')

    def setUp(self):
        super(StripeTestCase, self).setUp()

        self._stripe_original_attributes = {}

        for attr in self.RESTORE_ATTRIBUTES:
            self._stripe_original_attributes[attr] = getattr(stripe, attr)

        api_base = os.environ.get('STRIPE_API_BASE')
        if api_base:
            stripe.api_base = api_base
        stripe.api_key = os.environ.get(
            'STRIPE_API_KEY', 'tGN0bIwXnHdwOa85VABjPdSn8nWY7G7I')
        stripe.api_version = os.environ.get(
            'STRIPE_API_VERSION', '2017-04-06')

    def tearDown(self):
        super(StripeTestCase, self).tearDown()

        for attr in self.RESTORE_ATTRIBUTES:
            setattr(stripe, attr, self._stripe_original_attributes[attr])


class StripeUnitTestCase(StripeTestCase):
    REQUEST_LIBRARIES = ['urlfetch', 'requests', 'pycurl', 'urllib.request']

    def setUp(self):
        super(StripeUnitTestCase, self).setUp()

        self.request_patchers = {}
        self.request_mocks = {}
        for lib in self.REQUEST_LIBRARIES:
            patcher = patch("stripe.http_client.%s" % (lib,))

            self.request_mocks[lib] = patcher.start()
            self.request_patchers[lib] = patcher

    def tearDown(self):
        super(StripeUnitTestCase, self).tearDown()

        for patcher in six.itervalues(self.request_patchers):
            patcher.stop()


class StripeApiTestCase(StripeTestCase):

    def setUp(self):
        super(StripeApiTestCase, self).setUp()

        self.requestor_patcher = patch('stripe.api_requestor.APIRequestor')
        self.requestor_class_mock = self.requestor_patcher.start()
        self.requestor_mock = self.requestor_class_mock.return_value

    def tearDown(self):
        super(StripeApiTestCase, self).tearDown()

        self.requestor_patcher.stop()

    def mock_response(self, res):
        self.requestor_mock.request = Mock(return_value=(res, 'reskey'))


class StripeResourceTest(StripeApiTestCase):

    def setUp(self):
        super(StripeResourceTest, self).setUp()
        self.mock_response({})
