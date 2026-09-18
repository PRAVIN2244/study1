# What is DVC?

Think of DVC (Data Version Control) as Git for your data.

Git works great for: code and small text files.

But Git cannot handle:

- Large datasets
- Model files
- Data stored in cloud storage
- This is where DVC helps.

DVC lets you:

- Track versions of datasets
- Store large files outside Git (S3, GCS, Azure, local storage)
- Keep your Git repo clean and lightweight
- Reproduce your ML project anytime

### Wine Prediction Example

Imagine you're building a simple Wine Quality Prediction ML model.

You have:

- A CSV file → wine_data_sample.csv
- A training script → train.py
- A Git repo

Your dataset may change over time:

- You add more rows
- You clean the data
- You update features

DVC allows you to version these dataset changes without storing the actual data inside Git.

Without DVC -> Your CSV sits in your repo → Git becomes slow & heavy.

With DVC -> Git stores only a small metadata file:

- wine_data_sample.csv.dvc
- Actual data is stored in: `S3 bucket` or any external storage

You pull/push data similar to git pull / git push.

### How DVC Works (Very Simple Flow)

Add your dataset to DVC

`dvc add wine_data_sample.csv`

Commit the .dvc file to Git

`git add wine_data_sample.csv.dvc`
`git commit -m "Track dataset with DVC"`

Configure remote storage (e.g., S3)

`dvc remote add -d myremote s3://mybucket/dvcstore`

Push data to S3

`dvc push`

Anyone with your Git repo simply runs:

`dvc pull`

…and they get the exact same dataset version.