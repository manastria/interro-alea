import random
import logging
import json
import argparse
from enum import Enum
from datetime import datetime
from colorama import Fore, Style, init
from colorlog import ColoredFormatter

# Configuration du logger
VERBOSE = False

def parse_arguments():
    parser = argparse.ArgumentParser(description="Configurer le fichier du registre et le niveau de verbosité.")
    parser.add_argument("--file", type=str, default="aaa.json", help="Nom du fichier du registre.")
    parser.add_argument("--verbose", action="store_true", help="Activer la verbosité des logs.")
    return parser.parse_args()

def definir_enumerations():
    class Couleur(Enum):
        ROUGE = Fore.RED
        VERT = Fore.GREEN
        BLEU = Fore.BLUE
        JAUNE = Fore.YELLOW
        CYAN = Fore.CYAN
        MAGENTA = Fore.MAGENTA
        BLANC = Fore.WHITE
        NOIR = Fore.BLACK
    return Couleur

def affichage_couleur(string, couleur):
    print(f"{couleur.value}{string}{Style.RESET_ALL}")


def configure_logger(verbosity):
    """Configure le logger en fonction de la verbosité"""
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.DEBUG)

    if verbosity:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        log_format = "[%(levelname)s] %(message)s"
        colored_formatter = ColoredFormatter(
            "%(log_color)s" + log_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )

        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)
    else:
        file_handler = logging.FileHandler('my_logs.log', mode="w", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)

    return logger

def normaliser_poids(poids):
    """
    Normalise les poids des mots.

    Args:
    poids (dict): Dictionnaire contenant les mots et leurs poids.

    Returns:
    dict: Dictionnaire contenant les mots et leurs poids normalisés.
    """
    # Calculer le total des poids
    total_poids = sum(poids.values())
    
    # Normaliser les poids et retourner le dictionnaire
    return {mot: p / total_poids for mot, p in poids.items()}

def construire_cdf(poids_normalises):
    """
    Construit la fonction de distribution cumulée (CDF) à partir des poids normalisés.

    Args:
    poids_normalises (dict): Dictionnaire contenant les mots et leurs poids normalisés.

    Returns:
    dict: Dictionnaire contenant la CDF.
    """
    cdf = {}
    somme_cumulee = 0
    
    # Construire la CDF
    for mot, p in poids_normalises.items():
        somme_cumulee += p
        cdf[somme_cumulee] = mot

    return cdf

def choisir_mot(cdf):
    """
    Choisit un mot aléatoirement en utilisant la CDF.

    Args:
    cdf (dict): Dictionnaire contenant la CDF.

    Returns:
    str: Le mot choisi.
    """
    # Générer un nombre aléatoire entre 0 et 1
    rand_val = random.random()
    
    # Utiliser la CDF pour choisir un mot
    for seuil, mot in cdf.items():
        if rand_val <= seuil:
            return mot

def calculer_poids_etudiants(registre):
    aujourd_hui = datetime.today().strftime('%Y-%m-%d')

    # Calculer le nombre d'interrogations et la date la plus récente pour chaque étudiant
    stats = {}
    for etudiant, dates in registre.items():
        nb_interrogations = len(dates)
        derniere_date = max(dates, default=aujourd_hui)
        jours_depuis_derniere_date = (datetime.strptime(aujourd_hui, '%Y-%m-%d') - datetime.strptime(derniere_date, '%Y-%m-%d')).days

        stats[etudiant] = (nb_interrogations, derniere_date, jours_depuis_derniere_date)

    # Obtenir la valeur max, min et avg pour jours_depuis_derniere_date
    jours_depuis_derniere_date_max = max([d[2] for d in stats.values()])
    jours_depuis_derniere_date_min = min([d[2] for d in stats.values()])
    jours_depuis_derniere_date_avg = sum([d[2] for d in stats.values()]) / len(stats)

    # Obtenir la date la plus ancienne
    date_la_plus_ancienne = min([d[1] for d in stats.values()])
    
    if VERBOSE:
        print("Date la plus ancienne:", date_la_plus_ancienne)

    # Calculer les poids en fonction du nombre d'interrogations et de la date
    poids = {}
    for etudiant, (nb, date, jours_depuis_derniere_date) in stats.items():
        if nb == 0:
            poids[etudiant] = 6
        else:
            poids[etudiant] = (1 / (nb + 1)) * 2 + (jours_depuis_derniere_date - jours_depuis_derniere_date_min) / ((jours_depuis_derniere_date_max - jours_depuis_derniere_date_min) + 1)

    return poids

def lire_registre(fichier):
    with open(fichier, "r", encoding='utf-8') as f:
        return json.load(f)

def ecrire_registre(fichier, registre):
    with open(fichier, "w", encoding='utf-8') as f:
        json.dump(registre, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    args = parse_arguments()
    
    # Définir les énumérations de couleur
    Couleur = definir_enumerations()
    
    # Nom du fichier
    data_filename = args.file
    VERBOSE = args.verbose
    
    configure_logger(VERBOSE)
    
    # Charger le registre
    registre = lire_registre(data_filename)

    # Calculer les poids
    poids = calculer_poids_etudiants(registre)

    # Normaliser les poids
    poids_normalises = normaliser_poids(poids)

    if VERBOSE:
        # Afficher les poinds dans l'ordre décroissant
        print("Poids des étudiants:")
        for mot, p in sorted(poids.items(), key=lambda x: x[1], reverse=True):
            print(f"\t - {mot}: {p}")

    # Construction de la CDF
    cdf = construire_cdf(poids_normalises)

    # Choix d'un étudiant
    etudiant_choisi = choisir_mot(cdf)

    # Mettre à jour le registre
    registre[etudiant_choisi].append(datetime.today().strftime('%Y-%m-%d'))
    ecrire_registre(data_filename, registre)

    # Utiliser la fonction affichage_couleur pour afficher le nom de l'étudiant en bleu
    affichage_couleur(f"Étudiant choisi: {etudiant_choisi}", Couleur.BLEU)
