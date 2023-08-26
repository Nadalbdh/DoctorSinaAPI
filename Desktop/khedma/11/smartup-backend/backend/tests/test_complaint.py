import json
from decimal import Decimal
from unittest.mock import patch

from model_bakery import baker
from rest_framework import status
from rest_framework.renderers import JSONRenderer

from backend.exceptions import InconsistentCategoriesError, InconsistentRegionError
from backend.models import Complaint
from backend.serializers.serializers import ComplaintSerializer
from backend.tests.test_base import (
    authenticate_citizen_test,
    authenticate_manager_test,
    cleanup_test_files,
    ElBaladiyaAPITest,
    MunicipalityTestMixin,
    TestBase,
)


class ComplaintModelTest(MunicipalityTestMixin, TestBase):
    def test_mismatched_categories(self):
        category = baker.make("backend.complaintcategory", name="One category")
        sub_category = baker.make(
            "backend.complaintsubcategory",
            name="With its sub category",
            category=category,
        )
        other_category = baker.make(
            "backend.complaintcategory", name="But there is another"
        )

        try:
            baker.make(
                "backend.complaint", category=other_category, sub_category=sub_category
            )
            self.fail("Expected InconsistentCategoriesError to be raised")
        except InconsistentCategoriesError:
            pass

    def test_categories(self):
        category = baker.make("backend.complaintcategory", name="One category")
        sub_category = baker.make(
            "backend.complaintsubcategory",
            name="With its sub category",
            category=category,
        )
        baker.make("backend.complaint", category=category, sub_category=sub_category)

    def test_mismatched_region(self):
        region = baker.make("backend.region", municipality=self.other_municipality())
        try:
            self.make_with_municipality("backend.complaint", region=region)
            self.fail("Expected InconsistentCategoriesError to be raised")
        except InconsistentRegionError:
            pass

    def test_matched_region(self):
        region = self.make_with_municipality("backend.region")
        self.make_with_municipality("backend.complaint", region=region)


