import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.models import User, FarmerProfile, OwnerProfile, Equipment, Booking, Payment, Notification

app = create_app('development')

with app.app_context():
    db.create_all()

    if User.query.count() == 0:
        print("Seeding database with sample data...")

        # Admin
        admin = User(
            email='admin@farmrent.com',
            full_name='System Admin',
            phone='9999999999',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Farmers
        farmer1 = User(email='rahul@gmail.com', full_name='Rahul Patil', phone='9876543210', role='farmer')
        farmer1.set_password('pass123')
        db.session.add(farmer1)
        db.session.flush()
        db.session.add(FarmerProfile(user_id=farmer1.id, farm_name='Green Valley Farm', farm_location='Pune, Maharashtra', farm_size='10 acres', crop_types='Rice, Wheat, Soybean'))

        farmer2 = User(email='suresh@gmail.com', full_name='Suresh Jadhav', phone='9876543211', role='farmer')
        farmer2.set_password('pass123')
        db.session.add(farmer2)
        db.session.flush()
        db.session.add(FarmerProfile(user_id=farmer2.id, farm_name='Sunrise Agro Farm', farm_location='Nashik, Maharashtra', farm_size='15 acres', crop_types='Grapes, Onion'))

        # Owners
        owner1 = User(email='mahesh@gmail.com', full_name='Mahesh Kumar', phone='9876543220', role='owner')
        owner1.set_password('pass123')
        db.session.add(owner1)
        db.session.flush()
        db.session.add(OwnerProfile(user_id=owner1.id, business_name='Kumar Agro Equipment', business_address='Solapur, Maharashtra', business_type='Equipment Rental', gst_number='27AABCU9603R1ZM'))

        owner2 = User(email='prakash@gmail.com', full_name='Prakash Sharma', phone='9876543221', role='owner')
        owner2.set_password('pass123')
        db.session.add(owner2)
        db.session.flush()
        db.session.add(OwnerProfile(user_id=owner2.id, business_name='Sharma Farm Machinery', business_address='Satara, Maharashtra', business_type='Equipment Sales & Rental'))

        db.session.flush()

        # Equipment
        equip_data = [
            ('Mahindra 575 DI Tractor', 'Tractor', 'Powerful 45HP tractor suitable for all farm operations', 'Mahindra', '575 DI', 2022, 'Excellent', 1500, 8000, 25000, 5000, 'Pune, Maharashtra'),
            ('John Deere T5030 Harvester', 'Harvester', 'Self-propelled combine harvester for wheat and rice', 'John Deere', 'T5030', 2021, 'Good', 5000, 25000, 80000, 15000, 'Nashik, Maharashtra'),
            ('Sonalika RT-100 Rotavator', 'Rotavator', 'Heavy duty rotavator for soil preparation', 'Sonalika', 'RT-100', 2023, 'Excellent', 800, 4000, 12000, 2000, 'Solapur, Maharashtra'),
            ('Fieldmarshal Cultivator', 'Cultivator', '9-tine cultivator for inter-culture operations', 'Fieldmarshal', 'FC-9', 2022, 'Good', 600, 3000, 9000, 1500, 'Satara, Maharashtra'),
            ('Dharti Agro Seed Drill', 'Seed Drill', '11-row seed drill for precise seed placement', 'Dharti Agro', 'SD-11', 2023, 'Excellent', 700, 3500, 10000, 2000, 'Pune, Maharashtra'),
            ('Kverneland Sprayer', 'Sprayer', '600L capacity mounted sprayer for crop protection', 'Kverneland', 'LS-600', 2022, 'Good', 500, 2500, 8000, 1500, 'Nashik, Maharashtra'),
            ('Swaraj 855 FE Tractor', 'Tractor', '52HP tractor with power steering and AC cabin', 'Swaraj', '855 FE', 2023, 'Excellent', 1800, 9000, 28000, 6000, 'Satara, Maharashtra'),
            ('Shaktiman Power Weeder', 'Other', 'Multi-purpose power weeder for small farms', 'Shaktiman', 'PW-40', 2022, 'Good', 400, 2000, 6000, 1000, 'Solapur, Maharashtra'),
        ]

        for i, data in enumerate(equip_data):
            owner = owner1 if i % 2 == 0 else owner2
            equip = Equipment(
                owner_id=owner.id,
                name=data[0], category=data[1], description=data[2],
                brand=data[3], model=data[4], year=data[5], condition=data[6],
                daily_rate=data[7], weekly_rate=data[8], monthly_rate=data[9],
                security_deposit=data[10], location=data[11],
                is_available=True, is_approved=True, is_active=True
            )
            db.session.add(equip)

        db.session.commit()
        print("Database seeded successfully!")
        print("\nLogin credentials:")
        print("  Admin:    admin@farmrent.com / admin123")
        print("  Farmer:   rahul@gmail.com / pass123")
        print("  Farmer:   suresh@gmail.com / pass123")
        print("  Owner:    mahesh@gmail.com / pass123")
        print("  Owner:    prakash@gmail.com / pass123")
    else:
        print("Database already contains data. Skipping seed.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
