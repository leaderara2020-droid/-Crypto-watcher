name: Rapport Crypto Automatique

on:
  schedule:
    - cron: "0 */3 * * *"
  workflow_dispatch: {}

jobs:
  rapport:
    runs-on: ubuntu-latest
    steps:
      - name: Récupérer le code
        uses: actions/checkout@v4

      - name: Installer Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Installer les dépendances
        run: pip install requests

      - name: Exécuter le script
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python crypto_watcher.py
