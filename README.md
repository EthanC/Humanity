# Humanity

Humanity is a [GetFiveDollars.com](https://getfivedollars.com/) deal watcher that reports new deals via Discord.

> **What’s happening?**
> 
> It’s Black Friday, and this year it’s Cards Against Humanity's turn to experience the deals! We’re giving you $5, and you’re giving us the deals! AHAHAHAHAHA!
> 
> Every 20 minutes, we’ll reveal something we want, along with simple written requirements for how to give it to us. Follow the rules before the slots run out and you’ll get $5.

<p align="center">
    <img src="https://i.imgur.com/f9hmgRF.png" draggable="false">
</p>

## Usage

Open `config_example.json` and provide the configurable values, then save and rename the file to `config.json`.

Humanity is designed to be ran using a task scheduler, such as [cron](https://crontab.guru/).

```
python humanity.py
```
