from app.auth.models import Identity, Permission, Role


def test_identity_checks_permissions():
    identity = Identity(
        subject="user:analyst",
        display_name="Analyst",
        roles=(Role.ANALYST,),
        permissions=frozenset(
            {
                Permission.INTELLIGENCE_READ,
            }
        ),
    )

    assert identity.has_permission(
        Permission.INTELLIGENCE_READ
    )
    assert not identity.has_permission(
        Permission.USERS_MANAGE
    )


def test_role_values_are_stable():
    assert Role.VIEWER.value == "viewer"
    assert Role.ANALYST.value == "analyst"
    assert Role.RESPONDER.value == "responder"
    assert Role.ADMINISTRATOR.value == "administrator"
    assert Role.SERVICE.value == "service"


def test_permission_values_are_stable():
    assert (
        Permission.INTELLIGENCE_READ.value
        == "intelligence:read"
    )
    assert (
        Permission.ALERTS_INVESTIGATE.value
        == "alerts:investigate"
    )
    assert (
        Permission.RESPONSE_EXECUTE.value
        == "response:execute"
    )
    assert Permission.USERS_MANAGE.value == "users:manage"
    assert (
        Permission.SYSTEM_CONFIGURE.value
        == "system:configure"
    )
