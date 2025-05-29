import csv
from faker import Faker
import random
from dataclasses import dataclass
import unidecode
import gspread

tsv_data = """61900\tBrno 19\tBrno\tBohunice
62500\tBrno 25\tBrno\tBohunice
63900\tBrno 39\tBrno\tBohunice
64200\tBrno 42\tBrno\tBosonohy
61700\tBrno 17\tBrno\tBrněnské Ivanovice
62000\tBrno 20\tBrno\tBrněnské Ivanovice
61900\tBrno 19\tBrno\tBrno-Bohunice
62500\tBrno 25\tBrno\tBrno-Bohunice
63900\tBrno 39\tBrno\tBrno-Bohunice
64200\tBrno 42\tBrno\tBrno-Bosonohy
61700\tBrno 17\tBrno\tBrno-Brněnské Ivanovice
62000\tBrno 20\tBrno\tBrno-Brněnské Ivanovice
63500\tBrno 35\tBrno\tBrno-Bystrc
66471\tVeverská Bítýška\tBrno\tBrno-Bystrc
61300\tBrno 13\tBrno\tBrno-Černá Pole
61800\tBrno 18\tBrno\tBrno-Černovice
62700\tBrno 27\tBrno\tBrno-Černovice
62000\tBrno 20\tBrno\tBrno-Chrlice
64300\tBrno 43\tBrno\tBrno-Chrlice
66442\tModřice\tBrno\tBrno-Chrlice
61700\tBrno 17\tBrno\tBrno-Dolní Heršpice
61900\tBrno 19\tBrno\tBrno-Dolní Heršpice
62000\tBrno 20\tBrno\tBrno-Dvorska
62000\tBrno 20\tBrno\tBrno-Holásky
61700\tBrno 17\tBrno\tBrno-Horní Heršpice
61900\tBrno 19\tBrno\tBrno-Horní Heršpice
61300\tBrno 13\tBrno\tBrno-Husovice
61400\tBrno 14\tBrno\tBrno-Husovice
63800\tBrno 38\tBrno\tBrno-Husovice
62100\tBrno 21\tBrno\tBrno-Ivanovice
62100\tBrno 21\tBrno\tBrno-Jehnice
66434\tKuřim\tBrno\tBrno-Kníničky
63500\tBrno 35\tBrno\tBrno-Kníničky
62300\tBrno 23\tBrno\tBrno-Kohoutovice
60200\tBrno 2\tBrno\tBrno-Komárov
61700\tBrno 17\tBrno\tBrno-Komárov
61800\tBrno 18\tBrno\tBrno-Komárov
61600\tBrno 16\tBrno\tBrno-Komín
62400\tBrno 24\tBrno\tBrno-Komín
63500\tBrno 35\tBrno\tBrno-Komín
61200\tBrno 12\tBrno\tBrno-Královo Pole
61600\tBrno 16\tBrno\tBrno-Královo Pole
61200\tBrno 12\tBrno\tBrno-Lesná
61400\tBrno 14\tBrno\tBrno-Lesná
63800\tBrno 38\tBrno\tBrno-Lesná
62800\tBrno 28\tBrno\tBrno-Líšeň
63600\tBrno 36\tBrno\tBrno-Líšeň
61200\tBrno 12\tBrno\tBrno-Medlánky
62100\tBrno 21\tBrno\tBrno-Medlánky
60200\tBrno 2\tBrno\tBrno-město
63900\tBrno 39\tBrno\tBrno-město
62100\tBrno 21\tBrno\tBrno-Mokrá Hora
61400\tBrno 14\tBrno\tBrno-Obřany
64400\tBrno 44\tBrno\tBrno-Obřany
62100\tBrno 21\tBrno\tBrno-Ořešín
60300\tBrno 3\tBrno\tBrno-Pisárky
63700\tBrno 37\tBrno\tBrno-Pisárky
60200\tBrno 2\tBrno\tBrno-Ponava
61200\tBrno 12\tBrno\tBrno-Ponava
61900\tBrno 19\tBrno\tBrno-Přízřenice
61200\tBrno 12\tBrno\tBrno-Řečkovice
62100\tBrno 21\tBrno\tBrno-Řečkovice
61200\tBrno 12\tBrno\tBrno-Sadová
62700\tBrno 27\tBrno\tBrno-Slatina
64400\tBrno 44\tBrno\tBrno-Soběšice
60200\tBrno 2\tBrno\tBrno-Staré Brno
60300\tBrno 3\tBrno\tBrno-Staré Brno
63900\tBrno 39\tBrno\tBrno-Staré Brno
62500\tBrno 25\tBrno\tBrno-Starý Lískovec
60200\tBrno 2\tBrno\tBrno-Stránice
61600\tBrno 16\tBrno\tBrno-Stránice
61900\tBrno 19\tBrno\tBrno-Štýřice
63900\tBrno 39\tBrno\tBrno-Štýřice
60200\tBrno 2\tBrno\tBrno-Trnitá
61700\tBrno 17\tBrno\tBrno-Trnitá
62000\tBrno 20\tBrno\tBrno-Tuřany
62700\tBrno 27\tBrno\tBrno-Tuřany
64400\tBrno 44\tBrno\tBrno-Útěchov
60200\tBrno 2\tBrno\tBrno-Veveří
61600\tBrno 16\tBrno\tBrno-Veveří
60200\tBrno 2\tBrno\tBrno-Žabovřesky
61200\tBrno 12\tBrno\tBrno-Žabovřesky
61600\tBrno 16\tBrno\tBrno-Žabovřesky
63700\tBrno 37\tBrno\tBrno-Žabovřesky
60200\tBrno 2\tBrno\tBrno-Zábrdovice
61500\tBrno 15\tBrno\tBrno-Zábrdovice
64100\tBrno 41\tBrno\tBrno-Žebětín
63500\tBrno 35\tBrno\tBystrc
66471\tVeverská Bítýška\tBrno\tBystrc
61300\tBrno 13\tBrno\tČerná Pole (Brno-Královo Pole)
60200\tBrno 2\tBrno\tČerná Pole (Brno-sever)
61300\tBrno 13\tBrno\tČerná Pole (Brno-sever)
61400\tBrno 14\tBrno\tČerná Pole (Brno-sever)
60200\tBrno 2\tBrno\tČerná Pole (Brno-střed)
61800\tBrno 18\tBrno\tČernovice
62700\tBrno 27\tBrno\tČernovice
62000\tBrno 20\tBrno\tChrlice
64300\tBrno 43\tBrno\tChrlice
66442\tModřice\tBrno\tChrlice
61700\tBrno 17\tBrno\tDolní Heršpice
61900\tBrno 19\tBrno\tDolní Heršpice
62000\tBrno 20\tBrno\tDvorska
62000\tBrno 20\tBrno\tHolásky
61700\tBrno 17\tBrno\tHorní Heršpice
61900\tBrno 19\tBrno\tHorní Heršpice
61300\tBrno 13\tBrno\tHusovice
61400\tBrno 14\tBrno\tHusovice
63800\tBrno 38\tBrno\tHusovice
62100\tBrno 21\tBrno\tIvanovice
62100\tBrno 21\tBrno\tJehnice
63700\tBrno 37\tBrno\tJundrov (Brno-Jundrov)
66434\tKuřim\tBrno\tKníničky
63500\tBrno 35\tBrno\tKníničky
62300\tBrno 23\tBrno\tKohoutovice
60200\tBrno 2\tBrno\tKomárov
61700\tBrno 17\tBrno\tKomárov
61800\tBrno 18\tBrno\tKomárov
61600\tBrno 16\tBrno\tKomín
62400\tBrno 24\tBrno\tKomín
63500\tBrno 35\tBrno\tKomín
61200\tBrno 12\tBrno\tKrálovo Pole
61600\tBrno 16\tBrno\tKrálovo Pole
61200\tBrno 12\tBrno\tLesná
61400\tBrno 14\tBrno\tLesná
63800\tBrno 38\tBrno\tLesná
62800\tBrno 28\tBrno\tLíšeň
63600\tBrno 36\tBrno\tLíšeň
61400\tBrno 14\tBrno\tMaloměřice (Brno-Maloměřice a Obřany)
61200\tBrno 12\tBrno\tMedlánky
62100\tBrno 21\tBrno\tMedlánky
62100\tBrno 21\tBrno\tMokrá Hora
63400\tBrno 34\tBrno\tNový Lískovec
61400\tBrno 14\tBrno\tObřany
64400\tBrno 44\tBrno\tObřany
62100\tBrno 21\tBrno\tOřešín
60300\tBrno 3\tBrno\tPisárky (Brno-Jundrov)
63700\tBrno 37\tBrno\tPisárky (Brno-Jundrov)
60300\tBrno 3\tBrno\tPisárky (Brno-Kohoutovice)
62300\tBrno 23\tBrno\tPisárky (Brno-Kohoutovice)
63400\tBrno 34\tBrno\tPisárky (Brno-Kohoutovice)
60200\tBrno 2\tBrno\tPisárky (Brno-střed)
60300\tBrno 3\tBrno\tPisárky (Brno-střed)
63400\tBrno 34\tBrno\tPisárky (Brno-střed)
63900\tBrno 39\tBrno\tPisárky (Brno-střed)
64700\tBrno 47\tBrno\tPisárky (Brno-střed)
60200\tBrno 2\tBrno\tPonava
61200\tBrno 12\tBrno\tPonava
61900\tBrno 19\tBrno\tPřízřenice
61200\tBrno 12\tBrno\tŘečkovice
62100\tBrno 21\tBrno\tŘečkovice
61200\tBrno 12\tBrno\tSadová
62700\tBrno 27\tBrno\tSlatina
64400\tBrno 44\tBrno\tSoběšice
60200\tBrno 2\tBrno\tStaré Brno
60300\tBrno 3\tBrno\tStaré Brno
63900\tBrno 39\tBrno\tStaré Brno
62500\tBrno 25\tBrno\tStarý Lískovec
60200\tBrno 2\tBrno\tStránice
61600\tBrno 16\tBrno\tStránice
61900\tBrno 19\tBrno\tŠtýřice
63900\tBrno 39\tBrno\tŠtýřice
60200\tBrno 2\tBrno\tTrnitá (Brno-jih)
61700\tBrno 17\tBrno\tTrnitá (Brno-jih)
61800\tBrno 18\tBrno\tTrnitá (Brno-jih)
60200\tBrno 2\tBrno\tTrnitá (Brno-střed)
61700\tBrno 17\tBrno\tTrnitá (Brno-střed)
62000\tBrno 20\tBrno\tTuřany
62700\tBrno 27\tBrno\tTuřany
64400\tBrno 44\tBrno\tÚtěchov
60200\tBrno 2\tBrno\tVeveří
61600\tBrno 16\tBrno\tVeveří
60200\tBrno 2\tBrno\tŽabovřesky
61200\tBrno 12\tBrno\tŽabovřesky
61600\tBrno 16\tBrno\tŽabovřesky
63700\tBrno 37\tBrno\tŽabovřesky
60200\tBrno 2\tBrno\tZábrdovice (Brno-sever)
61300\tBrno 13\tBrno\tZábrdovice (Brno-sever)
61400\tBrno 14\tBrno\tZábrdovice (Brno-sever)
60200\tBrno 2\tBrno\tZábrdovice (Brno-střed)
60200\tBrno 2\tBrno\tZábrdovice (Brno-Židenice)
61500\tBrno 15\tBrno\tZábrdovice (Brno-Židenice)
64100\tBrno 41\tBrno\tŽebětín
62800\tBrno 28\tBrno\tŽidenice (Brno-Vinohrady)
63600\tBrno 36\tBrno\tŽidenice (Brno-Vinohrady)
61500\tBrno 15\tBrno\tŽidenice (Brno-Židenice)
61800\tBrno 18\tBrno\tŽidenice (Brno-Židenice)
62800\tBrno 28\tBrno\tŽidenice (Brno-Židenice)
63600\tBrno 36\tBrno\tŽidenice (Brno-Židenice)"""

