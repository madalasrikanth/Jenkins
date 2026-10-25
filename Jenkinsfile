pipeline {
    agent any
    environment {
        // Replace with your Docker Hub username/repository.
        IMAGE_NAME = 'dilli05/dilli07'
        IMAGE_TAG = "sla"
        K8S_NAMESPACE = 'banking'
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Python syntax check') {
            steps { sh 'python3 -m py_compile app.py' }
        }
        stage('Build Docker image') {
            steps { sh 'docker build -t dilli05/dilli07:sla .' }
        }
        stage('Push image to Docker Hub') {
            steps {
                // Create Jenkins credential ID dockerhub-creds:
                // Username with password; use a Docker Hub access token as password.
                withCredentials([usernamePassword(credentialsId: 'dilli05',
                    usernameVariable: 'dilli05/dilli07', passwordVariable: 'dckr_pat_twOp0dNgEemRwGgbeDkHgQgo1NY')]) {
                    sh '''
                      echo "dckr_pat_twOp0dNgEemRwGgbeDkHgQgo1NY" | docker login -u "dilli05/dilli07" --password-stdin
                      docker push "dilli05/dilli07:sla"
                      docker logout
                    '''
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                // Jenkins agent needs kubectl and secured cluster credentials.
                sh '''
                  sed "s|IMAGE_PLACEHOLDER|$IMAGE_NAME:$IMAGE_TAG|g" k8s/deployment.yaml > /tmp/banking-deployment.yaml
                  kubectl apply -f k8s/namespace.yaml
                  kubectl apply -f /tmp/banking-deployment.yaml
                  kubectl rollout status deployment/banking-app -n "$K8S_NAMESPACE" --timeout=120s
                '''
            }
        }
    }
    post {
        always { echo 'Pipeline execution finished.' }
    }
}
