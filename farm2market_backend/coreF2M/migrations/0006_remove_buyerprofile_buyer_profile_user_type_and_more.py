# Generated by Django 5.2.3 on 2025-06-26 20:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coreF2M', '0005_alter_buyerprofile_buyer_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='buyerprofile',
            name='buyer_profile_user_type',
        ),
        migrations.RemoveConstraint(
            model_name='buyerprofile',
            name='birth_date_not_future',
        ),
        migrations.RemoveConstraint(
            model_name='farmerlisting',
            name='listing_farmer_user_type',
        ),
        migrations.RemoveConstraint(
            model_name='farmerlisting',
            name='listing_farmer_approved',
        ),
        migrations.RemoveConstraint(
            model_name='farmerprofile',
            name='farmer_profile_user_type',
        ),
        migrations.RemoveConstraint(
            model_name='reservation',
            name='reservation_buyer_user_type',
        ),
        migrations.RemoveConstraint(
            model_name='reservation',
            name='reservation_buyer_approved',
        ),
        migrations.RemoveConstraint(
            model_name='reservation',
            name='reservation_total_calculation',
        ),
        migrations.RemoveConstraint(
            model_name='reservation',
            name='approved_at_required_when_approved',
        ),
        migrations.RemoveConstraint(
            model_name='reservation',
            name='rejection_reason_required_when_rejected',
        ),
    ]
