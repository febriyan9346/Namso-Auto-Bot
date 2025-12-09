# Namso Auto Bot

An automated bot for Namso Network that handles authentication, farming, monitoring, and daily check-ins with proxy support.

## Features

- 🔐 **Auto Authentication** - Automatic dashboard and extension login with OTP support
- 🌾 **Auto Farming** - Continuous farming with health checks and task submissions
- 🔄 **Token Refresh** - Automatic token refresh when expired (401 errors)
- 📊 **Real-time Monitoring** - Live stats display (SHARES, Daily Points, Validator Status)
- ✅ **Daily Check-in** - Automated daily check-ins (24-hour interval)
- 🌐 **Proxy Support** - Optional proxy rotation for multiple accounts
- 🎨 **Colorful Console** - Easy-to-read colored output
- ⚡ **Multi-Account** - Support for unlimited accounts

## Prerequisites

- Python 3.7 or higher
- Active Namso Network accounts
- Valid email access for OTP verification

## Installation

1. Clone this repository:
```bash
git clone https://github.com/febriyan9346/Namso-Auto-Bot.git
cd Namso-Auto-Bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure your accounts and proxies (see Configuration section)

## Configuration

### accounts.txt

Add your Namso accounts in the following format (one per line):
```
email@example.com:password123
another@example.com:pass456
```

### proxy.txt (Optional)

Add your proxies in the following format (one per line):
```
http://username:password@ip:port
http://ip:port
socks5://username:password@ip:port
```

**Note:** Each account will be assigned to a proxy in order (Account 1 → Proxy 1, Account 2 → Proxy 2, etc.)

## Usage

1. Run the bot:
```bash
python bot.py
```

2. Choose your mode:
   - **Option 1**: Run with proxy (requires proxy.txt)
   - **Option 2**: Run without proxy (direct connection)

3. Enter OTP codes when prompted for each account

4. The bot will start automatic farming and monitoring

## Bot Intervals

- **Farming Interval**: 60 seconds (1 minute)
- **Check-in Interval**: 86400 seconds (24 hours)

You can modify these values in the `bot.py` file:
```python
FARM_INTERVAL = 60       # Farming interval in seconds
CHECKIN_INTERVAL = 86400 # Check-in interval in seconds
```

## Console Output

The bot displays real-time information with color-coded status:

- 🟢 **Green**: Successful operations (Online, Login Success)
- 🔴 **Red**: Errors or failures (Token Expired, Mining Stopped)
- 🟡 **Yellow**: Warnings or pending actions (Rate Limit, OTP Request)
- 🔵 **Cyan**: Information headers and timestamps
- ⚪ **White**: Account identifiers

### Status Indicators

- **Online**: Mining is active and working properly
- **Rate Limit (429)**: Too many requests, temporary cooldown
- **Server Error (5xx)**: Namso server issues
- **CONNECTION ERROR**: Network connectivity issues
- **MINING STOPPED**: Mining halted (check account status)

## Features Breakdown

### 1. Dashboard Login
- Validates credentials
- Sends OTP to registered email
- Authenticates with OTP code
- Maintains session for monitoring

### 2. Extension Authentication
- Automatic token generation
- Bearer token authorization
- Auto-refresh on expiration
- Seamless reconnection

### 3. Farming Operations
- Health check pings
- Task submission
- Error handling and retry logic
- Automatic recovery from failures

### 4. Monitoring Dashboard
- Real-time SHARES tracking
- Daily points accumulation
- Validator status display
- Per-account statistics

## Troubleshooting

### OTP Not Received
- Check spam/junk folder
- Ensure email is correct in accounts.txt
- Wait a few minutes and try again

### Token Expired Errors
- Bot automatically refreshes tokens
- If persistent, check account credentials
- Verify account is not banned

### Proxy Connection Issues
- Verify proxy format is correct
- Test proxy independently
- Try without proxy (Option 2)

### Mining Stopped
- Check account status on Namso dashboard
- Verify validator requirements are met
- Review account activity limits

## Security Notes

- ⚠️ Keep `accounts.txt` and `proxy.txt` private
- ⚠️ Never share your credentials or tokens
- ⚠️ Use strong, unique passwords
- ⚠️ Consider using application-specific passwords

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The author is not responsible for any account actions, bans, or losses incurred from using this bot. Always follow Namso Network's terms of service.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

If you encounter issues or have questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Provide detailed error logs when reporting

## Changelog

### Version 1.0.0
- Initial release
- Multi-account support
- Proxy integration
- Auto token refresh
- Real-time monitoring
- Daily check-in automation

---

**Star ⭐ this repository if you find it helpful!**