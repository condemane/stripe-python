from __future__ import absolute_import, division, print_function

import stripe
from tests.helper import StripeMockTestCase


class CouponTest(StripeMockTestCase):
    def test_is_listable(self):
        coupons = stripe.Coupon.list()
        self.assert_requested(
            'get',
            '/v1/coupons'
        )
        self.assertIsInstance(coupons.data, list)
        self.assertIsInstance(coupons.data[0], stripe.Coupon)

    def test_is_retrievable(self):
        coupon = stripe.Coupon.retrieve('25OFF')
        self.assert_requested(
            'get',
            '/v1/coupons/25OFF'
        )
        self.assertIsInstance(coupon, stripe.Coupon)

    def test_is_creatable(self):
        coupon = stripe.Coupon.create(
            percent_off=25,
            duration='repeating',
            duration_in_months=3,
            id='250FF'
        )
        self.assert_requested(
            'post',
            '/v1/coupons'
        )
        self.assertIsInstance(coupon, stripe.Coupon)

    def test_is_saveable(self):
        coupon = stripe.Coupon.retrieve('25OFF')
        coupon.metadata['key'] = 'value'
        coupon.save()
        self.assert_requested(
            'post',
            '/v1/coupons/%s' % coupon.id
        )

    def test_is_modifiable(self):
        coupon = stripe.Coupon.modify('25OFF', metadata={'key': 'value'})
        self.assert_requested(
            'post',
            '/v1/coupons/25OFF'
        )
        self.assertIsInstance(coupon, stripe.Coupon)

    def test_is_deletable(self):
        coupon = stripe.Coupon.retrieve('25OFF')
        coupon.delete()
        self.assert_requested(
            'delete',
            '/v1/coupons/%s' % coupon.id
        )
        self.assertIsInstance(coupon, stripe.Coupon)
