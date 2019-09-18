Setting up Python worker nodes
======


First install python 3.7

```bash
sudo yum install -y python37
```

Then install `pip`
```bash
curl -O https://bootstrap.pypa.io/get-pip.py

python3 get-pip.py --user
```

Then install aws tools and pulsar client
```bash
pip install awscli pulsar-client --user
```

Install boto, boto3, smart-open
```bash
pip install smart-open --user
```