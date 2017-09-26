import random

from django.conf import settings
from django.db import IntegrityError
from django.db import models
from django.dispatch import Signal
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import CITextField

from .settings import (
    COUPON_TYPES,
    CODE_LENGTH,
    CODE_CHARS,
    SEGMENTED_CODES,
    SEGMENT_LENGTH,
    SEGMENT_SEPARATOR,
)


try:
    user_model = settings.AUTH_USER_MODEL
except AttributeError:
    from django.contrib.auth.models import User as user_model
redeem_done = Signal(providing_args=["coupon"])


class CouponManager(models.Manager):
    def create_coupon(
            self, type, value, users=[], valid_from=None, valid_until=None,
            prefix="", campaign=None, user_limit=None, limit_per_user=None):
        coupon = Coupon(
            value=value,
            code=Coupon.generate_code(prefix),
            type=type,
            valid_until=valid_until,
            campaign=campaign,
        )
        if valid_from is not None:
            coupon.valid_from = valid_from
        if user_limit is not None:  # otherwise use default value of model
            coupon.user_limit = user_limit
        if limit_per_user is not None: # otherwise use default value of model
            coupon.limit_per_user = limit_per_user
        try:
            coupon.save()
        except IntegrityError:
            # Try again with other code
            coupon = Coupon.objects.create_coupon(type, value, users, valid_until, prefix, campaign)
        if not isinstance(users, list):
            users = [users]
        for user in users:
            if user:
                CouponUser(user=user, coupon=coupon).save()
        return coupon

    def create_coupons(self, quantity, type, value, valid_from=None,
            valid_until=None, prefix="", campaign=None, limit_per_user=None):
        coupons = []
        for i in range(quantity):
            coupons.append(
                self.create_coupon(
                    type=type,
                    value=value,
                    users=None,
                    valid_from=valid_from,
                    valid_until=valid_until,
                    prefix=prefix,
                    campaign=campaign
                )
            )
        return coupons

    def used(self):
        return self.exclude(users__last_redeemed_at__isnull=True)

    def unused(self):
        return self.filter(users__last_redeemed_at__isnull=True)

    def expired(self):
        return self.filter(valid_until__lt=timezone.now())


@python_2_unicode_compatible
class Coupon(models.Model):
    value = models.IntegerField(_("Value"), help_text=_("Arbitrary coupon value"))
    code = CITextField(
        _("Code"), max_length=30, unique=True, blank=True,
        help_text=_("Leaving this field empty will generate a random code."))
    type = models.CharField(_("Type"), max_length=20, choices=COUPON_TYPES)
    user_limit = models.PositiveIntegerField(_("User limit"), default=1)
    limit_per_user = models.PositiveIntegerField(
        _("Coupon redeem limit per User"),
        default=1
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    valid_from = models.DateTimeField(
        _("Valid from"), default=timezone.now,
        help_text=_("Defaults to start right away"))
    valid_until = models.DateTimeField(
        _("Valid until"), blank=True, null=True,
        help_text=_("Leave empty for coupons that never expire"))
    campaign = models.ForeignKey('Campaign', verbose_name=_("Campaign"), blank=True, null=True, related_name='coupons')

    objects = CouponManager()

    class Meta:
        ordering = ['created_at']
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = Coupon.generate_code()
        super(Coupon, self).save(*args, **kwargs)

    def expired(self):
        return self.valid_until is not None and self.valid_until < timezone.now()

    @property
    def is_redeemed(self):
        """ Returns true is a coupon is redeemed (completely for all users) otherwise returns false. """
        fully_redeemed_users = [
            user for user in self.users.select_related('coupon').filter(
                last_redeemed_at__isnull=False
            ) if user.fully_redeemed
        ]
        return len(fully_redeemed_users) >= self.user_limit and self.user_limit is not 0

    @property
    def last_redeemed_at(self):
        coupon_user = self.users.filter(
            last_redeemed_at__isnull=False
        ).order_by('last_redeemed_at').last()

        if coupon_user:
            return coupon_user.last_redeemed_at

    @classmethod
    def generate_code(cls, prefix="", segmented=SEGMENTED_CODES):
        code = "".join(random.choice(CODE_CHARS) for i in range(CODE_LENGTH))
        if segmented:
            code = SEGMENT_SEPARATOR.join([code[i:i + SEGMENT_LENGTH] for i in range(0, len(code), SEGMENT_LENGTH)])
            return prefix + code
        else:
            return prefix + code

    def redeem(self, user=None):
        try:
            coupon_user = self.users.get(user=user)
        except CouponUser.DoesNotExist:
            try:  # silently fix unbouned or nulled coupon users
                coupon_user = self.users.get(user__isnull=True)
                coupon_user.user = user
            except CouponUser.DoesNotExist:
                coupon_user = CouponUser(coupon=self, user=user)
        coupon_user.last_redeemed_at = timezone.now()
        coupon_user.redeem_count += 1
        coupon_user.save()
        redeem_done.send(sender=self.__class__, coupon=self)


@python_2_unicode_compatible
class Campaign(models.Model):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class CouponUser(models.Model):
    coupon = models.ForeignKey(Coupon, related_name='users')
    user = models.ForeignKey(user_model, verbose_name=_("User"), null=True, blank=True)
    last_redeemed_at = models.DateTimeField(_("Last redeemed at"), blank=True, null=True)
    redeem_count = models.PositiveIntegerField(_("Redeem count"), default=0)

    class Meta:
        unique_together = (('coupon', 'user'),)

    @property
    def fully_redeemed(self):
        return self.redeem_count >= self.coupon.limit_per_user

    def __str__(self):
        return str(self.user)
