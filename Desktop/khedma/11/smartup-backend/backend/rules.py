import rules

from backend.enum import MunicipalityPermissions


@rules.predicate
def has_category_permission(user, complaint):
    if not hasattr(user, "manager"):
        return False
    manager = user.manager
    if not complaint.category:
        return True

    return manager.complaint_categories.filter(pk=complaint.category.pk).exists()


@rules.predicate
def has_dossier_permission(user, dossier):
    if not hasattr(user, "manager"):
        return False

    return user.has_perm(MunicipalityPermissions.MANAGE_DOSSIERS, dossier.municipality)


@rules.predicate
def is_owner(user, obj):
    if obj is None:
        return True

    return user == obj.created_by


@rules.predicate
def is_owner_of_related_dossier(user, obj):
    if obj is None:
        return True

    return user == obj.dossier.created_by


@rules.predicate
def is_follower(user, obj):
    """
    Check if a user is a follower
    """
    return user in obj.followers.all()


@rules.predicate
def is_follower_of_related_dossier(user, obj):
    if obj is None:
        return True

    return is_follower(user, obj.dossier)


@rules.predicate
def is_manager(user, obj):
    if obj is None:
        return hasattr(user, "manager")
    if hasattr(user, "manager"):
        return user.manager.municipality.pk == obj.municipality.pk

    return False


@rules.predicate
def is_manager_poll(user, obj):
    if obj is None:
        return hasattr(user, "manager")

    if hasattr(user, "manager"):
        return user.manager.municipality.pk == obj.poll.municipality.pk

    return False
