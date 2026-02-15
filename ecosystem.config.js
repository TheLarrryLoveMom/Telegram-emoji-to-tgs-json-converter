module.exports = {
  apps: [
    {
      name: "emoji-export-bot",
      script: "bot/main.py",
      interpreter: "python",
      cwd: __dirname,
      env: {
        PYTHONUNBUFFERED: "1"
      }
    }
  ]
};