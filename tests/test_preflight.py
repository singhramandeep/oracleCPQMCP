"""Tests for safe execution preflight checks on write tools."""



from __future__ import annotations



import httpx

import pytest

import respx



from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet

from oracle_cpq_mcp.core.cpq_client import CPQClient

from oracle_cpq_mcp.core.preflight import (

    build_confirmation_required_response,

    build_preflight_response,

    resolve_write_execution,

    run_create_group_preflight,

    run_deploy_datatables_preflight,

    run_update_user_preflight,

)





@pytest.fixture()

def profile() -> CPQProfile:

    return CPQProfile(

        customer_name="Test",

        customer_id="test",

        environment="dev",

        base_url="https://dev.example.com",

        read_only=False,
        credentials=[CredentialSet(username="user", password="s3cr3t!")],

        rest_version="v18",

        company_login_name="_host",

    )





@pytest.fixture()

def client(profile: CPQProfile) -> CPQClient:

    return CPQClient(profile)





def test_build_preflight_response_shape() -> None:

    payload = build_preflight_response(

        "update_user",

        action="update",

        status="preflight_ok",

        message="This will UPDATE user 'alice' in CPQ.",

        confirmation_prompt="This will UPDATE user 'alice' in CPQ. Confirm to proceed.",

        would_execute={"method": "PATCH", "path": "/users/1", "body": {}, "curl": "curl ..."},

        preflight={"party_number": "1"},

    )

    assert payload["dry_run"] is True

    assert payload["tool"] == "update_user"

    assert payload["action"] == "update"

    assert payload["status"] == "preflight_ok"

    assert "confirmation_token" in payload["next_step"]

    assert payload["confirmation_prompt"].startswith("This will UPDATE")

    assert payload["preflight"]["party_number"] == "1"

    assert "errors" not in payload





def test_build_confirmation_required_response_shape() -> None:

    payload = build_confirmation_required_response(

        "update_user",

        action="update",

        message="This will UPDATE user 'alice' in CPQ.",

        confirmation_prompt="This will UPDATE user 'alice' in CPQ. Confirm to proceed.",

        would_execute={"method": "PATCH", "path": "/users/1", "body": {}, "curl": "curl ..."},

        preflight={"party_number": "1"},

    )

    assert payload["dry_run"] is False

    assert payload["status"] == "confirmation_required"

    assert payload["action"] == "update"

    assert "confirmation_prompt" in payload





@respx.mock

def test_update_user_preflight_ok(client: CPQClient) -> None:

    get_route = respx.get("https://dev.example.com/rest/v18/users/12345").mock(

        return_value=httpx.Response(

            200,

            json={"partyNumber": "12345", "login": "alice", "email": "a@b.com"},

        )

    )

    patch_route = respx.patch("https://dev.example.com/rest/v18/users/12345").mock(

        return_value=httpx.Response(200, json={"partyNumber": "12345"})

    )



    result = run_update_user_preflight(client, "12345", {"email": "new@b.com"})



    assert result["dry_run"] is True

    assert result["status"] == "preflight_ok"

    assert result["action"] == "update"

    assert "This will UPDATE user 'alice'" in result["message"]

    assert result["preflight"]["fields_to_change"] == ["email"]

    assert get_route.called

    assert not patch_route.called





@respx.mock

def test_update_user_preflight_user_not_found(client: CPQClient) -> None:

    respx.get("https://dev.example.com/rest/v18/users/missing").mock(

        return_value=httpx.Response(404, json={"title": "Not found"})

    )

    patch_route = respx.patch("https://dev.example.com/rest/v18/users/missing").mock(

        return_value=httpx.Response(200, json={})

    )



    result = run_update_user_preflight(client, "missing", {"email": "x@y.com"})



    assert result["status"] == "preflight_failed"

    assert "errors" in result
    assert result["error"]["status"] == "error"
    assert result["error"]["code"] == "NOT_FOUND"
    assert "hint" in result["error"]

    assert not patch_route.called





@respx.mock

def test_update_user_preflight_invalid_input(client: CPQClient) -> None:

    get_route = respx.get(url__regex=r".*").mock(

        return_value=httpx.Response(200, json={})

    )



    result = run_update_user_preflight(client, "", {})



    assert result["status"] == "preflight_failed"

    assert not get_route.called





@respx.mock

def test_resolve_write_execution_confirmation_required(client: CPQClient) -> None:

    respx.get("https://dev.example.com/rest/v18/users/12345").mock(

        return_value=httpx.Response(200, json={"partyNumber": "12345", "login": "alice"})

    )

    patch_route = respx.patch("https://dev.example.com/rest/v18/users/12345").mock(

        return_value=httpx.Response(200, json={"partyNumber": "12345"})

    )



    result = resolve_write_execution(

        read_only=False,

        dry_run=False,

        confirmation_token=None,

        tool="update_user",

        action="update",

        preflight_fn=lambda: run_update_user_preflight(

            client, "12345", {"email": "new@b.com"}

        ),

        execute_fn=lambda: client.patch("/users/12345", json_body={"email": "new@b.com"}),

    )



    assert result["status"] == "confirmation_required"

    assert result["action"] == "update"

    assert "confirmation_prompt" in result

    assert not patch_route.called





@respx.mock

