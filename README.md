# Currency exchange rates bot

Currency exchange rates bot is a Python telegram bot for showing exchange rates.
The bot sends a request to third-party service API by user's command and respectively shows the information.
Supports exchange rates graph history in the chat.
Every request is saved in the local database.
If it's been less than 10 minutes before the last request was made, the information from the database is loaded.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirements.

```bash
pip install requirements.txt
```

## Usage

```python
TOKEN = "1234567890:AbcdEFghIJklMNopqRStuVwxYZ" # insert your own token, generated with BotFather, and just launch the application with python3
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)