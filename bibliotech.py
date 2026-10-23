# BiblioTech v1.3 - Version nettoyee
# Gestion de la bibliotheque municipale
# Les sorties des commandes historiques sont conservees pour faciliter la comparaison.

import csv
import logging
import os
import sys
from datetime import date, datetime, timedelta

# Durees maximales d'emprunt selon le type de document (en jours).
LOAN_DAYS_BOOK = 21
LOAN_DAYS_DVD = 7
LOAN_DAYS_MAGAZINE = 3
LOAN_DAYS = {
    "book": LOAN_DAYS_BOOK,
    "dvd": LOAN_DAYS_DVD,
    "magazine": LOAN_DAYS_MAGAZINE,
}

# Nombre maximal de documents selon le statut du membre.
MAX_LOANS_STUDENT = 5
MAX_LOANS_PREMIUM = 8
MAX_LOANS_DEFAULT = 3
MAX_LOANS = {"student": MAX_LOANS_STUDENT, "premium": MAX_LOANS_PREMIUM}

# Penalites par jour de retard et reduction pour les etudiants.
DAILY_FEE_BOOK = 0.5
DAILY_FEE_DVD = 1.0
DAILY_FEE_MAGAZINE = 0.2
DAILY_FEES = {
    "book": DAILY_FEE_BOOK,
    "dvd": DAILY_FEE_DVD,
    "magazine": DAILY_FEE_MAGAZINE,
}
STUDENT_DISCOUNT = 0.5

# Dossier des fichiers CSV, personnalisable avec une variable d'environnement.
DATA = os.environ.get("BIBLIOTECH_DATA", "data")
TODAY = None
# Le mode debug reste accessible avec l'option --debug.
debug = False


def get_today():
    # Une date imposee par --today permet de reproduire les tests.
    return date.today() if TODAY is None else TODAY


def parse_date(value):
    # Tous les fichiers utilisent le meme format de date.
    return datetime.strptime(value, "%Y-%m-%d").date()


def late_fee(
    days_late: int,
    kind: str,
    member_type: str,
    price: float,
) -> float:
    """Pénalité de retard, réduite selon le membre et plafonnée au prix."""

    # Aucun frais lorsque le document n'est pas en retard.
    if days_late <= 0:
        return 0.0

    # Un type de document inconnu utilise le tarif d'un livre.
    daily_rate = DAILY_FEES.get(kind, DAILY_FEE_BOOK)

    fee = days_late * daily_rate

    # Les etudiants paient la moitié du frais et les membres premium ne paient rien.
    if member_type == "student":
        fee *= STUDENT_DISCOUNT
    elif member_type == "premium":
        fee = 0

    # La penalite ne peut pas depasser le prix du document.
    return round(min(fee, price), 2)


