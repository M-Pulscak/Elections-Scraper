"""
volby.py: Třetí projekt do Engeto Online Python Akademie

author: Michal Pulščák
email: pumi666@atlas.cz
discord: pumi_666
"""

import sys
import csv
import requests
from bs4 import BeautifulSoup
from typing import List


# Globální proměnné pro ukládání dat
volici: List[str] = []
ucast: List[str] = []
platnych: List[str] = []


def stahni_html(link: str) -> BeautifulSoup:
    """Stáhne a vrátí HTML stránku jako BeautifulSoup objekt."""
    try:
        response = requests.get(link)
        response.raise_for_status()
        print(f"Stahuji data z URL: {link}")
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Chyba při stahování {link}: {e}")
        sys.exit(1)


def get_obce(html: BeautifulSoup) -> List[str]:
    """Vrátí seznam názvů obcí z hlavní stránky."""
    return [town.text for town in html.find_all("td", class_="overflow_name")]


def get_linky(html: BeautifulSoup) -> List[str]:
    """Vrátí seznam URL adres pro jednotlivé obce."""
    zaklad_url = "https://volby.cz/pls/ps2017nss/"
    return [
        f"{zaklad_url}{link.a['href']}"
        for link in html.find_all("td", class_="cislo")
        if link.a
    ]


def get_id(html: BeautifulSoup) -> List[str]:
    """Vrátí seznam ID obcí."""
    return [idcko.text for idcko in html.find_all("td", class_="cislo")]


def seznam_stran(link: str) -> List[str]:
    """Vrátí seznam politických stran z detailní stránky první obce."""
    html = stahni_html(link)
    return [strany.text for strany in html.find_all("td", class_="overflow_name")]


def data_volicu(link: List[str]) -> None:
    """Stahuje data o voličích, účasti a platných hlasech."""
    global volici, ucast, platnych

    def data(stranka: BeautifulSoup, header_id: str) -> List[str]:
        return [
            cell.text.replace('\xa0', ' ')
            for cell in stranka.find_all("td", headers=header_id)
        ]

    for x in link:
        html = stahni_html(x)
        volici.extend(data(html, "sa2"))
        ucast.extend(data(html, "sa3"))
        platnych.extend(data(html, "sa6"))


def seznam_vysledku(link: List[str]) -> List[List[str]]:
    """Vrací seznam procentuálních výsledků každé strany v jednotlivých obcích."""
    vysledky = []
    for x in link:
        html = stahni_html(x)
        volba = [
            volba.text.replace('\xa0', ' ')
            for volba in html.find_all("td", class_="cislo", headers=["t1sb4", "t2sb4"])
        ]
        vysledky.append(volba)
    return vysledky


def tvorba_radku(obec_id: List[str], obec: List[str], link: List[str]) -> List[List[str]]:
    """Vytváří data pro zápis do CSV."""
    data_volicu(link)
    vysledky = seznam_vysledku(link)
    radky = []
    for i, (id_obce, obce, volicu, vydane, platne) in enumerate(
        zip(obec_id, obec, volici, ucast, platnych)
    ):
        radky.append([id_obce, obce, volicu, vydane, platne] + vysledky[i])
    return radky


def uloz_csv(nazev_souboru: str, header: List[str], radky: List[List[str]]) -> None:
    """Uloží data do CSV souboru."""
    try:
        with open(nazev_souboru, "w", newline="", encoding="utf-8") as soubor:
            writer = csv.writer(soubor)
            writer.writerow(header)
            writer.writerows(radky)
        print(f"Data byla úspěšně uložena do souboru: {nazev_souboru}")
    except IOError as e:
        print(f"Chyba při ukládání souboru {nazev_souboru}: {e}")
        sys.exit(1)


def main():
    """Hlavní funkce programu."""
    if len(sys.argv) != 3:
        print(
            "Nesprávné argumenty.\n"
            "Zadej v tomto formátu: volby.py <odkaz> <vystupni_soubor.csv>"
        )
        sys.exit(1)

    odkaz, vystupni_soubor = sys.argv[1], sys.argv[2]

    # Získání HTML hlavní stránky
    html = stahni_html(odkaz)

    # Získání dat o obcích a odkazů
    obec = get_obce(html)
    link = get_linky(html)
    id_obce = get_id(html)

    # Získání politických stran z první obce
    strany = seznam_stran(link[0])

    # Vytvoření řádků pro CSV
    radek = tvorba_radku(id_obce, obec, link)

    # Hlavička CSV
    header = ["Kód obce", "Název obce", "Voliči v seznamu", "Vydané obálky", "Platné hlasy"] + strany

    # Uložení do souboru
    uloz_csv(vystupni_soubor, header, radek)


if __name__ == "__main__":
    main()
