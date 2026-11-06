import unittest
from datetime import datetime

from pydantic import ValidationError

from backend.schemas.delivery import VALID_STATUS_TRANSITIONS
from backend.schemas.parcel import ParcelCreate, ParcelResponse, calculate_shipping_charge
from backend.schemas.payment import PaymentUpdate


class WorkflowRuleTests(unittest.TestCase):
    def test_delivery_address_is_required_and_normalized(self):
        parcel_data = {
            "sender_name": "Sender",
            "sender_phone": "9876543210",
            "receiver_name": "Receiver",
            "receiver_phone": "9123456780",
            "source_city": "Chennai",
            "destination_city": "Coimbatore",
            "weight_kg": 1.25
        }

        with self.assertRaises(ValidationError):
            ParcelCreate(**parcel_data)

        with self.assertRaises(ValidationError):
            ParcelCreate(**parcel_data, receiver_address="   ")

        parcel = ParcelCreate(**parcel_data, receiver_address="  42 Main Street  ")
        self.assertEqual(parcel.receiver_address, "42 Main Street")

        camel_case_parcel = ParcelCreate(**parcel_data, receiverAddress="42 Alternate Road")
        self.assertEqual(camel_case_parcel.receiver_address, "42 Alternate Road")

    def test_legacy_parcel_response_allows_missing_delivery_address(self):
        response = ParcelResponse(
            sender_name="Sender",
            sender_phone="9876543210",
            receiver_name="Receiver",
            receiver_phone="9123456780",
            receiver_address=None,
            source_city="Chennai",
            destination_city="Coimbatore",
            weight_kg=1,
            parcel_id=1,
            tracking_id="PCTS-TEST-1",
            customer_id=1,
            charge=50,
            booked_at=datetime.now()
        )

        self.assertIsNone(response.receiver_address)

    def test_delivery_statuses_must_advance_one_milestone(self):
        self.assertEqual(VALID_STATUS_TRANSITIONS["Booked"], ["Picked Up"])
        self.assertEqual(VALID_STATUS_TRANSITIONS["Picked Up"], ["In Transit"])
        self.assertEqual(VALID_STATUS_TRANSITIONS["In Transit"], ["At Warehouse"])
        self.assertEqual(VALID_STATUS_TRANSITIONS["At Warehouse"], ["Out for Delivery"])
        self.assertEqual(
            VALID_STATUS_TRANSITIONS["Out for Delivery"],
            ["Delivered", "Failed Delivery"]
        )
        self.assertEqual(VALID_STATUS_TRANSITIONS["Failed Delivery"], ["Returned"])
        self.assertEqual(VALID_STATUS_TRANSITIONS["Returned"], [])
        self.assertEqual(VALID_STATUS_TRANSITIONS["Delivered"], [])

    def test_weight_precision_matches_database_scale(self):
        ParcelCreate(
            sender_name="Sender",
            sender_phone="9876543210",
            receiver_name="Receiver",
            receiver_phone="9123456780",
            receiver_address="42 Main Street",
            source_city="Chennai",
            destination_city="Coimbatore",
            weight_kg=1.25
        )

        with self.assertRaises(ValidationError):
            ParcelCreate(
                sender_name="Sender",
                sender_phone="9876543210",
                receiver_name="Receiver",
                receiver_phone="9123456780",
                receiver_address="42 Main Street",
                source_city="Chennai",
                destination_city="Coimbatore",
                weight_kg=1.251
            )

    def test_payment_amount_precision_matches_database_scale(self):
        PaymentUpdate(payment_status="Paid", amount="50.00")

        with self.assertRaises(ValidationError):
            PaymentUpdate(payment_status="Paid", amount="50.001")

    def test_shipping_price_tiers(self):
        self.assertEqual(calculate_shipping_charge(1), 50)
        self.assertEqual(calculate_shipping_charge(1.01), 30.3)
        self.assertEqual(calculate_shipping_charge(5), 150)
        self.assertEqual(calculate_shipping_charge(5.01), 100.2)
        self.assertEqual(calculate_shipping_charge(20), 400)
        self.assertEqual(calculate_shipping_charge(20.01), 300.15)


if __name__ == "__main__":
    unittest.main()
