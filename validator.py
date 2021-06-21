import atexit
import json
from typing import Dict
import consts
import subprocess
import time


class ValidatorHelper:
    def __init__(self, project: str):
        self.project = project

    def dump_config(self, cfg: Dict[str, str]) -> None:
        raw = json.dumps(cfg)
        with open(
            consts.VALIDATOR_CONFIG.format(project=self.project),
            "w"
        ) as config:
            config.write(raw)

    def spawn(self) -> subprocess.Popen[bytes]:
        p = subprocess.Popen(
            ["yarn", "run", "dev"],
            cwd=self.project,
            bufsize=1,
        )

        atexit.register(lambda: p.terminate())

        time.sleep(30)
        return p