def test_resolve_write_execution_confirmed_executes(client: CPQClient) -> None:

    respx.get("https://dev.example.com/rest/v18/users/12345").mock(

        return_value=httpx.Response(200, json={"partyNumber": "12345", "login": "alice"})

    )

    patch_route = respx.patch("https://dev.example.com/rest/v18/users/12345").mock(

        return_value=httpx.Response(200, json={"partyNumber": "12345", "email": "new@b.com"})

    )



    result = resolve_write_execution(

        read_only=False,

        dry_run=False,

        confirmation_token="valid-token-present",

        tool="update_user",

        action="update",

        preflight_fn=lambda: run_update_user_preflight(

            client, "12345", {"email": "new@b.com"}

        ),

        execute_fn=lambda: client.patch("/users/12345", json_body={"email": "new@b.com"}),

    )



    assert patch_route.called

    assert result["email"] == "new@b.com"





@respx.mock

def test_create_group_preflight_ok(client: CPQClient) -> None:

    respx.get("https://dev.example.com/rest/v18/companies/_host/groups/new_group").mock(

        return_value=httpx.Response(404, json={"title": "Not found"})

    )

    post_route = respx.post("https://dev.example.com/rest/v18/companies/_host/groups").mock(

        return_value=httpx.Response(201, json={"variableName": "new_group"})

    )



    result = run_create_group_preflight(

        client,

        {"variableName": "new_group", "label": "New Group"},

    )



    assert result["status"] == "preflight_ok"

    assert result["action"] == "create"

    assert "This will CREATE group 'new_group'" in result["message"]

    assert result["preflight"]["variableName"] == "new_group"

    assert not post_route.called





@respx.mock

def test_create_group_preflight_group_exists(client: CPQClient) -> None:

    respx.get("https://dev.example.com/rest/v18/companies/_host/groups/existing").mock(

        return_value=httpx.Response(200, json={"variableName": "existing"})

    )

    post_route = respx.post("https://dev.example.com/rest/v18/companies/_host/groups").mock(

        return_value=httpx.Response(201, json={})

    )



    result = run_create_group_preflight(client, {"variableName": "existing"})



    assert result["status"] == "preflight_failed"

    assert not post_route.called





@respx.mock

def test_create_group_preflight_missing_variable_name(client: CPQClient) -> None:

    result = run_create_group_preflight(client, {"label": "No Var Name"})



    assert result["status"] == "preflight_failed"

    assert any("variableName" in error for error in result["errors"])





@respx.mock

def test_deploy_datatables_preflight_ok(client: CPQClient) -> None:

    respx.get("https://dev.example.com/rest/v18/datatables/TableA").mock(

        return_value=httpx.Response(200, json={"name": "TableA"})

    )

    respx.get("https://dev.example.com/rest/v18/datatables/TableB").mock(

        return_value=httpx.Response(200, json={"name": "TableB"})

    )

    post_route = respx.post(

        "https://dev.example.com/rest/v18/datatables/actions/deploy"

    ).mock(return_value=httpx.Response(200, json={"status": "ok"}))



    result = run_deploy_datatables_preflight(client, ["TableA", "TableB"])



    assert result["status"] == "preflight_ok"

    assert result["action"] == "deploy"

    assert "This will DEPLOY 2 data table(s)" in result["message"]

    assert len(result["preflight"]["tables"]) == 2

    assert not post_route.called





@respx.mock

def test_deploy_datatables_preflight_table_missing(client: CPQClient) -> None:

    respx.get("https://dev.example.com/rest/v18/datatables/Missing").mock(

        return_value=httpx.Response(404, json={"title": "Not found"})

    )

    post_route = respx.post(

        "https://dev.example.com/rest/v18/datatables/actions/deploy"

    ).mock(return_value=httpx.Response(200, json={}))



    result = run_deploy_datatables_preflight(client, ["Missing"])



    assert result["status"] == "preflight_failed"

    assert not post_route.called





@respx.mock

def test_deploy_datatables_preflight_empty_list(client: CPQClient) -> None:

    result = run_deploy_datatables_preflight(client, [])



    assert result["status"] == "preflight_failed"

    assert any("non-empty" in error for error in result["errors"])


@respx.mock
def test_resolve_write_execution_read_only_blocks_execution(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/users/12345").mock(
        return_value=httpx.Response(200, json={"partyNumber": "12345", "login": "alice"})
    )
    patch_route = respx.patch("https://dev.example.com/rest/v18/users/12345").mock(
        return_value=httpx.Response(200, json={"partyNumber": "12345"})
    )

    result = resolve_write_execution(
        read_only=True,
        dry_run=False,
        confirmation_token="valid-token-present",
        tool="update_user",
        action="update",
        preflight_fn=lambda: run_update_user_preflight(
            client, "12345", {"email": "new@b.com"}
        ),
        execute_fn=lambda: client.patch("/users/12345", json_body={"email": "new@b.com"}),
    )

    assert result["status"] == "read_only_blocked"
    assert not patch_route.called


@respx.mock
def test_resolve_write_execution_read_only_annotates_preflight(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/users/12345").mock(
        return_value=httpx.Response(200, json={"partyNumber": "12345", "login": "alice"})
    )

    result = resolve_write_execution(
        read_only=True,
        dry_run=True,
        confirmation_token=None,
        tool="update_user",
        action="update",
        preflight_fn=lambda: run_update_user_preflight(
            client, "12345", {"email": "new@b.com"}
        ),
        execute_fn=lambda: client.patch("/users/12345", json_body={"email": "new@b.com"}),
    )

    assert result["status"] == "preflight_ok"
    assert result["read_only"] is True
    assert result["execution_blocked"] is True
    assert "READ_ONLY=true" in result["message"]


