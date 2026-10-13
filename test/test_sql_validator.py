from query.sql_validator import validate_sql_statement


def test_valid_select_is_allowed():
    assert validate_sql_statement("SELECT COUNT(*) FROM CAPA WHERE Status = 'Open';") is True


def test_rejects_data_modification():
    try:
        validate_sql_statement("DELETE FROM CAPA WHERE Status = 'Open';")
    except ValueError:
        return
    raise AssertionError("DELETE statement should have been rejected")
