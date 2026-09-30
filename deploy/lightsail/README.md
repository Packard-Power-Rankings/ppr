# AWS Lightsail Deployment

This deployment runs Packard Power Rankings on one Ubuntu Lightsail instance. Caddy is the only public container: it obtains and renews HTTPS certificates, serves the compiled React application, and sends `/api` requests to FastAPI. MongoDB and Redis have no host ports.

```text
Browser -> Caddy :80/:443 -> React files
                         `-> /api -> FastAPI -> MongoDB
                                             `-> Redis -> ARQ worker
```

The production stack is defined in [`../../docker-compose.lightsail.yml`](../../docker-compose.lightsail.yml). Local development continues to use `docker-compose.yml`.

## 1. Create the Instance

In AWS Lightsail:

1. Create an Ubuntu 24.04 LTS Linux instance.
2. Choose at least the 2 GB plan for evaluation or the 4 GB plan for production use.
3. Create and attach a static IP to the instance.
4. In the instance networking firewall, allow TCP `80` and `443` from all addresses.
5. Keep TCP `22` restricted to your own IP whenever possible.
6. Create an `A` record such as `rankings.example.com` pointing to the static IP.

Wait for public DNS to resolve before starting the application. Caddy needs the domain to reach the instance on ports 80 and 443 before it can obtain a certificate.

## 2. Install Docker

Connect to the instance, clone this repository, and run the included Ubuntu bootstrap script:

```bash
git clone <repository-url> ppr
cd ppr
sudo ./deploy/lightsail/bootstrap-ubuntu.sh
```

Log out and reconnect after the script completes. Confirm that Docker and Compose are available:

```bash
docker version
docker compose version
```

The bootstrap installs Docker from Docker's official Ubuntu package repository, enables the Docker service, installs Git and `jq`, and adds the login user to the `docker` group.

## 3. Configure Production Secrets

Create the ignored production environment file with independent generated secrets:

```bash
make lightsail-init DOMAIN=rankings.example.com
```

The command uses `openssl rand -hex 32` for the MongoDB password, Redis password, setup token, and JWT signing key, and writes the file with owner-only permissions. To rotate a value later, generate a new URL-safe secret with:

```bash
openssl rand -hex 32
```

The generated domain settings for `rankings.example.com` are:

````env
DOMAIN=packardpowerrankings.com
CORS_ORIGINS=packardpowerrankings.com/
ALLOWED_HOSTS=packardpowerrankings.com/

Do not put `https://` in `DOMAIN` or `ALLOWED_HOSTS`. Passwords should use the documented hexadecimal format because `MONGO_PASS` is embedded in a MongoDB connection URI.

Validate the file and rendered Compose configuration without starting anything:

```bash
make lightsail-check
````

## 4. Deploy

Build and start the stack:

```bash
make lightsail-up
```

The initial image build can take several minutes on the 2 GB plan. Check container health and logs:

```bash
make lightsail-status
make lightsail-logs
```

After Caddy obtains the certificate, verify the public endpoint:

```bash
make lightsail-health
```

The application and API documentation are available at:

```text
https://packardpowerrankings.com/
https://packardpowerrankings.com/api/docs
```

## 5. Create the First Admin

Create the single initial admin from the Lightsail shell. This avoids putting the password in shell history:

```bash
set -a
source .env/production
set +a
read -r -p "Admin username: " ADMIN_USERNAME
read -r -s -p "Admin password: " ADMIN_PASSWORD
printf '\n'
jq -n --arg username "$ADMIN_USERNAME" --arg password "$ADMIN_PASSWORD" \
  '{username: $username, password: $password}' |
  curl --fail --show-error --silent \
    -X POST "https://$DOMAIN/api/setup/admin/" \
    -H "X-Setup-Token: $SETUP_TOKEN" \
    -H 'Content-Type: application/json' \
    --data-binary @-
printf '\n'
unset ADMIN_PASSWORD
```

After the account is created, replace `SETUP_TOKEN` with a new random value and apply it:

```bash
make lightsail-up
```

The endpoint also refuses to create a second account, but rotating the setup token removes a reusable bootstrap credential.

## Routine Operations

```bash
make lightsail-status    # container state and health
make lightsail-logs      # follow bounded container logs
make lightsail-health    # public HTTPS health check
make lightsail-restart   # restart all containers
make lightsail-down      # stop containers; keep data volumes
make lightsail-up        # rebuild and reconcile the stack
```

To deploy a new revision:

```bash
git pull --ff-only
make lightsail-up
make lightsail-health
```

Do not run `docker compose down --volumes`. The `mongo_data`, `redis_data`, `archive_data`, `caddy_data`, and `caddy_config` volumes contain persistent state.

## Backups

Create a compressed logical MongoDB backup before deployments and data maintenance:

```bash
make lightsail-backup
```

MongoDB and generated season archive backups are written with owner-only permissions under the ignored `backups/` directory. Copy both files to storage outside the instance. A disk snapshot alone is not a substitute for a tested restore.

To restore a backup, stop application writes first and deliberately run `mongorestore --drop`:

```bash
make lightsail-down
docker compose --env-file .env/production -f docker-compose.lightsail.yml up -d --wait db
cat backups/ppr-mongodb-YYYYMMDDTHHMMSSZ.archive.gz |
  docker compose --env-file .env/production -f docker-compose.lightsail.yml \
    exec -T db sh -c \
    'exec mongorestore --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip --drop'
make lightsail-up
```

The restore command replaces collections present in the archive. Take another backup before using it.

## Security Notes

- Only Caddy publishes host ports. Never add public MongoDB or Redis ports.
- Keep `.env/production` out of Git and readable only by the deployment user (`chmod 600 .env/production`).
- Enable Lightsail automatic snapshots and AWS billing alerts.
- Apply Ubuntu security updates regularly and rebuild images after dependency updates.
- Review `make lightsail-logs` after each deployment; Docker log rotation is capped at three 10 MB files per container.
- The backend container runs as a non-root user. MongoDB and Redis authenticate with independently generated credentials.
- Use the application smoke test against local or disposable data, not the production database; its fixture workflows intentionally write and delete records.

## Troubleshooting

**Caddy cannot obtain a certificate:** confirm the DNS `A` record points to the attached static IP and the Lightsail firewall allows inbound TCP 80 and 443.

**A container remains unhealthy:** run `make lightsail-status`, then `make lightsail-logs`. Backend startup waits for authenticated MongoDB and Redis health checks.

**The site loads but API requests fail:** confirm `DOMAIN`, `CORS_ORIGINS`, and `ALLOWED_HOSTS` use the same public hostname, then rebuild with `make lightsail-up`.

**The build runs out of memory:** use the 4 GB Lightsail plan, or add temporary swap for the image build. The running stack should still be monitored before attempting a smaller plan.
