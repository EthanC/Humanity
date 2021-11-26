import json
from datetime import datetime
from sys import exit, stderr
from typing import Any, Dict, Optional

from loguru import logger
from notifiers.logging import NotificationHandler

from utils import Utility


class Humanity:
    """
    GetFiveDollars.com deal watcher that reports new deals via Discord.

    https://github.com/EthanC/Humanity
    """

    def Initialize(self: Any) -> None:
        """Initialize Humanity and begin primary functionality."""

        logger.info("Humanity")
        logger.info("https://github.com/EthanC/Humanity")

        self.config: Dict[str, Any] = Humanity.LoadConfig(self)

        Humanity.SetupLogging(self)

        self.changed: bool = False
        self.history: Dict[str, Any] = Humanity.LoadHistory(self)

        Humanity.ProcessDeals(self)

        if self.changed is True:
            Humanity.SaveHistory(self)

        logger.success("Finished processing deals")

    def LoadConfig(self: Any) -> Dict[str, Any]:
        """Load the configuration values specified in config.json"""

        try:
            with open("config.json", "r") as file:
                config: Dict[str, Any] = json.loads(file.read())
        except Exception as e:
            logger.critical(f"Failed to load configuration, {e}")

            exit(1)

        logger.success("Loaded configuration")

        return config

    def SetupLogging(self: Any) -> None:
        """Setup the logger using the configured values."""

        settings: Dict[str, Any] = self.config["logging"]

        if (level := settings["severity"].upper()) != "DEBUG":
            try:
                logger.remove()
                logger.add(stderr, level=level)

                logger.success(f"Set logger severity to {level}")
            except Exception as e:
                # Fallback to default logger settings
                logger.add(stderr, level="DEBUG")

                logger.error(f"Failed to set logger severity to {level}, {e}")

        if settings["discord"]["enable"] is True:
            level: str = settings["discord"]["severity"].upper()
            url: str = settings["discord"]["webhookUrl"]

            try:
                # Notifiers library does not natively support Discord at
                # this time. However, Discord will accept payloads which
                # are compatible with Slack by appending to the url.
                # https://github.com/liiight/notifiers/issues/400
                handler: NotificationHandler = NotificationHandler(
                    "slack", defaults={"webhook_url": f"{url}/slack"}
                )

                logger.add(
                    handler,
                    level=level,
                    format="```\n{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}\n```",
                )

                logger.success(f"Enabled logging to Discord with severity {level}")
            except Exception as e:
                logger.error(f"Failed to enable logging to Discord, {e}")

    def LoadHistory(self: Any) -> Dict[str, Any]:
        """Load the last seen deals specified in history.json"""

        try:
            with open("history.json", "r") as file:
                history: Dict[str, Any] = json.loads(file.read())
        except FileNotFoundError:
            history: Dict[str, Any] = {}
            self.changed = True

            logger.success("Deal history not found, created empty file")
        except Exception as e:
            logger.critical(f"Failed to load deal history, {e}")

            exit(1)

        logger.success("Loaded deal history")

        return history

    def ProcessDeals(self: Any) -> None:
        """Get the current deals and determine whether or not they are new."""

        data: Optional[Dict[str, Any]] = Utility.GET(
            self, "https://www.getfivedollars.com/feed.json"
        )

        if data is None:
            logger.debug("Failed to process deals, response is empty")

            return

        for deal in data["stunts"]:
            shortName: str = deal["shortName"]
            closed: bool = deal["closed"]

            deal["nextTime"] = data["nextStuntRevealTime"]

            if self.history.get(shortName) is not None:
                continue

            success: bool = Humanity.Notify(self, Humanity.BuildEmbed(self, deal))

            if success is True:
                logger.info(f"Notified for deal {shortName}")

                self.history[shortName] = {"seen": True, "closed": closed}
                self.changed = True

    def BuildEmbed(self: Any, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Discord Embed object containing the deal information."""

        payload: Dict[str, Any] = {}

        payload["title"] = deal["title"]
        payload["description"] = Utility.ConvertHTML(
            self,
            deal["description"] + deal["form"]["description"],
            4096,
            # Exclude common headings
            ["<h2>Requirements</h2>", "<h4>Requirements</h4>", "<h4>Submission</h4>"],
        )
        payload["color"] = (
            int("66BB6A", base=16)
            if deal["closed"] is False
            else int("66BB6A", base=16)
        )
        payload["fields"] = []

        payload["fields"].append(
            {
                "name": "Deal Start",
                "value": Utility.ConvertTimestamp(self, deal["startTime"]),
                "inline": True,
            }
        )
        payload["fields"].append(
            {
                "name": "Next Deal",
                "value": Utility.ConvertTimestamp(self, deal["nextTime"]),
                "inline": True,
            }
        )

        if deal.get("form") is not None:
            for entry in deal["form"]["fields"][:25]:
                if (hint := entry.get("hint")) is None:
                    continue
                # Exclude common fields
                elif (label := entry.get("label")) in [
                    "Your mobile phone number",
                    "Your email",
                ]:
                    continue

                payload["fields"].append(
                    {
                        "name": label,
                        "value": Utility.ConvertHTML(self, hint, 1024),
                        "inline": False,
                    }
                )

        for entry in deal["media"]:
            if entry["contentType"] == "image/jpeg":
                payload["image"] = entry["url"]

                break

        return payload

    def Notify(self: Any, data: Dict[str, Any]) -> bool:
        """Report deal updates to the configured Discord webhook."""

        settings: Dict[str, Any] = self.config["discord"]

        payload: Dict[str, Any] = {
            "username": settings["username"],
            "avatar_url": settings["avatarUrl"],
            "embeds": [
                {
                    "title": data["title"],
                    "description": data["description"],
                    "url": "https://getfivedollars.com/",
                    "timestamp": datetime.utcnow().isoformat(),
                    "color": data["color"],
                    "footer": {
                        "text": "Humanity",
                        "icon_url": "https://i.imgur.com/x5iJkUG.png",
                    },
                    "fields": data["fields"],
                }
            ],
        }

        if (img := data.get("image")) is not None:
            payload["embeds"][0]["image"] = {"url": img}

        return Utility.POST(self, settings["webhookUrl"], payload)

    def SaveHistory(self: Any) -> None:
        """Save the latest deals to history.json"""

        if self.config.get("debug") is True:
            logger.warning("Debug is active, not saving deal history")

            return

        try:
            with open("history.json", "w+") as file:
                file.write(json.dumps(self.history, indent=4))
        except Exception as e:
            logger.critical(f"Failed to save deal history, {e}")

            exit(1)

        logger.success("Saved deal history")


if __name__ == "__main__":
    try:
        Humanity.Initialize(Humanity)
    except KeyboardInterrupt:
        exit()
