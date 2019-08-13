import requests
from datetime import datetime, timezone
import time
import subprocess
import os
import shutil


def get_token():
    params = {"grant_type": "client_credentials"}
    r_token = requests.post("https://" + OAUTH_KEY + ":" + OAUTH_SECRET + "@bitbucket.org/site/oauth2/access_token", params)
    data = r_token.json()
    return data['access_token']


def get_branches(access_token):
    repo_names = []
    url = "https://api.bitbucket.org/2.0/repositories/" + USER + "?access_token=" + access_token + "&pagelen=100"
    ignored_branch = ["develop", "master", "release/"]
    while True:
        r = requests.get(url=url)
        data = r.json()

        for repo in data["values"]:
            repo_names.append(repo["slug"])

        if "next" in data:
            url = data["next"]
        else:
            break

    try:
        shutil.rmtree(repos_dir)
    except Exception as e:
        print(e)

    os.mkdir(repos_dir)

    skip_repo = []

    for repo_name in repo_names:
        if repo_name in skip_repo:
            continue
        time.sleep(3)
        branch_names = []
        url_branch = "https://api.bitbucket.org/2.0/repositories/" + USER + "/" + repo_name + "/refs/branches?access_token=" + access_token + "&pagelen=100&next="
        while True:
            r = requests.get(url=url_branch)
            data = r.json()

            for branch in data["values"]:
                flag = 0
                for ign in ignored_branch:
                    if ign in branch["name"]:
                        flag = 1
                if flag == 0:
                    branch_names.append(branch["name"])

            if "next" in data:
                url_branch = data["next"]
            else:
                break

        for branch_name in branch_names:
            url_commit = "https://api.bitbucket.org/2.0/repositories/" + USER + "/" + repo_name + "/commits/" + branch_name + "?access_token=" + access_token + "&pagelen=1"

            r = requests.get(url=url_commit)
            commit = r.json()
            commit_time = datetime.strptime(commit["values"][0]["date"].replace(":", ""), "%Y-%m-%dT%H%M%S%z")
            commit_time_epoch = commit_time.timestamp()
            current_time = datetime.now(tz=timezone.utc)
            current_time_epoch = current_time.timestamp()
            if (commit_time_epoch + 15 * 86400) < current_time_epoch:
                print(repo_name + ":" + branch_name)
                f = open(repos_dir + repo_name + ".txt", "a")
                f.write(branch_name + "\n")


def delete_branches(access_token):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(repos_dir):
        for file in f:
            if '.txt' in file:
                files.append(os.path.join(r, file))
    for file in files:
        repo_name = file.replace("repos/", "").replace(".txt", "")
        print(repo_name + "------------------")
        f = open(file, "r")
        for branch_name in f:
            branch_name = branch_name.replace("\n", "")
            subprocess.call("curl -X DELETE 'https://bitbucket.org/!api/2.0/repositories/" + USER + "/" + repo_name + "/refs/branches/" + branch_name + "?access_token=" + access_token + "'", shell=True)
            print(repo_name + "/" + branch_name)
            time.sleep(1)


USER = "<bitbucket_username>"
repos_dir = "repos/"
OAUTH_KEY = "<oauth_key>"
OAUTH_SECRET = "<oauth_secret>"
ACCESS_TOKEN = get_token()
get_branches(access_token=ACCESS_TOKEN)
delete_branches(access_token=ACCESS_TOKEN)
