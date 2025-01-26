# n0va Stuff

## Overview
Welcome to the n0va project! This repository contains the selfbot, our actual bot, and a Python EXE builder. Below you will find details on each component.

## Components

### 1. Selfbot
The selfbot is designed to automate tasks on Discord using your user account. It allows for various functionalities such as status updates, message management, and more.

#### Features:
- Custom status messages
- AFK system with notifications
- Message deletion timer
- Mimicking other users

#### Usage:
To run the selfbot, ensure you have the required dependencies installed. Use the following command to install them:
```bash
pip install -r requirements.txt
```

Then, run the selfbot with:
```bash
python selfbot.py
```

### 2. Actual Bot
The actual bot is built to provide various functionalities on Discord servers. It is designed to be user-friendly and efficient.

#### Features:
- Command handling
- Event listeners
- Integration with external APIs

#### Usage:
To run the actual bot, follow the same installation steps as the selfbot. Ensure you have the bot token configured in your `config.json` file.

### 3. Python EXE Builder
The Python EXE builder allows you to convert your Python scripts into standalone executable files. This is useful for distributing your applications without requiring users to have Python installed.

#### Usage:
To build an executable, navigate to the directory containing your script and run:
```bash
python build.py < NOTE YOU DO HAVE TO CHANGED FILE TYPE THIS MAKES THE SELF BOT, AND YOU HAVE TO INCLUDE A ICON.ICO FILE
```
Replace `selfbot.py` with the name of your Python file. The executable will be created in the `dist` folder.

## Contributing
We welcome contributions to the n0va project! If you have suggestions or improvements, please feel free to submit a pull request.

## License
This project is licensed under the n0va License - see the [LICENSE](LICENSE) file for details.

## Contact
For any inquiries, please reach out to the project maintainers.
Or - support@n0va.earth(one)
