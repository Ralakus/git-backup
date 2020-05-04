
from rdk import RDK
from rdk import RC

import os
import git
import time
import shutil

class BackupServer:
    # The amount of time in seconds between backups
    CV_backup_interval = 10
    # The file to read the repos to backup, must be a file with each ssh link separated by newlines
    CV_repo_file = "backup_list.txt"
    # The directory to clone each backup to
    CV_backup_dir = "backups/"

    def __init__(self):
        self.IV_repos = []
        self.IV_repos_to_be_cloned = []
        self.IV_repos_to_be_removed = []

    def loadReposFromFile(self):
        call_result = {}
        debug_data = []
        return_msg = 'BackupServer:loadReposFromFile '
        repos = []
        repos_to_be_cloned = []
        repos_to_be_removed = []

        ## Move cloned repos into repos to maintain and clear the to_be lists
        for repo in self.IV_repos_to_be_cloned:
            self.IV_repos.append(repo)
        self.IV_repos_to_be_cloned = []
        self.IV_repos_to_be_removed = []
        ##</end> Move cloned repos into repos to maintain and clear the to_be lists

        ## Try to open repo file
        try:
            file = open(self.CV_repo_file)
            for line in file:
                if line is not "" and not line.startswith("#"):
                    repos.append(line)
            file.close()
        except:
            return_msg += "failed to open file {}".format(self.CV_repo_file)
            return { RDK.success: RC.file_failure, RDK.return_msg: return_msg, RDK.debug_data: debug_data }
        ##</end> Try to open repo file

        # Repos that aren't removed or to be cloned
        non_delta_repos = []

        ## Sort delta repositories
        for repo in repos:
            if not repo in self.IV_repos:
                repos_to_be_cloned.append(repo)
            else:
                non_delta_repos.append(repo)
        
        for repo in self.IV_repos:
            if not repo in repos:
                repos_to_be_removed.append(repo)
            else:
                non_delta_repos.append(repo)
        ##</end> Sort delta repositories

        self.IV_repos = non_delta_repos
        self.IV_repos_to_be_cloned = repos_to_be_cloned
        self.IV_repos_to_be_removed = repos_to_be_removed

        return { RDK.success: RC.success, RDK.return_msg: return_msg, RDK.debug_data: debug_data }

    def backup(self):
        call_result = {}
        debug_data = []
        return_msg = 'BackupServer:backup '

        if not os.path.exists(self.CV_backup_dir):
            os.makedirs(self.CV_backup_dir)

        for cloned in self.IV_repos_to_be_cloned:
            name = os.path.basename(cloned)
            path = "{}/{}".format(self.CV_backup_dir, name)

            if not os.path.exists(path):
                git.Repo.clone_from(cloned, path)

        for pull in self.IV_repos:
            name = os.path.basename(pull)
            path = "{}/{}".format(self.CV_backup_dir, name)

            repo = git.Repo(path)
            origin = repo.remotes.origin
            origin.pull()

        for removed in self.IV_repos_to_be_removed:
            name = os.path.basename(removed)
            path = "{}/{}".format(self.CV_backup_dir, name)

            # Reason to ignore error is so it doesn't throw an exception if the directory doesn't exist
            shutil.rmtree(path, ignore_errors=True)

        return { RDK.success: RC.success, RDK.return_msg: return_msg, RDK.debug_data: debug_data }

    def run(self):
        call_result = {}
        debug_data = []
        return_msg = 'BackupServer:run '
        first_run = True

        while True:
            if first_run:
                first_run = False
            else:
                time.sleep(self.CV_backup_interval)

            print("Loading repo file...")
            call_result = self.loadReposFromFile()
            if call_result[RDK.success] is not RC.success:
                print("Error, failed to load and parse {}".format(self.CV_repo_file))
                continue

            print("Updating backups...")
            call_result = self.backup()
            if call_result[RDK.success] is not RC.success:
                print("Error, failed to backup repos")
                continue

            print("Done")

        return { RDK.success: RC.success, RDK.return_msg: return_msg, RDK.debug_data: debug_data }

backup_server = BackupServer()
backup_server.run()
    