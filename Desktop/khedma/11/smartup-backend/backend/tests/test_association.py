from django.urls import reverse
from model_bakery import baker

from backend.tests.test_base import authenticate_citizen_test, ElBaladiyaAPITest


class AssociationTest(ElBaladiyaAPITest):
    @authenticate_citizen_test
    def test_get_all_associations(self):
        associations = baker.make("backend.association", _quantity=8)
        response = self.client.get(
            reverse("backend:associations"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 8)

    @authenticate_citizen_test
    def test_get_association_by_id(self):
        association = baker.make(
            "backend.association", president_name="AAZERTY", full_name="TOUNESLINA"
        )
        response = self.client.get(
            reverse("backend:association", args=[association.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["full_name"], association.full_name)
        self.assertEqual(response.data["president_name"], association.president_name)
