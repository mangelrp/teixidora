# teixidora

Scripts para el proyecto Teixidora.

## Instalación

Suponemos que nos encontramos en un sistema GNU/Linux, preferiblemente Ubuntu.

* Instalar dependencias: `sudo apt-get install virtualenv python-pip python3`
* Crear un entorno separado: `virtualenv -p python3 bot-teixidora`
* Entrar en el entorno: `cd bot-teixidora; source bin/activate`
* Instalar pywikibot: `git clone --recursive https://gerrit.wikimedia.org/r/pywikibot/core.git`
* Instalar requests: `pip install requests`
* Modificar los datos del fichero `user-config.py` si es necesario.
* Copiar el fichero `user-config.py` al directorio `core`. Bien con `cp` si está en local o con `scp` si es en remoto.
* Copiar el fichero `teixidora_family.py` al directorio `core/pywikibot/families`.
* Copiar el fichero `pad2semwiki.py` al directorio `core`.
* Copiar el fichero `agendas.py` al directorio `core`.

Después de esto, ya se pueden ejecutar los scripts `pad2semwiki.py` y `agendas.py`, tanto manualmente, como si se prefiere periódicamente con cron.

Esas podrían ser unas tareas de ejemplo para cron:

`*/10 *  * * *   cd bot-teixidora && . bin/activate && cd core && python pad2semwiki.py && cd .. && cd ..`

`*/15 *  * * *   cd bot-teixidora && . bin/activate && cd core && python agendas.py && cd .. && cd ..`
