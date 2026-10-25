# Banking Management System — Python, Docker, Jenkins and Kubernetes

A learning/demo Flask app with account creation, deposits, withdrawals, balance lookup and transaction history.

## Important limitations
- Demo only. Do not use real banking/customer data.
- SQLite + Kubernetes `emptyDir` is for learning only: data is lost when the pod is replaced and multiple replicas do not share a database. For a stronger project, use PostgreSQL/MySQL with persistent storage and backups.
- The sample APIs do not implement real authentication or authorization. Add proper security before any non-demo use.
- Jenkins agent must have Python 3, Docker CLI/daemon, `kubectl`, and secure Kubernetes credentials.

## Run locally
```bash
python3 -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Run with Docker
```bash
docker build -t banking-management:local .
docker run --rm -p 5000:5000 -v banking-data:/data banking-management:local
```
Open http://localhost:5000

## Kubernetes manual deployment
1. Build and push the image:
```bash
docker build -t YOUR_DOCKERHUB_USERNAME/banking-management:v1 .
docker push YOUR_DOCKERHUB_USERNAME/banking-management:v1
```
2. In `k8s/deployment.yaml`, replace `IMAGE_PLACEHOLDER` with that image and tag.
3. Apply:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods,svc -n banking
```
For Minikube, run `minikube service banking-service -n banking`. For a remote cluster, ensure NodePort access is allowed.

## Jenkins setup
1. Push this project to GitHub or another Git server.
2. Create a Jenkins Pipeline job for the repository.
3. Add a Jenkins username/password credential with ID `dockerhub-creds`; use a Docker Hub access token as the password.
4. Replace `IMAGE_NAME` in `Jenkinsfile` with your Docker Hub repository.
5. Ensure the Jenkins agent has Docker access, `kubectl`, and narrowly scoped credentials for the target Kubernetes cluster.
6. Run the pipeline. It checks Python syntax, builds and pushes the image, deploys, and waits for rollout.

## API examples
Create account:
```bash
curl -X POST http://localhost:5000/api/accounts -H "Content-Type: application/json" -d "{\"name\":\"Demo User\"}"
```
Deposit:
```bash
curl -X POST http://localhost:5000/api/deposit -H "Content-Type: application/json" -d "{\"account_no\":1,\"amount\":500}"
```
Balance:
```bash
curl http://localhost:5000/api/accounts/1
```
