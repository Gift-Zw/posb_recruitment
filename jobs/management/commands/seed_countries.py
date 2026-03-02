"""
Management command to seed the database with countries (ISO-2 and ISO-3 codes).
Zimbabwe is prioritized at the top of the dropdown.

Usage: python manage.py seed_countries
"""
from django.core.management.base import BaseCommand
from jobs.models import Country


COUNTRIES = [
    # Priority countries (sort_order=0, appear first in dropdowns)
    {"name": "Zimbabwe", "iso2": "ZW", "iso3": "ZWE", "sort_order": 0},
    {"name": "South Africa", "iso2": "ZA", "iso3": "ZAF", "sort_order": 1},
    {"name": "Botswana", "iso2": "BW", "iso3": "BWA", "sort_order": 1},
    {"name": "Zambia", "iso2": "ZM", "iso3": "ZMB", "sort_order": 1},
    {"name": "Mozambique", "iso2": "MZ", "iso3": "MOZ", "sort_order": 1},
    {"name": "Malawi", "iso2": "MW", "iso3": "MWI", "sort_order": 1},
    {"name": "Namibia", "iso2": "NA", "iso3": "NAM", "sort_order": 1},
    {"name": "Tanzania", "iso2": "TZ", "iso3": "TZA", "sort_order": 2},
    {"name": "Kenya", "iso2": "KE", "iso3": "KEN", "sort_order": 2},
    {"name": "Uganda", "iso2": "UG", "iso3": "UGA", "sort_order": 2},
    {"name": "Rwanda", "iso2": "RW", "iso3": "RWA", "sort_order": 2},
    {"name": "Democratic Republic of the Congo", "iso2": "CD", "iso3": "COD", "sort_order": 2},
    {"name": "Eswatini", "iso2": "SZ", "iso3": "SWZ", "sort_order": 2},
    {"name": "Lesotho", "iso2": "LS", "iso3": "LSO", "sort_order": 2},
    # Other African countries (sort_order=5)
    {"name": "Algeria", "iso2": "DZ", "iso3": "DZA", "sort_order": 5},
    {"name": "Angola", "iso2": "AO", "iso3": "AGO", "sort_order": 5},
    {"name": "Benin", "iso2": "BJ", "iso3": "BEN", "sort_order": 5},
    {"name": "Burkina Faso", "iso2": "BF", "iso3": "BFA", "sort_order": 5},
    {"name": "Burundi", "iso2": "BI", "iso3": "BDI", "sort_order": 5},
    {"name": "Cabo Verde", "iso2": "CV", "iso3": "CPV", "sort_order": 5},
    {"name": "Cameroon", "iso2": "CM", "iso3": "CMR", "sort_order": 5},
    {"name": "Central African Republic", "iso2": "CF", "iso3": "CAF", "sort_order": 5},
    {"name": "Chad", "iso2": "TD", "iso3": "TCD", "sort_order": 5},
    {"name": "Comoros", "iso2": "KM", "iso3": "COM", "sort_order": 5},
    {"name": "Congo", "iso2": "CG", "iso3": "COG", "sort_order": 5},
    {"name": "Cote d'Ivoire", "iso2": "CI", "iso3": "CIV", "sort_order": 5},
    {"name": "Djibouti", "iso2": "DJ", "iso3": "DJI", "sort_order": 5},
    {"name": "Egypt", "iso2": "EG", "iso3": "EGY", "sort_order": 5},
    {"name": "Equatorial Guinea", "iso2": "GQ", "iso3": "GNQ", "sort_order": 5},
    {"name": "Eritrea", "iso2": "ER", "iso3": "ERI", "sort_order": 5},
    {"name": "Ethiopia", "iso2": "ET", "iso3": "ETH", "sort_order": 5},
    {"name": "Gabon", "iso2": "GA", "iso3": "GAB", "sort_order": 5},
    {"name": "Gambia", "iso2": "GM", "iso3": "GMB", "sort_order": 5},
    {"name": "Ghana", "iso2": "GH", "iso3": "GHA", "sort_order": 5},
    {"name": "Guinea", "iso2": "GN", "iso3": "GIN", "sort_order": 5},
    {"name": "Guinea-Bissau", "iso2": "GW", "iso3": "GNB", "sort_order": 5},
    {"name": "Liberia", "iso2": "LR", "iso3": "LBR", "sort_order": 5},
    {"name": "Libya", "iso2": "LY", "iso3": "LBY", "sort_order": 5},
    {"name": "Madagascar", "iso2": "MG", "iso3": "MDG", "sort_order": 5},
    {"name": "Mali", "iso2": "ML", "iso3": "MLI", "sort_order": 5},
    {"name": "Mauritania", "iso2": "MR", "iso3": "MRT", "sort_order": 5},
    {"name": "Mauritius", "iso2": "MU", "iso3": "MUS", "sort_order": 5},
    {"name": "Morocco", "iso2": "MA", "iso3": "MAR", "sort_order": 5},
    {"name": "Niger", "iso2": "NE", "iso3": "NER", "sort_order": 5},
    {"name": "Nigeria", "iso2": "NG", "iso3": "NGA", "sort_order": 5},
    {"name": "Sao Tome and Principe", "iso2": "ST", "iso3": "STP", "sort_order": 5},
    {"name": "Senegal", "iso2": "SN", "iso3": "SEN", "sort_order": 5},
    {"name": "Seychelles", "iso2": "SC", "iso3": "SYC", "sort_order": 5},
    {"name": "Sierra Leone", "iso2": "SL", "iso3": "SLE", "sort_order": 5},
    {"name": "Somalia", "iso2": "SO", "iso3": "SOM", "sort_order": 5},
    {"name": "South Sudan", "iso2": "SS", "iso3": "SSD", "sort_order": 5},
    {"name": "Sudan", "iso2": "SD", "iso3": "SDN", "sort_order": 5},
    {"name": "Togo", "iso2": "TG", "iso3": "TGO", "sort_order": 5},
    {"name": "Tunisia", "iso2": "TN", "iso3": "TUN", "sort_order": 5},
    # Key international countries (sort_order=10)
    {"name": "United Kingdom", "iso2": "GB", "iso3": "GBR", "sort_order": 10},
    {"name": "United States", "iso2": "US", "iso3": "USA", "sort_order": 10},
    {"name": "Australia", "iso2": "AU", "iso3": "AUS", "sort_order": 10},
    {"name": "Canada", "iso2": "CA", "iso3": "CAN", "sort_order": 10},
    {"name": "China", "iso2": "CN", "iso3": "CHN", "sort_order": 10},
    {"name": "India", "iso2": "IN", "iso3": "IND", "sort_order": 10},
    {"name": "Germany", "iso2": "DE", "iso3": "DEU", "sort_order": 10},
    {"name": "France", "iso2": "FR", "iso3": "FRA", "sort_order": 10},
    {"name": "Brazil", "iso2": "BR", "iso3": "BRA", "sort_order": 10},
    {"name": "Japan", "iso2": "JP", "iso3": "JPN", "sort_order": 10},
    {"name": "United Arab Emirates", "iso2": "AE", "iso3": "ARE", "sort_order": 10},
    {"name": "Saudi Arabia", "iso2": "SA", "iso3": "SAU", "sort_order": 10},
    {"name": "Netherlands", "iso2": "NL", "iso3": "NLD", "sort_order": 10},
    {"name": "Portugal", "iso2": "PT", "iso3": "PRT", "sort_order": 10},
    {"name": "Ireland", "iso2": "IE", "iso3": "IRL", "sort_order": 10},
    {"name": "New Zealand", "iso2": "NZ", "iso3": "NZL", "sort_order": 10},
    {"name": "Singapore", "iso2": "SG", "iso3": "SGP", "sort_order": 10},
    {"name": "Sweden", "iso2": "SE", "iso3": "SWE", "sort_order": 10},
    {"name": "Switzerland", "iso2": "CH", "iso3": "CHE", "sort_order": 10},
    {"name": "Italy", "iso2": "IT", "iso3": "ITA", "sort_order": 10},
    {"name": "Spain", "iso2": "ES", "iso3": "ESP", "sort_order": 10},
]


class Command(BaseCommand):
    help = "Seed the database with countries and their ISO-2 / ISO-3 codes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing countries before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing countries..."))
            Country.objects.all().delete()

        created = 0
        updated = 0

        for data in COUNTRIES:
            country, was_created = Country.objects.update_or_create(
                iso2=data["iso2"],
                defaults={
                    "name": data["name"],
                    "iso3": data["iso3"],
                    "sort_order": data["sort_order"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(f"  + {country.name} ({country.iso2}/{country.iso3})")
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone: {created} created, {updated} updated, {Country.objects.count()} total countries."
        ))
