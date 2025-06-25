# Steve

A bot for the SBI discord server built with Pycord featuring meeting recording and other utilities.

## Installation

### Prerequisites
- Python 3.12
- uv (Python package and project manager)
- FFmpeg

### Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:Wavefire5201/sbi-discord-bot.git
   cd sbi-discord-bot
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Configure environment variables**

   Fill out `.env.example` file and rename to `.env`.

4. **Run the bot**
   ```bash
   uv run steve/main.py
   ```


## Commands

### Voice Recording
- `/join` - Start recording in your current voice channel
- `/stop` - Stop the current recording
- `/status` - Check current recording status

### AI Chat
- `/joke` - Get a random AI-generated joke
- `/chat <message>` - Chat with the AI

### General
- `/help` - Display help information


## Development

### Adding New Features
1. Create new cog files in `cogs/`
2. Add cog name to the `cogs` list in `main.py`
3. Use `from utils import get_logger` for consistent logging


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper error handling and logging
4. Test thoroughly
5. Submit a pull request
