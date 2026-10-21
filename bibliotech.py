# BiblioTech v1.3 - Version nettoyee
# Gestion de la bibliotheque municipale
# Refactorisation : code plus lisible sans changer les messages de l'application.

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


def late_fee(days, book, member):
    # Aucun frais lorsque le document n'est pas en retard.
    if days <= 0:
        return 0.0

    # Un type de document inconnu utilise le tarif d'un livre.
    daily_fee = DAILY_FEES.get(book["kind"], DAILY_FEE_BOOK)
    fee = days * daily_fee

    # Les etudiants paient la moitie et les membres premium ne paient rien.
    if member["type"] == "student":
        fee *= STUDENT_DISCOUNT
    elif member["type"] == "premium":
        fee = 0

    # La penalite ne peut pas depasser le prix du document.
    return round(min(fee, book["price"]), 2)


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
        # with ferme automatiquement le fichier, meme en cas d'erreur.
        with open(os.path.join(DATA, filename), encoding="utf-8") as file:
            lines = file.readlines()
        # La premiere ligne contient les noms des colonnes.
        return [line.strip().split(";") for line in lines[1:] if line.strip()]

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
        with open(os.path.join(DATA, "loans.csv"), "w", encoding="utf-8") as file:
            file.write("id;member_id;book_id;start;due;returned;fee\n")
            for loan in self.l:
                file.write(
                    f"{loan['id']};{loan['member']};{loan['book']};"
                    f"{loan['start']};{loan['due']};{loan['returned']};"
                    f"{loan['fee']:.2f}\n"
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
            1
            for loan in self.l
            if loan["member"] == mid and loan["returned"] == ""
        )

    def dispo(self, bid):
        """Calcule le nombre d'exemplaires disponibles."""
        book = self.find("b", bid)
        borrowed = sum(
            1
            for loan in self.l
            if loan["book"] == bid and loan["returned"] == ""
        )
        return book["copies"] - borrowed

    def _has_overdue_loans(self, member_id):
        # Seuls les emprunts non rendus peuvent bloquer un nouvel emprunt.
        return any(
            loan["member"] == member_id
            and loan["returned"] == ""
            and parse_date(loan["due"]) < get_today()
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

        if not member["active"]:
            print("Refus : membre inactif")
            return False

        if self._has_overdue_loans(mid):
            print("Refus : emprunts en retard")
            return False

        max_loans = MAX_LOANS.get(member["type"], MAX_LOANS_DEFAULT)
        if self.nb(mid) >= max_loans:
            print("Refus : limite d'emprunts atteinte (" + str(max_loans) + ")")
            return False

        if self._already_borrowed(mid, bid):
            print("Refus : deja emprunte par ce membre")
            return False

        if self.dispo(bid) <= 0:
            print("Refus : plus d'exemplaire disponible")
            return False

        # Les retours anticipes evitent les nombreux niveaux de if imbriques.
        today = get_today()
        loan_days = LOAN_DAYS.get(book["kind"], LOAN_DAYS_BOOK)
        due = today + timedelta(days=loan_days)
        new_id = self._next_loan_id()
        self.l.append(
            {
                "id": new_id,
                "member": mid,
                "book": bid,
                "start": str(today),
                "due": str(due),
                "returned": "",
                "fee": 0,
            }
        )
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
        days_late = max((today - parse_date(loan["due"])).days, 0)
        fee = late_fee(days_late, book, member)
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
            if loan["returned"] == "" and parse_date(loan["due"]) < get_today()
        ]
        if not late_loans:
            print("Aucun retard.")
            return

        late_loans.sort(key=lambda loan: (loan["due"], loan["id"]))
        total = 0
        for loan in late_loans:
            book = self.find("b", loan["book"])
            member = self.find("m", loan["member"])
            # Calculer nbj avant de l'utiliser corrige une erreur du fichier initial.
            days_late = (get_today() - parse_date(loan["due"])).days
            fee = late_fee(days_late, book, member)
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
        print(
            f"Membres : {len(self.m)} dont {active_members} actifs"
        )

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
                days_late = (get_today() - parse_date(loan["due"])).days
                if days_late > 0:
                    overdue_count += 1
                    member = self.find("m", loan["member"])
                    outstanding += late_fee(days_late, book, member)
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
            print(
                f"  {position}. {title} ({-negative_count})"
            )

    def export(self, fname, sep):
        """Exporte les emprunts vers un fichier CSV."""
        with open(fname, "w", encoding="utf-8") as file:
            file.write(
                sep.join(
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
                + "\n"
            )
            count = 0
            for loan in self.l:
                book = self.find("b", loan["book"])
                member = self.find("m", loan["member"])
                end = (
                    parse_date(loan["returned"])
                    if loan["returned"]
                    else get_today()
                )
                days_late = max((end - parse_date(loan["due"])).days, 0)
                fee = late_fee(days_late, book, member)
                file.write(
                    sep.join(
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
                    + "\n"
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
        for name in sorted(
            self.plugins, key=lambda key: self.plugins[key]["priority"]
        ):
            try:
                results.append(
                    self.plugins[name]["fn"](
                        event, payload, **self.plugins[name]["options"]
                    )
                )
            except Exception:
                # Conserver le comportement initial : une extension en erreur
                # n'empeche pas les autres extensions de fonctionner.
                continue
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


# Vérifie les arguments avant d'enregistrer un emprunt.
def handle_borrow(lib, args):
    if len(args) < 3:
        print("Usage : borrow <id_membre> <id_document>")
        return 1
    if lib.borrow_document(args[1], args[2]) is False:
        return 2
    return 0


# Vérifie l'identifiant avant d'enregistrer un retour.
def handle_return(lib, args):
    if len(args) < 2:
        print("Usage : return <id_emprunt>")
        return 1
    lib.ret(args[1])
    return 0


# Vérifie le nom du fichier avant l'export CSV.
def handle_export(lib, args):
    if len(args) < 2:
        print("Usage : export <fichier.csv>")
        return 1
    lib.export(args[1], ";")
    return 0


# Ces fonctions permettent d'exécuter les commandes sans arguments.
def handle_overdue(lib):
    lib.overdue()


def handle_report(lib):
    lib.report()


# Fonction principale : choisit la commande et renvoie son code de résultat.
def process(args):
    """Exécute la commande demandée par l'utilisateur."""
    lib = Library()
    if not args:
        print(
            "Usage : python bibliotech.py <commande> "
            "[arguments] [--today AAAA-MM-JJ]"
        )
        print("Commandes : list, members, borrow, return, overdue, report, export")
        return 1

    command = args[0]

    # Commandes ne demandant aucun argument supplémentaire.
    simple_commands = {
        "list": show_books,
        "members": show_members,
        "overdue": handle_overdue,
        "report": handle_report,
    }
    if command in simple_commands:
        simple_commands[command](lib)
        return 0

    # Commandes qui vérifient leurs propres arguments.
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
