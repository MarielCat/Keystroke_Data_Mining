# Présentation : partie « Résultats et limites »

**9 diapos (D1 à D9), environ 4 min 30.** La D3 est optionnelle : sans elle,
on est autour de 4 min.

Le but de cette partie : montrer **ce que le programme arrive à faire**, puis
**là où il coince**, sans retourner dans la technique (déjà expliquée avant).

- Les images sont dans [`Presentation_assets/img/`](Presentation_assets/img/).
  Elles viennent des vraies données (script `Presentation_assets/make_figures.py`).
- 📸 = **photo ou capture à faire par toi**, parce qu'il faut ton écran, ton nom
  ou un vrai essai en direct.

| Diapo | Message en une phrase | Image |
|---|---|---|
| D1 | Comment on a testé le programme | 📸 capture de l'appli |
| D2 | Plus on écrit, plus il a raison | `2_sur_10_essais.png` (ou `1_plus_on_ecrit.png`) |
| D3 *(optionnelle)* | Nos essais à nous, en direct | 📸 ton tableau d'essais |
| D4 | Limite : une personne inconnue reçoit quand même un nom | `3_personne_inconnue.png` |
| D5 | Limite : avec trop peu de texte, il y a une part de hasard | 📸 capture « Pas assez de texte » |
| D6 | Limite : deux personnes peuvent taper pareil | `4_confusions.png` |
| D7 | Limite : on n'est que 4 | `5_plus_de_monde.png` |
| D8 | Limite : on ne tape pas toujours pareil | aucune (ou 📸 deux claviers) |
| D9 | Conclusion | aucune |

---

## D1 : Comment on a testé

**Sur la diapo**
- Titre : *Le programme devine-t-il qui tape ?*
- 📸 Capture de l'appli avec le verdict « D'après l'entraînement, c'est Noé qui tape. »
- 2 puces :
  - On tape un texte, le programme dit qui c'est
  - On l'a testé des centaines de fois sur des phrases qu'il n'avait jamais vues

📸 **À faire** : lance `python app.py`, tape 2 ou 3 phrases, clique sur
*Qui tape ?*, puis capture la fenêtre avec Win + Maj + S.

**À dire (≈25 s)**
> Pour savoir si le programme marche vraiment, on a mis de côté une partie des
> phrases de chacun, que le programme n'a jamais vues pendant l'entraînement.
> Ensuite on lui a donné des morceaux de ces phrases, plus ou moins longs, et
> on lui a demandé à chaque fois : « qui a tapé ça ? ». On l'a fait des
> centaines de fois, et on a compté combien de fois il avait raison.

---

## D2 : Plus on écrit, plus il a raison

**Sur la diapo**
- Titre : *Plus on écrit, plus il a raison*
- Image : `img/2_sur_10_essais.png`. Si tu préfères des barres, prends
  `img/1_plus_on_ecrit.png` : c'est le même résultat.
- Rien d'autre, l'image parle toute seule.

**À dire (≈40 s)**
> Voilà le résultat principal. Avec un seul mot, le programme trouve la bonne
> personne environ 7 fois sur 10. Ça peut paraître peu, mais s'il répondait au
> hasard entre nous quatre, il n'aurait raison qu'une fois sur quatre. Avec
> quelques mots ou une phrase, on monte à 9 fois sur 10. Et à partir de deux
> phrases, il ne se trompe quasiment plus : 99 %, puis 100 % avec cinq
> phrases.
> Donc en gros : un mot, c'est un indice ; une phrase, c'est assez fiable ;
> deux phrases ou plus, c'est presque sûr.

**Si on te pose la question**
- *Ça dépend des gens ?* Oui. Avec un seul mot, Noé est reconnu 9 fois sur 10,
  Constance seulement 1 fois sur 2. Certains ont un rythme plus « marqué » que
  d'autres.
- *Combien de tests ?* 150 morceaux de texte par personne et par longueur, donc
  600 essais pour chaque barre.

---

## D3 : Nos essais en direct *(optionnelle)*

**Sur la diapo**
- Titre : *Et quand on essaie nous-mêmes ?*
- 📸 Ton tableau de résultats (modèle ci-dessous), ou une capture par longueur.