class Library:
    """Gestion des livres, membres, emprunts et extensions de BiblioTech."""

    def __init__(self):
        # On conserve b, m et l pour rester compatible avec les appels existants.
        self.b = []
        self.m = []
        self.l = []
        self.plugins = {}
        self.load()

    @staticmethod
    def _read_rows(filename):
        # Les champs peuvent contenir des points-virgules entre guillemets.
        with open(os.path.join(DATA, filename), encoding="utf-8", newline="") as file:
            reader = csv.reader(file, delimiter=";")
            next(reader, None)
            return [row for row in reader if any(cell.strip() for cell in row)]

    def load(self):
        """Charge les livres, les membres et les emprunts depuis les CSV."""
        # Reinitialiser les collections evite les doublons si load est rappelee.
        self.b = []
        self.m = []
        self.l = []

        for row in self._read_rows("books.csv"):
            self.b.append(
                {
                    "id": row[0],
                    "title": row[1],
                    "author": row[2],
                    "kind": row[3],
                    "price": float(row[4]),
                    "copies": int(row[5]),
                }
            )

        for row in self._read_rows("members.csv"):
            self.m.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "type": row[3],
                    "active": row[4] == "1",
                }
            )

        for row in self._read_rows("loans.csv"):
            # Une penalite absente ou non numerique vaut zero.
            try:
                fee = float(row[6])
            except (ValueError, IndexError):
                fee = 0.0
            self.l.append(
                {
                    "id": row[0],
                    "member": row[1],
                    "book": row[2],
                    "start": row[3],
                    "due": row[4],
                    "returned": row[5],
                    "fee": fee,
                }
            )

        if debug:
            print("chargement ok", len(self.b), len(self.m), len(self.l))

    def save(self):
        """Enregistre les emprunts dans loans.csv."""
        with open(
            os.path.join(DATA, "loans.csv"), "w", encoding="utf-8", newline=""
        ) as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\n")
            writer.writerow(
                ["id", "member_id", "book_id", "start", "due", "returned", "fee"]
            )
            for loan in self.l:
                writer.writerow(
                    [
                        loan["id"],
                        loan["member"],
                        loan["book"],
                        loan["start"],
                        loan["due"],
                        loan["returned"],
                        f"{loan['fee']:.2f}",
                    ]
                )

    def find(self, t, id):
        """Recherche un livre (b), un membre (m) ou un emprunt (l)."""
        collections = {"b": self.b, "m": self.m, "l": self.l}
        for item in collections.get(t, []):
            if item["id"] == id:
                return item
        return None

    def nb(self, mid):
        """Compte les emprunts encore en cours pour un membre."""
        return sum(
            1 for loan in self.l if loan["member"] == mid and loan["returned"] == ""
        )

    def dispo(self, bid):
        """Calcule le nombre d'exemplaires disponibles."""
        book = self.find("b", bid)
        borrowed = sum(
            1 for loan in self.l if loan["book"] == bid and loan["returned"] == ""
        )
        return book["copies"] - borrowed

    @staticmethod
    def _days_late(loan, end=None):
        """Retourne le retard signe a la date de reference."""
        reference = get_today() if end is None else end
        return (reference - parse_date(loan["due"])).days

    def _has_overdue_loans(self, member_id):
        # Seuls les emprunts non rendus peuvent bloquer un nouvel emprunt.
        return any(
            loan["member"] == member_id
            and loan["returned"] == ""
            and self._days_late(loan) > 0
            for loan in self.l
        )

    def _already_borrowed(self, member_id, book_id):
        # Un membre ne peut pas emprunter deux fois le meme document en cours.
        return any(
            loan["member"] == member_id
            and loan["book"] == book_id
            and loan["returned"] == ""
            for loan in self.l
        )

    def _next_loan_id(self):
        # On cherche le plus grand numero pour eviter de reutiliser un identifiant.
        maximum = max((int(loan["id"][1:]) for loan in self.l), default=0)
        return "L" + str(maximum + 1).zfill(3)

    def refusal_reason(self, member, book):
        """Retourne la raison de refus ou None si l'emprunt est autorisé."""

        member_id = member["id"]
        book_id = book["id"]

        # L'ordre des contrôles est conservé pour respecter le comportement initial.
        if not member["active"]:
            return "Refus : membre inactif"

        if self.has_overdue_loan(member_id):
            return "Refus : emprunts en retard"

        max_loans = MAX_LOANS.get(member["type"], MAX_LOANS_DEFAULT)

        if self.nb(member_id) >= max_loans:
            return f"Refus : limite d'emprunts atteinte ({max_loans})"

        if self._already_borrowed(member_id, book_id):
            return "Refus : deja emprunte par ce membre"

        if self.dispo(book_id) <= 0:
            return "Refus : plus d'exemplaire disponible"

        return None

    def create_loan(self, member, book):
        """Crée et sauvegarde un nouvel emprunt autorisé."""

        today = get_today()

        # La durée dépend du type de document
        loan_days = LOAN_DAYS.get(book["kind"], LOAN_DAYS_BOOK)
        due = today + timedelta(days=loan_days)

        new_id = self._next_loan_id()

        loan = {
            "id": new_id,
            "member": member["id"],
            "book": book["id"],
            "start": str(today),
            "due": str(due),
            "returned": "",
            "fee": 0,
        }

        self.l.append(loan)
        self.save()

        print(
            "Emprunt "
            + new_id
            + " enregistre : "
            + book["title"]
            + " pour "
            + member["name"]
            + ", retour avant le "
            + str(due)
        )

        return True

    def borrow_document(self, mid, bid):
        """Enregistre un emprunt apres verification des regles de la bibliotheque."""

        member = self.find("m", mid)

        if member is None:
            print("Erreur : membre inconnu")
            return False

        book = self.find("b", bid)

        if book is None:
            print("Erreur : livre inconnu")
            return False

        reason = self.refusal_reason(member, book)

        if reason is not None:
            print(reason)
            return False

        return self.create_loan(member, book)

    def borrow(self, member_id, book_id):
        """Point d'entrée principale pour emprunter un document."""
        return self.borrow_document(member_id, book_id)

    def has_overdue_loan(self, member_id):
        """Indique si le membre a un emprunt en retard."""
        return self._has_overdue_loans(member_id)

    def do_stuff(self, mid, bid):
        # Ancien nom conserve pour ne pas casser les appels externes existants.
        return self.borrow_document(mid, bid)

    def ret(self, lid):
        """Enregistre le retour d'un document et sa penalite eventuelle."""
        loan = self.find("l", lid)
        if loan is None:
            print("Erreur : emprunt inconnu")
            return
        if loan["returned"] != "":
            print("Erreur : emprunt deja rendu")
            return

        book = self.find("b", loan["book"])
        member = self.find("m", loan["member"])
        today = get_today()
        days_late = max(self._days_late(loan, today), 0)
        fee = late_fee(days_late, book["kind"], member["type"], book["price"])
        loan["returned"] = str(today)
        loan["fee"] = fee
        self.save()
        print(
            "Retour enregistre : "
            + book["title"]
            + ". Retard : "
            + str(days_late)
            + " jour(s). Penalite : "
            + f"{fee:.2f}"
            + " EUR"
        )

    def overdue(self):
        """Affiche les emprunts en retard et les rappels correspondants."""
        late_loans = [
            loan
            for loan in self.l
            if loan["returned"] == "" and self._days_late(loan) > 0
        ]
        if not late_loans:
            print("Aucun retard.")
            return

        late_loans.sort(key=lambda loan: (loan["due"], loan["id"]))
        total = 0
        for loan in late_loans:
            book = self.find("b", loan["book"])
            member = self.find("m", loan["member"])
            days_late = self._days_late(loan)
            fee = late_fee(days_late, book["kind"], member["type"], book["price"])
            total += fee
            print(
                loan["id"]
                + " | "
                + member["name"]
                + " | "
                + book["title"]
                + " | "
                + str(days_late)
                + " jour(s) | "
                + f"{fee:.2f}"
                + " EUR"
            )
            # Le programme simule l'envoi du mail en l'affichant a l'ecran.
            print(
                "EMAIL -> "
                + member["email"]
                + " : Rappel, vous devez rendre '"
                + book["title"]
                + "' (retard "
                + str(days_late)
                + " jours)"
            )
        print("Total des penalites en cours : " + f"{total:.2f}" + " EUR")

    def report(self):
        """Affiche les statistiques generales de la bibliotheque."""
        print("=== RAPPORT BIBLIOTECH ===")
        print("Date : " + str(get_today()))
        copies = sum(book["copies"] for book in self.b)
        print(f"Titres : {len(self.b)} ({copies} exemplaires)")
        active_members = sum(1 for member in self.m if member["active"])
        print(f"Membres : {len(self.m)} dont {active_members} actifs")

        current = 0
        overdue_count = 0
        collected = 0
        outstanding = 0
        book_counts = {}
        type_counts = {}

        for loan in self.l:
            # Ces compteurs servent au classement des documents et des types.
            book_counts[loan["book"]] = book_counts.get(loan["book"], 0) + 1
            book = self.find("b", loan["book"])
            type_counts[book["kind"]] = type_counts.get(book["kind"], 0) + 1

            if loan["returned"] == "":
                current += 1
                days_late = self._days_late(loan)
                if days_late > 0:
                    overdue_count += 1
                    member = self.find("m", loan["member"])
                    outstanding += late_fee(
                        days_late,
                        book["kind"],
                        member["type"],
                        book["price"],
                    )
            else:
                collected += loan["fee"]

        print(
            "Emprunts : "
            + str(len(self.l))
            + " au total, "
            + str(current)
            + " en cours, "
            + str(overdue_count)
            + " en retard"
        )
        print("Penalites encaissees : " + f"{collected:.2f}" + " EUR")
        print("Penalites en attente : " + f"{outstanding:.2f}" + " EUR")
        for kind in sorted(type_counts):
            print("  - " + kind + " : " + str(type_counts[kind]) + " emprunt(s)")

        # Trier par nombre d'emprunts decroissant, puis par titre.
        ranking = sorted(
            (-count, self.find("b", book_id)["title"])
            for book_id, count in book_counts.items()
        )
        print("Top 3 :")
        for position, (negative_count, title) in enumerate(ranking[:3], start=1):
            print(f"  {position}. {title} ({-negative_count})")

    def export(self, fname, sep):
        """Exporte les emprunts vers un fichier CSV."""
        with open(fname, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file, delimiter=sep, lineterminator="\n")
            writer.writerow(
                [
                    "loan_id",
                    "member",
                    "title",
                    "start",
                    "due",
                    "returned",
                    "days_late",
                    "fee",
                ]
            )
            count = 0
            for loan in self.l:
                book = self.find("b", loan["book"])
                member = self.find("m", loan["member"])
                end = parse_date(loan["returned"]) if loan["returned"] else get_today()
                days_late = max(self._days_late(loan, end), 0)
                fee = late_fee(days_late, book["kind"], member["type"], book["price"])
                writer.writerow(
                    [
                        loan["id"],
                        member["name"],
                        book["title"],
                        loan["start"],
                        loan["due"],
                        loan["returned"],
                        str(days_late),
                        f"{fee:.2f}",
                    ]
                )
                count += 1
        print("Export termine : " + str(count) + " lignes dans " + fname)

    def register_plugin(self, name, fn, priority=0, options=None):
        """Enregistre une extension avec ses options et sa priorite."""
        # None evite de partager un dictionnaire mutable entre plusieurs appels.
        if options is None:
            options = {}
        self.plugins[name] = {"fn": fn, "priority": priority, "options": options}

    def run_plugins(self, event, payload=None):
        """Execute les extensions par ordre de priorite."""
        results = []
        for name in sorted(self.plugins, key=lambda key: self.plugins[key]["priority"]):
            try:
                results.append(
                    self.plugins[name]["fn"](
                        event, payload, **self.plugins[name]["options"]
                    )
                )
            except Exception:
                # Signaler l'erreur sans interrompre les autres extensions
                logging.exception("Erreur lors de l'execution de l'extension %s", name)
        return results


