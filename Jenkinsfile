pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker compose down --rmi all --remove-orphans'
                sh 'docker compose up -d'
            }
        }

        stage('Verify Containers') {
            steps {
                sh 'docker compose ps'
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    for i in $(seq 1 15); do
                        if curl -f http://localhost/health; then
                            exit 0
                        fi
                        echo "Waiting for app to be ready... ($i/15)"
                        sleep 5
                    done
                    echo "Health check failed, dumping logs:"
                    docker compose logs
                    exit 1
                '''
            }
        }
    }

    post {
        success {
            echo 'Deployment successful!'
        }

        failure {
            echo 'Deployment failed!'
        }
    }
}
