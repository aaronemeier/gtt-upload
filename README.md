# gtt-upload
Small utility for automated Gitlab time tracking reports to OneDrive.

## Preparation
- Register a new app on https://apps.dev.microsoft.com
  - Generate new application secret/password 
  - Set Redirect URI to http://localhost:8080/
- Copy `config/config.dist.sh` to `config/config.sh` and set it up according to your needs:
  - GITLAB_URL: "http://example.gitlab.com/api/v4/"
  - GITLAB_TOKEN: Personal Access Token from Gitlab
  - GITLAB_PROJECT: Gitlab workspace (e.g. "Group/Project/Repository")
  - GTT_CLIENT_SECRET: Secret from the apps registration for OneDrive upload
  - GTT_CLIENT_ID: Specify a client Id for authentication for OneDrive upload
  - ONEDRIVE_FILE: Set the filename for OneDrive Timetracking.xlsx
- Copy `config/users.dist.csv`to `config/users.csv` and setup user mapping: This will replace usernames in the report
- Install and setup docker


## Run
At first, we have to run interactively to authenticate
```bash
docker build --rm -t gtt-upload:latest ./ && docker run  -v $PWD/.root/:/root/ --env-file config/config.cfg -it gtt-upload:latest
```
After that the session has been saved and we can upload without any interaction.  
We can use the following command to run it via cron and we don't have to rebuild the image everytime:
```bash
docker run  -v $PWD/.root/:/root/ --env-file config/config.cfg gtt-upload:latest
```