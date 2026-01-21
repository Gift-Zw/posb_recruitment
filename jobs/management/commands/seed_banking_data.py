"""
Management command to seed the database with banking job categories and skills.
Designed for POSB (People's Own Savings Bank) in Zimbabwe.

Usage: python manage.py seed_banking_data
"""
from django.core.management.base import BaseCommand
from jobs.models import JobCategory, Skill


class Command(BaseCommand):
    help = 'Seed the database with banking job categories and skills for POSB Zimbabwe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories and skills before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing categories and skills...'))
            JobCategory.objects.all().delete()
            Skill.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing data.'))

        # Job Categories for Banking
        categories_data = [
            {
                'name': 'Banking Operations',
                'description': 'Roles in day-to-day banking operations, transaction processing, and branch operations.'
            },
            {
                'name': 'Customer Service',
                'description': 'Customer-facing roles including tellers, customer service representatives, and relationship managers.'
            },
            {
                'name': 'Finance & Accounting',
                'description': 'Financial analysis, accounting, budgeting, and financial reporting positions.'
            },
            {
                'name': 'IT & Technology',
                'description': 'Information technology roles including software development, system administration, and cybersecurity.'
            },
            {
                'name': 'Risk Management',
                'description': 'Risk assessment, credit risk analysis, operational risk, and enterprise risk management.'
            },
            {
                'name': 'Compliance & Legal',
                'description': 'Regulatory compliance, legal affairs, anti-money laundering, and regulatory reporting.'
            },
            {
                'name': 'Human Resources',
                'description': 'HR management, recruitment, employee relations, and organizational development.'
            },
            {
                'name': 'Marketing & Communications',
                'description': 'Marketing, brand management, public relations, and customer communications.'
            },
            {
                'name': 'Credit & Lending',
                'description': 'Credit analysis, loan processing, credit risk assessment, and loan portfolio management.'
            },
            {
                'name': 'Treasury & Investments',
                'description': 'Treasury operations, investment management, foreign exchange, and liquidity management.'
            },
            {
                'name': 'Branch Management',
                'description': 'Branch operations management, branch administration, and regional management roles.'
            },
            {
                'name': 'Internal Audit',
                'description': 'Internal auditing, compliance auditing, and risk assessment auditing.'
            },
            {
                'name': 'Product Development',
                'description': 'Banking product development, product management, and innovation roles.'
            },
            {
                'name': 'Digital Banking',
                'description': 'Digital banking solutions, mobile banking, online banking, and fintech integration.'
            },
        ]

        # Skills for Banking
        skills_data = [
            # Banking & Finance Skills
            {'name': 'Banking Operations', 'description': 'Knowledge of banking operations, procedures, and processes.'},
            {'name': 'Credit Analysis', 'description': 'Ability to analyze creditworthiness and assess loan applications.'},
            {'name': 'Financial Analysis', 'description': 'Financial statement analysis, ratio analysis, and financial modeling.'},
            {'name': 'Risk Assessment', 'description': 'Identifying, analyzing, and mitigating financial and operational risks.'},
            {'name': 'Loan Processing', 'description': 'Processing loan applications, documentation, and disbursement.'},
            {'name': 'Treasury Management', 'description': 'Managing bank liquidity, investments, and treasury operations.'},
            {'name': 'Foreign Exchange', 'description': 'FX trading, currency conversion, and foreign exchange risk management.'},
            {'name': 'Investment Management', 'description': 'Portfolio management, investment analysis, and asset allocation.'},
            {'name': 'Regulatory Compliance', 'description': 'Knowledge of banking regulations and compliance requirements.'},
            {'name': 'Anti-Money Laundering (AML)', 'description': 'AML procedures, KYC, and suspicious transaction monitoring.'},
            {'name': 'Know Your Customer (KYC)', 'description': 'Customer due diligence and verification procedures.'},
            {'name': 'Banking Regulations', 'description': 'Knowledge of Reserve Bank of Zimbabwe regulations and banking laws.'},
            
            # Customer Service Skills
            {'name': 'Customer Relationship Management', 'description': 'Building and maintaining customer relationships.'},
            {'name': 'Customer Service', 'description': 'Providing excellent customer service and support.'},
            {'name': 'Cross-selling', 'description': 'Identifying and promoting relevant banking products to customers.'},
            {'name': 'Account Management', 'description': 'Managing customer accounts and addressing account-related queries.'},
            {'name': 'Conflict Resolution', 'description': 'Resolving customer complaints and disputes effectively.'},
            
            # Technical Skills
            {'name': 'Core Banking Systems', 'description': 'Experience with core banking software (e.g., Flexcube, Temenos).'},
            {'name': 'SQL', 'description': 'Database querying and management using SQL.'},
            {'name': 'Python', 'description': 'Python programming for banking applications and automation.'},
            {'name': 'Java', 'description': 'Java development for banking systems.'},
            {'name': '.NET', 'description': '.NET framework development.'},
            {'name': 'Cybersecurity', 'description': 'Information security, network security, and data protection.'},
            {'name': 'System Administration', 'description': 'Managing and maintaining IT systems and infrastructure.'},
            {'name': 'Database Management', 'description': 'Database design, administration, and optimization.'},
            {'name': 'API Integration', 'description': 'Integrating banking systems with third-party APIs.'},
            {'name': 'Cloud Computing', 'description': 'Cloud infrastructure and services (AWS, Azure, etc.).'},
            {'name': 'Mobile App Development', 'description': 'Developing mobile banking applications.'},
            {'name': 'Web Development', 'description': 'Web application development for banking portals.'},
            
            # Accounting & Finance Skills
            {'name': 'Accounting', 'description': 'General accounting principles and practices.'},
            {'name': 'Financial Reporting', 'description': 'Preparing financial statements and reports.'},
            {'name': 'IFRS', 'description': 'International Financial Reporting Standards.'},
            {'name': 'Budgeting', 'description': 'Budget preparation, monitoring, and variance analysis.'},
            {'name': 'Cost Accounting', 'description': 'Cost analysis and cost management.'},
            {'name': 'Auditing', 'description': 'Internal and external auditing procedures.'},
            {'name': 'Taxation', 'description': 'Tax compliance and tax planning.'},
            
            # Soft Skills
            {'name': 'Communication', 'description': 'Effective verbal and written communication skills.'},
            {'name': 'Leadership', 'description': 'Leading teams and managing people.'},
            {'name': 'Teamwork', 'description': 'Collaborating effectively with team members.'},
            {'name': 'Problem Solving', 'description': 'Analyzing problems and developing solutions.'},
            {'name': 'Analytical Thinking', 'description': 'Critical thinking and data analysis.'},
            {'name': 'Attention to Detail', 'description': 'Meticulous attention to accuracy and detail.'},
            {'name': 'Time Management', 'description': 'Managing time and priorities effectively.'},
            {'name': 'Negotiation', 'description': 'Negotiating terms and agreements.'},
            {'name': 'Presentation Skills', 'description': 'Presenting information clearly and effectively.'},
            {'name': 'Project Management', 'description': 'Managing projects from initiation to completion.'},
            
            # Zimbabwe-Specific Skills
            {'name': 'Zimbabwe Banking Regulations', 'description': 'Knowledge of RBZ regulations and local banking laws.'},
            {'name': 'Zimbabwe Financial Markets', 'description': 'Understanding of Zimbabwe financial markets and economy.'},
            {'name': 'Multi-currency Operations', 'description': 'Operating in multi-currency environment (USD, ZWL, etc.).'},
            {'name': 'Shona Language', 'description': 'Proficiency in Shona language for customer service.'},
            {'name': 'Ndebele Language', 'description': 'Proficiency in Ndebele language for customer service.'},
            
            # Specialized Banking Skills
            {'name': 'Retail Banking', 'description': 'Retail banking products and services.'},
            {'name': 'Corporate Banking', 'description': 'Corporate banking and commercial lending.'},
            {'name': 'Trade Finance', 'description': 'Letters of credit, trade documentation, and trade finance products.'},
            {'name': 'Wealth Management', 'description': 'Private banking and wealth management services.'},
            {'name': 'Mortgage Lending', 'description': 'Mortgage origination, processing, and servicing.'},
            {'name': 'Microfinance', 'description': 'Microfinance operations and small business lending.'},
            {'name': 'Digital Payments', 'description': 'Digital payment systems, mobile money, and payment processing.'},
            {'name': 'Card Operations', 'description': 'Credit card and debit card operations and management.'},
        ]

        # Create Categories
        self.stdout.write(self.style.SUCCESS('Creating job categories...'))
        categories_created = 0
        categories_updated = 0
        
        for cat_data in categories_data:
            category, created = JobCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                categories_created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created category: {category.name}'))
            else:
                categories_updated += 1
                category.description = cat_data['description']
                category.save()
                self.stdout.write(self.style.WARNING(f'  Updated category: {category.name}'))

        # Create Skills
        self.stdout.write(self.style.SUCCESS('\nCreating skills...'))
        skills_created = 0
        skills_updated = 0
        
        for skill_data in skills_data:
            skill, created = Skill.objects.get_or_create(
                name=skill_data['name'],
                defaults={'description': skill_data['description']}
            )
            if created:
                skills_created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created skill: {skill.name}'))
            else:
                skills_updated += 1
                skill.description = skill_data['description']
                skill.save()
                self.stdout.write(self.style.WARNING(f'  Updated skill: {skill.name}'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Seeding Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Categories: {categories_created} created, {categories_updated} updated'))
        self.stdout.write(self.style.SUCCESS(f'  Skills: {skills_created} created, {skills_updated} updated'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('\nDatabase seeding completed successfully!'))