# Affiche les documents et le nombre d'exemplaires disponibles.
def show_books(lib):
    for book in lib.b:
        available = lib.dispo(book["id"])
        print(
            f"{book['id']} | {book['title']} | {book['author']} | "
            f"{book['kind']} | {available}/{book['copies']} disponible(s)"
        )


# Affiche les membres et leur nombre d'emprunts en cours.
def show_members(lib):
    for member in lib.m:
        status = "actif" if member["active"] else "inactif"
        print(
            f"{member['id']} | {member['name']} | {member['type']} | "
            f"{status} | {lib.nb(member['id'])} emprunt(s) en cours"
        )


# Verifie les arguments avant d'enregistrer un emprunt.
def handle_borrow(lib, args):
    if len(args) < 3:
        print("Usage : borrow <id_membre> <id_document>")
        return 1
    if lib.borrow(args[1], args[2]) is False:
        return 2
    return 0


# Verifie l'identifiant avant d'enregistrer un retour.
def handle_return(lib, args):
    if len(args) < 2:
        print("Usage : return <id_emprunt>")
        return 1
    # Le code retour historique reste 0 meme pour un emprunt inconnu.
    lib.ret(args[1])
    return 0


# Verifie le nom du fichier avant l'export CSV.
def handle_export(lib, args):
    if len(args) < 2:
        print("Usage : export <fichier.csv>")
        return 1
    lib.export(args[1], ";")
    return 0


# Fonction principale : choisit la commande et renvoie son code de resultat.
def process(args):
    """Execute la commande demandee par l'utilisateur."""
    lib = Library()
    if not args:
        print(
            "Usage : python bibliotech.py <commande> [arguments] [--today AAAA-MM-JJ]"
        )
        print("Commandes : list, members, borrow, return, overdue, report, export")
        return 1

    command = args[0]

    # Commandes ne demandant aucun argument supplementaire.
    simple_commands = {
        "list": show_books,
        "members": show_members,
        "overdue": Library.overdue,
        "report": Library.report,
    }
    if command in simple_commands:
        simple_commands[command](lib)
        return 0

    # Commandes qui verifient leurs propres arguments.
    commands_with_args = {
        "borrow": handle_borrow,
        "return": handle_return,
        "export": handle_export,
    }
    if command in commands_with_args:
        return commands_with_args[command](lib, args)

    print("Commande inconnue : " + command)
    return 1


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if "--today" in arguments:
        index = arguments.index("--today")
        TODAY = parse_date(arguments[index + 1])
        arguments = arguments[:index] + arguments[index + 2 :]
    if "--debug" in arguments:
        debug = True
        arguments.remove("--debug")
    sys.exit(process(arguments))
