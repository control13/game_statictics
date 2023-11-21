# SPL Game Statistics

Das ist Repo, welches verschiedene Scripte beinhaltet für die Spielanalyse von [SPL](https://spl.robocup.org/) Spielen. Einige Scripte sind im Zusammenhang mit den Aufgaben aus dem ersten [Hackathon](https://github.com/SchulteDavid/nao_hackathon) der [HTWK-Robots](https://robots.htwk-leipzig.de/startseite).

Aktuelle Input-Source sind die Logs des [TeamCommunicationMonitors](https://github.com/RoboCup-SPL/GameController) (TCM). Die Packages dafür finden sich nur in dem alten Repo. Das neue Repo des [GameControllers](https://github.com/RoboCup-SPL/GameController3) hat dem TCM-Log nicht.

Die Daten liegen aktuell als Binary vor und können [hier](https://spl.robocup.org/downloads/) oder [hier](https://github.com/bhuman/SPLGames) gezogen werden. Mit `java -jar LogExporter.jar <log>` (im `bin` Ordner des TCM-Repos) können die Logs in ein lesbares Format exportiert werden. Der Logexporter exportiert aktuell nicht alle nötigen Daten. Die gepatchte Version ist aber noch nicht gepusht.

Ziel ist es in Zukunft, [diese](https://github.com/bhuman/VideoAnalysis) GroundTruth-Daten zu verwenden.

## tcmViewer

Ein Programm, um die Log-Daten einer Halbzeit zu visualisieren. Aktuelle Baustellen:
- Commandline-Flag für das Austauschen der Seiten
- Farben der Spieler von Teamnummer abhängig machen (Farbkollisionen beachten) (zuordnung der Farben und Teamnamen zur Teamnummer gibt es [hier](https://github.com/RoboCup-SPL/GameController3/blob/master/config/teams.yaml))
- Legende (Welche Farbe ist welches Team)
- Programm geht bei CTRL-C nicht kaputt
- Ball visualisieren
  - globaler Ball:
    - etwas komplizierter, weil von jedem Roboter eine Ballsichtung eingeht, die auch noch ein Alter hat
    - die Extremen müssen ausgeschlossen werden und dann ein Mittel aus alle Beobachtungen pro Zeitpunkt gebildet werden
    - evtl. bietet es sich an, über die Zeitpunkte hinweg zu glätten
  - lokale Bälle:
    - für jeden Roboter anzeigen (Punkt mit Strich verbunden), was jeder Roboter denkt
- was unter "HeatMap + Spielerpfad" gemacht werden soll, könnte auch hier mit angezeigt werden, z. B. durch mit der Maus über den Spieler hovert
- visualisieren des States der Roboter ("SET", "READY", ...), Markierung von Robotern, die hingefallen sind
- Roboter die Penalized sind, am "Rand" des Feldes darstellen

### Libs

Alles, was hier entwickelt wird, könnte auch in Libraries untergebracht werden, damit man für künftige Analysen auf fertige Funktionen zurückgreifen kann.

## HeatMap + Spielerpfad

Für jeden Roboter oder den Ball in einer Heatmap zeigen, wie häufig er an einer Stelle war. Dafür kann das Feld in 50cm x 50cm (?) große Felder unterteilt werden. Zusätzlich kann der Laufpfad des Roboters/Balls in einer anderen Farbe eingezeichnet werden.

## [Abseits](https://de.wikipedia.org/wiki/Abseitsregel#Fu%C3%9Fball)

In der SPL gibt es derzeit keine Abseitsregel. Abseits ist generell schwierig zu Pfeifen, da sowohl der Ball als auch der mehrere Spieler vom Schiedsrichter im Blick behalten werden müssen. Mit den geparsten Daten soll überprüft werden, wie oft das Abseits vorliegt.
Im [Beispiel](https://www.youtube.com/live/VAHpvp0eZ4g?si=ox62htX6w8KTVQbD&t=26154) schießt das rote Team (BHuman) nach einem aktiven Abseits ein Tor gegen des blauen Teams (HTWK).

Da es unter den [Fifa-Regeln (S. 36, S.112ff.)](https://digitalhub.fifa.com/m/364bb41574401d23/original/aopbnhwz4xqtknlqlasr-pdf.pdf) beim Abseits eine Rolle spielt, wer zuletzt den Ball gespielt hat und ob der Spieler aktiv oder passiv ins Spielgeschehen eingreift, ist es schwierig, die Abseitsregel 1:1 auf die SPL zu übertragen. Daher werden folgende Vereinfachungen vorgenommen:
- es gibt keine passiven Abseitsstellungen
- es wird ignoriert, ob der Ball zuletzt von einem Spieler des verteidigenden Teams gespielt wurde oder von Angreifer kommt (dafür müsste festgelegt werden, was es bedeutet, wenn ein Spieler den Ball spielt)
- die x-Koordinate wird für die Höhe verwendet
- es wird (vorerst) als Abseits gewertet, auch wenn der Roboter das Abseits betritt, nachdem der Ball gespielt wurde


## GameController Statistik

Hier werden nicht die TCM-Daten verwendet, sondern die GameController-Logs, also wann welches Event auf dem Feld stattfand, wie z. B. FOUL, FALLEN ROBOT oder GOAL.

Einfache Fragestellungen können sein:
- verliert ein Team, welches häufiger hinfällt?
- gewinnen aggressivere Teams (PUSHING/FOUL) häufiger oder seltener?