class ComplaintViewTest(ElBaladiyaAPITest):
    url_name = "backend:complaint"
    default_model = "backend.complaint"

    ### Unauthenticated tests
    def test_get_many_unauthenticated(self):
        self.make_with_municipality(_quantity=10)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_one_unauthenticated(self):
        self.make_with_municipality(_quantity=10)

        complaint = self.make_with_municipality()

        response = self.client.get(self.get_url(complaint.pk), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_unauthenticated(self):
        complaint_data = {
            "problem": "Jo3t",
            "address": "Fel ghorba",
            "category": baker.make("backend.complaintcategory").name,
            "is_public": True,
        }

        response = self.client.post(self.get_url(), complaint_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEmpty(Complaint.objects.all())

    def test_update_unauthenticated(self):
        complaint = self.make_with_municipality(problem="corina")

        complaint_data = {"problem": "Corona"}

        response = self.client.put(
            self.get_url(complaint.pk), complaint_data, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        complaint.refresh_from_db()
        self.assertEqual(complaint.problem, "corina")

    def test_delete_unauthenticated(self):
        complaint = self.make_with_municipality()

        response = self.client.delete(self.get_url(complaint.pk), format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        complaint.refresh_from_db()
        self.assertIsNotNone(complaint.pk)

    @authenticate_citizen_test
    def test_create_all(self):
        category = baker.make("backend.complaintcategory", name="الطرقات")
        sub_category = baker.make(
            "backend.complaintsubcategory", name="وجود حفر بالطريق", category=category
        )
        region = baker.make(
            "backend.region", municipality=self.municipality, name="everywhere"
        )

        complaint_data = {
            "problem": "like wtf",
            "longitude": 10,
            "latitude": 9,
            "address": "9odem dar",
            "category": category.name,
            "sub_category": sub_category.name,
            "is_public": False,
            "solution": "pls",
            "region": region.name,
        }

        response = self.client.post(self.get_url(), complaint_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # TODO assert data is correct

    @authenticate_citizen_test
    def test_create_ambiguous_sub_categories(self):
        category1 = baker.make("backend.complaintcategory", name="The One")
        sub_category1 = baker.make(
            "backend.complaintsubcategory", name="Sub", category=category1
        )
        category2 = baker.make("backend.complaintcategory", name="The Other")
        _ = baker.make("backend.complaintsubcategory", name="Sub", category=category2)

        complaint_data = {
            "problem": "The Thing isn not working",
            "address": "There",
            "category": category1.name,
            "sub_category": sub_category1.name,
        }

        response = self.client.post(self.get_url(), complaint_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @authenticate_citizen_test
    def test_update_valid_region(self):
        region = self.make_with_municipality("backend.region", name="somewhere")
        complaint = self.make_with_municipality(
            region=region, created_by=self.citizen.user
        )

        self.assertEqual(region, complaint.region)

        # Changeregion
        other_region = self.make_with_municipality(
            "backend.region", name="somewhere else"
        )
        data = {
            "region": other_region.name,
        }

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(other_region, complaint.region)

    @authenticate_citizen_test
    def test_update_ivalid_region(self):
        region = self.make_with_municipality("backend.region", name="somewhere")
        complaint = self.make_with_municipality(
            region=region, created_by=self.citizen.user
        )

        self.assertEqual(region, complaint.region)

        # Changeregion
        other_region = baker.make(
            "backend.region",
            name="somewhere else, far far away",
            municipality=self.other_municipality(),
        )

        data = {
            "region": other_region.name,
        }

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        complaint.refresh_from_db()
        self.assertEqual(region, complaint.region)

    @authenticate_citizen_test
    def test_update_remove_region(self):
        region = self.make_with_municipality("backend.region", name="here")
        complaint = self.make_with_municipality(
            region=region, created_by=self.citizen.user
        )

        self.assertEqual(region, complaint.region)

        data = {"region": None}

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertIsNone(complaint.region)

    @authenticate_citizen_test
    def test_update_category(self):
        category = baker.make("backend.complaintcategory", name="التراتيب العمرانية")
        complaint = self.make_with_municipality(
            category=category, created_by=self.citizen.user
        )

        self.assertEqual(complaint.category, category)

        new_category = baker.make("backend.complaintcategory", name="الصحّة والبيئة")

        data = {"category": new_category.name}

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.category, new_category)

    @authenticate_citizen_test
    def test_update_valid_subcategory_same_category(self):
        category = baker.make("backend.complaintcategory", name="The bigs")
        sub_category = baker.make(
            "backend.complaintsubcategory", name="The big sad", category=category
        )
        complaint = self.make_with_municipality(
            category=category, sub_category=sub_category, created_by=self.citizen.user
        )

        self.assertEqual(complaint.category, category)
        self.assertEqual(complaint.sub_category, sub_category)

        new_sub_category = baker.make(
            "backend.complaintsubcategory", name="The big laugh", category=category
        )

        data = {"sub_category": new_sub_category.name}

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.sub_category, new_sub_category)

    @authenticate_citizen_test
    def test_update_remove_subcategory(self):
        category = baker.make("backend.complaintcategory", name="The bigs")
        sub_category = baker.make(
            "backend.complaintsubcategory", name="The big sad", category=category
        )
        complaint = self.make_with_municipality(
            category=category, sub_category=sub_category, created_by=self.citizen.user
        )

        self.assertEqual(complaint.category, category)
        self.assertEqual(complaint.sub_category, sub_category)

        data = {"sub_category": None}

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertIsNone(complaint.sub_category)

    @authenticate_citizen_test
    def test_update_invalid_category(self):
        category = baker.make("backend.complaintcategory", name="Games")
        sub_category = baker.make(
            "backend.complaintsubcategory", name="FPS", category=category
        )
        complaint = self.make_with_municipality(
            category=category, sub_category=sub_category, created_by=self.citizen.user
        )

        self.assertEqual(complaint.category, category)
        self.assertEqual(complaint.sub_category, sub_category)

        new_category = baker.make("backend.complaintcategory", name="Crypto")

        data = {"category": new_category.name}

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        complaint.refresh_from_db()
        self.assertEqual(complaint.category, category)

    @authenticate_citizen_test
    def test_update_invalid_category_subcategory(self):
        category = baker.make("backend.complaintcategory", name="Songs")
        sub_category = baker.make(
            "backend.complaintsubcategory", name="Rock", category=category
        )
        complaint = self.make_with_municipality(
            category=category, sub_category=sub_category, created_by=self.citizen.user
        )

        self.assertEqual(complaint.category, category)
        self.assertEqual(complaint.sub_category, sub_category)

        new_category = baker.make("backend.complaintcategory", name="Books")
        new_sub_category = baker.make(
            "backend.complaintsubcategory", name="RnB", category=category
        )

        data = {
            "category": new_category.name,
            "sub_category": new_sub_category.name,
        }

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        complaint.refresh_from_db()
        self.assertEqual(complaint.category, category)
        self.assertEqual(complaint.sub_category, sub_category)

    @authenticate_citizen_test
    def test_update_remove_category(self):
        category = baker.make("backend.complaintcategory", name="Lectures")
        complaint = self.make_with_municipality(
            category=category, created_by=self.citizen.user
        )

        self.assertEqual(complaint.category, category)

        data = {
            "category": None,
        }

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertIsNone(complaint.category)

    @authenticate_citizen_test
    def test_update_invalid_remove_category(self):
        category = baker.make("backend.complaintcategory", name="Food")
        sub_category = baker.make(
            "backend.complaintsubcategory", name="Sweets", category=category
        )
        complaint = self.make_with_municipality(
            category=category, sub_category=sub_category, created_by=self.citizen.user
        )

        self.assertEqual(complaint.category, category)
        self.assertEqual(complaint.sub_category, sub_category)

        data = {
            "category": None,
        }

        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        complaint.refresh_from_db()
        self.assertEqual(complaint.category, category)
        self.assertEqual(complaint.sub_category, sub_category)

    @cleanup_test_files
    @authenticate_citizen_test
    def test_create_image_complaint(self):
        image = ""
        with open("test_resources/base64") as f:
            image = f.read()

        complaint_data = {
            "problem": "It's wednesday",
            "address": "The world",
            "category": baker.make("backend.complaintcategory").name,
            "image": image,
        }

        response = self.client.post(self.get_url(), complaint_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        complaint = Complaint.objects.last()
        self.assertIsNotNone(complaint.image)

    @authenticate_citizen_test
    def test_privacy_many(self):
        user = self.citizen.user
        complaint_mine = self.make_with_municipality(created_by=user)
        self.make_with_municipality(is_public=False)
        complaint_other_public = self.make_with_municipality(is_public=True)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # TODO test serialization later
        expected = [c.pk for c in [complaint_mine, complaint_other_public]]
        self.assertCountEqual([r["id"] for r in response.data], expected)

    @authenticate_citizen_test
    def test_hits(self):
        complaint = self.make_with_municipality()

        self.assertEqual(complaint.hits_count, 0)

        response = self.client.get(self.get_url(complaint.pk), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.hits_count, 1)

    @authenticate_citizen_test
    def test_pagination(self):
        self.make_with_municipality(_quantity=50)

        response = self.client.get("%s?page=2&per_page=15" % self.get_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 15)

    @authenticate_citizen_test
    def test_contact_number_for_citizen(self):
        citizen = baker.make("backend.citizen", user__username="22222222")
        complaint = self.make_with_municipality(created_by=citizen.user)

        response = self.client.get(self.get_url(complaint.pk), format="json")
        self.assertEqual(response.data["contact_number"], None)

    @authenticate_manager_test
    def test_contact_number_for_manager(self):
        citizen = baker.make("backend.citizen", user__username="22222222")
        complaint = self.make_with_municipality(created_by=citizen.user)
        response = self.client.get(self.get_url(complaint.pk), format="json")
        self.assertEqual(response.data["contact_number"], "22222222")

    @authenticate_citizen_test
    def test_get_private_only(self):
        self.make_with_municipality(created_by=self.citizen.user, _quantity=4)
        self.make_with_municipality(_quantity=2, is_public=True)
        self.make_with_municipality(_quantity=5, is_public=False)

        response_all = self.client.get(self.get_url())

        self.assertEqual(response_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_all.data), 6)

        response = self.client.get(
            "%s?private_only=True" % self.get_url(), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    @authenticate_citizen_test
    def test_get_private_only_false(self):
        self.make_with_municipality(created_by=self.citizen.user, _quantity=2)
        self.make_with_municipality(_quantity=5, is_public=True)
        self.make_with_municipality(_quantity=3, is_public=False)

        response = self.client.get(
            "%s?private_only=False" % self.get_url(), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 7)

    @authenticate_citizen_test
    def test_operation_update_citizen(self):
        complaint = self.make_with_municipality(created_by=self.citizen.user)

        data = {
            "status": "DONE",
            "note": "Shhhh",
        }

        response = self.client.post(
            self.get_url(pk=complaint.pk, url_name="backend:complaint-update"),
            data=data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(complaint.operation_updates.count(), 1)

        opu = complaint.operation_updates.first()
        self.assertEqual(opu.status, "RECEIVED")
        self.assertEqual(opu.operation, complaint)
        self.assertEqual(opu.created_by, self.citizen.user)

    @authenticate_manager_test
    def test_manager_get_with_permission(self):
        categoryA = baker.make("backend.complaintcategory", name="A")
        categoryB = baker.make("backend.complaintcategory", name="B")
        categoryC = baker.make("backend.complaintcategory", name="C")

        self.make_with_municipality(_quantity=5, category=categoryA)
        self.make_with_municipality(_quantity=4, category=categoryB)
        self.make_with_municipality(_quantity=13, category=categoryC)

        self.manager.complaint_categories.set([categoryB, categoryA])

        response = self.client.get(self.get_url() + "?manager_category_filter=True")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)

    @authenticate_manager_test
    def test_manager_operation_status_update_with_permission(self):
        food = baker.make("backend.complaintcategory", name="food")
        drinks = baker.make("backend.complaintcategory", name="drinks")
        complaint = self.make_with_municipality(category=food)

        self.manager.complaint_categories.set([food, drinks])

        data = {
            "status": "ACCEPTED",
            "note": "Sorry",
        }
        response = self.client.post(self.get_url(complaint.pk) + "/update", data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, "ACCEPTED")
        self.assertEqual(complaint.last_operation_update.note, "Sorry")

    @authenticate_manager_test
    def test_manager_operation_update_without_permission(self):
        food = baker.make("backend.complaintcategory", name="food")
        drinks = baker.make("backend.complaintcategory", name="drinks")
        complaint = self.make_with_municipality(category=food)

        self.manager.complaint_categories.set([drinks])

        data = {"status": "PROCESSING"}
        response = self.client.post(self.get_url(complaint.pk) + "/update", data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, "RECEIVED")

    @authenticate_manager_test
    def test_manager_operation_update_with_no_permission(self):
        category1 = baker.make("backend.complaintcategory", name="games")

        complaint = self.make_with_municipality(category=category1)

        data = {"status": "PROCESSING"}
        response = self.client.post(self.get_url(complaint.pk) + "/update", data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, "RECEIVED")

    @authenticate_manager_test
    def test_manager_edit_with_permission(self):
        category = baker.make("backend.complaintcategory")
        complaint = self.make_with_municipality(problem="3g", category=category)
        self.manager.complaint_categories.set([category])

        data = {"problem": "3g: slow"}
        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        complaint.refresh_from_db()
        self.assertEqual(complaint.problem, "3g: slow")

    @authenticate_manager_test
    def test_manager_edit_without_permission(self):
        category = baker.make("backend.complaintcategory")
        complaint = self.make_with_municipality(problem="food", category=category)
        self.manager.complaint_categories.set([baker.make("backend.complaintcategory")])

        data = {"problem": "food: salty"}
        response = self.client.put(self.get_url(complaint.pk), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        complaint.refresh_from_db()
        self.assertEqual(complaint.problem, "food")

    @authenticate_manager_test
    def test_manager_delete_with_permission(self):
        category = baker.make("backend.complaintcategory")
        complaint = self.make_with_municipality(problem="si mounir", category=category)
        self.manager.complaint_categories.set([category])

        response = self.client.delete(self.get_url(complaint.pk))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        complaint.refresh_from_db()
        self.assertIsNotNone(complaint.pk)

    @authenticate_manager_test
    def test_manager_delete_without_permission(self):
        category = baker.make("backend.complaintcategory")
        complaint = self.make_with_municipality(problem="si mounir", category=category)
        self.manager.complaint_categories.set([baker.make("backend.complaintcategory")])

        response = self.client.delete(self.get_url(complaint.pk))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        complaint.refresh_from_db()
        self.assertIsNotNone(complaint.pk)


class ComplaintSerializerTest(MunicipalityTestMixin, TestBase):
    def test_serialization(self):
        category = baker.make("backend.complaintcategory", name="kaskrout")
        sub_category = baker.make(
            "backend.complaintsubcategory", name="bel thon", category=category
        )
        region = self.make_with_municipality("backend.region", name="ghadi")
        citizen = baker.make("backend.citizen")

        complaint = self.make_with_municipality(
            "backend.complaint",
            category=category,
            sub_category=sub_category,
            region=region,
            longitude=Decimal(10.0000000),
            latitude=Decimal(10.0000000),
            address="9odem dar",
            created_by=citizen.user,
            problem="fih bsal",
            solution="maghir bsal!",
            is_public=True,
        )

        time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        decimal_places = Decimal(10) ** -7

        # Basically the to_dict method
        expected = {
            "id": complaint.pk,
            "municipality": complaint.municipality_id,
            "problem": complaint.problem,
            "image": None,
            "solution": complaint.solution,
            "is_public": complaint.is_public,
            "longitude": str(complaint.longitude.quantize(decimal_places)),
            "latitude": str(complaint.latitude.quantize(decimal_places)),
            "address": complaint.address,
            "created_by": complaint.created_by.get_full_name(),
            "created_by_id": complaint.created_by.pk,
            "followers": list(complaint.followers.all().values_list("id", flat=True)),
            "updates": [
                {
                    "date": operation_update.created_at.strftime(time_format),
                    "status": operation_update.status,
                    "note": operation_update.note,
                    "created_by": operation_update.created_by.id
                    if operation_update.created_by is not None
                    else None,
                    "id": complaint.pk,
                    "created_by_name": operation_update.created_by.get_full_name()
                    if operation_update.created_by is not None
                    else None,
                    "image": None,
                }
                for operation_update in complaint.operation_updates.all()
            ],
            "score": complaint.score,
            "category": complaint.category.name,
            "sub_category": complaint.sub_category.name,
            "region": complaint.region.name,
            "hits": complaint.hits_count,
            "contact_number": None,
            "created_at": complaint.created_at.strftime(time_format),
            "user_vote": 0,
        }

        # Simulate serialization and deserialization
        actual = JSONRenderer().render(ComplaintSerializer(complaint).data)
        actual = json.loads(actual)

        self.assertDictEqual(actual, expected)