📸 **À faire** : 10 essais pour chaque longueur, en notant si le nom affiché est le bon.
- Pour tester **un seul mot**, lance `python app.py --min-keys 3`. Sans cette
  option, l'appli refuse les textes de moins de 20 frappes.
- Pour une phrase ou plus, `python app.py` suffit.
- Clique sur *Effacer* entre deux essais. Si tu peux, fais aussi taper les
  autres membres du groupe.

| Qui tape | Longueur | Essais réussis sur 10 |
|---|---|---|
| Noé | 1 mot | … /10 |
| Noé | 1 phrase | … /10 |
| Noé | 2-3 phrases | … /10 |
| (autre membre) | 1 mot | … /10 |
| (autre membre) | 1 phrase | … /10 |
| (autre membre) | 2-3 phrases | … /10 |

Envoie-moi tes résultats et je t'en fais un graphique propre.

**À dire (≈30 s)** *(à adapter à tes chiffres)*
> On a aussi essayé nous-mêmes, en direct sur l'application. Avec un seul mot,
> j'ai été reconnu … fois sur 10 ; avec une phrase, … fois ; avec deux ou trois
> phrases, … fois. On retrouve la même tendance : plus on écrit, plus il est sûr.

---

## D4 : Limite 1 : il ne connaît que nous quatre

**Sur la diapo**
- Titre : *Quelqu'un d'inconnu ? Il donne quand même un nom*
- Image : `img/3_personne_inconnue.png`
- 📸 Bonus : capture de l'appli quand un ami qui n'est pas dans les données
  tape sur ton ordi. Il recevra quand même un nom.

**À dire (≈35 s)**
> Première limite, et c'est la plus importante. Le programme ne connaît que
> les quatre personnes sur lesquelles il a été entraîné, et il ne sait pas
> dire « je ne connais pas cette personne ». Il choisit toujours le nom le
> plus proche.
> Pour le montrer, on a retiré une personne de l'entraînement et on l'a fait
> taper. Par exemple, quand le programme ne connaît pas Noé et que Noé tape,
> il répond « Fatima » 97 % du temps. Il se trompe, mais il est très sûr de
> lui. Donc si quelqu'un d'extérieur prend le clavier, le programme ne le
> remarquera pas : il lui donnera juste le nom de la personne qui tape le plus
> comme lui.

---

## D5 : Limite 2 : trop peu de texte = une part de hasard

**Sur la diapo**
- Titre : *Avec un mot, il y a une part de chance*
- 📸 Capture de l'appli après avoir tapé un seul mot (avec `python app.py`
  normal) : elle affiche « Pas assez de texte ».
- 2 puces :
  - 1 mot : faux 3 fois sur 10
  - Sous 20 frappes, l'appli préfère ne pas répondre

**À dire (≈25 s)**
> Deuxième limite : avec très peu de texte, il y a une part de hasard. Un mot,
> c'est cinq ou six touches : le programme a très peu d'informations pour
> comparer, donc il se trompe environ trois fois sur dix. C'est pour ça que
> l'application refuse de répondre en dessous de 20 frappes, et qu'il vaut
> mieux taper au moins une ou deux phrases avant de lui faire confiance.

---

## D6 : Limite 3 : deux personnes peuvent taper pareil

**Sur la diapo**
- Titre : *Deux personnes peuvent avoir un rythme proche*
- Image : `img/4_confusions.png`

**À dire (≈30 s)**
> Troisième limite : par hasard, deux personnes peuvent avoir une façon de
> taper assez proche. Avec une phrase, le programme se trompe dans 6 % des
> cas, et ce ne sont pas des erreurs au hasard : c'est surtout Mariel qui
> est confondue avec Constance ou avec Fatima. Noé, au contraire, n'est
> presque jamais confondu. Plus il y a de gens, plus il y a de chances que
> deux personnes tapent de la même manière.

---

## D7 : Limite 4 : on n'est que 4

**Sur la diapo**
- Titre : *4 personnes, c'est facile. 30, beaucoup moins*
- Image : `img/5_plus_de_monde.png`

