# Moodfilms + Ruotanen Dispatch Agent v3

Tämä versio ottaa huomioon sen, että Moodfilms on Webnodessa eikä Moodfilmsin juureen voi vapaasti lisätä tiedostoja.

Siksi arkkitehtuuri on:

```text
Moodfilms.com
= kaupallinen Webnode-sivusto
= header-linkit dispatch-syötteeseen
= ei root-tiedostovaatimusta

ruotanen.com
= tekninen dispatch hub
= /dispatch/moodfilms/feed.xml
= /dispatch/moodfilms/updates.json
= /dispatch/moodfilms/index.json
= /dispatch/moodfilms/targets.json
= /dispatch/moodfilms/latest.md
```

## Voiko tämän laittaa GitHubiin?

Kyllä. Tämä on tehty niin, että se toimii kolmella tavalla:

### 1. Paikallisesti Macilla

Tuplaklikkaa:

```text
Run Dispatch Agent.command
```

Se kysyy uuden päivityksen tiedot ja tekee tiedostot.

### 2. GitHubissa ilman automaattista palvelinpäivitystä

Laita tämä kansio GitHub-repoon. GitHub Action löytyy:

```text
.github/workflows/dispatch.yml
```

GitHubissa voit ajaa workflow_dispatch-ajon ja täyttää lomakkeeseen:

```text
title
url
summary
tags
type
submit_indexnow
```

Action tekee artifactin:

```text
moodfilms-ruotanen-dispatch-output
```

Lataa artifact ja siirrä `upload-to-ruotanen/dispatch/moodfilms/` ruotanen.comiin.

Tämä on turvallinen GitHub-versio.

### 3. GitHubissa täysautomaattisesti FTP:llä

Mukana on myös malli:

```text
.github/workflows/dispatch-optional-ftp-deploy.yml.disabled
```

Se on tarkoituksella pois päältä, koska se vaatii FTP-tunnukset GitHub Secrets -kohtaan.

Jos haluat käyttää sitä:

1. Nimeä tiedosto:
   ```text
   dispatch-optional-ftp-deploy.yml.disabled
   ->
   dispatch-optional-ftp-deploy.yml
   ```

2. Lisää GitHub-repoon Secrets:
   ```text
   FTP_SERVER
   FTP_USERNAME
   FTP_PASSWORD
   ```

3. Korjaa workflowssa `server-dir` oikeaksi ruotanen.comin palvelinpoluksi.

Tämä voi tehdä lähes automaattisen putken:

```text
GitHub workflow form
→ dispatch files generated
→ IndexNow ping ruotanen.com dispatch URLs
→ upload-to-ruotanen deploy ruotanen.comiin
→ LinkedIn/GBP drafts artifactina
```

## Mitä lisätään Moodfilmsin Webnodeen?

Lisää kerran Webnoden headeriin tiedosto:

```text
webnode-header-snippets/moodfilms-global-header-extra.html
```

Se sisältää vain linkit ruotanen.comin dispatch-syötteeseen. Se ei vaadi Moodfilmsin juureen tiedostoja.

## Mitä ladataan ruotanen.comiin?

Lataa kansion sisältö:

```text
upload-to-ruotanen/
```

niin että julkiset URL:t ovat:

```text
https://ruotanen.com/dispatch/moodfilms/feed.xml
https://ruotanen.com/dispatch/moodfilms/updates.json
https://ruotanen.com/dispatch/moodfilms/index.json
https://ruotanen.com/dispatch/moodfilms/targets.json
https://ruotanen.com/dispatch/moodfilms/latest.md
```

## IndexNow

IndexNow lähetetään vain ruotanen.comin dispatch-URL:eille, koska Moodfilms/Webnode ei anna välttämättä lisätä IndexNow key -tiedostoa Moodfilmsin juureen.

Tämä on tietoinen ratkaisu eikä virhe.

## Manual-submit

Koska Moodfilmsin omia URL:eja ei voida siististi IndexNow-pingata ilman root key -tiedostoa, työkalu tekee:

```text
manual-submit/bing-submit-urls-moodfilms.txt
manual-submit/google-search-console-check-urls-moodfilms.txt
```

Näitä voi käyttää Bing Webmaster Toolsissa ja Google Search Consolessa.

## Drafts

Työkalu tekee luonnokset:

```text
drafts/linkedin-draft.md
drafts/google-business-profile-post.md
```

Näitä ei julkaista automaattisesti. Tämä on tarkoituksella, jotta sivuston ääni pysyy omana eikä muutu koneelliseksi.