names_list = [
    "Ulrychský",
    "Čivanský",
    "Lopoch",
    "Filupný",
    "Krpenný",
    "Haluzka",
    "Holedný",
    "Pratický",
    "Kolinář",
    "Mlína",
    "Lípan",
    "Hlohovecký",
    "Hlohovec",
    "Lastovecký",
    "Trochař",
    "Frča",
    "Frýča",
    "Kalandrovský",
    "Troubela",
    "Dvorec",
    "Pahlný",
    "Polendovský",
    "Olbracht",
    "Pletichý",
    "Salovský",
    "Kunys",
    "Smíkela",
    "Smýkela",
    "Forota"
]

@dataclass
class Address:
    name: str
    street: str
    zip_code: str
    city: str
    district: str
    city_part: str
    phone_number: str
    email: str

class FakeBrnoAddress():
    credentials_path = 'credentials.json'
    sheet_url = "https://docs.google.com/spreadsheets/d/1fLbHDyXkSKqLYJJtTPLXIpGHftFxUAYF1dGp-lu7AU4"
    def __init__(self):
        # Split the TSV data into lines
        lines = tsv_data.split('\n')

        # Create a CSV reader object
        reader = csv.DictReader(lines, delimiter='\t', fieldnames=['zip_code', 'city_part', 'city', 'district'])

        # Convert the CSV reader object to a list of dictionaries
        self.brno_addresses = list(reader)

        # Create a Faker instance with Czech locale
        self.fake = Faker('cs_CZ')
    def address(self):
        # Randomly select an address from the dataset
        selected_address = random.choice(self.brno_addresses)

        name = self.fake.first_name_male()
        last_name = random.choice(names_list)
        # last_name = self.fake.last_name_male()
        # Generate the required fields
        address = Address(
            name=name + " " + last_name,
            street=self.fake.street_address(),
            zip_code=selected_address["zip_code"],
            city=selected_address["city"],
            district=selected_address["district"],
            city_part=selected_address["city_part"],
            phone_number='772' + str(random.randint(100000, 999999)),
            email=unidecode.unidecode(name).lower() + '.' + unidecode.unidecode(last_name).lower() + str(random.randint(100, 999)) + '@seznam.cz'
        )
        return address
    
    def sheet_address(self):
        # Connect to the sheet
        client = gspread.service_account(self.credentials_path)
        sheet = client.open_by_url(self.sheet_url)
        worksheet = sheet.worksheet('addresses')
        
        # Get all records
        records = worksheet.get_all_records()
        
        # Filter unused addresses
        unused_addresses = [record for record in records if not record['used']]
        
        # Check if there are any unused addresses
        if not unused_addresses:
            raise Exception("No unused addresses available in the sheet")
        
        # Select random unused address
        selected_address = random.choice(unused_addresses)
        
        # Create address object
        address = Address(
            name=selected_address["name"],
            street=selected_address["street"],
            zip_code=selected_address["zip_code"],
            city=selected_address["city"],
            city_part=selected_address["city"],
            district="Jihomoravsky Kraj",
            phone_number='+420' + str(selected_address["phone_number"]),
            email=selected_address["email"]
        )
        
        # Find the row index of the selected address (adding 2 because of header row and 0-based indexing)
        row_index = records.index(selected_address) + 2
        
        # Update the 'used' field to True
        worksheet.update_cell(row_index, worksheet.find('used').col, 'True')
        
        return address
    
if __name__ == "__main__":
    fake_address = FakeBrnoAddress()
    print(fake_address.address())
