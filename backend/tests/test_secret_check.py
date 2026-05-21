"""SECRET_KEY hardening in config.assert_production_secrets."""


def test_assert_production_secrets_exits_on_insecure_key_in_prod(monkeypatch):
    import config

    monkeypatch.setattr(config.settings, "SECRET_KEY", "development-secret-key")
    monkeypatch.setattr(config.settings, "ENVIRONMENT", "production")

    exited = {"code": None}

    def fake_exit(code):
        exited["code"] = code
        raise SystemExit(code)

    monkeypatch.setattr(config.sys, "exit", fake_exit)
    try:
        config.assert_production_secrets()
    except SystemExit:
        pass
    assert exited["code"] == 1, "must exit(1) in production with insecure key"


def test_assert_production_secrets_passes_with_strong_key(monkeypatch):
    import config

    monkeypatch.setattr(
        config.settings,
        "SECRET_KEY",
        "u3kf-very-long-strong-secret-key-not-default-0123456789",
    )
    monkeypatch.setattr(config.settings, "ENVIRONMENT", "production")
    # Should not raise / exit
    config.assert_production_secrets()


def test_assert_production_secrets_dev_only_warns(monkeypatch, capsys):
    import config

    monkeypatch.setattr(config.settings, "SECRET_KEY", "development-secret-key-change-in-production")
    monkeypatch.setattr(config.settings, "ENVIRONMENT", "development")
    config.assert_production_secrets()
    err = capsys.readouterr().err
    assert "WARNING" in err
