# On Digital Ocean \(Ubuntu\)

{% hint style="info" %}
The instructions have been tested on `Digital Ocean Droplet ($5)`
{% endhint %}

## Create a new droplet

* Launch a new droplet

![](../.gitbook/assets/digitalocean_launch_droplet.png)

* Select image distribution 

![](../.gitbook/assets/dg_choose_ditribution.png)

* Select droplet type
  * For testing out Airbyte, a `$20/month` droplet is likely sufficient.
  * For long-running Airbyte installations, we recommend a `$40/month` instance.

![](../.gitbook/assets/dg_droplet_type.png)

* `Region` 
  * You can choose datacenter close to you
* `Authentication`
  * Password
* `Create Droplet`

![](../.gitbook/assets/dg_droplet_creating.png)

* Wait for the droplet to become `Running`

## Install environment

{% hint style="info" %}
Note: The following commands will be entered either on your local terminal or in your ssh session on the instance terminal. The comments above each command block will indicate where to enter the commands.
{% endhint %}

* Connect to your instance

* `Click on Console`

![](../.gitbook/assets/dg_console.png)

* Install `docker`

```bash
# In your ssh session on the instance terminal
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker $USER
```

* Install `docker-compose`

```bash
# In your ssh session on the instance terminal
sudo wget https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m) -O /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```
## Install & start Airbyte

* Connect to your instance

* `Click on Console`

![](../.gitbook/assets/dg_console.png)

* Install Airbyte

```bash
# In your ssh session on the instance terminal
mkdir airbyte && cd airbyte
wget https://raw.githubusercontent.com/airbytehq/airbyte/master/{.env,docker-compose.yaml}
docker-compose up -d
```

## Troubleshooting

If you encounter any issues, just connect to our [Slack](https://slack.airbyte.io). Our community will help! We also have a [FAQ](../troubleshooting/on-deploying.md) section in our docs for common problems.
