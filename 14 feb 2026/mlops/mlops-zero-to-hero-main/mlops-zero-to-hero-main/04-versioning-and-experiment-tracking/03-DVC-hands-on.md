# Learn DVC using a project

Please refer to the below repository for this lecture.

https://github.com/iam-veeramalla/Wine-Prediction-Model

## commands used
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install dvc dvc_s3
dvc init
dvc add data/winse_sample.csv
ls data/  #win_sample.csv(stored in s3) wine_sample.csv.dvc (checksum file stored in github)

#create an s3 bucket and add as remote for dvc
#configure aws cli cred locally.

dvc remote add -d wineremote s3://bucketname/foldername   ---> saved to .dvc/config --> should be saved to git.
dvc push

#saved to s3 as bucketname/foldername/md5/version_count/checksumvalueasfilename
```
