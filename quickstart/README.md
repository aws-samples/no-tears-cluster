# Cloud9 COVID-19 Cluster

To get started, clone this repo locally:

```bash
git clone https://github.com/sean-smith/covid19hpc
cd covid19hpc/
```

Edit the Makefile to put in your bucket and region:

```bash
s3_bucket=seaam
region=us-east-1
```

Then create it:

```bash
make create
```
