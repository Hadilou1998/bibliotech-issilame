# Importation de pytest afin de tester plusieurs cas d'usage
import pytest

# Importation de la fonction que nous allons tester
from bibliotech import late_fee


# Chaque ligne représente un cas de calcul de pénalité.
@pytest.mark.parametrize(
    "days_late, kind, member_type, price, expected",
    [
        (0, "book", "standard", 20.0, 0.0),
        (-3, "book", "standard", 20.0, 0.0),
        (4, "book", "standard", 20.0, 2.0),
        (10, "dvd", "standard", 20.0, 10.0),
        (10, "magazine", "standard", 20.0, 2.0),
        (10, "dvd", "student", 20.0, 5.0),
        (10, "dvd", "premium", 20.0, 0.0),
        (100, "dvd", "standard", 12.0, 12.0),
        (4, "unknown", "standard", 20.0, 2.0),
    ],
)
def test_late_fee(days_late, kind, member_type, price, expected):
    # Le montant doit respecter les règles de pénalité
    result = late_fee(days_late, kind, member_type, price)

    assert result == pytest.approx(expected)
