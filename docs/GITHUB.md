# GitHub-käyttö lyhyesti

## Turvallisin automaatio

1. Luo uusi GitHub-repo, esimerkiksi:
   `moodfilms-ruotanen-dispatch-agent`

2. Lisää tämän paketin sisältö repoon.

3. GitHubissa:
   Actions → Dispatch Agent → Run workflow

4. Täytä:
   - title
   - url
   - summary
   - tags
   - submit_indexnow = true

5. Lataa workflow-artifact:
   `moodfilms-ruotanen-dispatch-output`

6. Lataa `upload-to-ruotanen/dispatch/moodfilms/` ruotanen.comiin.

## Täysautomaattinen deploy

On mahdollista, mutta vaatii FTP/SFTP-salaisuudet GitHubiin.

Suosittelen ensin turvallista mallia:
GitHub tekee tiedostot ja pingauksen, sinä lataat outputin palvelimelle.

Kun tämä toimii, automatisoidaan myös FTP.
