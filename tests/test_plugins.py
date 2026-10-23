import logging


def test_plugin_error_does_not_stop_other_plugins(library, caplog):
    # Cette extension simule une erreur.
    def broken_plugin(event, payload):
        raise ValueError("Erreur de test")

    # Cette extension doit fonctionner malgré la précédente.
    def working_plugin(event, payload):
        return "Extension executee"

    library.register_plugin("broken", broken_plugin, priority=1)
    library.register_plugin("working", working_plugin, priority=2)

    with caplog.at_level(logging.ERROR):
        result = library.run_plugins("test")

    assert result == ["Extension executee"]
    assert "Erreur lors de l'execution de l'extension broken" in caplog.text
    assert "ValueError: Erreur de test" in caplog.text
