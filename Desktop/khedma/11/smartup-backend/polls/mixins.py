from rules.contrib.rest_framework import AutoPermissionViewSetMixin


class PollPermissionViewSetMixin(AutoPermissionViewSetMixin):
    permission_type_map = {
        **AutoPermissionViewSetMixin.permission_type_map,
        "multi_vote": "vote",
        "single_vote": "vote",
    }
