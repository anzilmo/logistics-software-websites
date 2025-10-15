from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from .models import Plan, Membership, Profile

@receiver(post_save, sender=Profile)
def sync_membership_from_profile(sender, instance: "Profile", **kwargs):
    """
    Keep exactly one active Membership in sync with profile.membership_tier.
    """
    user = instance.user
    tier = (instance.membership_tier.name if instance.membership_tier else "").strip().lower()
    if not tier:
        # no tier -> cancel any active membership
        m = user.memberships.filter(status="active").first()
        if m:
            m.cancel(when=timezone.now())
        return

    plan = Plan.objects.filter(slug=tier, active=True).first()
    if not plan:
        # unknown tier -> do nothing (or cancel)
        return

    # ensure unique active membership (constraint already enforces this)
    active = user.memberships.filter(status="active").first()
    if active:
        # switch plan + snapshot new price
        active.plan = plan
        active.price = plan.price
        active.currency = plan.currency
        active.billing_cycle = plan.billing_cycle
        active.auto_renew = True
        active.ends_at = None
        active.save(update_fields=["plan","price","currency","billing_cycle","auto_renew","ends_at"])
    else:
        Membership.objects.create(
            user=user,
            plan=plan,
            status="active",
            started_at=timezone.now(),
            auto_renew=True,
            price=plan.price,              # snapshot
            currency=plan.currency,
            billing_cycle=plan.billing_cycle,
        )