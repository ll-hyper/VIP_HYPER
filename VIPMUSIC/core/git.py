import asyncio
import shlex
import os
from typing import Tuple

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

import config

from ..logging import LOGGER

loop = asyncio.get_event_loop_policy().get_event_loop()


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return loop.run_until_complete(install_requirements())


def git():
    REPO_LINK = config.UPSTREAM_REPO

    # GitHub Username aur Token ko environment variables se fetch karo
    GIT_USERNAME = os.getenv("GIT_USERNAME", "vishalpandeynkp1")
    GIT_TOKEN = os.getenv("GIT_TOKEN", None)

    if GIT_TOKEN:
        TEMP_REPO = REPO_LINK.replace("https://", "")
        UPSTREAM_REPO = f"https://{GIT_USERNAME}:{GIT_TOKEN}@{TEMP_REPO}"
    else:
        UPSTREAM_REPO = config.UPSTREAM_REPO

    try:
        repo = Repo()
        LOGGER(__name__).info(f"Git Client Found [VPS DEPLOYER]")
    except GitCommandError:
        LOGGER(__name__).info(f"Invalid Git Command")
    except InvalidGitRepositoryError:
        repo = Repo.init()
        if "origin" in repo.remotes:
            origin = repo.remote("origin")
        else:
            origin = repo.create_remote("origin", UPSTREAM_REPO)
        origin.fetch()
        repo.create_head(
            config.UPSTREAM_BRANCH,
            origin.refs[config.UPSTREAM_BRANCH],
        )
        repo.heads[config.UPSTREAM_BRANCH].set_tracking_branch(
            origin.refs[config.UPSTREAM_BRANCH]
        )
        repo.heads[config.UPSTREAM_BRANCH].checkout(True)

        try:
            repo.create_remote("origin", config.UPSTREAM_REPO)
        except BaseException:
            pass

    nrs = repo.remote("origin")
    nrs.fetch(config.UPSTREAM_BRANCH)
    try:
        nrs.pull(config.UPSTREAM_BRANCH)
    except GitCommandError:
        repo.git.reset("--hard", "FETCH_HEAD")
    install_req("pip3 install --no-cache-dir -r requirements.txt")
    LOGGER(__name__).info(f"Fetched Updates from: {REPO_LINK}")
