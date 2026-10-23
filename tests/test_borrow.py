def test_inactive_member_is_refused(library, capsys):
    # Un membre qui a un emprunt en retard ne peut pas emprunter.
    result = library.borrow_document("M004", "B002")

    # Vérifier que l'opération a échoué.
    assert result is False
    assert "Refus : membre inactif" in capsys.readouterr().out


def test_already_borrowed_document_is_refused(library, capsys):
    # Un membre ne peut pas emprunter deux fois le même document.
    result = library.borrow_document("M005", "B001")

    # Vérifier que l'opération a échoué.
    assert result is False
    assert "Refus : deja emprunte par ce membre" in capsys.readouterr().out


def test_unavailable_document_is_refused(library, capsys):
    # Aucun emprunt si tous les exemplaires sont déjà pris.
    result = library.borrow_document("M005", "B003")

    # Vérifier que l'opération a échoué.
    assert result is False
    assert "Refus : plus d'exemplaire disponible" in capsys.readouterr().out


def test_member_loan_limit_is_refused(library, capsys):
    # Les emprunts successifs utilisent uniquement les données temporaires.
    assert library.borrow_document("M005", "B005") is True
    assert library.borrow_document("M005", "B002") is True

    capsys.readouterr()

    # Un membre atteint sa limite et ne peut plus emprunter.
    result = library.borrow_document("M005", "B007")

    # Vérifier que l'opération a échoué.
    assert result is False
    assert "Refus : limite d'emprunts atteinte" in capsys.readouterr().out


def test_successful_borrow(library, capsys):
    # Un emprunt autorisé doit être enregistré avec la bonne échéance.
    result = library.borrow_document("M005", "B005")

    # Vérifier que l'opération a réussi.
    assert result is True

    loan = library.find("l", "L013")

    assert loan is not None
    assert loan["member"] == "M005"
    assert loan["book"] == "B005"
    assert loan["due"] == "2026-10-28"
    assert loan["returned"] == ""

    assert "Emprunt L013 enregistre" in capsys.readouterr().out


def test_member_with_overdue_loan_is_refused(library, capsys):
    # Un emprunt en retard bloque tout nouvel emprunt.
    result = library.borrow_document("M001", "B002")

    # Vérifier que l'opération a échoué.
    assert result is False
    assert "Refus : emprunts en retard" in capsys.readouterr().out