**À dire (≈25 s)**
> Ce qui nous amène à la quatrième limite : on n'est que quatre. On a testé
> ce qui se passe quand on ajoute des gens : avec deux personnes, le
> programme se trompe 2 % du temps ; avec trois, 4 % ; avec quatre, 5 %.
> Chaque nouvelle personne rend la tâche plus dure. Avec toute la classe,
> les erreurs seraient forcément plus fréquentes, et nos bons résultats
> sont donc un peu trop optimistes.

---

## D8 : Limite 5 : on ne tape pas toujours pareil

**Sur la diapo**
- Titre : *On ne tape pas toujours de la même façon*
- 4 puces courtes (une icône par puce si tu veux) :
  - 😴 la fatigue, le jour, l'humeur
  - ⌨️ un autre clavier (chacun a enregistré sur son ordi)
  - 🇬🇧 que de l'anglais pendant l'entraînement
  - 📝 recopier une phrase ≠ écrire librement
- 📸 Optionnel : une photo de deux claviers différents (ton ordi et un clavier externe).

**À dire (≈30 s)**
> Dernière limite : notre façon de taper n'est pas fixe. Un jour où on est
> fatigué, on ne tape pas pareil. Une personne qui a tapé sur plusieurs jours
> est toujours reconnue, mais le programme est moins sûr de lui les autres
> jours. Ensuite, chacun a enregistré ses données sur son propre ordinateur :
> une partie de ce que le programme reconnaît, c'est peut-être le clavier
> plutôt que la personne. Enfin, on s'est entraînés en anglais, donc si on
> tape en français, il sera moins fiable.

⚠️ **À vérifier par toi** : est-ce que chacun a bien enregistré sur son propre
ordinateur ? C'est très probable d'après les fichiers, mais c'est toi qui le
sais. Sinon, retire la puce clavier.

---

## D9 : Conclusion

**Sur la diapo**
- Titre : *Ce qu'il faut retenir*
- 3 puces :
  - ✅ Notre façon de taper suffit à nous reconnaître : 2 phrases ≈ 99 % de réussite
  - ⚠️ Mais seulement parmi 4 personnes connues, et le rythme varie
  - ➡️ La suite : plus de monde, plusieurs jours, et savoir dire « inconnu »

**À dire (≈20 s)**
> Pour résumer : oui, notre façon de taper suffit à nous reconnaître. Avec deux
> phrases, le programme ne se trompe presque jamais. Mais ça marche parmi
> quatre personnes qu'il connaît, et notre rythme change selon le jour ou le
> clavier. Pour aller plus loin, il faudrait plus de participants, des
> enregistrements sur plusieurs jours, et surtout un programme capable de dire
> « je ne connais pas cette personne ». Merci !

---

## Tous les chiffres (pour les questions)

| Longueur de texte | Bonne personne trouvée | Détail par personne |
|---|---|---|
| 1 mot (~6 touches) | 72 % (≈ 7/10) | Constance 54 %, Fatima 73 %, Mariel 73 %, Noé 90 % |
| 3-4 mots (~20 touches) | 87 % (≈ 9/10) | Constance 67 %, Fatima 89 %, Mariel 94 %, Noé 99 % |
| 1 phrase (~50 touches) | 94 % (≈ 9/10) | Constance 86 %, Fatima 97 %, Mariel 92 %, Noé 100 % |
| 2 phrases (~100 touches) | 99 % (10/10) | Constance 99 %, Fatima 100 %, Mariel 97 %, Noé 100 % |
| 5 phrases (~250 touches) | 100 % (10/10) | tout le monde à 100 % |

- Hasard pur : 25 % (1 chance sur 4).
- Personne inconnue (retirée de l'entraînement, 2 phrases tapées) :
  Noé → « Fatima » 97 % ; Constance → « Mariel » 78 % ;
  Fatima → « Noé » 54 % / « Mariel » 46 % ; Mariel → « Constance » 51 % / « Fatima » 47 %.
- Erreurs avec une phrase selon le nombre de personnes : 2 % (2 pers.), 4 % (3), 5 % (4).
- Comment on a testé : pour chaque personne, le dernier tiers de ses phrases
  libres a été mis de côté (jamais vu à l'entraînement). On en a tiré
  150 morceaux au hasard par personne et par longueur.
