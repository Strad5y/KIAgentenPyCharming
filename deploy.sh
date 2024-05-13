#!/bin/bash
cd /home/jonne/Programme/KIAgentenPyCharming
git pull origin main
# Falls du einen virtuellen Python-Umgebung verwendest und Abh�ngigkeiten aktualisieren m�chtest:
# source venv/bin/activate
# pip install -r requirements.txt
# Deaktiviere die virtuelle Umgebung nach Bedarf
# deactivate

# Deinen Server neu starten, z.B. mit systemd
sudo systemctl restart backend.service
