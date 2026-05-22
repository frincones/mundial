"""
Star players por selección — los delanteros principales que históricamente marcan goles.
Se usa en el simulador Monte Carlo para predecir el máximo goleador (Bota de Oro).

Cada jugador tiene un "goal share" — porcentaje de los goles de su selección que
típicamente anota. La suma por equipo ronda 0.7-0.85 (el resto son mediocampistas/defensores).
"""

# (player_name, position, goal_share) — los top 3 anotadores típicos por equipo
STAR_PLAYERS = {
    "ARG": [("Lionel Messi", "FWD", 0.45), ("Lautaro Martínez", "FWD", 0.30), ("Julián Álvarez", "FWD", 0.25)],
    "ESP": [("Lamine Yamal", "FWD", 0.32), ("Álvaro Morata", "FWD", 0.28), ("Nico Williams", "FWD", 0.24), ("Mikel Oyarzabal", "FWD", 0.16)],
    "FRA": [("Kylian Mbappé", "FWD", 0.48), ("Ousmane Dembélé", "FWD", 0.22), ("Bradley Barcola", "FWD", 0.18), ("Marcus Thuram", "FWD", 0.12)],
    "BRA": [("Vinícius Júnior", "FWD", 0.30), ("Raphinha", "FWD", 0.26), ("Estêvão", "FWD", 0.22), ("Matheus Cunha", "FWD", 0.18)],
    "ENG": [("Harry Kane", "FWD", 0.40), ("Bukayo Saka", "FWD", 0.22), ("Phil Foden", "MID", 0.18), ("Jude Bellingham", "MID", 0.14)],
    "POR": [("Cristiano Ronaldo", "FWD", 0.38), ("João Félix", "FWD", 0.22), ("Bruno Fernandes", "MID", 0.20), ("Rafael Leão", "FWD", 0.15)],
    "GER": [("Florian Wirtz", "MID", 0.28), ("Kai Havertz", "FWD", 0.26), ("Niclas Füllkrug", "FWD", 0.22), ("Jamal Musiala", "MID", 0.20)],
    "NED": [("Memphis Depay", "FWD", 0.32), ("Cody Gakpo", "FWD", 0.26), ("Donyell Malen", "FWD", 0.22), ("Xavi Simons", "MID", 0.14)],
    "BEL": [("Romelu Lukaku", "FWD", 0.42), ("Kevin De Bruyne", "MID", 0.20), ("Jérémy Doku", "FWD", 0.20), ("Leandro Trossard", "FWD", 0.15)],
    "CRO": [("Andrej Kramarić", "FWD", 0.32), ("Ante Budimir", "FWD", 0.26), ("Mateo Kovačić", "MID", 0.18), ("Petar Sučić", "MID", 0.16)],
    "URU": [("Darwin Núñez", "FWD", 0.36), ("Federico Valverde", "MID", 0.22), ("Maximiliano Araújo", "FWD", 0.20), ("Facundo Pellistri", "FWD", 0.16)],
    "COL": [("Luis Díaz", "FWD", 0.34), ("James Rodríguez", "MID", 0.26), ("Jhon Durán", "FWD", 0.22), ("Jhon Córdoba", "FWD", 0.16)],
    "MEX": [("Raúl Jiménez", "FWD", 0.34), ("Hirving Lozano", "FWD", 0.24), ("Santiago Giménez", "FWD", 0.24), ("Edson Álvarez", "MID", 0.14)],
    "USA": [("Christian Pulisic", "FWD", 0.36), ("Folarin Balogun", "FWD", 0.24), ("Ricardo Pepi", "FWD", 0.20), ("Giovanni Reyna", "MID", 0.16)],
    "CAN": [("Jonathan David", "FWD", 0.38), ("Alphonso Davies", "MID", 0.24), ("Cyle Larin", "FWD", 0.22), ("Tajon Buchanan", "FWD", 0.14)],
    "MAR": [("Achraf Hakimi", "DEF", 0.20), ("Hakim Ziyech", "MID", 0.26), ("Brahim Díaz", "MID", 0.24), ("Youssef En-Nesyri", "FWD", 0.26)],
    "JPN": [("Takefusa Kubo", "MID", 0.26), ("Daichi Kamada", "MID", 0.22), ("Daizen Maeda", "FWD", 0.22), ("Ayase Ueda", "FWD", 0.20)],
    "KOR": [("Son Heung-min", "FWD", 0.40), ("Lee Kang-in", "MID", 0.22), ("Hwang Hee-chan", "FWD", 0.20), ("Cho Gue-sung", "FWD", 0.14)],
    "AUS": [("Mitchell Duke", "FWD", 0.30), ("Mathew Leckie", "FWD", 0.26), ("Sam Kuol", "FWD", 0.20), ("Riley McGree", "MID", 0.16)],
    "SUI": [("Granit Xhaka", "MID", 0.22), ("Breel Embolo", "FWD", 0.28), ("Dan Ndoye", "FWD", 0.22), ("Zeki Amdouni", "FWD", 0.18)],
    "TUR": [("Arda Güler", "MID", 0.28), ("Kerem Aktürkoğlu", "FWD", 0.24), ("Hakan Çalhanoğlu", "MID", 0.22), ("Cenk Tosun", "FWD", 0.16)],
    "AUT": [("Marcel Sabitzer", "MID", 0.28), ("Marko Arnautović", "FWD", 0.26), ("Christoph Baumgartner", "MID", 0.20), ("Michael Gregoritsch", "FWD", 0.16)],
    "NOR": [("Erling Haaland", "FWD", 0.55), ("Martin Ødegaard", "MID", 0.22), ("Alexander Sørloth", "FWD", 0.15), ("Antonio Nusa", "FWD", 0.08)],
    "ECU": [("Enner Valencia", "FWD", 0.34), ("Moisés Caicedo", "MID", 0.20), ("Pervis Estupiñán", "DEF", 0.16), ("Kevin Rodríguez", "FWD", 0.20)],
    "SEN": [("Sadio Mané", "FWD", 0.32), ("Ismaïla Sarr", "FWD", 0.24), ("Boulaye Dia", "FWD", 0.22), ("Nicolas Jackson", "FWD", 0.18)],
    "CIV": [("Sébastien Haller", "FWD", 0.30), ("Simon Adingra", "FWD", 0.24), ("Nicolas Pépé", "FWD", 0.22), ("Franck Kessié", "MID", 0.16)],
    "EGY": [("Mohamed Salah", "FWD", 0.50), ("Omar Marmoush", "FWD", 0.22), ("Mostafa Mohamed", "FWD", 0.16), ("Trezeguet", "FWD", 0.10)],
    "IRN": [("Mehdi Taremi", "FWD", 0.36), ("Sardar Azmoun", "FWD", 0.28), ("Mehdi Ghayedi", "FWD", 0.18), ("Saman Ghoddos", "MID", 0.14)],
    "ALG": [("Riyad Mahrez", "FWD", 0.34), ("Islam Slimani", "FWD", 0.22), ("Saïd Benrahma", "FWD", 0.22), ("Amine Gouiri", "FWD", 0.16)],
    "TUN": [("Wahbi Khazri", "MID", 0.24), ("Hannibal Mejbri", "MID", 0.22), ("Naïm Sliti", "MID", 0.20), ("Issam Jebali", "FWD", 0.20)],
    "PAR": [("Antonio Sanabria", "FWD", 0.30), ("Miguel Almirón", "MID", 0.26), ("Julio Enciso", "MID", 0.22), ("Diego Gómez", "MID", 0.16)],
    "SCO": [("Scott McTominay", "MID", 0.32), ("Che Adams", "FWD", 0.24), ("John McGinn", "MID", 0.22), ("Lyndon Dykes", "FWD", 0.16)],
    "RSA": [("Lyle Foster", "FWD", 0.28), ("Themba Zwane", "MID", 0.22), ("Percy Tau", "FWD", 0.22), ("Lebo Mothiba", "FWD", 0.18)],
    "CZE": [("Patrik Schick", "FWD", 0.34), ("Mojmír Chytil", "FWD", 0.22), ("Tomáš Souček", "MID", 0.20), ("Lukáš Provod", "MID", 0.16)],
    "BIH": [("Edin Džeko", "FWD", 0.40), ("Ermedin Demirović", "FWD", 0.24), ("Miralem Pjanić", "MID", 0.18), ("Smail Prevljak", "FWD", 0.12)],
    "QAT": [("Akram Afif", "MID", 0.32), ("Almoez Ali", "FWD", 0.28), ("Hassan Al-Haydos", "MID", 0.20), ("Mohammed Muntari", "FWD", 0.14)],
    "HAI": [("Duckens Nazon", "FWD", 0.30), ("Frantzdy Pierrot", "FWD", 0.26), ("Carnejy Antoine", "FWD", 0.20), ("Derrick Etienne", "MID", 0.16)],
    "CUW": [("Leandro Bacuna", "MID", 0.26), ("Juriën Gaari", "MID", 0.22), ("Tahith Chong", "MID", 0.20), ("Brandley Kuwas", "FWD", 0.20)],
    "GHA": [("Mohammed Kudus", "MID", 0.32), ("Inaki Williams", "FWD", 0.26), ("Antoine Semenyo", "FWD", 0.20), ("Jordan Ayew", "FWD", 0.16)],
    "JOR": [("Yazan Al-Naimat", "FWD", 0.30), ("Musa Al-Taamari", "FWD", 0.26), ("Mahmoud Al-Mardi", "MID", 0.18), ("Ali Olwan", "FWD", 0.18)],
    "PAN": [("Cesar Yanis", "FWD", 0.28), ("Ismael Diaz", "FWD", 0.26), ("Ivan Anderson", "MID", 0.20), ("Anibal Godoy", "MID", 0.18)],
    "COD": [("Cédric Bakambu", "FWD", 0.32), ("Yoane Wissa", "FWD", 0.26), ("Fiston Mayele", "FWD", 0.20), ("Théo Bongonda", "FWD", 0.14)],
    "KSA": [("Salem Al-Dawsari", "FWD", 0.32), ("Saleh Al-Shehri", "FWD", 0.26), ("Firas Al-Buraikan", "FWD", 0.22), ("Abdullah Al-Hamdan", "FWD", 0.14)],
    "UZB": [("Eldor Shomurodov", "FWD", 0.36), ("Khojimat Erkinov", "MID", 0.22), ("Igor Sergeev", "FWD", 0.22), ("Jasurbek Yakhshiboev", "FWD", 0.14)],
    "IRQ": [("Aymen Hussein", "FWD", 0.32), ("Mohanad Ali", "FWD", 0.28), ("Ali Al-Hamadi", "FWD", 0.22), ("Bashar Resan", "MID", 0.14)],
    "NZL": [("Chris Wood", "FWD", 0.42), ("Liberato Cacace", "DEF", 0.16), ("Marko Stamenić", "MID", 0.20), ("Kosta Barbarouses", "FWD", 0.16)],
    "SWE": [("Alexander Isak", "FWD", 0.36), ("Viktor Gyökeres", "FWD", 0.32), ("Anthony Elanga", "FWD", 0.18), ("Dejan Kulusevski", "MID", 0.14)],
    "CPV": [("Garry Rodrigues", "FWD", 0.30), ("Ryan Mendes", "FWD", 0.26), ("Bebé", "FWD", 0.22), ("Stopira", "DEF", 0.14)],
}
