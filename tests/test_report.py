def test_report_displays_statistics(library, capsys):
    """Vérifie que le rapport affiche les statistiques correctes."""
    library.report()
    output = capsys.readouterr().out

    assert "=== RAPPORT BIBLIOTECH ===" in output
    assert "Emprunts :" in output
    assert "Penalites encaissees :" in output
    assert "Penalites en attente :" in output
    assert "Top 3 :" in output
